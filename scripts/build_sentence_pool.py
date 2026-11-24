#!/usr/bin/env python3
"""
Usage:
    python build_sentence_pool.py build DIR [DIR ...]
    python build_sentence_pool.py sample N [SEED]
"""
import csv
import hashlib
import json
import logging
import random
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path

logging.getLogger("pypdf").setLevel(logging.ERROR)

OUT = Path("sentence_pool")
DOC_EXT = {".pdf", ".docx", ".txt"}
MIN_WORDS, MAX_WORDS = 3, 100

def read_pages(path):
    ext = path.suffix.lower()
    if ext == ".pdf":
        from pypdf import PdfReader
        return [(p.extract_text() or "") for p in PdfReader(str(path)).pages]
    if ext == ".docx":
        import docx
        d = docx.Document(str(path))
        parts = [p.text for p in d.paragraphs]
        for tbl in d.tables:
            for row in tbl.rows:
                cells = []
                for c in row.cells:
                    if c.text.strip() and c.text not in cells:
                        cells.append(c.text)
                parts.append("")
                parts.extend(cells)
        return ["\n".join(parts)]
    raw = path.read_bytes()
    for enc in ("utf-8-sig", "cp1250", "latin-1"):
        try:
            return [raw.decode(enc)]
        except UnicodeDecodeError:
            pass
    return [""]


PAGE_NUM = re.compile(r"^\s*(faqe\s*)?\d{1,4}\s*(/\s*\d{1,4})?\s*$", re.I)
STAGE = re.compile(r"^\s*\((?:[^()]{0,120})\)\s*$")
SPEAKER = re.compile(
    r"^((?:[A-ZÇËŠŽĆČ][a-zçëšžćčđ']+|[A-ZÇË]\.)(?:[ \-](?:[A-ZÇËŠŽĆČ][a-zçëšžćčđ']+|[A-ZÇË]\.)){1,3})"
    r"\s+[–—-]\s+(.*)$")


def normalize(text):
    text = unicodedata.normalize("NFC", text)
    text = text.replace(" ", " ").replace("­", "")
    return re.sub(r"[ \t]+", " ", text)


def repeated_lines(pages):
    if len(pages) < 4:
        return set()
    c = Counter()
    for p in pages:
        c.update({ln.strip() for ln in p.splitlines() if ln.strip()})
    return {ln for ln, n in c.items() if n >= max(3, 0.4 * len(pages)) and len(ln) < 120}


UC = "A-ZÇËŠŽĆČĐ"
SPEAKER_UPPER = re.compile(rf"^((?:[{UC}][{UC}'\-]+\.? ){{0,5}}[{UC}][{UC}'\-]+)\s*:\s*(.*)$")


def match_speaker(ln):
    m = SPEAKER.match(ln)
    if m and len(m.group(1).split()) <= 4:
        return m.group(1), m.group(2)
    m = SPEAKER_UPPER.match(ln)
    if m and len(m.group(1)) >= 5:
        return m.group(1).title(), m.group(2)
    return None


def join_lines(lines):
    paras, cur, speaker = [], "", None
    for ln in lines:
        ln = ln.strip()
        if not ln:
            if cur:
                paras.append((speaker, cur)); cur = ""
            continue
        m = match_speaker(ln)
        if m:
            if cur:
                paras.append((speaker, cur))
            speaker, cur = m
            continue
        if not cur:
            cur = ln
        elif cur.endswith("-") and not cur.endswith(" -"):
            prev = cur.rsplit(None, 1)[-1][:-1]
            cur = cur + ln if prev.isupper() else cur[:-1] + ln
        else:
            cur = cur + " " + ln
    if cur:
        paras.append((speaker, cur))
    return paras


TOKEN = re.compile(r"[A-Za-zÇËçë]+")


def repair_splits(par, vocab):
    par = re.sub(r"(\w) -(?=\w)", r"\1-", par)
    par = re.sub(r"(?<=\w) {2,}(?=\w)", " ", par)
    words = par.split(" ")
    out, i, fixed = [], 0, 0
    while i < len(words):
        a = words[i]
        if i + 1 < len(words):
            b = words[i + 1]
            ma, mb = re.fullmatch(r"(\W*)([A-Za-zÇËçë]+)", a), re.fullmatch(r"([A-Za-zÇËçë]+)(\W*)", b)
            if ma and mb:
                la, lb = ma.group(2).lower(), mb.group(1).lower()
                joined = la + lb
                if (vocab.get(joined, 0) >= 3 and
                        (vocab.get(la, 0) <= 1 or vocab.get(lb, 0) <= 1) and
                        not (ma.group(2)[0].isupper() and mb.group(1)[0].isupper())):
                    out.append(a + b); i += 2; fixed += 1
                    continue
        out.append(a); i += 1
    return " ".join(out), fixed


ABBR = {"nr", "z", "znj", "zj", "dt", "etj", "p.sh", "sh", "prof", "dr", "mr", "neni", "pika",
        "fq", "vol", "art", "lit", "zv", "nënkryet", "kryet", "ing", "av", "rr", "nd", "nj", "st"}
SENT_END = re.compile(r"(?<=[.!?…])[\"”’»]?\s+(?=[\"“„«(]?[A-ZÇËŠŽĆČ0-9])")


def split_sentences(par):
    parts, out = SENT_END.split(par), []
    buf = ""
    for p in parts:
        buf = (buf + " " + p).strip() if buf else p.strip()
        last = re.findall(r"([A-Za-zçëÇË.]+)\.$", buf)
        if last and (last[0].lower().rstrip(".") in ABBR or re.fullmatch(r"[A-ZÇË]", last[0])):
            continue
        if re.search(r"\b\d{1,3}\.$", buf) and len(buf.split()) < 3:
            continue
        out.append(buf); buf = ""
    if buf:
        out.append(buf)
    return out


SQ = set("dhe të në për që një është nga me se si por ka janë ky kjo këtë cili cila tij saj "
         "ose edhe nuk do mund duke pas kur ku sot".split())
SR = set("i u na za je se od da koji koja koje su sa ili ovog ovaj kao biti zakona prema".split())
EN = set("the of and to in is for on with by that this are as be or from an shall".split())


def is_albanian(s):
    words = re.findall(r"[a-zçëšžćčđ]+", s.lower())
    if not words:
        return False
    sq = sum(w in SQ for w in words) + 2 * len(re.findall(r"[ëç]", s.lower()))
    sr = sum(w in SR for w in words) + 2 * len(re.findall(r"[šžćčđ]", s.lower()))
    en = sum(w in EN for w in words)
    if en >= 2 or {"the", "shall", "of"} & set(words):
        return False
    return sq > 0 and sq >= 1.5 * max(sr, en)


def foreign_line(s):
    low = s.lower()
    if re.search(r"[šžćčđ]", low) and not re.search(r"[ëç]", low):
        return True
    words = re.findall(r"[a-z]+", low)
    if len(words) >= 3 and not re.search(r"[ëç]", low):
        sq = sum(w in SQ for w in words)
        sr = sum(w in SR for w in words)
        en = sum(w in EN for w in words)
        return sq == 0 and max(sr, en) >= 2
    return False


def keep(s):
    w = s.split()
    if not (MIN_WORDS <= len(w) <= MAX_WORDS):
        return "gjatësia"
    letters = sum(ch.isalpha() for ch in s)
    if letters < 0.6 * len(s.replace(" ", "")):
        return "shumë numra/simbole"
    up = sum(ch.isupper() for ch in s if ch.isalpha())
    if letters and up > 0.7 * letters:
        return "titull me shkronja të mëdha"
    if not is_albanian(s):
        return "jo shqip"
    return ""


def dedup_key(s):
    s = re.sub(r"\d+", "0", s.lower())
    return re.sub(r"[^a-zçë0 ]", "", s).split().__str__()


COUNTRY_HEADERS = {
    "XK": ["republika e kosovës", "republika e kosoves", "kuvendi i republikës së kosovës"],
    "MK": ["maqedonisë së veriut", "maqedonise se veriut", "republika e maqedonisë"],
    "AL": ["republika e shqipërisë", "republika e shqiperise", "kuvendi i shqipërisë"],
}
KOSOVO_FILE_ID = re.compile(r"_(?=[A-Za-z0-9]*[A-Z][A-Za-z0-9]*[A-Z])(?=[A-Za-z0-9]*[a-z][A-Za-z0-9]*[a-z])[A-Za-z0-9]{10}\.\w+$")


def guess_meta(path, first_text, n_speakers, source=""):
    t = first_text.lower()
    name = path.name.lower()
    hits = [(t.find(h, 0, 1500), c) for c, hs in COUNTRY_HEADERS.items() for h in hs]
    hits = [(pos, c) for pos, c in hits if pos >= 0]
    if re.search(r"(^|[-_ ])\d{18}", path.name):
        country = "AL"
    elif KOSOVO_FILE_ID.search(path.name):
        country = "XK"
    elif hits:
        country = min(hits)[1]
    elif source.startswith("opendata"):
        country = "AL"
    elif "kuvendi" in t[:1500]:
        country = "AL"
    else:
        country = "?"
    head = t[:2500]
    if "procesverbal" in name or "_ts_" in name or "procesverbal" in head or n_speakers >= 10:
        doc_type = "transkript"
    elif "urdhër dhe rendi" in name or "rendi i ditës" in t[:400]:
        doc_type = "rend_dite"
    elif "raport" in name or "buletin" in name or "\nraport" in head:
        doc_type = "raport"
    elif "strategji" in name:
        doc_type = "strategji"
    elif "vendim" in name or "vendim" in t[:300]:
        doc_type = "vendim"
    elif "perkthim zyrtar" in t[:500] or "traktat" in head or "marrëveshj" in name:
        doc_type = "traktat"
    elif "ligj" in name or "memorandum" in name or "projektligj" in head or "propozim-ligj" in t[:3000]:
        doc_type = "ligj"
    elif "tabel" in name:
        doc_type = "tabela"
    else:
        doc_type = "tjeter"
    return country, doc_type


def load_overrides():
    f = Path("sources.csv")
    if not f.exists():
        return {}
    with open(f, encoding="utf-8-sig") as fh:
        return {r["file"]: r for r in csv.DictReader(fh)}


def build(dirs):
    OUT.mkdir(exist_ok=True)
    overrides = load_overrides()
    files, src_of = [], {}
    for d in dirs:
        root = Path(d).expanduser().resolve()
        label = root.parent.name if root.name.lower() in ("files", "pdf", "docs") else root.name
        for p in sorted(root.rglob("*")):
            if p.is_file() and p.suffix.lower() in DOC_EXT and not p.name.startswith("."):
                rel = p.relative_to(root).parts
                src_of[p] = rel[0] if len(rel) > 1 else label
                files.append(p)
    print(f"{len(files)} dokumente te {', '.join(dirs)}")
    seen_files, seen_sent = {}, {}
    docs, metas, n_out = [], [], 0
    parsed = []
    vocab = Counter()
    for path in files:
        source = src_of[path]
        rec = {"file": path.name, "source": source, "pages": 0, "words": 0,
               "paragraphs": 0, "kept": 0, "duplicates": 0, "repaired_splits": 0, "problem": ""}
        h = hashlib.md5(path.read_bytes()).hexdigest()
        if h in seen_files:
            rec["problem"] = f"kopje e njëjtë me {seen_files[h]}"
            docs.append(rec); print(f"  KOPJE     {path.name}"); continue
        seen_files[h] = path.name
        try:
            pages = [normalize(p) for p in read_pages(path)]
        except Exception as e:
            rec["problem"] = f"nuk u lexua: {e}"
            docs.append(rec); print(f"  GABIM     {path.name}: {e}"); continue
        rec["pages"] = len(pages)
        rec["words"] = sum(len(p.split()) for p in pages)
        if rec["words"] < 30 * max(1, len(pages)) / 5:
            rec["problem"] = "PDF i skanuar (pa tekst) - duhet OCR ose anashkalohet"
            docs.append(rec); print(f"  SKANUAR   {path.name}"); continue
        rep = repeated_lines(pages)
        lines = []
        for p in pages:
            for ln in p.splitlines():
                st = ln.strip()
                if st in rep or PAGE_NUM.match(st) or foreign_line(st):
                    continue
                lines.append("" if STAGE.match(st) else ln)
        paras = join_lines(lines)
        for _, par in paras:
            vocab.update(w.lower() for w in TOKEN.findall(par))
        n_speakers = len({sp for sp, _ in paras if sp})
        ov = overrides.get(path.name, {})
        country, doc_type = guess_meta(path, "\n".join(pages[:2]), n_speakers, source)
        country = ov.get("country") or country
        doc_type = ov.get("doc_type") or doc_type
        metas.append({"file": path.name, "source": source, "country": country,
                      "doc_type": doc_type, "speakers": n_speakers})
        rec["paragraphs"] = len(paras)
        parsed.append((rec, path, source, h, country, doc_type, paras))
        docs.append(rec)

    with open(OUT / "sentences.jsonl", "w", encoding="utf-8") as out:
        for rec, path, source, h, country, doc_type, paras in parsed:
            reasons = Counter()
            for pi, (speaker, par) in enumerate(paras):
                par, nfix = repair_splits(par, vocab)
                rec["repaired_splits"] += nfix
                for si, s in enumerate(split_sentences(par)):
                    s = s.strip(" ;:")
                    why = keep(s)
                    if why:
                        reasons[why] += 1; continue
                    k = dedup_key(s)
                    if k in seen_sent:
                        rec["duplicates"] += 1; continue
                    sid = f"{h[:8]}-{pi:04d}-{si:02d}"
                    seen_sent[k] = sid
                    out.write(json.dumps({
                        "id": sid, "text": s, "file": path.name, "source": source,
                        "country": country, "doc_type": doc_type, "speaker": speaker,
                    }, ensure_ascii=False) + "\n")
                    rec["kept"] += 1; n_out += 1
            rec["problem"] = "; ".join(f"{k}: {v}" for k, v in reasons.most_common())
            print(f"  {rec['kept']:6d} fjali  {country} {doc_type:10s} {path.name[:70]}")

    with open(OUT / "documents.csv", "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=list(docs[0].keys())); w.writeheader(); w.writerows(docs)
    with open(OUT / "sources_detected.csv", "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=["file", "source", "country", "doc_type", "speakers"])
        w.writeheader(); w.writerows(metas)

    print("\n=== PËRMBLEDHJE ===")
    print(f"Fjali unike: {n_out}")
    sents = [json.loads(l) for l in open(OUT / "sentences.jsonl", encoding="utf-8")]
    for key in ("country", "doc_type", "source"):
        print(f"Sipas {key}: " + ", ".join(f"{k}={v}" for k, v in Counter(s[key] for s in sents).most_common()))
    skipped = [d for d in docs if d["problem"].startswith(("kopje", "PDF", "nuk"))]
    if skipped:
        print(f"Dokumente të anashkaluara: {len(skipped)} (shih documents.csv)")
    print(f"\nRezultatet: {OUT}/")


def sample(n, seed=42):
    sents = [json.loads(l) for l in open(OUT / "sentences.jsonl", encoding="utf-8")]
    rnd = random.Random(seed)
    groups = {}
    for s in sents:
        groups.setdefault((s["country"], s["doc_type"]), []).append(s)
    picked = []
    for key, items in groups.items():
        k = min(len(items), max(min(10, len(items)), round(n * len(items) / len(sents))))
        by_doc = {}
        for s in items:
            by_doc.setdefault(s["file"], []).append(s)
        queues = [rnd.sample(v, len(v)) for v in by_doc.values()]
        rnd.shuffle(queues)
        take = []
        while len(take) < k:
            for q in queues:
                if q and len(take) < k:
                    take.append(q.pop())
        picked += take
    rnd.shuffle(picked)
    picked = picked[:n]
    f = OUT / f"sample_{n}_seed{seed}.tsv"
    with open(f, "w", encoding="utf-8") as fh:
        fh.write("id\tsource\tcountry\tdoc_type\ttext\n")
        for s in picked:
            fh.write(f"{s['id']}\t{s['source']}\t{s['country']}\t{s['doc_type']}\t{s['text']}\n")
    print(f"{len(picked)} fjali u ruajtën te {f} (seed={seed}, që mostra të jetë e përsëritshme)")


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "build":
        build(sys.argv[2:])
    elif len(sys.argv) >= 3 and sys.argv[1] == "sample":
        sample(int(sys.argv[2]), int(sys.argv[3]) if len(sys.argv) > 3 else 42)
    else:
        print(__doc__)

#!/usr/bin/env python3
"""
Usage: python check_test.py EXPORT.json [PROJECT_ID]
"""
import csv
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

STRIP = " \t\n.,;:!?\"'“”„«»()[]…"

DOC_HEADS = ("kod", "strategji", "ligj", "projektligj", "marrëveshj", "memorandum", "plan",
             "rregullor", "kart", "deklarat", "agjend", "standard", "procedur", "konvent",
             "kushtetut", "direktiv", "vkm", "vendim", "raport", "protokoll", "statut",
             "udhëzim", "urdhër", "rezolut", "programi i qeverisë", "dokument", "kapitull")
POSITION = re.compile(r"^(zëvendës)?(ministri|ministrin|ministrit|ministrja|ministren|ministres|ministër|"
                      r"kryeministr\w*|kryetar\w*|sekretar\w*|drejtor|drejtori|drejtorin|drejtorit|"
                      r"drejtoresh\w*|deputet\w*|ambasador\w*|komisioner\w*|zv\.?)$", re.I)
COMMON_CAP = {"për", "duke", "parë", "në", "nga", "me", "dhe", "ky", "kjo", "këto", "këta", "të", "e", "i",
              "si", "por", "edhe", "nëse", "kur", "ku", "çdo", "neni", "pika", "nr", "zoti", "zonja",
              "projektligji", "ligji", "ligjit", "ligjin", "vendimi", "kreu", "seksioni", "aneksi", "shtojca"}
GENERIC_ALONE = re.compile(r"^(ministri|drejtori|komision|komitet|parlament|inspektorat|agjenci|"
                           r"bord|byro|ambasad|konsullat|sektor|zyr|institucion|shoqat|shoqëri|"
                           r"ndërmarrj|qendr|bashki|gjykat|prokurori|këshill|autoritet|"
                           r"departament|njësi|grup|fond|shërbim|hekurudh)\w*$", re.I)
NON_ENTITY_ACRONYMS = {"TVSH", "VKM", "PDF", "TCPDF", "OSHMA", "KM"}
TYPES = ("PER", "ORG", "LOC", "MISC")


def spans_of(result, text):
    out = []
    for r in result or []:
        if r.get("type") != "labels":
            continue
        s, e = r["value"]["start"], r["value"]["end"]
        while s < e and text[s] in STRIP:
            s += 1
        while e > s and text[e - 1] in STRIP:
            e -= 1
        if e > s:
            out.append((s, e, r["value"]["labels"][0], r.get("origin", "")))
    return out


def norm(s):
    return re.sub(r"\s+", " ", s).strip().lower()


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    path = Path(sys.argv[1])
    m = re.search(r"project-(\d+)", path.name)
    project = sys.argv[2] if len(sys.argv) > 2 else (m.group(1) if m else "1")
    tasks = json.load(open(path, encoding="utf-8"))

    rows, labelled = [], []
    by_string = defaultdict(Counter)
    forms = defaultdict(Counter)
    info = {}
    for t in tasks:
        anns = [a for a in t.get("annotations", []) if not a.get("was_cancelled")]
        if not anns:
            continue
        a = max(anns, key=lambda a: a.get("updated_at") or "")
        text = t["data"]["text"]
        sp = spans_of(a["result"], text)
        info[t["id"]] = (t["data"].get("id", ""), text, a.get("lead_time") or 0, sp)
        for s, e, lab, org in sp:
            labelled.append((t["id"], s, e, lab, org))
            by_string[norm(text[s:e])][lab] += 1
            forms[text[s:e]][lab] += 1

    def add(tid, span, lab, origin, reason, rule):
        did, text, lead, _ = info[tid]
        rows.append([tid, f"http://localhost:8080/projects/{project}/data?task={tid}",
                     span, lab, "sugjerim" if origin == "prediction" else "manual",
                     reason, rule, round(lead, 1), text])

    ruled_out = set()
    for tid, s, e, lab, org in labelled:
        text = info[tid][1]
        span = text[s:e]
        low = span.lower()
        first = span.split()[0]
        c = by_string[norm(span)]
        if len(c) > 1 and (c[lab] < max(c.values()) or list(c.values()).count(max(c.values())) > 1):
            add(tid, span, lab, org, "i njëjti string me lloje të ndryshme: " +
                ", ".join(f"{k}x{v}" for k, v in by_string[norm(span)].items()), "6 (konsistenca)")
        if span[0].islower() and not re.match(r"^e-[A-Z]", span):
            add(tid, span, lab, org, "fillon me shkronjë të vogël (emër i përgjithshëm?)", "3 (Capitals decide)")
        if any(low.startswith(h) for h in DOC_HEADS):
            add(tid, span, lab, org, "duket si dokument (ligj, kod, strategji, marrëveshje, plan...)", "2, 5 (Documents -> O)")
        if POSITION.match(first) and lab != "PER":
            add(tid, span, lab, org, "duket si pozicion/rol, jo institucion", "5 (Positions -> O)")
        if len(span.split()) == 1 and GENERIC_ALONE.match(span) and lab == "ORG":
            add(tid, span, lab, org, "fjalë institucioni e vetme, pa emrin e plotë", "5 (Generic institution words -> O)")
        if lab in ("MISC", "LOC", "PER") and len(span.split()) > 1 and GENERIC_ALONE.match(first) \
                and not re.match(r"(fond|këshillim)", first, re.I):
            add(tid, span, lab, org, "emër institucioni (Sektori, Drejtoria, Shërbimi, Agjencia...) i etiketuar " + lab,
                "2, 5 (Named departments -> ORG)")
        if lab == "ORG" and re.match(r"(samit|konferenc|festival|forum|kongres|lufta)", low):
            add(tid, span, lab, org, "duket si ngjarje, jo organizatë", "2 (Events -> MISC)")
        if re.sub(r"[-‑].*$", "", span).upper() in NON_ENTITY_ACRONYMS:
            add(tid, span, lab, org, "akronim që nuk është entitet", "4 (TVSH-së -> O)")
        if any(r[0] == tid and r[2] == span and not r[6].startswith("6") for r in rows):
            ruled_out.add(norm(span))

    HEADS = ("Zyr", "Bank", "Minist", "Agjenc", "Drejtori", "Komision", "Këshill", "Prokurori",
             "Gjykat", "Bashki", "Kuvend", "Universitet", "Instituti", "Autoritet")
    for tid, (did, text, lead, sp) in info.items():
        ss = sorted(sp)
        for i in range(len(ss)):
            for j in range(i + 1, len(ss)):
                if ss[j][0] < ss[i][1]:
                    a, b = text[ss[i][0]:ss[i][1]], text[ss[j][0]:ss[j][1]]
                    add(tid, f"{a} [{ss[i][2]}]  <->  {b} [{ss[j][2]}]", "-", "",
                        "dy spane mbivendosen: fshi njërin", "3 (Flat spans, longest wins)")
        for s_, e_, lab, org in sp:
            seg = text[s_:e_]
            parts = re.split(r",\s+|\s+dhe\s+", seg)
            if lab == "ORG" and len(parts) > 1 and sum(p.startswith(HEADS) for p in parts) >= 2:
                add(tid, seg, lab, org, "disa institucione në një span", "3 (Coordinated names are separate spans)")

    names = {k: c for k, c in forms.items() if len(k) >= 3 and norm(k) not in ruled_out}
    for tid, (did, text, lead, sp) in info.items():
        covered = [(s, e) for s, e, *_ in sp]
        for name, c in names.items():
            for mm in re.finditer(r"(?<!\w)" + re.escape(name) + r"(?!\w)", text):
                if not any(s <= mm.start() and mm.end() <= e for s, e in covered):
                    if not any(s < mm.end() and mm.start() < e for s, e in covered):
                        add(tid, text[mm.start():mm.end()], "-", "", "e etiketuar diku tjetër si " +
                            "/".join(c) + ", por jo këtu", "6 (konsistenca)")

    for tid, (did, text, lead, sp) in info.items():
        if lead >= 3:
            continue
        toks = list(re.finditer(r"\S+", text))
        missing = []
        for i, mt in enumerate(toks):
            w = mt.group().strip(STRIP)
            if i == 0 or not w or not w[0].isupper() or len(w) < 2 or w.lower() in COMMON_CAP:
                continue
            if GENERIC_ALONE.match(w) or any(w.lower().startswith(h) for h in DOC_HEADS):
                continue
            if re.fullmatch(r"[IVXLC]+", w):
                continue
            if toks[i - 1].group().endswith((".", ":", "?", "!", "–", "-", "“", "\"", "„", "(")):
                continue
            if any(s <= mt.start() < e for s, e, *_ in sp):
                continue
            missing.append(w)
        if missing:
            add(tid, ", ".join(dict.fromkeys(missing)), "-", "", f"pranuar për {lead:.1f} s; fjalë me shkronjë "
                "të madhe pa etiketë", "kontrollo nëse mungon një entitet")

    seen, uniq = set(), []
    for r in rows:
        key = (r[0], r[2], r[5])
        if key not in seen:
            seen.add(key)
            uniq.append(r)
    uniq.sort(key=lambda r: (r[6], r[0]))
    with open("test_review.csv", "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.writer(fh)
        w.writerow(["task", "hape", "span", "etiketa", "burimi", "pse", "rregulli", "sekonda", "fjalia"])
        w.writerows(uniq)

    lab = Counter(x[3] for x in labelled)
    lead = sorted(v[2] for v in info.values())
    print(f"{len(info)} fjali të anotuara | {len(labelled)} spane: " + ", ".join(f"{k}={lab[k]}" for k in TYPES))
    if lead:
        print(f"koha: mediana {lead[len(lead)//2]:.1f} s për fjali, gjithsej {sum(lead)/60:.0f} min, "
              f"{sum(x < 3 for x in lead)} fjali nën 3 s")
    print(f"\nPër t'u parë: {len(uniq)} raste në {len({r[0] for r in uniq})} fjali")
    for k, v in Counter(r[6] for r in uniq).most_common():
        print(f"  {v:4}  {k}")
    print("\nRuajtur: test_review.csv")


if __name__ == "__main__":
    main()

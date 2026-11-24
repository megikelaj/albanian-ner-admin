#!/usr/bin/env python3
"""
Usage: python export_to_bio.py EXPORT.json NAME
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

STRIP = " \t\n.,;:!?\"'“”„«»()[]…"
TOKEN = re.compile(r"\w+(?:[-‑’'`]\w+)*|[^\w\s]")
TYPES = ("PER", "ORG", "LOC", "MISC")


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    src = Path(sys.argv[1])
    name = sys.argv[2] if len(sys.argv) > 2 else src.stem
    out = Path("bio")
    out.mkdir(exist_ok=True)
    tasks = json.load(open(src, encoding="utf-8"))

    rows, skipped, unannotated, widened = [], 0, 0, 0
    ent = Counter()
    by_country = Counter()
    for t in tasks:
        anns = [a for a in t.get("annotations", []) if not a.get("was_cancelled")]
        if not anns:
            unannotated += 1
            continue
        a = max(anns, key=lambda a: a.get("updated_at") or "")
        if any(r["type"] == "choices" and "SKIP" in r["value"].get("choices", []) for r in a["result"]):
            skipped += 1
            continue
        text = t["data"]["text"]
        toks = [(m.start(), m.end(), m.group()) for m in TOKEN.finditer(text)]
        tags = ["O"] * len(toks)
        spans = []
        for r in a["result"]:
            if r["type"] != "labels":
                continue
            s, e = r["value"]["start"], r["value"]["end"]
            while s < e and text[s] in STRIP:
                s += 1
            while e > s and text[e - 1] in STRIP:
                e -= 1
            if e > s:
                spans.append((s, e, r["value"]["labels"][0]))
        for s, e, lab in sorted(spans):
            idx = [i for i, (ts, te, _) in enumerate(toks) if ts < e and s < te]
            if not idx:
                continue
            if toks[idx[0]][0] != s or toks[idx[-1]][1] != e:
                widened += 1
            if any(tags[i] != "O" for i in idx):
                sys.exit(f"Spane që mbivendosen te task {t['id']}: rregulloji në Label Studio.")
            tags[idx[0]] = "B-" + lab
            for i in idx[1:]:
                tags[i] = "I-" + lab
            ent[lab] += 1
            by_country[(t["data"].get("country", ""), lab)] += 1
        rows.append({"id": t["data"].get("id", t["id"]), "task": t["id"],
                     "country": t["data"].get("country", ""), "doc_type": t["data"].get("doc_type", ""),
                     "tokens": [x[2] for x in toks], "ner_tags": tags})

    with open(out / f"{name}.conll", "w", encoding="utf-8") as fh:
        for r in rows:
            for tok, tag in zip(r["tokens"], r["ner_tags"]):
                fh.write(f"{tok}\t{tag}\n")
            fh.write("\n")
    with open(out / f"{name}.jsonl", "w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")

    ntok = sum(len(r["tokens"]) for r in rows)
    lines = [f"Burimi: {src.name}",
             f"Fjali: {len(rows)} (SKIP: {skipped}, pa anotim: {unannotated})",
             f"Fjalë (tokens): {ntok}",
             f"Entitete: {sum(ent.values())}  " + "  ".join(f"{k}={ent[k]}" for k in TYPES),
             f"Fjali pa asnjë entitet: {sum(all(x == 'O' for x in r['ner_tags']) for r in rows)}",
             f"Spane të zgjeruara deri në kufirin e fjalës: {widened}", "",
             "Sipas shtetit:"]
    for c in sorted({r["country"] for r in rows}):
        n = sum(r["country"] == c for r in rows)
        lines.append(f"  {c}: {n} fjali  " + "  ".join(f"{k}={by_country[(c, k)]}" for k in TYPES))
    (out / f"{name}_stats.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    print(f"\nRuajtur: bio/{name}.conll, bio/{name}.jsonl, bio/{name}_stats.txt")


if __name__ == "__main__":
    main()

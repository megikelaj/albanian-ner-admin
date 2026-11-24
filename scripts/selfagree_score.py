#!/usr/bin/env python3
"""
Usage: python selfagree_score.py ROUND1.json ROUND2.json [EXCLUDE_IDS.txt]
"""
import csv
import json
import re
import sys
from collections import Counter

TYPES = ["PER", "ORG", "LOC", "MISC"]
STRIP = " \t\n.,;:!?\"'“”„«»()[]…"


def clean(text, s, e):
    while s < e and text[s] in STRIP:
        s += 1
    while e > s and text[e - 1] in STRIP:
        e -= 1
    return s, e


def load(path):
    out = {}
    for t in json.load(open(path, encoding="utf-8")):
        anns = [a for a in t.get("annotations", []) if not a.get("was_cancelled")]
        text = t["data"]["text"]
        if not anns:
            if t.get("annotations"):
                out[t["data"]["id"]] = {"text": text, "spans": set(), "skip": True}
            continue
        a = max(anns, key=lambda a: a.get("updated_at") or "")
        spans, skip = set(), False
        for r in a["result"]:
            if r["type"] == "labels":
                s, e = clean(text, r["value"]["start"], r["value"]["end"])
                if e > s:
                    spans.add((s, e, r["value"]["labels"][0]))
            elif r["type"] == "choices" and "SKIP" in r["value"].get("choices", []):
                skip = True
        out[t["data"]["id"]] = {"text": text, "spans": spans, "skip": skip}
    return out


def prf(a, b):
    tp = len(a & b)
    p = tp / len(b) if b else 1.0
    r = tp / len(a) if a else 1.0
    f = 2 * p * r / (p + r) if p + r else 0.0
    return p, r, f, tp


def bio(text, spans):
    toks = [(m.start(), m.end()) for m in re.finditer(r"\w+|[^\w\s]", text)]
    tags = ["O"] * len(toks)
    for s, e, lab in sorted(spans):
        first = True
        for i, (ts, te) in enumerate(toks):
            if ts >= s and te <= e:
                tags[i] = ("B-" if first else "I-") + lab
                first = False
    return tags


def kappa(x, y):
    n = len(x)
    po = sum(a == b for a, b in zip(x, y)) / n
    cx, cy = Counter(x), Counter(y)
    pe = sum(cx[k] * cy[k] for k in cx) / (n * n)
    return (po - pe) / (1 - pe) if pe < 1 else 1.0


def main():
    if len(sys.argv) not in (3, 4):
        sys.exit(__doc__)
    r1, r2 = load(sys.argv[1]), load(sys.argv[2])
    ids = sorted(set(r1) & set(r2))
    missing = len(ids) < len(r1) or len(ids) < len(r2)
    if len(sys.argv) == 4:
        excl = {l.strip() for l in open(sys.argv[3], encoding="utf-8") if l.strip()}
        ids = [i for i in ids if i not in excl]
        print(f"Lënë jashtë: {len(excl)} fjali (nga {sys.argv[3]})")
    print(f"Raundi 1: {len(r1)} fjali | Raundi 2: {len(r2)} fjali | të përbashkëta: {len(ids)}")
    if missing:
        print("  KUJDES: disa fjali janë anotuar vetëm në një raund; ato nuk numërohen.")

    A, B, rows, t1, t2 = set(), set(), [], [], []
    skip_diff = 0
    for i in ids:
        a, b = r1[i], r2[i]
        A |= {(i,) + s for s in a["spans"]}
        B |= {(i,) + s for s in b["spans"]}
        skip_diff += a["skip"] != b["skip"]
        t1 += bio(a["text"], a["spans"])
        t2 += bio(b["text"], b["spans"])
        txt = a["text"]
        for s, e, lab in sorted(a["spans"] ^ b["spans"]):
            where = "vetëm R1" if (s, e, lab) in a["spans"] else "vetëm R2"
            other = [f"{txt[s2:e2]} [{l2}]" for s2, e2, l2 in (b["spans"] if where == "vetëm R1" else a["spans"])
                     if s2 < e and s < e2]
            kind = ("lloj tjetër" if any(x[0] == s and x[1] == e for x in (b["spans"] if where == "vetëm R1" else a["spans"]))
                    else "kufij të tjerë" if other else "mungon në raundin tjetër")
            rows.append([i, where, txt[s:e], lab, kind, "; ".join(other), txt])

    p, r, f, tp = prf(A, B)
    print(f"\nSpane: R1={len(A)}  R2={len(B)}  të njëjta={tp}")
    print(f"F1 i saktë (kufij + lloj):  {f:.3f}   (P={p:.3f}, R={r:.3f})")
    _, _, fu, _ = prf({x[:3] for x in A}, {x[:3] for x in B})
    print(f"F1 vetëm kufijtë (pa lloj): {fu:.3f}")
    part = sum(any(x[0] == y[0] and x[3] == y[3] and x[1] < y[2] and y[1] < x[2] for y in B) for x in A)
    part2 = sum(any(x[0] == y[0] and x[3] == y[3] and x[1] < y[2] and y[1] < x[2] for y in A) for x in B)
    pp, pr = (part2 / len(B) if B else 1), (part / len(A) if A else 1)
    print(f"F1 i pjesshëm (mbivendosje, i njëjti lloj): {2*pp*pr/(pp+pr) if pp+pr else 0:.3f}")
    print(f"Cohen's kappa (fjalë, BIO): {kappa(t1, t2):.3f}   mbi {len(t1)} fjalë")
    print(f"SKIP i ndryshëm: {skip_diff} fjali")

    print("\nSipas llojit:      R1    R2   F1")
    for T in TYPES:
        a = {x for x in A if x[3] == T}
        b = {x for x in B if x[3] == T}
        print(f"  {T:5}         {len(a):5} {len(b):5}  {prf(a, b)[2]:.3f}")

    print("\nLlojet e mospërputhjeve:", dict(Counter(r[4] for r in rows)))
    with open("selfagree_differences.csv", "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.writer(fh)
        w.writerow(["id", "ku", "span", "lloji", "mospërputhja", "në raundin tjetër", "fjalia"])
        w.writerows(rows)
    print("Ruajtur: selfagree_differences.csv")
    print("\nObjektivi: F1 i saktë >= 0.85.")


if __name__ == "__main__":
    main()

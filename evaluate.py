#!/usr/bin/env python3
"""
Usage: python evaluate.py PREDICTIONS [--gold data/test.jsonl] [--types PER,ORG,LOC] [--ignore-misc] [--json]
"""
import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ALL = ["PER", "ORG", "LOC", "MISC"]


def keep(tags, types):
    out, prev = [], "O"
    for t in tags:
        t = (t or "O").strip()
        if t == "O" or "-" not in t or t.split("-", 1)[1] not in types:
            out.append("O"); prev = "O"; continue
        p, y = t.split("-", 1)
        if p not in ("B", "I") or (p == "I" and prev not in ("B-" + y, "I-" + y)):
            p = "B"
        out.append(f"{p}-{y}"); prev = out[-1]
    return out


def spans(tags):
    out, start = set(), None
    for i, t in enumerate(list(tags) + ["O"]):
        if start is not None and not (t.startswith("I-") and t[2:] == start[1]):
            out.add((start[0], i, start[1])); start = None
        if t.startswith("B-"):
            start = (i, t[2:])
    return out


def prf(tp, np_, ng):
    p = tp / np_ if np_ else 0.0
    r = tp / ng if ng else 0.0
    return p, r, (2 * p * r / (p + r) if p + r else 0.0)


def score(pairs, types):
    tp, npred, ngold = Counter(), Counter(), Counter()
    for g, p in pairs:
        G, P = spans(g), spans(p)
        for s in G & P: tp[s[2]] += 1
        for s in P: npred[s[2]] += 1
        for s in G: ngold[s[2]] += 1
    res = {"micro": dict(zip(("P", "R", "F1"), prf(sum(tp.values()), sum(npred.values()), sum(ngold.values()))))}
    for t in types:
        res[t] = dict(zip(("P", "R", "F1"), prf(tp[t], npred[t], ngold[t])))
        res[t]["support"] = ngold[t]
    res["macro_F1"] = sum(res[t]["F1"] for t in types) / len(types)
    return res


def load_predictions(path, gold):
    path = Path(path)
    first = path.read_text(encoding="utf-8").lstrip()[:1]
    if first == "{":
        preds = {}
        for line in path.open(encoding="utf-8"):
            if line.strip():
                r = json.loads(line)
                preds[str(r["id"])] = r.get("pred") or r.get("ner_tags")
        missing = [g["id"] for g in gold if g["id"] not in preds]
        if missing:
            sys.exit(f"{len(missing)} test sentences have no prediction, e.g. {missing[:3]}")
        return [preds[g["id"]] for g in gold]
    sents, cur = [], []
    for line in path.open(encoding="utf-8"):
        line = line.rstrip("\n")
        if not line.strip():
            if cur: sents.append(cur); cur = []
            continue
        cur.append(line.split("\t")[-1] if "\t" in line else line.split()[-1])
    if cur: sents.append(cur)
    if len(sents) != len(gold):
        sys.exit(f"The CoNLL file has {len(sents)} sentences, the test set has {len(gold)}.")
    return sents


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("predictions")
    ap.add_argument("--gold", default=str(Path(__file__).parent / "data" / "test.jsonl"))
    ap.add_argument("--types", default=",".join(ALL))
    ap.add_argument("--ignore-misc", action="store_true")
    ap.add_argument("--json", action="store_true", help="print the scores as JSON")
    a = ap.parse_args()
    types = [t.strip() for t in a.types.split(",") if t.strip()]
    gold = [json.loads(l) for l in open(a.gold, encoding="utf-8") if l.strip()]
    preds = load_predictions(a.predictions, gold)

    pairs, meta = [], []
    for g, p in zip(gold, preds):
        if len(p) != len(g["tokens"]):
            sys.exit(f"Sentence {g['id']}: {len(p)} predicted tags for {len(g['tokens'])} tokens.")
        p = list(p)
        if a.ignore_misc:
            p = ["O" if gt.endswith("-MISC") else pt for gt, pt in zip(g["ner_tags"], p)]
        pairs.append((keep(g["ner_tags"], types), keep(p, types)))
        meta.append(g)

    out = {"types": types, "ignore_misc": a.ignore_misc, "sentences": len(pairs), "all": score(pairs, types)}
    for key in ("country", "doc_type"):
        groups = defaultdict(list)
        for m, pr in zip(meta, pairs):
            groups[m.get(key, "")].append(pr)
        out[key] = {k: {"n": len(v), **score(v, types)["micro"]} for k, v in sorted(groups.items())}

    if a.json:
        print(json.dumps(out, indent=1)); return
    m = out["all"]["micro"]
    print(f"Sentences: {out['sentences']} | types: {', '.join(types)}" + (" | gold MISC spans ignored" if a.ignore_misc else ""))
    print(f"Micro  P {m['P']:.3f}  R {m['R']:.3f}  F1 {m['F1']:.3f}   | macro F1 {out['all']['macro_F1']:.3f}")
    for t in types:
        s = out["all"][t]
        print(f"  {t:5} P {s['P']:.3f}  R {s['R']:.3f}  F1 {s['F1']:.3f}  (gold {s['support']})")
    for key in ("country", "doc_type"):
        print(f"By {key}: " + ", ".join(f"{k} {v['F1']:.3f} (n={v['n']})" for k, v in out[key].items()))


if __name__ == "__main__":
    main()

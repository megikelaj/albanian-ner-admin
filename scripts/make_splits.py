#!/usr/bin/env python3
import csv
import json
import random
import re
from collections import Counter, defaultdict
from pathlib import Path

POOL = Path("sentence_pool")
SEED = 2026
TEST_DOC_SHARE = 0.3
SELFAGREE_N = 150
QUOTAS = {("AL", "transkript"): 400, ("AL", "tjeter"): 160,
          ("XK", "transkript"): 80, ("XK", "tjeter"): 40, ("MK", "tjeter"): 60}


def group(doc_type):
    return "transkript" if doc_type == "transkript" else "tjeter"


def not_text(t):
    letters = [c for c in t if c.isalpha()]
    if not letters or "{" in t or '":' in t:
        return True
    if sum(c.isdigit() for c in t) > 0.25 * len(t.replace(" ", "")):
        return True
    return sum(c.isupper() for c in letters) > 0.6 * len(letters) and len(t.split()) >= 4


def main():
    sents = [json.loads(l) for l in open(POOL / "sentences.jsonl", encoding="utf-8")]
    pilot = set()
    pf = POOL / "sample_300_seed42.tsv"
    if pf.exists():
        with open(pf, encoding="utf-8") as f:
            next(f)
            pilot = {line.split("\t", 1)[0] for line in f}
    sents = [s for s in sents if s["id"] not in pilot and not not_text(s["text"])]
    print(f"{len(sents)} fjali të përdorshme (pa pilotin {len(pilot)} dhe pa rreshtat jo-tekst)")

    by_doc = defaultdict(list)
    for s in sents:
        by_doc[s["file"]].append(s)
    rnd = random.Random(SEED)

    strata = defaultdict(list)
    for f, items in by_doc.items():
        strata[(items[0]["country"], group(items[0]["doc_type"]))].append(f)
    test_docs, test = set(), []
    for key, docs in sorted(strata.items()):
        quota = QUOTAS.get(key, 0)
        n = len(docs)
        k = n if key[0] == "MK" else (max(1, round(TEST_DOC_SHARE * n)) if n >= 2 else 0)
        if not quota or not k:
            continue
        docs = sorted(docs)
        rnd.shuffle(docs)
        chosen = docs[:k]
        test_docs.update(chosen)
        queues = [rnd.sample(by_doc[f], len(by_doc[f])) for f in chosen]
        take = []
        while len(take) < quota and any(queues):
            for q in queues:
                if q and len(take) < quota:
                    take.append(q.pop())
        test += take
    rnd.shuffle(test)

    train_docs = [f for f in by_doc if f not in test_docs]
    queues = [rnd.sample(by_doc[f], len(by_doc[f])) for f in train_docs]
    rnd.shuffle(queues)
    selfagree = []
    while len(selfagree) < SELFAGREE_N and any(queues):
        for q in queues:
            if q and len(selfagree) < SELFAGREE_N:
                selfagree.append(q.pop())

    with open(POOL / "test_700.tsv", "w", encoding="utf-8") as fh:
        fh.write("id\tsource\tcountry\tdoc_type\ttext\n")
        for s in test:
            fh.write(f"{s['id']}\t{s['source']}\t{s['country']}\t{s['doc_type']}\t{s['text']}\n")
    r1 = [{"data": {k: s[k] for k in ("id", "source", "country", "doc_type", "text")}} for s in selfagree]
    r2 = r1[:]
    random.Random(SEED + 1).shuffle(r2)
    json.dump(r1, open(POOL / "selfagree_150_r1.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump(r2, open(POOL / "selfagree_150_r2.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    with open(POOL / "split_documents.csv", "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.writer(fh)
        w.writerow(["file", "country", "doc_type", "split", "sentences_in_pool", "sentences_in_test"])
        tc = Counter(s["file"] for s in test)
        for f, items in sorted(by_doc.items()):
            w.writerow([f, items[0]["country"], items[0]["doc_type"],
                        "test" if f in test_docs else "train", len(items), tc.get(f, 0)])

    print(f"\nTEST: {len(test)} fjali nga {len(test_docs)} dokumente")
    print("  sipas shtetit:", dict(Counter(s["country"] for s in test)))
    print("  sipas llojit: ", dict(Counter(s["doc_type"] for s in test)))
    print(f"TRAJNIM: {len(train_docs)} dokumente, {sum(len(by_doc[f]) for f in train_docs)} fjali")
    print(f"VETË-MARRËVESHJE: {len(selfagree)} fjali nga dokumentet e trajnimit")
    print("\nSkedarët te sentence_pool/: test_700.tsv, selfagree_150_r1.json, "
          "selfagree_150_r2.json, split_documents.csv")


if __name__ == "__main__":
    main()

# Albanian NER for administrative and parliamentary text

A gold-standard named entity recognition (NER) test set for Albanian institutional text, with the annotation guidelines, the data-processing scripts and the evaluation notebooks used in the MSc thesis *Named Entity Recognition for Albanian Administrative and Parliamentary Text* (Megiola Kelaj, University of New York Tirana, 2026).

**On the Hugging Face Hub:** dataset [Megiola/albanian-admin-ner-test](https://huggingface.co/datasets/Megiola/albanian-admin-ner-test) | model [Megiola/albanian-ner-mdeberta-v3-wikiann](https://huggingface.co/Megiola/albanian-ner-mdeberta-v3-wikiann)

## The test set

| | |
|---|---|
| Sentences | 691 (693 drawn, 2 marked SKIP) |
| Tokens | 19,370 |
| Entities | 588: ORG 316, LOC 136, PER 94, MISC 42 |
| Sentences without entities | 401 |
| Countries | Albania 558, Kosovo 109, North Macedonia 24 sentences |
| Document types | transcripts 480, reports 89, laws 51, other 42, strategies 29 |
| Sources | opendata.gov.al and the document archives of the parliaments of Albania, Kosovo and North Macedonia |

The test sentences come from 18 documents. The training side of the corpus (35 documents, 21,988 unannotated sentences) was split off by document, so no document contributes to both sides. data/split_documents.csv lists all 53 documents, which side each one is on, and the site it came from.

Entity types follow CoNLL-2003 (PER, ORG, LOC, MISC), with Albanian-specific rules for inflected names, linking articles, acronyms with case suffixes (`BERZH-it`), documents (not entities), positions (not entities) and generic institution words. See `guidelines/annotation_guidelines_v1.md`.

## Files

- `DATASHEET.md`: the full datasheet (motivation, composition, collection, labelling, uses, licence, maintenance).
- `evaluate.py`: scores any prediction file (JSONL or CoNLL) against the test set, with no dependencies: `python evaluate.py my_predictions.jsonl --types PER,ORG,LOC`.
- `data/test.conll`: one token and its BIO tag per line, a blank line between sentences.
- `data/test.jsonl`: one sentence per line with id, country, doc_type, tokens, ner_tags. The id has the form doc_code-paragraph-sentence, for example cb9dee28-0500-02.
- `data/split_documents.csv`: the document-level split. One row per document: doc_code (the first 8 characters of the MD5 hash of the original file, which is also the start of every sentence id), file (the file name as downloaded), source (the site), country, doc_type, split (test or train), sentences_in_pool, sentences_drawn_for_test and sentences_in_release (after the 2 SKIP lines were removed).
- `guidelines/annotation_guidelines_v1.md`: the full guidelines, hard cases and decision log.
- `scripts/`: corpus inventory and cleaning, document-level split, rule-based pre-annotation, consistency check, BIO export, self-agreement scoring.
- `notebooks/albanian_ner_baselines.ipynb`: XLM-R, mDeBERTa-v3 and Glot500 fine-tuned on WikiANN-sq and scored on the test set (Colab, T4).
- `notebooks/albanian_ner_llm.ipynb`: Qwen3-8B and Qwen2.5-7B-Instruct, zero-shot and few-shot (Colab or Kaggle, T4).

## Main results (micro F1 on PER, ORG, LOC)

| System | WikiANN-sq test | This test set |
|---|---|---|
| mDeBERTa-v3 base (WikiANN, 3 seeds) | 0.935 | 0.630 ± 0.071 |
| XLM-RoBERTa base (WikiANN, 3 seeds) | 0.929 | 0.572 ± 0.045 |
| Glot500 base (WikiANN, 3 seeds) | 0.920 | 0.526 ± 0.017 |
| Qwen3-8B, guidelines + 8 examples (no training) | - | 0.693 |

## Annotation quality

One annotator. Self-agreement on 143 sentences annotated twice, four days apart: exact span F1 0.663, word-level Cohen's kappa 0.777 (PER 1.000, LOC 0.786, ORG 0.673, MISC 0.267). Most disagreements were early decisions made before the guidelines were finalised; MISC labels should be used with care. Details are in the thesis.

## Licence

- Annotations and guidelines: CC BY 4.0.
- Code: MIT.
- Source text: information published by Albanian public bodies on opendata.gov.al may be reused under Albania's standard licence for the reuse of public sector information (Law No. 33/2022), with attribution to the source. Parliamentary texts are official documents published by the parliaments of Albania, Kosovo and North Macedonia. Please cite the original sources when you reuse the text.

No personal data of private individuals is included: files with named lists of private persons were excluded during collection.

## Citation

Kelaj, M. (2026). *Named Entity Recognition for Albanian Administrative and Parliamentary Text: A Gold-Standard Test Set and an Evaluation of Multilingual Encoders and Open Language Models.* MSc thesis, University of New York Tirana.

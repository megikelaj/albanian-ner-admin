# Datasheet: Albanian administrative NER test set

Following the questions of *Datasheets for Datasets* (Gebru et al., Communications of the ACM 64(12), 2021).

## Motivation

**Why was the dataset created?** To measure how well named entity recognition (NER) systems work on the formal Albanian of public institutions. The only large Albanian NER dataset, WikiANN-sq, was generated automatically from Wikipedia, and the only manually annotated one, AlbNER, is small and also from Wikipedia. There was no gold-standard test set for parliamentary, legal and administrative text.

**Who created it?** Megiola Kelaj, as part of an MSc thesis in Computer Science at the University of New York Tirana (advisor: Dr. Marjana Prifti Skenduli), November 2026.

**Funding.** None.

## Composition

**What do the instances represent?** Sentences from Albanian-language documents published by public institutions, with each token tagged in the BIO scheme for four entity types: PER (people), ORG (organisations and institutions), LOC (places), MISC (other named entities: events, named funds, programmes, portals, products).

**How many instances?** 691 sentences, 19,370 tokens, 588 entities.

| Type | Entities |
|---|---|
| ORG | 316 |
| LOC | 136 |
| PER | 94 |
| MISC | 42 |

401 sentences contain no entity. 41% of the entities are one token long, 25% are four tokens or longer.

| Country of origin | Sentences | Document type | Sentences |
|---|---|---|---|
| Albania | 558 | Parliamentary transcripts | 480 |
| Kosovo | 109 | Reports | 89 |
| North Macedonia | 24 | Laws and draft laws | 51 |
| | | Other | 42 |
| | | Strategies | 29 |

**Is it a sample?** Yes. The full corpus has about 30,000 sentences from 53 documents. Documents, not sentences, were split into a test side (18 documents) and a training side (35 documents), about 30% of the documents of each country and type group going to the test side (all North Macedonian documents, as there were too few to train on). Test sentences were drawn in turn from each test document up to a quota per group, so that no long session dominates. Table rows, JSON fragments and all-capital headings were excluded.

**What does each instance contain?** `id` (source document and position), `country` (AL, XK, MK), `doc_type`, `tokens`, `ner_tags` (IOB2).

**Splits.** This release contains **only a test split**. There are no gold training or validation splits: the 22,000 sentences of the training side are not annotated. Systems should be trained on other data (for example WikiANN-sq or AlbNER) and tested here.

**Errors and noise.** The data was annotated by one person. Self-agreement on a separate sample of 143 sentences, annotated twice four days apart, was 0.663 exact span F1 (PER 1.000, LOC 0.786, ORG 0.673, MISC 0.267; word-level Cohen's kappa 0.777). Most disagreements were early decisions made before the guidelines were finalised, and the test set was annotated after that point and checked twice with an automatic consistency script. Still, the labels are not perfect, especially for MISC and for long ORG names. One known error (the acronym IQBSUVP, labelled MISC instead of ORG in 4 sentences) was corrected after the first evaluation.

**Confidential or sensitive data.** The text comes from documents that public institutions publish themselves. The people named are almost all public officials acting in their public role (members of parliament, ministers, heads of agencies). Files with named lists of private individuals (for example beneficiaries of subsidies) were identified during collection and excluded completely.

## Collection process

**How was the data acquired?** Documents were downloaded from four public sources: the Albanian open data portal (https://opendata.gov.al/datasets-list), through its API; the Assembly of Albania (Kuvendi i Shqipërisë, https://www.parlament.al/doksearch); the Assembly of the Republic of Kosovo (Kuvendi i Republikës së Kosovës, https://www.kuvendikosoves.org); and the Assembly of the Republic of North Macedonia (Kuvendi i Republikës së Maqedonisë së Veriut, https://www.sobranie.mk/home-al.nspx), of which only the Albanian-language versions were used. The parliamentary documents are transcripts, draft laws and explanatory reports. Text was extracted from PDF, Word, Excel and text files.

**Time frame.** Collected in November 2026 (corpus build of 16 November 2026).

**Ethical review.** No formal review board process. Only published public-sector documents were used; files with personal data of private individuals were excluded.

## Preprocessing, cleaning and labelling

**Cleaning.** Sentence splitting; repair of words broken at PDF line ends (rejoined when the joined form occurs elsewhere in the corpus, and always for a hyphen followed by a case suffix such as "UÇK -së"); removal of Serbian, Macedonian and English lines, page headers and duplicates; speaker labels removed from transcripts.

**Labelling.** In Label Studio, by one annotator who is a native speaker of Albanian, following written guidelines (`guidelines/annotation_guidelines_v1.md`). A rule-based tagger suggested labels; every suggestion was accepted, corrected or deleted by hand, and missed entities were added (471 suggestions; 133 entities added, 45 boundaries corrected in the first pass). An automatic consistency check then listed every span that conflicted with a written rule (documents, lowercase spans, positions, generic institution words, overlapping spans, merged institutions, the same string with different labels), and each case was reviewed (99 cases, then 55). No language model labelled any gold data.

**Key annotation decisions.** Flat spans, longest name wins. Inflected forms are annotated as written, including case endings and linking articles (*Ministrisë së Drejtësisë*). Acronyms with case suffixes are one entity (*BERZH-it*). Documents (laws, codes, strategies, the constitution), positions (*Ministri i Shtetit për Diasporën*) and single generic institution words (*Ministrisë*, *Parlamenti*) are not entities; *Kuvendi* and *Qeveria* alone are ORG. Countries are always LOC. *në* + a place name ends a name.

**Raw data.** The unannotated sentence pool and the document-level split are kept by the author and available on request.

## Uses

**Intended use.** Evaluating Albanian NER systems on institutional text: fine-tuned encoders, language models with prompts, rule-based systems. Studying domain shift from Wikipedia to administrative text, and the effect of annotation conventions.

**Results so far** (micro F1 on PER, ORG, LOC): mDeBERTa-v3 base trained on WikiANN-sq 0.630 ± 0.071 (3 seeds), XLM-RoBERTa base 0.572 ± 0.045, Glot500 base 0.526 ± 0.017; Qwen3-8B with the guideline rules and eight examples in its prompt 0.693 (no training).

**Uses to avoid.** Do not train on this set and report results on it. Do not treat differences of one or two points between systems as meaningful: the set is small, and paired bootstrap tests in the thesis show that differences of about 4 points are not significant. Do not use the MISC labels as a reliable reference for MISC alone. The text is formal and institutional; results do not carry over to news or social media.

## Distribution

**Licence.** Annotations and guidelines: CC BY 4.0. Code: MIT. Source text: information published by Albanian public bodies on opendata.gov.al may be reused under Albania's standard licence for the reuse of public sector information (Law No. 33/2022), with attribution to the source; parliamentary texts are official documents published by the parliaments of Albania, Kosovo and North Macedonia. Please cite the original sources when reusing the text; each sentence `id` identifies its source document.

**Where.** GitHub (code, data, guidelines) and the Hugging Face Hub (dataset and the best fine-tuned model).

## Maintenance

**Maintainer.** Megiola Kelaj. Corrections are recorded in the decision log of the guidelines (section 7) and in new versions of this dataset.

**Extensions.** Welcome. New annotation should follow `guidelines/annotation_guidelines_v1.md`, and new hard cases should be added to its tables and decision log. The natural next step is annotating part of the training side to create gold training and validation splits.

## Citation

Kelaj, M. (2026). *Named Entity Recognition for Albanian Administrative and Parliamentary Text: A Gold-Standard Test Set and an Evaluation of Multilingual Encoders and Open Language Models.* MSc thesis, University of New York Tirana.

# Albanian NER Annotation Guidelines v1

2026-11-16

## 1. Purpose and scope

These guidelines define how named entities are marked in the Albanian NER corpus: four types (PER, ORG, LOC, MISC), flat spans, one label per span. This is version 1, revised after the 300-sentence pilot, the test-set annotation and the self-agreement study (24 November 2026).

- **Corpus:** 30,681 unique sentences from parliamentary transcripts, committee reports, laws and government reports from Albania, Kosovo and North Macedonia (build of 16 November 2026).
- **Unit:** one sentence at a time. Speaker labels ("Edona Bilali –", "GANIMETE MUSLIU:") are already removed from the text and are not annotated.
- **Tag set:** the four CoNLL-2003 types, so results are comparable with WikiANN (PER, ORG, LOC) and AlbNER (PER, ORG, LOC, MISC).
- **Output format:** BIO tags per token (B-PER, I-PER, ..., O), exported from the annotation tool.
- **Not annotated:** dates, numbers, amounts, percentages, roles and titles, common nouns, nationality adjectives written in lowercase.

**Skip, don't annotate:** lines that are not running text. That means table rows and number dumps, JSON fragments, page headers ("SEANCË PLENARE PUBLIKE E enjte, 17 shtator 2026"), signature blocks, staffing tables ("Drejtoria e Informacionit dhe Teknologjisë Drejtor 1 II-1 VII/1") and non-Albanian fragments. Mark them SKIP in the tool. In the pilot sample, 17 of 300 lines are of this kind. Lists of names inside real text ("Marrin pjesë: Ina Zhupa, Erion Malaj, ...") are annotated normally.

The goal is consistency, not perfection: when a case is unclear, apply the closest rule, log the decision in section 7, and use the same decision every time after.

## 2. Entity types

Every entity gets exactly one of four labels; anything that is not a proper name of one of these kinds stays O.

| Tag | What it covers | Examples from the corpus | Not this tag |
|---|---|---|---|
| **PER** | Named people: full names, first or last name alone, double-barrelled surnames, nicknames, names in quotation marks | Edi Rama, Ganimete Musliu, Bilali, Neta, Bujar, Doarsa Kica-Xhelili, Igor Simiq, "Rina Ajdari" | Roles alone (kryeministri, deputetja); "Zoti" meaning God; a person's name inside an institution's name (shkolla "Halit Bërzeshta" -> ORG) |
| **ORG** | Named institutions and organizations: parliaments and their bodies, committees, ministries, courts, councils, agencies, named departments, parties and parliamentary groups, municipalities as institutions, universities, public enterprises, media and official gazettes, international bodies and blocs, armed groups | Kuvendi i Shqipërisë, Komisioni për Veprimtaritë Prodhuese, Konferencën e Kryetarëve, Këshilli i Ministrave, Gjykata Kushtetuese, GJEDNJ-së, Drejtoria e Informacionit dhe Teknologjisë, Partia Socialiste, Bashkia Maliq, Universitetin "Ismail Qemali" Vlorë, RTK-ja, Gazeta Zyrtare, Bashkimi Evropian, NATO-s, CEFTA-s, UÇK-së | Generic lowercase references (qeveria shqiptare, komisioni, sektorit të monitorimit); acronyms that are not entities (TVSH-së) |
| **LOC** | Named places: countries, regions, cities, villages, rivers, mountains, roads, airports and other named facilities | Shqipëria, Republikës Federale të Gjermanisë, Ballkani Perëndimor, Evropës Qendrore, Elbasan, Bruksel, Strasburg, Hagë, Meja, Rruga e Kombit, Milot-Rrëshen | The institution of a place (Bashkia Tiranë -> ORG); compass words (nga Veriu deri në Jug) |
| **MISC** | Other proper names that are not documents: events, named funds, programmes and instruments, named portals and products, works of art | Festivalin e Kanës, Lufta e Dytë Botërore, Plani i Rritjes, IPA, WBIF, Western Balkans Fund, Korniza e Investimeve për Ballkanin Perëndimor, e-Albania | Documents of any kind: laws, codes, treaties, strategies, action plans, directives, reports (Kodit Zgjedhor, Strategjia Kombëtare e Diasporës, Planit Kombëtar të Veprimit) -> O; nationality adjectives |

Countries are always LOC, even when they act like an organization ("Shqipëria nënshkroi marrëveshjen"). This avoids case-by-case metonymy decisions and matches WikiANN and CoNLL practice.

## 3. General span rules

A span covers the name itself and nothing else: no titles, roles, quotes or trailing punctuation.

1. **Proper names only.** Annotate a span only if it names one specific person, organization, place or thing. Common nouns stay O, even when capitalized at the start of a sentence.
2. **Titles and roles are outside the span.** "zotin **Edi Rama**" -> PER = Edi Rama. The same for zoti, zonja, z., znj., deputeti, ministri, kryetarja, Prof., Dr.
3. **Roles that contain an institution: tag the institution only if its full name is there.** "kryetare e **Kuvendit**" -> ORG = Kuvendit. "ministrin e Punëve të Brendshme" -> O, because "Punëve të Brendshme" alone is not a name.
4. **Flat spans, longest name wins.** No nesting: "**Grupi Parlamentar i PDK-së**" is one ORG; PDK-së is not tagged separately inside it. "**Bashkia Maliq**" is one ORG; Maliq is not a separate LOC.
5. **Annotate as written.** Keep the inflected form, the spelling and any typo or split word from the source. Never correct the text.
6. **Quotation marks and punctuation are outside the span.** shkolla "**Halit Bërzeshta**" -> the span starts after the opening quote. Commas, full stops and brackets after a name are not included.
7. **Capitals decide generic vs. specific.** "**Qeveria** ndan shumën" (capitalized, the specific government) -> ORG; "qeveria shqiptare" -> O. "**Kuvendi** nuk i ka parë" -> ORG.
8. **Coordinated names are separate spans.** "**Bashkisë Belsh**, **Bashkisë Cërrik** dhe **Bashkisë Elbasan**" -> three ORG spans, each including its own "Bashkisë". "hekurudha **Tiranë**–**Durrës**" -> two LOC spans.

## 4. Albanian-specific rules

Albanian inflects names for case and definiteness, so the span always follows the surface form in the text.

1. **Inflected forms are annotated whole.** "zonjës **Bilali**", "**Republikës së Kosovës**", "**Ministrisë së Financave**", "**Bashkinë Maliq**": the case ending stays inside the span.
2. **Linking articles inside a multi-word name are part of it.** i, e, të, së between the parts of an official name stay inside: "**Kuvendi i Shqipërisë**", "**Bashkia e Klosit**", "**Korniza e Investimeve për Ballkanin Perëndimor**". A linking article before the name is outside: "kryetare e **Kuvendit**".
3. **"në" + a place name ends a name; "në" + a lowercase noun inside an official name does not.** "**Gjykata Themelore** në **Pejë**", "**Fakultetit Ekonomik** në **Vlorë**", "**Dhomat e Specializuara** në **Hagë**" -> ORG + LOC. But "**Grupin Evropian të Autoriteteve Rajonale dhe Lokale në fushën e Imigracionit**" -> one ORG.
4. **Acronyms with suffixes: the whole token, but only if the acronym names an entity.** "**BERZH-it**", "**PDK-së**", "**KLSH-në**", "**MZSH-ve**", "**UÇK-së**" -> ORG including the hyphen and suffix. "TVSH-së" (value added tax) -> O.
5. **Lowercase head: only the name. Capitalized head: the whole name, inner quotes included.** "aeroporti i **Vlorës**", "qarkun **Elbasan**", shkolla "**Halit Bërzeshta**" -> only the name. "**Aeroporti Ndërkombëtar i Tiranës**" -> LOC; "**Universitetin "Ismail Qemali" Vlorë**", "**Ndërmarrjes Publike "Remisioni i Maqedonisë"**" -> one ORG each.
6. **Words in capitals are annotated like normal text.** "KUVENDI I SHQIPËRISË" in a sentence -> ORG.
7. **Text without diacritics is annotated as written.** Kosovo documents often drop ë and ç: "**Komisionin per Buxhet**", "**Komisionin per Integrim Evropian**" -> ORG.
8. **Nationality, ethnic and community words stay O.** shqiptar, kosovar, evropian, serbe; "komunitetet rom, ashkali dhe egjiptian". Exception: inside an official name ("Lista serbe", "Bashkimi Evropian").
9. **Foreign names in Albanian spelling are normal names.** "**Igor Simiq**", "**Aleksandar Veljanovski**", "**Dzerzhinsky-n**" -> PER, suffix included.
10. **Two places joined in one token are one span.** "**Milot-Rrëshen**" -> one LOC. With a spaced dash ("Tiranë – Durrës") they are two spans.

## 5. Hard cases and decisions

Each row is a real sentence pattern from the corpus with the label it gets; spans are in bold.

| Case | Example | Decision |
|---|---|---|
| Title + person | "...me Kryeministrin e Republikës së Shqipërisë, zotin **Edi Rama**" | Kryeministrin -> O; **Republikës së Shqipërisë** -> LOC; **Edi Rama** -> PER |
| Role with a minister's name | "...për ministrin **Hekuran Murati**" | ministrin -> O; name -> PER |
| Law titles in quotes | Projektligji "Për ratifikimin e marrëveshjes ndërmjet **Republikës së Shqipërisë** dhe **Republikës së Polonisë**..." | The title itself is not tagged; names inside it are tagged normally |
| Law numbers | "ligjin nr. 21/2024 "Për zonat e mbrojtura"" | All O |
| Constitution, rules of procedure | "neni 80 i Kushtetutës", "Rregullores së Kuvendit" | Kushtetutës, Rregullores -> O (documents, not entities); **Kuvendit** -> ORG |
| Courts | "**Gjykata Kushtetuese** u nda katër me katër" | ORG |
| Court + place with "në" | "**Gjykata Themelore** në **Pejë**" | ORG + LOC |
| Institution named after a person | shkolla "**Halit Bërzeshta**" | ORG, never PER |
| Municipality vs. city | "**Bashkia Maliq** ende nuk..., ndërsa **Tirana** duket..." | Bashkia Maliq -> ORG; Tirana -> LOC |
| Party groups | "nga **Grupi Parlamentar i PDK-së**"; "**GP Lista serbe**" | One ORG each, abbreviation GP included |
| City used for an institution | "vendimit në **Hagë**" | LOC (place names stay LOC, no metonymy) |
| Fund or framework | "**Kornizës së Investimeve për Ballkanin Perëndimor** (**WBIF**)" | Two MISC spans; brackets outside |
| Media with suffix | "punëtorët e **RTK-së**"; "**Radiotelevizionit të Kosovës**" | ORG |
| Name split by the PDF | "Krye ministri" | Annotate the fragments as written (here O, it is a role) |

### Added from the 300-sentence pilot sample

| Case | Example | Decision |
|---|---|---|
| Committee with an inserted word | "Shprehet **Komisioni përgjegjës për Bujqësinë, Ushqimin dhe Zhvillimin Rural**" | One ORG, inserted word included |
| Long committee name + place | "**Komisionit të Posaçëm parlamentar për fazën e dytë të Reformës Administrativo-Territoriale** në **Republikën e Shqipërisë**" | ORG up to "Territoriale"; then LOC |
| Positions, not institutions | "Ministri i Shtetit për Diasporën", "Zëvendësministër i Ekonomisë dhe Inovacionit", "Ministren e Arsimit" | O. A full institution name inside a position is still tagged: "Sekretarit të Përgjithshëm të **Këshillit të Evropës**" |
| Quoted titles vs. quoted names | Projektligji "Për krijimin e **Agjencisë Kombëtare të Shërbimeve Arsimore**"; fjalët: "**Rina Ajdari**" | A quoted title -> O, names inside it tagged; a quoted name -> its type |
| Documents | Kodit Zgjedhor, Strategjia Kombëtare e Diasporës, Direktivën për shërbimet mediatike, Kapitullit 27, acquis | O |
| Place inside a document title | Memorandumit të Mirëkuptimit të **Parisit** | Document -> O; Parisit -> LOC |
| Treaty body and trade bloc | "**Komitetit të Përbashkët të Marrëveshjes së Tregtisë së Lirë të Evropës Qendrore** (**CEFTA-s**)"; "vendeve të **CEFTA-s**" | One ORG + one ORG; CEFTA as a bloc -> ORG |
| Delegations, parliamentary bodies | "**Delegacionit të Kuvendit të Republikës së Maqedonisë së Veriut**", "**Konferencën e Kryetarëve**" | One ORG each, longest span |
| "Zoti" | "Do Zoti ta arrijmë" vs. "Zoti **Gonxhja**, lekët..." | God -> O; title Zoti -> O, surname -> PER |
| Surnames after roles or in lists | "Kryeministri **Kurti**"; "kolegët **Sinaj**, **Dhima** dhe **Pendavinji**" | Each surname -> PER |
| Signature abbreviation | "**Aleksandar Veljanovski**,d.v." | PER without ",d.v." |
| Capitalized salutations | "Media, Qytetarë të dashur", "Kabinet qeveritar" | O |
| Event containing a place | "**Festivalin e Kanës**" | One MISC; Kanës not tagged separately |
| Named departments | "**Drejtoria e Financës dhe Administrimit**", "**Sektorit të Redaktorëve**" | ORG when capitalized; "sektorit të monitorimit" -> O |

### Added after the pilot annotation (18 November 2026)

These are the cases where the pilot labels departed from the rules above; each row gives the rule to apply from now on.

| Case | Pilot label | Correct label |
|---|---|---|
| Documents: Constitution, codes, strategies, conventions, agreements, regulations, quoted law titles | Kushtetutën, Kodin e Punës, Strategjia Kombëtare e Energjisë, Konventës për Statusin e Refugjatëve, "Për tregjet e kriptoaseteve", MiCA, acquis -> MISC | O |
| Crime categories and phenomena | Vepra Penale, Trafikimi i Armëve dhe Municioneve, Dhuna në Familje, Fenomeni "Brain Drain" -> MISC | O |
| Generic or plural institution words | Komisioni (alone), Ministritë, Bordit, Ambasadën, Konsullatat, Parlamenti, firma e ndërtimit, shëndetin publik -> ORG | O, unless the full name follows. Kuvendi / Qeveria alone stay ORG (rule 7) |
| Common nouns and parties to an agreement | Palëve Kontraktuese, integrimit evropian -> MISC | O |
| Kosovo committees without diacritics | Komisionin per Buxhet, Komisionin per Integrim Evropian -> MISC | ORG |
| Companies | Albpetroli -> LOC | ORG |
| Agency acronyms | AKBN -> MISC | ORG |
| Name without its head word | "Evropën dhe Punët e Jashtme", "Transformimit Digjital", "Borxhit Shtetëror" -> ORG | Span the whole name with its head: Ministria për Evropën dhe Punët e Jashtme, Drejtoria e Përgjithshme e Borxhit Shtetëror. Only a fragment in the text -> O |
| Lowercase government + country | qeverisë së Kanadasë -> ORG | Only Kanadasë -> LOC |
| Punctuation inside the span | "RENJKP,", "Biblioteka Kombëtare.", "Komisionin per Buxhet;" | Span ends before the punctuation (fixed automatically at export) |
| Same span with two labels | ECO -> MISC and ORG | One label per span |
| Several institutions in a list | One span over "Ministrisë së Brendshme, Ministrisë së Financave dhe Ekonomisë, ..." (a suggestion error) | One span per institution |
| Professional bodies (correct in the pilot) | Urdhrit të Mjekut, Urdhrit të Farmacistëve -> ORG | ORG |

### Added after the test set and the self-agreement study (23-24 November 2026)

These cases came up in the consistency check of the test set, in the first evaluation, and in the comparison of the two self-agreement rounds.

| Case | Example | Decision |
|---|---|---|
| Constitution | "neni 80 i Kushtetutës", "Kushtetutës së Republikës së Kosovës" | Document -> O (never MISC or ORG); a country inside the title -> LOC |
| Official gazette | "Gazetën Zyrtare të Republikës së Kosovës" | One ORG, as in section 2 (the gazette is an institution and publication, not a document) |
| Institutions that sound abstract | "Shërbimin Informativ Kombëtar", "Shërbimin Ligjor Qeveritar" | ORG, never MISC |
| Institution acronyms, with or without suffix | IQBSUVP (Kosovo central inspectorate), KLSH, MZSH, BE, "BE-" | ORG; a trailing hyphen without a suffix stays outside the span |
| Job titles in staff tables | "Specialist finance", "Magazinier", "Shofer" | Roles -> O; a line that is only a staff table -> SKIP (section 1) |
| Long committee names with commas | "Komisioni për Burimet Natyrore, Infrastrukturën dhe Zhvillimin" | One ORG for the whole name; never cut at the first comma |
| Sentence with no entities | an ordinary sentence without names | Submit it empty; SKIP is only for lines that are not running text |

When a new hard case appears, add a row here and log it in section 7.

## 6. Annotation workflow and quality control

One annotator labels all data, so consistency is checked with self-agreement, a drift check and an automatic consistency script.

1. **Pilot.** Annotate 100 sentences from sample_300_seed42.tsv with these guidelines. Record the time taken. Turn every unclear case into a rule (sections 5 and 7). Result: guidelines v1.
2. **Test documents first.** Choose the test-set documents before the main annotation, by document, never by sentence, covering Albania and Kosovo and transcripts plus reports. Annotate the test set before any training data.
3. **Self-agreement, round 1.** Draw a fresh sample (`sample 150 7`), annotate it with v1, save the export, and do not open it again.
4. **Self-agreement, round 2.** Annotate the same sentences again in shuffled order in a separate project, at least 5 days later (2-3 weeks is the norm; the shorter gap is reported as a limitation). Compare with exact span-level F1, plus boundary-only and type-only agreement, per type.
5. **Rule-based suggestions are checked one by one****.** The test set was pre-annotated by rules (rules-v1); every suggestion was accepted, corrected or deleted by hand, and the automatic consistency check was run afterwards. The self-agreement sample is never pre-annotated, and no language model labels any gold data.
6. **Consistency check.** Before export, list every string labelled differently in different places (e.g. "Bashkia Tiranë" as ORG once and LOC once) and fix it by the rules.
7. **Drift check.** Halfway through the main annotation, re-annotate 50 earlier sentences and compare.

Target for self-agreement: exact span F1 >= 0.85 overall. Lower values mean a rule is unclear and needs rewriting, not that the data is unusable.

## 7. Decision log

Every new rule or change goes here, newest first, so the final guidelines can show how they evolved.

| Date | Case | Example | Decision | Section |
|---|---|---|---|---|
| 2026-11-24 | Self-agreement review (round 1 vs round 2) | Kushtetutës as MISC/ORG, Shërbimin Informativ Kombëtar, KLSH, MZSH, BE, staff-table titles, committee names cut at a comma | Seven hard cases added; empty sentences are submitted, not skipped | 1, 5 |
| 2026-11-23 | Gold correction after the first evaluation | IQBSUVP in 4 test sentences | MISC -> ORG; all saved predictions re-scored, no score changed by more than 0.5 points | 4, 5 |
| 2026-11-20 | Test-set consistency check | 99 flagged cases, then 55 (overlaps, merged institutions) | Each case fixed by the rules; overlapping spans removed, merged institutions split; 2 lines marked SKIP | 3, 6 |
| 2026-11-18 | Pilot review (299 sentences) | 191 suggestions kept, 0 corrected, 79 spans added | Pre-labels must be checked one by one; list spans and suggestion merges split | 5, 6 |
| 2026-11-18 | Generic and plural institution words | Komisioni alone, Ministritë, Ambasadën | O; Kuvendi and Qeveria alone stay ORG | 5 |
| 2026-11-18 | Crime categories, phenomena | Vepra Penale, Dhuna në Familje | O | 5 |
| 2026-11-18 | Partial names | Transformimit Digjital | Span the whole name with its head, else O | 5 |
| 2026-11-16 | Lines that are not running text | Table rows, JSON, headers, signatures | SKIP, not annotated (17 of 300 in the pilot sample) | 1 |
| 2026-11-16 | "në" inside names | Gjykata Themelore në Pejë vs. ... në fushën e Imigracionit | Ends the name only before a place name | 4 |
| 2026-11-16 | Acronyms that are not entities | TVSH-së | O | 4 |
| 2026-11-16 | Documents vs. MISC | Strategjia Kombëtare e Diasporës, Kodit Zgjedhor | All documents O; MISC narrowed to events, funds, programmes, portals, works | 2 |
| 2026-11-16 | Quoted titles vs. quoted names | "Për krijimin e ..." vs. "Rina Ajdari" | Titles O, names tagged | 5 |
| 2026-11-16 | Positions | Ministri i Shtetit për Diasporën | O; full institution names inside still tagged | 5 |
| 2026-11-16 | Law titles and the Constitution | "Për zonat e mbrojtura", Kushtetutës | Not tagged; names inside titles are tagged | 5 |
| 2026-11-16 | Countries acting as actors | "Shqipëria nënshkroi..." | Always LOC, no metonymy | 2 |
| 2026-11-16 | Nationality adjectives | shqiptar, kosovar, serbe | O, unless part of an official name | 4 |
| 2026-11-16 | Tag set | - | PER, ORG, LOC, MISC only, for comparability with WikiANN and AlbNER | 1 |

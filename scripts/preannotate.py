#!/usr/bin/env python3
"""
Usage: python preannotate.py SENTENCES.tsv
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

MODEL_VERSION = "rules-v1"

TITLES = {
    "zoti", "zotit", "zotin", "zotëri", "z", "zonja", "zonjës", "zonjën", "zonjë", "znj",
    "deputeti", "deputetit", "deputetin", "deputetja", "deputetes", "deputeten", "deputete",
    "ministri", "ministrit", "ministrin", "ministër", "ministrja", "ministres", "ministren", "ministre",
    "zëvendësministri", "zëvendësministrja", "zëvendësministres", "zëvendësministren",
    "kryeministri", "kryeministrit", "kryeministrin", "kryetari", "kryetarit", "kryetarin",
    "kryetarja", "kryetares", "kryetaren", "kolegu", "kolegut", "kolegun", "kolegia",
    "kolegen", "koleges", "kolegët", "relatori", "relatorit", "relatorin", "relatorja",
    "nënkryetari", "nënkryetarja", "drejtori", "drejtorit", "drejtorin", "drejtoresha",
    "drejtoreshës", "drejtoreshën", "prof", "dr", "presidenti", "presidentit", "presidenten",
    "ambasadori", "ambasadorit", "sekretari", "sekretarja", "avokati",
}
TITLE_WORDS_IN_SPEAKERS = {
    "Ministri", "Ministrja", "Ministrit", "Kryetarja", "Kryetari", "Kryesuesi", "Kryesuesja",
    "Zëvendëskryeministri", "Zëvendëskryeministrja", "Zëvendësministri", "Zëvendësministrja",
    "Kryeministri", "Kryeministrja", "Presidentja", "Presidenti", "Deputeti", "Deputetja",
    "Ushtruesi", "Detyrës", "Së", "Parë", "E", "I", "Të", "Dhe",
}

ORG_HEADS = {}
for stem, forms in {
    "komision": "Komisioni Komisionit Komisionin Komisioneve Komisioni",
    "ministri": "Ministria Ministrisë Ministrinë Ministrive Ministritë",
    "gjykat": "Gjykata Gjykatës Gjykatën Gjykatat Gjykatave",
    "kuvend": "Kuvendi Kuvendit Kuvendin",
    "këshill": "Këshilli Këshillit Këshillin",
    "agjenci": "Agjencia Agjencisë Agjencinë Agjencitë",
    "bashki": "Bashkia Bashkisë Bashkinë Bashkitë",
    "universitet": "Universiteti Universitetit Universitetin",
    "bank": "Banka Bankës Bankën Bankat",
    "parti": "Partia Partisë Partinë",
    "grup": "Grupi Grupit Grupin",
    "drejtori": "Drejtoria Drejtorisë Drejtorinë Drejtoritë",
    "autoritet": "Autoriteti Autoritetit Autoritetin",
    "inspektorat": "Inspektorati Inspektoratit Inspektoratin",
    "prokurori": "Prokuroria Prokurorisë Prokurorinë",
    "qeveri": "Qeveria Qeverisë Qeverinë",
    "institut": "Instituti Institutit Institutin",
    "fakultet": "Fakulteti Fakultetit Fakultetin",
    "delegacion": "Delegacioni Delegacionit Delegacionin",
    "konferenc": "Konferenca Konferencës Konferencën",
    "komitet": "Komiteti Komitetit Komitetin",
    "sekretariat": "Sekretariati Sekretariatit Sekretariatin",
    "ent": "Enti Entit Entin",
    "zyr": "Zyra Zyrës Zyrën",
    "shoqat": "Shoqata Shoqatës Shoqatën",
    "sektor": "Sektori Sektorit Sektorin",
    "departament": "Departamenti Departamentit Departamentin",
    "dhom": "Dhoma Dhomës Dhomën Dhomat Dhomave",
    "kryesi": "Kryesia Kryesisë Kryesinë",
    "polici": "Policia Policisë Policinë",
    "organizat": "Organizata Organizatës Organizatën",
    "bashkim": "Bashkimi Bashkimit Bashkimin",
    "list": "Lista Listës Listën",
    "avokat": "Avokati Avokatit Avokatin",
    "akademi": "Akademia Akademisë Akademinë",
    "ndërmarrj": "Ndërmarrja Ndërmarrjes Ndërmarrjen",
    "shërbim": "Shërbimi Shërbimit Shërbimin",
    "kontroll": "Kontrolli Kontrollit",
    "byro": "Byroja Byrosë Byronë",
    "radiotelevizion": "Radiotelevizioni Radiotelevizionit Radiotelevizionin",
    "kabinet": "Kabineti Kabinetit Kabinetin",
    "sindikat": "Sindikata Sindikatës Sindikatën",
    "fond": "Fondi Fondit Fondin",
    "nënkomision": "Nënkomisioni Nënkomisionit Nënkomisionin",
    "spital": "Spitali Spitalit Spitalin",
    "gazet": "Gazeta Gazetës Gazetën",
}.items():
    for f in forms.split():
        ORG_HEADS[f] = stem
ORG_STANDALONE = {"Kuvendi", "Kuvendit", "Kuvendin", "Qeveria", "Qeverisë", "Qeverinë",
                  "Kryesia", "Kryesisë", "Kryesinë", "Policia", "Policisë", "Policinë",
                  "Prokuroria", "Prokurorisë"}
MISC_HEADS = {"fond"}

ORG_ACRONYMS = set("""BE PDK LDK AAK PS PD LSI VV UÇK SPAK KLSH KLP KLGJ GJEDNJ BERZH BEI NATO OSBE
OKB CEFTA RTK RTSH RTM AMVV MZSH ERLAI ILD OST OSHEE ASHK AKSHI QKB SIGMA KPP KQZ AKP ISHP BSH FMN
KE PE KiE BB AKU AKZM ISSH ASP KRRT AKSHE ZVRPP IKMT AMF QKMF QMF GJK KGJK KPK AQP ATK BQK FSK MPJ
MPB MD MASR MFE MIE MKTS MEI MB MSHMS MTM MBPZHR UNMIK EULEX KFOR OSCE USAID UNDP UNICEF FAO OBT
GP LS SHBA""".split())
NOT_ENTITY_ACRONYMS = {"TVSH", "NIPT", "NUIS", "GDP", "PBB", "TVA", "PR", "IT", "KM", "PET", "CT",
                       "DP", "NP", "OB", "LEK", "EUR", "USD", "SMS", "PDF", "VKM", "QAP", "ID"}
LOC_ACRONYMS = {"SHBA"}
MISC_NAMES = {"WBIF", "IPA", "e-Albania", "Erasmus", "Horizon"}
MISC_PHRASES = ["Festivalin e Kanës", "Festivali i Kanës", "Plani i Rritjes", "Planit të Rritjes", "Planin e Rritjes",
                "Western Balkans Fund", "Lufta e Dytë Botërore", "Luftës së Dytë Botërore",
                "Procesi i Berlinit", "Procesit të Berlinit"]

LOC_BASE = """Shqipëri Kosovë Maqedoni Serbi Greqi Itali Gjermani Francë Austri Zvicër Turqi Kroaci
Slloveni Bosnjë Bullgari Rumani Hungari Poloni Spanjë Angli Britani Amerikë Rusi Ukrainë Kinë
Japoni Belgjikë Holandë Suedi Norvegji Danimarkë Finlandë Irlandë Portugali Çeki Sllovaki Moldavi
Evropë Europë Ballkan Azi Afrikë Bangladesh Kamerun Izrael Egjipt Australi Milano Kopenhagë
Tiranë Durrës Vlorë Elbasan Korçë Fier Berat Sarandë Lushnjë Kukës Lezhë Dibër Pogradec Kavajë
Krujë Përmet Tepelenë Delvinë Rinas Shëngjin Himarë Divjakë Mat Klos Belsh Cërrik Maliq Bulqizë
Librazhd Peqin Gramsh Kuçovë Mallakastër Patos Roskovec Selenicë Mirditë Pukë Tropojë
Prishtinë Prizren Pejë Gjakovë Mitrovicë Ferizaj Gjilan Podujevë Vushtrri Drenas Malishevë Deçan
Rahovec Suharekë Lipjan Kamenicë Dragash Istog Klinë Skenderaj Obiliq Shtime Kaçanik
Shkup Tetovë Gostivar Strugë Kumanovë Kërçovë Ohër Manastir Preshevë Bujanoc Medvegjë Ulqin Tuz
Bruksel Strasburg Hagë Paris Romë Athinë Beograd Vjenë Berlin Londër Uashington Gjenevë
Domje Nartë Voskopojë Shupenzë Maqellarë""".split()
LOC_IRREGULAR = {
    "Shkodër": "Shkodër Shkodra Shkodrës Shkodrën",
    "Gjirokastër": "Gjirokastër Gjirokastra Gjirokastrës Gjirokastrën",
    "Vorë": "Vorë Vora Vorës Vorën",
    "Hagë": "Hagë Haga Hagës Hagën",
    "Zvicër": "Zvicër Zvicra Zvicrës Zvicrën",
    "Ohër": "Ohër Ohri Ohrit Ohrin",
    "Meja": "Meja Mejës Mejën",
    "Mallakastër": "Mallakastër Mallakastra Mallakastrës",
    "Evropë": "Evropë Evropa Evropës Evropën Europë Europa Europës Europën",
    "Amerikë": "Amerikë Amerika Amerikës Amerikën",
    "Mat": "Matit Matin",
    "Kanada": "Kanada Kanadaja Kanadasë Kanadanë",
    "SHBA": "SHBA SHBA-të SHBA-ve",
}
LOC_PHRASES = ["Ballkanin Perëndimor", "Ballkani Perëndimor", "Ballkanit Perëndimor",
               "Evropës Qendrore", "Evropa Qendrore", "Evropën Qendrore", "Evropës Juglindore",
               "Mali i Zi", "Malit të Zi", "Malin e Zi", "Bosnjë Hercegovinë", "Bosnjë Hercegovinës",
               "Bosnje e Hercegovinë", "Nju Jork", "Fushë Kosovë", "Fushë Kosovës",
               "Maqedonia e Veriut", "Maqedonisë së Veriut", "Maqedoninë e Veriut",
               "Rruga e Kombit", "Rrugës së Kombit", "Mbretëria e Bashkuar", "Mbretërisë së Bashkuar"]
CONNECT = {"i", "e", "të", "së", "për", "dhe", "mbi", "ndaj"}
STOP_CAP = {"Neni", "Nenit", "Nenin", "Kreu", "Pika", "Pikës", "Ligji", "Ligjit", "Vendimi",
            "Vendimit", "Projektligji", "Projektligjit", "Në", "Për", "Nga", "Me", "Dhe",
            "Dhënie", "Shprehet", "Masa", "Masës", "Neni", "Propozues"}
LOWER_INSIDE_ORG = {"përgjegjës", "parlamentar", "parlamentare", "kombëtar", "kombëtare",
                    "posaçëm", "posaçme"}


def inflect(base):
    if base in LOC_IRREGULAR:
        return LOC_IRREGULAR[base].split()
    forms = {base}
    if base.endswith("ë"):
        s = base[:-1]
        forms |= {s + "a", s + "ës", s + "ën", s + "ë"}
    elif base.endswith("i"):
        forms |= {base + "a", base + "së", base + "në", base + "ja", base + "të"}
    else:
        forms |= {base + "i", base + "it", base + "in", base + "u", base + "ut", base + "un"}
    return sorted(forms)


LOC_BASE += ["Meja", "Ohër", "Kanada"]
LOC_FORMS = {f for b in LOC_BASE for f in inflect(b)}
for v in LOC_IRREGULAR.values():
    LOC_FORMS |= set(v.split())

TOKEN_RE = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿËëÇçŠšŽžĆćČčĐđ]+(?:[-‐’'][A-Za-zÀ-ÖØ-öø-ÿËëÇçŠšŽžĆćČčĐđ]+)*|\d+(?:[.,]\d+)*|\S")
UP = re.compile(r"^[A-ZÇËŠŽĆČĐ]")


def tokens(text):
    return [(m.start(), m.end(), m.group()) for m in TOKEN_RE.finditer(text)]


def is_cap(t):
    return bool(UP.match(t)) and t.lower() != t


def base_acronym(t):
    return re.split(r"[-‐]", t, maxsplit=1)[0]


def is_acronym(t):
    b = base_acronym(t)
    return len(b) >= 2 and b.isupper() and b.isalpha() and len(b) <= 7


def strip_case(name):
    for suf in ("it", "in", "ës", "ën", "së", "ut", "un", "es", "en", "ja", "a", "i", "u", "ë", "s", "n", "t"):
        if name.endswith(suf) and len(name) - len(suf) >= 3:
            return name[: -len(suf)]
    return name


def learn_people(pool_path):
    full, surnames = Counter(), Counter()
    if not pool_path.exists():
        return set(), set()
    for line in open(pool_path, encoding="utf-8"):
        s = json.loads(line)
        sp = s.get("speaker") or ""
        parts = [p for p in re.split(r"\s+", sp) if p and p not in TITLE_WORDS_IN_SPEAKERS]
        if len(parts) >= 2 and all(is_cap(p) for p in parts):
            full[" ".join(parts)] += 1
            surnames[strip_case(parts[-1])] += 1
        toks = [t for _, _, t in tokens(s["text"])]
        for i, t in enumerate(toks[:-1]):
            if t.lower().rstrip(".") in TITLES:
                name = []
                for u in toks[i + 1:i + 4]:
                    if is_cap(u) and u not in ORG_HEADS and u not in LOC_FORMS and not is_acronym(u):
                        name.append(u)
                    else:
                        break
                if len(name) >= 2:
                    full[" ".join(name)] += 1
                    surnames[strip_case(name[-1])] += 1
                elif len(name) == 1:
                    surnames[strip_case(name[0])] += 1
    return {n for n in full}, {s for s in surnames if len(s) >= 3}


def extend_name(toks, i, person_starts=frozenset()):
    j, end, has_per = i + 1, i, False
    while j < len(toks):
        t = toks[j][2]
        nxt = toks[j + 1][2] if j + 1 < len(toks) else ""
        if t in STOP_CAP or (t, nxt) in person_starts or (t in FIRST_NAMES and is_cap(nxt)):
            break
        if (len(t) == 1 and t.isupper()) or (t.isupper() and len(t) > 7 and not toks[i][2].isupper()):
            break
        if j > i + 1 and toks[j - 1][2] in {",", "dhe", "e"} and t in ORG_HEADS:
            break
        if is_cap(t) or is_acronym(t):
            end = j; j += 1
        elif t in CONNECT and (is_cap(nxt) or is_acronym(nxt)) and not (t == "dhe" and nxt in ORG_HEADS):
            has_per |= t == "për"
            j += 1
        elif t.lower() in LOWER_INSIDE_ORG and j == i + 1:
            j += 1
        elif t == "," and is_cap(nxt) and nxt not in ORG_HEADS and any(toks[k][2] == "dhe" and k + 1 < len(toks) and is_cap(toks[k + 1][2])
                                              for k in range(j + 1, min(j + 6, len(toks) - 1))):
            j += 1
        elif t in {"“", "\"", "„", "”"} and is_cap(nxt):
            j += 1
        else:
            break
    return end


FIRST_NAMES = set()


def annotate(text, people_full, people_surnames):
    toks = tokens(text)
    person_starts = {tuple(n.split()[:2]) for n in people_full if len(n.split()) >= 2}
    cands = []
    words = [t for _, _, t in toks]

    def phrase_hits(phrases, label):
        for ph in phrases:
            ptoks = [t for _, _, t in tokens(ph)]
            n = len(ptoks)
            for i in range(len(words) - n + 1):
                if words[i:i + n] == ptoks:
                    cands.append((i, i + n - 1, label))
    phrase_hits(LOC_PHRASES, "LOC")
    phrase_hits(MISC_PHRASES, "MISC")
    phrase_hits(sorted(people_full, key=len, reverse=True), "PER")

    for i, (_, _, t) in enumerate(toks):
        low = t.lower().rstrip(".")
        if re.match(r"Republik(a|ës|ën|e)$", t):
            end = extend_name(toks, i, person_starts)
            if end > i:
                cands.append((i, end, "LOC"))
            continue
        if t in ORG_HEADS:
            end = extend_name(toks, i, person_starts)
            stem = ORG_HEADS[t]
            if end > i:
                cands.append((i, end, "MISC" if stem in MISC_HEADS else "ORG"))
            elif t in ORG_STANDALONE:
                cands.append((i, i, "ORG"))
            continue
        if is_acronym(t):
            b = base_acronym(t)
            if b in NOT_ENTITY_ACRONYMS:
                continue
            if b in LOC_ACRONYMS:
                cands.append((i, i, "LOC"))
            elif b in MISC_NAMES:
                cands.append((i, i, "MISC"))
            elif b in ORG_ACRONYMS or "-" in t:
                cands.append((i, i, "ORG"))
            continue
        if t in MISC_NAMES:
            cands.append((i, i, "MISC"))
            continue
        if low in TITLES:
            name_end = None
            first = i + 2 if i + 1 < len(toks) and toks[i + 1][2] == "." else i + 1
            for k in range(first, min(first + 3, len(toks))):
                u = toks[k][2]
                if is_cap(u) and u not in ORG_HEADS and u not in LOC_FORMS and not is_acronym(u) \
                        and not u.startswith("Republik"):
                    name_end = k
                else:
                    break
            if name_end is not None:
                cands.append((first, name_end, "PER"))
            continue
        if t in LOC_FORMS:
            cands.append((i, i, "LOC"))
            continue
        if is_cap(t) and i > 0 and strip_case(t) in people_surnames and len(t) >= 4:
            prev = toks[i - 1][2]
            if prev in {",", "dhe"} or prev.lower() in TITLES:
                cands.append((i, i, "PER"))

    cands.sort(key=lambda c: (-(c[1] - c[0]), c[0]))
    taken, result = set(), []
    for a, b, lab in cands:
        if any(k in taken for k in range(a, b + 1)):
            continue
        taken.update(range(a, b + 1))
        result.append((toks[a][0], toks[b][1], lab))
    def free_name_run(k):
        run = []
        while k < len(toks) and len(run) < 3:
            u = toks[k][2]
            if is_cap(u) and u not in ORG_HEADS and u not in LOC_FORMS and u not in STOP_CAP \
                    and not is_acronym(u) and k not in taken:
                run.append(k); k += 1
            else:
                break
        return run
    list_start = {k + 1 for k in range(len(toks) - 1)
                  if toks[k][2] == ":" and k > 0 and toks[k - 1][2].lower() in {"pjesë", "mungojnë", "ftuar"}}
    changed = True
    while changed:
        changed = False
        per_ends = {toks[e_][0] for e_ in []}
        spans = sorted(result)
        per_tok = set()
        for s_, e_, lab in spans:
            if lab == "PER":
                per_tok |= {k for k, t in enumerate(toks) if t[0] >= s_ and t[1] <= e_}
        for k in range(len(toks)):
            if k in taken:
                continue
            prev_sep = k > 0 and toks[k - 1][2] in {",", "dhe"} and k > 1 and (k - 2) in per_tok
            starts_list = k in list_start
            run = free_name_run(k)
            if not run:
                continue
            after = run[-1] + 1
            next_is_per = after + 1 < len(toks) and toks[after][2] in {",", "dhe"} and (after + 1) in per_tok
            if (prev_sep or starts_list or next_is_per) and (len(run) >= 2 or prev_sep):
                taken.update(run)
                result.append((toks[run[0]][0], toks[run[-1]][1], "PER"))
                changed = True
                break
    return sorted(result)


def looks_like_skip(text):
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return True
    if "{" in text or '":' in text or "\\r\\n" in text:
        return True
    digits = sum(c.isdigit() for c in text)
    if digits > 0.25 * len(text.replace(" ", "")):
        return True
    up = sum(c.isupper() for c in letters)
    if up > 0.6 * len(letters) and len(text.split()) >= 4:
        return True
    if re.search(r"\b[IVX]{1,4}-\d\b|\b\d [IVX]{1,4}-\d\b", text):
        return True
    return False


def read_tasks(path):
    path = Path(path)
    if path.suffix == ".json":
        data = json.load(open(path, encoding="utf-8"))
        return [d["data"] if "data" in d else d for d in data]
    rows = []
    with open(path, encoding="utf-8") as f:
        header = f.readline().rstrip("\n").split("\t")
        for line in f:
            vals = line.rstrip("\n").split("\t")
            if len(vals) == len(header):
                rows.append(dict(zip(header, vals)))
    return rows


def main():
    if len(sys.argv) < 2:
        print(__doc__); return
    src = Path(sys.argv[1])
    pool = Path("sentence_pool/sentences.jsonl")
    people_full, people_surnames = learn_people(pool)
    FIRST_NAMES.update(n.split()[0] for n in people_full if len(n.split()) >= 2)
    print(f"Emra personash të mësuar nga korpusi: {len(people_full)} emra të plotë, "
          f"{len(people_surnames)} mbiemra")
    tasks, counts, n_skip = [], Counter(), 0
    for row in read_tasks(src):
        text = row["text"]
        result = []
        if looks_like_skip(text):
            n_skip += 1
            result.append({"from_name": "skip", "to_name": "text", "type": "choices",
                           "value": {"choices": ["SKIP"]}})
        else:
            for s, e, lab in annotate(text, people_full, people_surnames):
                counts[lab] += 1
                result.append({"from_name": "label", "to_name": "text", "type": "labels",
                               "value": {"start": s, "end": e, "text": text[s:e], "labels": [lab]}})
        tasks.append({"data": row, "predictions": [{"model_version": MODEL_VERSION, "result": result}]})
    out = src.with_name(src.stem + "_preannotated.json")
    json.dump(tasks, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"{len(tasks)} fjali | sugjerime: " + ", ".join(f"{k}={v}" for k, v in sorted(counts.items()))
          + f" | SKIP={n_skip}")
    print(f"Ruajtur te: {out}")


if __name__ == "__main__":
    main()

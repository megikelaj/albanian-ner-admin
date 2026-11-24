#!/usr/bin/env python3
"""
Usage: python opendata_inventory_v2.py probe|download|inventory
"""
import hashlib
import json
import re
import sys
import time
from pathlib import Path
from urllib.parse import urljoin, urlparse

import logging
import warnings

import requests

logging.getLogger("pypdf").setLevel(logging.ERROR)
warnings.filterwarnings("ignore")

BASE = "https://opendata.gov.al"
API = BASE + "/api"
OUT = Path("opendata_al")
RAW, FILES = OUT / "raw", OUT / "files"
DELAY = 1.0
MAX_BYTES = 50 * 1024 ** 2
FILE_EXT = (".csv", ".json", ".xml", ".xlsx", ".xls", ".pdf", ".docx", ".doc",
            ".rdf", ".txt", ".odt")

session = requests.Session()
session.headers.update({
    "User-Agent": "thesis-research-inventory/0.1 (academic, non-commercial)",
    "Accept": "application/json",
})

FILTER_BASE = {
    "title": None, "metadataQuality": None, "keyWords": None, "formats": None,
    "categories": None, "publishers": None, "isFromOpenDataPortal": None,
    "license": None, "publishedFrom": None, "publishedTo": None,
    "requestedPage": 1, "requestedPageSize": 10,
}
PAGE_SIZES = (10,)

SPARQL_LIST = """PREFIX dcat: <http://www.w3.org/ns/dcat#>
PREFIX dct: <http://purl.org/dc/terms/>
SELECT ?dataset ?title ?url WHERE {
  ?dataset a dcat:Dataset ; dct:title ?title ; dcat:distribution ?dist .
  OPTIONAL { ?dist dcat:downloadURL ?d }
  OPTIONAL { ?dist dcat:accessURL ?a }
  BIND(COALESCE(?d, ?a) AS ?url)
}"""


def save(name, data):
    RAW.mkdir(parents=True, exist_ok=True)
    (RAW / name).write_text(json.dumps(data, ensure_ascii=False, indent=2),
                            encoding="utf-8")


def call(method, path, **kw):
    time.sleep(DELAY)
    url = path if path.startswith("http") else API + path
    try:
        r = session.request(method, url, timeout=60, **kw)
        if "json" in r.headers.get("content-type", ""):
            return r.status_code, r.json()
        return r.status_code, r.text[:2000]
    except Exception as e:
        return None, str(e)


def shape(obj, depth=0, max_depth=3):
    if depth >= max_depth:
        return type(obj).__name__
    if isinstance(obj, dict):
        return {k: shape(v, depth + 1) for k, v in list(obj.items())[:15]}
    if isinstance(obj, list):
        return [shape(obj[0], depth + 1)] if obj else []
    return type(obj).__name__


def walk_strings(obj):
    if isinstance(obj, dict):
        for v in obj.values():
            yield from walk_strings(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from walk_strings(v)
    elif isinstance(obj, str):
        yield obj


URL_RE = re.compile(r"https?://[^\s\"'<>]+", re.I)
SLUG_IN_URL = re.compile(r"/dataset/([\w\-]+)")


def find_urls(obj):
    found = set()
    for s in walk_strings(obj):
        for u in URL_RE.findall(s):
            if urlparse(u).path.lower().endswith(FILE_EXT):
                found.add(u)
        if s.startswith("/") and s.lower().endswith(FILE_EXT):
            found.add(urljoin(BASE, s))
    return found


def find_slugs(obj):
    slugs = set()

    def walk(o):
        if isinstance(o, dict):
            for k in ("slug", "Slug"):
                v = o.get(k)
                if isinstance(v, str) and re.fullmatch(r"[\w\-]+", v):
                    slugs.add(v)
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
    walk(obj)
    for s in walk_strings(obj):
        slugs.update(SLUG_IN_URL.findall(s))
    return slugs


def sparql(query):
    for method, kw in (("GET", {"params": {"query": query}}),
                       ("POST", {"data": {"query": query}})):
        code, body = call(method, "/Sparql",
                          headers={"Accept": "application/sparql-results+json"}, **kw)
        if code == 200 and isinstance(body, dict) and "results" in body:
            return body
    return None


def probe():
    for path in ("/Institution", "/DcatCategory", "/Dataset/getMostAccessedDataSets"):
        code, body = call("GET", path)
        print(f"GET {path} -> {code}")
        if isinstance(body, (dict, list)):
            print("   ", json.dumps(shape(body), ensure_ascii=False)[:600])
            save(path.strip("/").replace("/", "_") + ".json", body)
        else:
            print("   ", str(body)[:200])
    for size in PAGE_SIZES:
        b = {**FILTER_BASE, "requestedPageSize": size}
        code, body = call("POST", "/Dataset/filter", json=b)
        print(f"POST /Dataset/filter (pageSize={size}) -> {code}, "
              f"{len(find_slugs(body)) if isinstance(body, (dict, list)) else 0} datasete")
        if isinstance(body, (dict, list)):
            print("   ", json.dumps(shape(body), ensure_ascii=False)[:600])
            save(f"filter_size{size}.json", body)
    res = sparql(SPARQL_LIST + " LIMIT 5")
    print("SPARQL ->", "funksionon" if res else "nuk funksionoi")
    if res:
        save("sparql_sample.json", res)
    print(f"\nPërgjigjet e plota u ruajtën te {RAW}/")


def collect():
    slugs, url_slug = set(), {}
    res = sparql(SPARQL_LIST)
    if res:
        for b in res["results"]["bindings"]:
            m = SLUG_IN_URL.search(b["dataset"]["value"])
            slug = m.group(1) if m else ""
            if slug:
                slugs.add(slug)
            if "url" in b:
                url_slug[b["url"]["value"]] = slug
        print(f"SPARQL: {len(slugs)} datasete, {len(url_slug)} URL skedarësh")

    for size in PAGE_SIZES:
        found_here = 0
        for page in range(1, 2000):
            body = {**FILTER_BASE, "requestedPage": page, "requestedPageSize": size}
            code, data = call("POST", "/Dataset/filter", json=body)
            if code != 200 or not isinstance(data, (dict, list)):
                print(f"  faqja {page}: ndaloi (status {code})")
                break
            for u in find_urls(data):
                url_slug.setdefault(u, "")
            new = find_slugs(data) - slugs
            if not new:
                break
            slugs |= new
            found_here += len(new)
            print(f"  faqja {page} (madhësia {size}): +{len(new)}, gjithsej {len(slugs)}")
        if found_here:
            break
    print(f"Gjithsej {len(slugs)} datasete të gjetura")

    for i, s in enumerate(sorted(slugs), 1):
        code, data = call("GET", f"/Dataset/get/{s}")
        if code == 200 and isinstance(data, (dict, list)):
            save(f"dataset_{s}.json", data)
            for u in find_urls(data):
                url_slug[u] = s
        print(f"[{i}/{len(slugs)}] {s}: {code}")
    return url_slug


def download():
    url_slug = collect()
    FILES.mkdir(parents=True, exist_ok=True)
    manifest = []
    for i, (u, slug) in enumerate(sorted(url_slug.items()), 1):
        name = hashlib.md5(u.encode()).hexdigest()[:10] + "_" + Path(urlparse(u).path).name[-80:]
        dest = FILES / name
        status = "ekzistonte"
        if not dest.exists():
            time.sleep(DELAY)
            try:
                with session.get(u, stream=True, timeout=120,
                                 headers={"Accept": "*/*"}) as r:
                    r.raise_for_status()
                    size = 0
                    with open(dest, "wb") as f:
                        for chunk in r.iter_content(65536):
                            size += len(chunk)
                            if size > MAX_BYTES:
                                raise ValueError("mbi kufirin e madhësisë")
                            f.write(chunk)
                status = "ok"
            except Exception as e:
                dest.unlink(missing_ok=True)
                status = f"gabim: {e}"
        manifest.append({"url": u, "file": name, "slug": slug, "status": status})
        print(f"[{i}/{len(url_slug)}] {status}  {u}")
    (OUT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2),
                                       encoding="utf-8")
    print(f"\nManifesti: {OUT / 'manifest.json'}")


PII_COLS = re.compile(
    r"emer|emri|mbiem|atesi|atësi|personal|\bnid\b|nipt|nuis|telefon|cel\b|e-?mail|"
    r"adres|datelindj|datëlindj|iban|llogari|perfitues|përfitues|fermer", re.I)
PATTERNS = {
    "email": re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+"),
    "telefon": re.compile(r"(?:\+355\s?|00355\s?|\b0)6[789]\s?\d{3}\s?\d{4}\b"),
    "iban_al": re.compile(r"\bAL\d{2}[A-Z0-9 ]{20,32}\b"),
    "id_10kar": re.compile(r"\b[A-Z]\d{8}[A-Z]\b"),
}
SENSITIVE_NAME = re.compile(r"emeror|perfitues|përfitues|viktim|trafik|ndihm|\bpak\b|_pak\b", re.I)
TABLE_EXT = (".csv", ".xlsx", ".xls")
DOC_EXT = (".pdf", ".docx", ".doc", ".odt", ".txt")


def read_text(path):
    raw = path.read_bytes()
    for enc in ("utf-8-sig", "cp1250", "latin-1"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return ""


def fix_header(df):
    unnamed = sum(str(c).startswith("Unnamed") for c in df.columns)
    if len(df.columns) == 0 or unnamed < len(df.columns) / 2:
        return df
    for i in range(min(15, len(df))):
        row = df.iloc[i]
        if row.notna().sum() >= max(2, len(df.columns) / 2):
            new = df.iloc[i + 1:].copy()
            new.columns = [str(v) if v == v else f"col{j}" for j, v in enumerate(row)]
            return new.reset_index(drop=True)
    return df


def read_tables(path, ext):
    import pandas as pd
    if ext == ".csv":
        for enc in ("utf-8-sig", "cp1250", "latin-1"):
            try:
                df = pd.read_csv(path, sep=None, engine="python", encoding=enc,
                                 dtype=str, on_bad_lines="skip")
                raw_lines = sum(1 for ln in read_text(path).splitlines() if ln.strip()) - 1
                note = ""
                if raw_lines > len(df):
                    note = (f"CSV i keqformatuar: {raw_lines} rreshta, "
                            f"{raw_lines - len(df)} u anashkaluan në analizë")
                return [df], note, raw_lines
            except Exception:
                continue
        return [], "CSV nuk u lexua", None
    try:
        engine = "xlrd" if ext == ".xls" else None
        sheets = pd.read_excel(path, sheet_name=None, dtype=str, engine=engine)
        dfs = [fix_header(d.dropna(how="all")) for d in sheets.values()]
        return dfs, f"{len(dfs)} fletë", None
    except ImportError as e:
        return [], f"mungon libraria: {e}", None
    except Exception as e:
        return [], f"Excel nuk u lexua: {str(e)[:80]}", None


def read_document(path, ext):
    try:
        if ext == ".pdf":
            from pypdf import PdfReader
            r = PdfReader(str(path))
            text = "\n".join((p.extract_text() or "") for p in r.pages)
            note = "PDF i skanuar? (pa tekst)" if len(text.split()) < 20 * max(1, len(r.pages)) / 10 else ""
            return text, len(r.pages), note
        if ext == ".docx":
            import docx
            d = docx.Document(str(path))
            parts = [p.text for p in d.paragraphs]
            for t in d.tables:
                for row in t.rows:
                    parts.append(" ".join(c.text for c in row.cells))
            return "\n".join(parts), None, ""
        if ext == ".txt":
            return read_text(path), None, ""
        return "", None, f"format {ext} - hape me dorë (p.sh. konvertoje në .docx)"
    except ImportError as e:
        return "", None, f"mungon libraria: {e}"
    except Exception as e:
        return "", None, f"gabim leximi: {str(e)[:80]}"


def inventory():
    import pandas as pd
    manifest = {m["file"]: m for m in json.loads((OUT / "manifest.json").read_text(encoding="utf-8"))}
    rows = []
    files = sorted(p for p in FILES.iterdir() if p.is_file())
    for n, path in enumerate(files, 1):
        try:
            rows.append(analyze_file(path, manifest))
        except Exception as e:
            rows.append({"file": path.name, "format": path.suffix.lower().lstrip("."),
                         "note": f"gabim gjatë analizës: {type(e).__name__}: {str(e)[:80]}"})
        if n % 50 == 0:
            print(f"  analizuar {n}/{len(files)}")
    finish_inventory(rows)


def analyze_file(path, manifest):
    if True:
        ext = path.suffix.lower()
        rec = {"file": path.name, "slug": manifest.get(path.name, {}).get("slug", ""),
               "format": ext.lstrip("."), "kb": round(path.stat().st_size / 1024, 1),
               "rows": None, "cols": None, "pages": None, "words": None, "columns": "",
               "free_text_cols": "", "max_mean_words": 0.0, "pii_like_cols": "", "note": ""}
        text = ""
        if ext in TABLE_EXT:
            dfs, note, raw_rows = read_tables(path, ext)
            rec["note"] = note
            if dfs:
                rec["rows"] = raw_rows if raw_rows else sum(len(d) for d in dfs)
                rec["cols"] = max(len(d.columns) for d in dfs)
                cols = [str(c) for d in dfs for c in d.columns]
                rec["columns"] = " | ".join(cols[:15])
                rec["pii_like_cols"] = " | ".join(sorted({c for c in cols if PII_COLS.search(c)}))
                free = []
                for d in dfs:
                    for j, c in enumerate(d.columns):
                        s = d.iloc[:, j].dropna().astype(str)
                        if len(s):
                            mw = float(s.str.split().str.len().mean())
                            rec["max_mean_words"] = max(rec["max_mean_words"], round(mw, 1))
                            if mw >= 8:
                                free.append(str(c))
                rec["free_text_cols"] = " | ".join(free[:10])
                text = "\n".join(d.astype(str).to_csv(index=False) for d in dfs)[:5_000_000]
        elif ext in DOC_EXT:
            text, pages, note = read_document(path, ext)
            rec["pages"], rec["words"] = pages, len(text.split())
            rec["note"] = ("DOKUMENT me tekst - kandidat për NER. " + note).strip()
        elif ext in (".json", ".xml", ".rdf"):
            text = read_text(path)[:5_000_000]
        for name, rx in PATTERNS.items():
            rec[f"hits_{name}"] = len(rx.findall(text)) if text else 0
        rec["sensitive_name"] = bool(SENSITIVE_NAME.search(path.name))
        return rec


def finish_inventory(rows):
    import pandas as pd
    inv = pd.DataFrame(rows)
    if inv.empty:
        print("Asnjë skedar te", FILES)
        return
    for c, default in (("pii_like_cols", ""), ("free_text_cols", ""), ("note", ""),
                       ("sensitive_name", False), ("max_mean_words", 0.0)):
        inv[c] = inv[c].fillna(default) if c in inv else default
    hit_cols = [c for c in inv.columns if c.startswith("hits_")]
    inv[hit_cols] = inv[hit_cols].fillna(0)
    inv["pii_signal"] = (inv[hit_cols].sum(axis=1)
                         + inv["pii_like_cols"].str.len().gt(0).astype(int)
                         + inv["sensitive_name"].astype(int))
    inv["mos_e_ndaj"] = inv["pii_signal"] > 0
    inv["is_document"] = inv["format"].isin(["pdf", "docx", "doc", "odt", "txt"])
    inv = inv.sort_values(["is_document", "max_mean_words", "pii_signal"], ascending=False)
    inv.to_csv(OUT / "inventory.csv", index=False, encoding="utf-8-sig")

    tables = inv[inv["format"].isin(["csv", "xlsx", "xls"])]
    docs = inv[inv["is_document"]]
    print("\n=== PËRMBLEDHJE ===")
    print("Skedarë sipas formatit:\n", inv["format"].value_counts().to_string())
    print("Rreshta gjithsej (CSV + Excel):", int(tables["rows"].fillna(0).sum()))
    print("Tabela me kolona tekst të lirë (>= 8 fjalë mesatarisht):",
          int((tables["free_text_cols"] != "").sum()))
    print(f"Dokumente tekstuale: {len(docs)}, me gjithsej {int(docs['words'].fillna(0).sum())} fjalë")
    print("Skedarë me sinjale të dhënash personale (MOS I NDAJ):", int(inv["mos_e_ndaj"].sum()))
    problems = inv[inv["note"].str.contains("mungon|nuk u lexua|gabim", na=False)]
    if len(problems):
        print(f"Skedarë që nuk u lexuan: {len(problems)} (shih kolonën 'note')")
    print(f"\nInventari i plotë: {OUT / 'inventory.csv'}")
    print("Inventari përmban vetëm statistika dhe emra kolonash, jo vlerat - mund të ndahet.")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    {"probe": probe, "download": download, "inventory": inventory}.get(
        cmd, lambda: print(__doc__))()

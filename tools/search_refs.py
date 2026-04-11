#!/usr/bin/env python3
"""
search_refs.py — Ricerca bibliografica accademica per la tesi LaTeX.
Interroga Semantic Scholar (con chiave gratuita) e arXiv (categoria ottica/fisica).

Uso da Claude Code:
    python tools/search_refs.py "stokes parameters imaging polarimeter"
    python tools/search_refs.py "CMOS sensor polarimetry" --limit 8
    python tools/search_refs.py --arxiv "mueller matrix birefringence"
    python tools/search_refs.py --verify 10.1364/OE.26.029669

Chiave Semantic Scholar (gratuita, elimina i 429):
    Registrati su https://www.semanticscholar.org/product/api
    Poi (PowerShell): $env:SS_API_KEY="la_tua_chiave"
    oppure crea un file .env con: SS_API_KEY=la_tua_chiave
"""

import os
import sys
import json
import time
import argparse
import urllib.request
import urllib.parse
import urllib.error
import xml.etree.ElementTree as ET
from textwrap import dedent

# Legge .env se presente (nessuna dipendenza esterna)
_env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
if os.path.exists(_env_path):
    with open(_env_path) as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _v = _line.split("=", 1)
                os.environ.setdefault(_k.strip(), _v.strip())

SS_API_KEY = os.environ.get("SS_API_KEY", "")

# Categorie arXiv rilevanti per polarimetria/ottica/imaging
ARXIV_CATS = "cat:physics.optics OR cat:eess.IV OR cat:physics.ins-det"

SS_BASE   = "https://api.semanticscholar.org/graph/v1"
SS_FIELDS = "title,authors,year,externalIds,venue,publicationTypes,abstract,citationCount"


# ── Semantic Scholar ──────────────────────────────────────────────────────────

def search_semantic_scholar(query: str, limit: int = 5) -> list[dict]:
    params = urllib.parse.urlencode({"query": query, "limit": limit, "fields": SS_FIELDS})
    url = f"{SS_BASE}/paper/search?{params}"
    headers = {"User-Agent": "ThesisPolarimeter/1.0"}
    if SS_API_KEY:
        headers["x-api-key"] = SS_API_KEY

    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=12) as r:
                return json.loads(r.read()).get("data", [])
        except urllib.error.HTTPError as e:
            if e.code == 429:
                wait = 15 * (attempt + 1)
                print(f"[SS] Rate limit 429 — attendo {wait}s (tentativo {attempt+1}/3)...", file=sys.stderr)
                if attempt == 2:
                    print("[SS] Limite raggiunto. Ottieni una chiave gratuita:", file=sys.stderr)
                    print("     https://www.semanticscholar.org/product/api", file=sys.stderr)
                    print("     Poi aggiungi SS_API_KEY=... nel file .env del repo.", file=sys.stderr)
                    return []
                time.sleep(wait)
            else:
                print(f"[SS] HTTP {e.code}: {e.reason}", file=sys.stderr)
                return []
        except Exception as e:
            print(f"[SS] Errore: {e}", file=sys.stderr)
            return []
    return []


def ss_to_bibtex(paper: dict) -> tuple[str, str] | None:
    title = paper.get("title", "").strip()
    year  = paper.get("year") or "????"
    authors_raw = paper.get("authors", [])
    venue = paper.get("venue", "").strip()
    ext   = paper.get("externalIds", {})
    doi, arxiv_id = ext.get("DOI", ""), ext.get("ArXiv", "")

    if not title or not authors_raw:
        return None

    authors_bib = " and ".join(a.get("name", "Unknown") for a in authors_raw)
    first_last  = authors_raw[0].get("name", "Unknown").split()[-1]
    first_word  = "".join(c for c in title.split()[0] if c.isalpha())
    key = f"{first_last}{year}{first_word}"

    entry_type = "@article" if venue else "@misc"
    fields = {"author": authors_bib, "title": f"{{{title}}}", "year": str(year)}
    if venue:    fields["journal"]       = f"{{{venue}}}"
    if doi:      fields["doi"]           = doi
    if arxiv_id: fields["eprint"]        = arxiv_id; fields["archivePrefix"] = "arXiv"

    body = ",\n  ".join(f"{k} = {v}" for k, v in fields.items())
    return key, f"{entry_type}{{{key},\n  {body}\n}}"


# ── arXiv ─────────────────────────────────────────────────────────────────────

ARXIV_BASE = "https://export.arxiv.org/api/query"
ARXIV_NS   = "http://www.w3.org/2005/Atom"


def search_arxiv(query: str, limit: int = 5, optics_only: bool = True) -> list[dict]:
    """
    optics_only=True aggiunge un filtro per categorie rilevanti,
    evitando falsi positivi come 'Mueller' in fisica delle particelle
    o 'Stokes' in fluidodinamica.
    """
    full_query = f"({ARXIV_CATS}) AND all:{query}" if optics_only else f"all:{query}"
    params = urllib.parse.urlencode({"search_query": full_query, "max_results": limit, "sortBy": "relevance"})
    try:
        with urllib.request.urlopen(f"{ARXIV_BASE}?{params}", timeout=12) as r:
            root = ET.fromstring(r.read())
    except Exception as e:
        print(f"[arXiv] Errore: {e}", file=sys.stderr)
        return []

    papers = []
    for entry in root.findall(f"{{{ARXIV_NS}}}entry"):
        arxiv_id = (entry.findtext(f"{{{ARXIV_NS}}}id") or "").split("/abs/")[-1].split("v")[0]
        title    = (entry.findtext(f"{{{ARXIV_NS}}}title") or "").strip().replace("\n", " ")
        summary  = (entry.findtext(f"{{{ARXIV_NS}}}summary") or "").strip()
        year     = (entry.findtext(f"{{{ARXIV_NS}}}published") or "????")[:4]
        authors  = [a.findtext(f"{{{ARXIV_NS}}}name") or "" for a in entry.findall(f"{{{ARXIV_NS}}}author")]
        cats     = [c.get("term", "") for c in entry.findall(f"{{{ARXIV_NS}}}category")]
        papers.append({"arxiv_id": arxiv_id, "title": title, "year": year,
                       "authors": authors, "abstract": summary, "categories": cats})
    return papers


def arxiv_to_bibtex(paper: dict) -> tuple[str, str] | None:
    title, year, authors, arxiv_id = (
        paper.get("title", "").strip(), paper.get("year", "????"),
        paper.get("authors", []), paper.get("arxiv_id", "")
    )
    if not title or not authors:
        return None
    first_last = authors[0].split()[-1] if authors else "Unknown"
    first_word = "".join(c for c in title.split()[0] if c.isalpha())
    key = f"{first_last}{year}{first_word}"
    bibtex = dedent(f"""\
        @misc{{{key},
          author        = {{{" and ".join(authors)}}},
          title         = {{{{{title}}}}},
          year          = {{{year}}},
          eprint        = {{{arxiv_id}}},
          archivePrefix = {{arXiv}},
          url           = {{https://arxiv.org/abs/{arxiv_id}}}
        }}""")
    return key, bibtex


# ── CrossRef (verifica DOI) ───────────────────────────────────────────────────

def verify_doi(doi: str) -> dict | None:
    url = f"https://api.crossref.org/works/{urllib.parse.quote(doi)}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "ThesisPolarimeter/1.0"})
        with urllib.request.urlopen(req, timeout=12) as r:
            return json.loads(r.read()).get("message", {})
    except urllib.error.HTTPError as e:
        print(f"[CrossRef] {'DOI non trovato' if e.code == 404 else f'HTTP {e.code}'}: {doi}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"[CrossRef] Errore: {e}", file=sys.stderr)
        return None


def crossref_to_bibtex(meta: dict, doi: str) -> tuple[str, str] | None:
    title   = (meta.get("title") or [""])[0]
    year    = str((meta.get("published", {}).get("date-parts") or [[None]])[0][0] or "????")
    authors = meta.get("author", [])
    journal = (meta.get("container-title") or [""])[0]
    if not title:
        return None
    authors_bib = " and ".join(f"{a.get('family','')}, {a.get('given','')}".strip(", ") for a in authors)
    first_last  = authors[0].get("family", "Unknown") if authors else "Unknown"
    first_word  = "".join(c for c in title.split()[0] if c.isalpha())
    key = f"{first_last}{year}{first_word}"
    fields = {"author": f"{{{authors_bib}}}", "title": f"{{{{{title}}}}}",
              "journal": f"{{{journal}}}", "year": year, "doi": doi}
    if meta.get("volume"): fields["volume"] = meta["volume"]
    if meta.get("issue"):  fields["number"] = meta["issue"]
    if meta.get("page"):   fields["pages"]  = f"{{{meta['page']}}}"
    body = ",\n  ".join(f"{k} = {v}" for k, v in fields.items())
    return key, f"@article{{{key},\n  {body}\n}}"


# ── Output ────────────────────────────────────────────────────────────────────

def print_results(results: list[tuple], source: str, optics_only: bool = True):
    if not results:
        tip = " Prova --no-filter per cercare su tutto arXiv." if "arXiv" in source and optics_only else ""
        print(f"\n[{source}] Nessun risultato.{tip}")
        return
    print(f"\n{'='*60}\n  {source} — {len(results)} risultati\n{'='*60}")
    for i, item in enumerate(results, 1):
        key, bibtex, abstract, cats = item if len(item) == 4 else (*item, "", [])
        cats_str = ", ".join(cats[:3]) if cats else ""
        print(f"\n[{i}] {key}" + (f"  |  {cats_str}" if cats_str else ""))
        if abstract:
            print(f"    {abstract[:170].strip()}...")
        print(f"\n{bibtex}\n" + "-"*60)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    p = argparse.ArgumentParser(description="Ricerca bibliografica per tesi in polarimetria/ottica.")
    p.add_argument("query", nargs="?", help="Query di ricerca (in inglese)")
    p.add_argument("--limit", type=int, default=5, metavar="N")
    p.add_argument("--arxiv",     action="store_true", help="Solo arXiv")
    p.add_argument("--ss",        action="store_true", help="Solo Semantic Scholar")
    p.add_argument("--no-filter", action="store_true", help="Disabilita filtro categoria arXiv")
    p.add_argument("--verify",    metavar="DOI",       help="Verifica un DOI su CrossRef")
    args = p.parse_args()

    if args.verify:
        print(f"\nVerifica DOI: {args.verify}")
        meta = verify_doi(args.verify)
        if meta:
            r = crossref_to_bibtex(meta, args.verify)
            if r:
                key, bib = r
                print(f"\n✓ Verificato. Chiave: {key}\n\n{bib}")
            else:
                print("✗ Metadati incompleti.")
        return

    if not args.query:
        p.print_help(); sys.exit(1)

    optics_only = not args.no_filter

    if not SS_API_KEY and not args.arxiv:
        print("[!] Nessuna SS_API_KEY — soggetto a rate limit 429.", file=sys.stderr)
        print("    Chiave gratuita: https://www.semanticscholar.org/product/api", file=sys.stderr)
        print("    Aggiungila in .env: SS_API_KEY=la_tua_chiave\n", file=sys.stderr)

    if not args.arxiv:
        print(f"[SS] Ricerca: «{args.query}»...", file=sys.stderr)
        papers = search_semantic_scholar(args.query, args.limit)
        time.sleep(0.5)
        results = [(k, b, (pp.get("abstract") or ""), []) for pp in papers if (r := ss_to_bibtex(pp)) for k, b in [r]]
        print_results(results, "Semantic Scholar")

    if not args.ss:
        note = "(physics.optics, eess.IV, ins-det)" if optics_only else "(tutte le categorie)"
        print(f"[arXiv] {note} Ricerca: «{args.query}»...", file=sys.stderr)
        papers = search_arxiv(args.query, args.limit, optics_only)
        results = [(k, b, (pp.get("abstract") or "")[:200], pp.get("categories", []))
                   for pp in papers if (r := arxiv_to_bibtex(pp)) for k, b in [r]]
        print_results(results, "arXiv", optics_only)

    print("\n[→] Copia le voci BibTeX rilevanti in Thesis_bibliography.bib")
    print("[→] Verifica un DOI con: python tools/search_refs.py --verify <DOI>\n")


if __name__ == "__main__":
    main()

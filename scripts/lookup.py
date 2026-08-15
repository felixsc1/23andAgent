#!/usr/bin/env python3
"""Look up genotypes in the local 23andMe file and curated marker panels.

Never uploads the genome. Network is used only by the `annotate` subcommand,
which sends rsIDs (not the raw file) to public APIs.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "raw_genome"
INDEX_PATH = ROOT / "data" / "genome.sqlite"
MARKERS_PATH = ROOT / "data" / "panels" / "markers.json"

COMPLEMENT = str.maketrans("ACGTacgt", "TGCAtgca")
USER_AGENT = "23andme-personal-genome-lookup/1.0 (local research; not a medical device)"


def find_genome_file() -> Path:
    files = sorted(RAW_DIR.glob("genome_*.txt")) + sorted(RAW_DIR.glob("*.txt"))
    files = [p for p in files if p.is_file()]
    if not files:
        raise FileNotFoundError(f"No 23andMe .txt file found in {RAW_DIR}")
    return files[0]


def normalize_genotype(gt: str | None) -> str | None:
    if gt is None:
        return None
    gt = gt.strip().upper()
    if gt in {"", "--", "NN", "00"}:
        return None
    if len(gt) == 2:
        return "".join(sorted(gt))
    return gt


def complement_genotype(gt: str | None) -> str | None:
    norm = normalize_genotype(gt)
    if not norm:
        return None
    return normalize_genotype(norm.translate(COMPLEMENT))


def connect(create: bool = False) -> sqlite3.Connection:
    if not create and not INDEX_PATH.exists():
        raise FileNotFoundError("Genome index missing. Run: python scripts/lookup.py index")
    INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(INDEX_PATH)
    con.row_factory = sqlite3.Row
    return con


def index_genome(force: bool = False) -> dict:
    genome = find_genome_file()
    if INDEX_PATH.exists() and not force:
        con = connect()
        meta = dict(con.execute("SELECT * FROM meta").fetchone())
        con.close()
        if meta.get("source_name") == genome.name:
            return {"status": "exists", **meta}

    INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    if INDEX_PATH.exists():
        INDEX_PATH.unlink()

    con = connect(create=True)
    con.execute(
        """
        CREATE TABLE snps (
            rsid TEXT PRIMARY KEY,
            chromosome TEXT NOT NULL,
            position INTEGER NOT NULL,
            genotype TEXT,
            nocall INTEGER NOT NULL DEFAULT 0
        )
        """
    )
    con.execute("CREATE TABLE meta (source_name TEXT, source_path TEXT, snp_count INTEGER, nocall_count INTEGER, build TEXT)")

    rows = []
    nocalls = 0
    with genome.open(encoding="utf-8", errors="replace") as fh:
        for line in fh:
            if not line.strip() or line.startswith("#"):
                continue
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 4 or parts[0] == "rsid":
                continue
            rsid, chrom, pos, gt = parts[0], parts[1], int(parts[2]), parts[3]
            nocall = 1 if gt in {"--", "NN", "00"} else 0
            nocalls += nocall
            rows.append((rsid, chrom, pos, None if nocall else gt, nocall))
            if len(rows) >= 50000:
                con.executemany("INSERT OR REPLACE INTO snps VALUES (?, ?, ?, ?, ?)", rows)
                rows.clear()
    if rows:
        con.executemany("INSERT OR REPLACE INTO snps VALUES (?, ?, ?, ?, ?)", rows)

    count = con.execute("SELECT COUNT(*) FROM snps").fetchone()[0]
    con.execute(
        "INSERT INTO meta VALUES (?, ?, ?, ?, ?)",
        (genome.name, str(genome), count, nocalls, "GRCh37"),
    )
    con.commit()
    con.close()
    return {
        "status": "built",
        "source_name": genome.name,
        "snp_count": count,
        "nocall_count": nocalls,
        "build": "GRCh37",
    }


def ensure_index() -> sqlite3.Connection:
    if not INDEX_PATH.exists():
        index_genome()
    return connect()


def load_markers() -> dict:
    return json.loads(MARKERS_PATH.read_text(encoding="utf-8"))


def lookup_rsids(rsids: list[str]) -> list[dict]:
    con = ensure_index()
    out = []
    for raw in rsids:
        rsid = raw.strip()
        row = con.execute("SELECT * FROM snps WHERE rsid = ? COLLATE NOCASE", (rsid,)).fetchone()
        if row is None:
            out.append(
                {
                    "rsid": rsid,
                    "present": False,
                    "status": "not_on_chip",
                    "chromosome": None,
                    "position": None,
                    "genotype": None,
                    "genotype_sorted": None,
                    "complement_sorted": None,
                }
            )
            continue
        gt = row["genotype"]
        status = "nocall" if row["nocall"] else "called"
        out.append(
            {
                "rsid": row["rsid"],
                "present": True,
                "status": status,
                "chromosome": row["chromosome"],
                "position": row["position"],
                "genotype": gt,
                "genotype_sorted": normalize_genotype(gt),
                "complement_sorted": complement_genotype(gt),
            }
        )
    con.close()
    return out


def enrich_with_catalog(records: list[dict], catalog: dict) -> list[dict]:
    by_rsid = {m["rsid"].lower(): m for m in catalog["markers"]}
    enriched = []
    for rec in records:
        marker = by_rsid.get(rec["rsid"].lower())
        item = dict(rec)
        if marker:
            item["catalog"] = {
                "gene": marker.get("gene"),
                "name": marker.get("name"),
                "panels": marker.get("panels", []),
                "evidence": marker.get("evidence"),
                "topic": marker.get("topic"),
                "caveat": marker.get("caveat"),
                "sources": marker.get("sources", []),
            }
        else:
            item["catalog"] = None
        enriched.append(item)
    return enriched


def panel_records(panel: str, catalog: dict) -> list[dict]:
    wanted = [m["rsid"] for m in catalog["markers"] if panel in m.get("panels", [])]
    if not wanted:
        known = sorted({p for m in catalog["markers"] for p in m.get("panels", [])})
        raise SystemExit(f"Unknown panel {panel!r}. Known: {', '.join(known)}")
    return enrich_with_catalog(lookup_rsids(wanted), catalog)


def gene_records(gene: str, catalog: dict) -> list[dict]:
    wanted = [m["rsid"] for m in catalog["markers"] if m.get("gene", "").lower() == gene.lower()]
    if not wanted:
        # Fall back to any indexed SNP is not possible by gene; catalog only.
        raise SystemExit(f"No curated markers for gene {gene!r}. Try: python scripts/lookup.py rsid rs...")
    return enrich_with_catalog(lookup_rsids(wanted), catalog)


def search_catalog(query: str, catalog: dict) -> list[dict]:
    q = query.lower()
    hits = []
    for m in catalog["markers"]:
        blob = " ".join(
            [
                m.get("rsid", ""),
                m.get("gene", ""),
                m.get("name", ""),
                m.get("topic", ""),
                " ".join(m.get("panels", [])),
            ]
        ).lower()
        if q in blob:
            hits.append(m["rsid"])
    return enrich_with_catalog(lookup_rsids(hits), catalog)


def http_get_json(url: str, timeout: int = 30):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        return {"error": f"HTTP {exc.code}", "url": url}
    except urllib.error.URLError as exc:
        return {"error": str(exc.reason), "url": url}


def annotate_rsid(rsid: str) -> dict:
    rsid = rsid.strip()
    time.sleep(0.15)
    ensembl = http_get_json(
        f"https://rest.ensembl.org/variation/human/{rsid}?content-type=application/json"
    )
    time.sleep(0.15)
    gwas = http_get_json(
        f"https://www.ebi.ac.uk/gwas/rest/api/singleNucleotidePolymorphisms/{rsid}/associations?size=25"
    )
    time.sleep(0.15)
    myvariant = http_get_json(
        f"https://myvariant.info/v1/variant/{rsid}?fields=clinvar.rcv.clinical_significance,clinvar.rcv.conditions.name,dbsnp.rsid,cadd.phred"
    )
    associations = []
    embedded = gwas.get("_embedded", {}) if isinstance(gwas, dict) else {}
    for assoc in embedded.get("associations", [])[:15]:
        associations.append(
            {
                "pvalue": assoc.get("pvalue"),
                "or": assoc.get("orPerCopyNum"),
                "beta": assoc.get("betaNum"),
                "risk_frequency": assoc.get("riskFrequency"),
                "links": assoc.get("_links", {}).get("efoTraits", {}).get("href"),
            }
        )
    return {
        "rsid": rsid,
        "ensembl": ensembl if isinstance(ensembl, dict) else {"raw": ensembl},
        "gwas_associations": associations,
        "gwas_error": gwas.get("error") if isinstance(gwas, dict) else None,
        "myvariant": myvariant,
        "provenance": {
            "ensembl": f"https://rest.ensembl.org/variation/human/{rsid}",
            "gwas": f"https://www.ebi.ac.uk/gwas/rest/api/singleNucleotidePolymorphisms/{rsid}/associations",
            "myvariant": f"https://myvariant.info/v1/variant/{rsid}",
            "snpedia": f"https://www.snpedia.com/index.php/{rsid}",
            "clinvar": f"https://www.ncbi.nlm.nih.gov/clinvar/?term={rsid}[Variant%20ID]",
        },
    }


def dump(obj) -> None:
    json.dump(obj, sys.stdout, indent=2, default=str)
    sys.stdout.write("\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Local 23andMe genotype lookup")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_index = sub.add_parser("index", help="Build or rebuild the SQLite index")
    p_index.add_argument("--force", action="store_true")

    p_rsid = sub.add_parser("rsid", help="Look up one or more rsIDs")
    p_rsid.add_argument("rsids", nargs="+")

    p_panel = sub.add_parser("panel", help="Look up a curated panel")
    p_panel.add_argument("name")

    p_gene = sub.add_parser("gene", help="Look up curated markers for a gene")
    p_gene.add_argument("symbol")

    p_search = sub.add_parser("search", help="Search curated markers")
    p_search.add_argument("query")

    sub.add_parser("panels", help="List curated panels")
    sub.add_parser("stats", help="Index statistics")

    p_ann = sub.add_parser("annotate", help="Fetch public annotations for rsIDs (sends rsIDs only)")
    p_ann.add_argument("rsids", nargs="+")

    args = parser.parse_args()

    if args.cmd == "index":
        dump(index_genome(force=args.force))
        return

    catalog = load_markers()

    if args.cmd == "stats":
        con = ensure_index()
        meta = dict(con.execute("SELECT * FROM meta").fetchone())
        con.close()
        dump(
            {
                **meta,
                "index": str(INDEX_PATH),
                "catalog_markers": len(catalog["markers"]),
                "build_note": catalog.get("build_note"),
            }
        )
        return

    if args.cmd == "panels":
        panels: dict[str, int] = {}
        for m in catalog["markers"]:
            for p in m.get("panels", []):
                panels[p] = panels.get(p, 0) + 1
        dump({"panels": panels, "evidence_levels": catalog.get("evidence_levels")})
        return

    if args.cmd == "rsid":
        dump(enrich_with_catalog(lookup_rsids(args.rsids), catalog))
        return
    if args.cmd == "panel":
        dump(panel_records(args.name, catalog))
        return
    if args.cmd == "gene":
        dump(gene_records(args.symbol, catalog))
        return
    if args.cmd == "search":
        dump(search_catalog(args.query, catalog))
        return
    if args.cmd == "annotate":
        dump(
            {
                "local": enrich_with_catalog(lookup_rsids(args.rsids), catalog),
                "public": [annotate_rsid(r) for r in args.rsids],
                "disclaimer": "Educational lookup only. Not medical advice. Confirm strand before interpreting literature.",
            }
        )
        return


if __name__ == "__main__":
    main()

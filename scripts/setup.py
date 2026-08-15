#!/usr/bin/env python3
"""First-time setup: find the local 23andMe raw file and build data/genome.sqlite."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))

from lookup import RAW_DIR, INDEX_PATH, find_genome_file, index_genome  # noqa: E402


PLACE_HINT = """Place your 23andMe raw genotype file here:

  {raw_dir}

Typical 23andMe download name:

  genome_YourName_v5_Full_YYYYMMDDHHMMSS.txt

In 23andMe: Settings → 23andMe Data → Download Raw Data.
Do not commit or upload that file. It stays gitignored.
"""


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create raw_genome/ if needed and build the local SQLite index."
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Rebuild data/genome.sqlite even if it already matches the raw file",
    )
    args = parser.parse_args()

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)

    print("23andAgent setup")
    print(f"  raw file dir : {RAW_DIR}")
    print(f"  sqlite index : {INDEX_PATH}")
    print()

    try:
        genome = find_genome_file()
    except FileNotFoundError:
        print(PLACE_HINT.format(raw_dir=RAW_DIR))
        print("Then re-run:  python scripts/setup.py")
        return 1

    print(f"Found raw file: {genome.name}")
    result = index_genome(force=args.force)
    status = result.get("status")
    if status == "exists":
        print("Index already up to date (pass --force to rebuild).")
    else:
        print("Built SQLite index.")
    print(f"  SNPs indexed : {result.get('snp_count')}")
    print(f"  no-calls     : {result.get('nocall_count')}")
    print(f"  build        : {result.get('build')}")
    print()
    print("Try:")
    print("  python scripts/lookup.py stats")
    print("  python scripts/lookup.py panels")
    print("  python scripts/lookup.py rsid rs429358 rs7412")
    print("  python scripts/lookup.py panel personality")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

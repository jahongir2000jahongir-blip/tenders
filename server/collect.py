"""CLI entry point for cron: `python -m server.collect [--source CODE ...] [--demo] [--purge-demo]`."""
from __future__ import annotations

import argparse
import logging
import sys

from . import db, pipeline
from .scrapers import COLLECTORS


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="tenders.best collector")
    ap.add_argument("--source", action="append", help="run only this source (repeatable)")
    ap.add_argument("--list", action="store_true", help="list sources and exit")
    ap.add_argument("--demo", action="store_true", help="insert demo tenders (marked source=demo)")
    ap.add_argument("--purge-demo", action="store_true", help="delete demo tenders")
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args(argv)

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    db.init()

    if args.list:
        for code in COLLECTORS:
            print(code)
        return 0
    if args.purge_demo:
        from .demo import purge
        print(f"removed {purge()} demo tenders")
        return 0
    if args.demo:
        from .demo import seed
        print(f"inserted {seed()} demo tenders")
        return 0

    results = pipeline.run_all(args.source)
    bad = [r for r in results if r.status != "ok"]
    for r in results:
        print(f"{r.source:14s} {r.status:6s} fetched={r.fetched:4d} added={r.added:4d} "
              f"updated={r.updated:4d} dup={r.duplicates:3d} {r.error or ''}")
    return 1 if bad and len(bad) == len(results) else 0


if __name__ == "__main__":
    sys.exit(main())

from __future__ import annotations
import argparse
from pathlib import Path
from .store import load_opportunities
from .board import build_board
from .quality import quality_report

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="data/opportunities.json")
    parser.add_argument("--output", default="reports/TODAY_MONEY_BOARD.md")
    args = parser.parse_args()
    opportunities = load_opportunities(args.data)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(build_board(opportunities), encoding="utf-8")
    quality = output.parent / "SOURCE_QUALITY_CHECK.md"
    quality.write_text(quality_report(opportunities), encoding="utf-8")
    print(f"generated {output} from {len(opportunities)} opportunities")

if __name__ == "__main__":
    main()

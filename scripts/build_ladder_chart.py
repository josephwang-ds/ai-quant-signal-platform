#!/usr/bin/env python3
"""The leakage ladder as an SVG, for the README.

    python scripts/build_ladder_chart.py

A README with no picture is a wall of text, and the one picture this project
should have is the ladder: five bars falling from the score a naive pipeline
reports to the score that survives its own audit, with the count of impossible
entries beside them.

Drawn as SVG rather than captured as a screenshot for the same reason every page
here is generated: a picture of a number is a copy, and copies drift. The one it
would replace already did -- a hand-written write-up sat in this repository for
weeks claiming an ROC AUC the code had long since moved away from.

Self-contained, no external fonts or scripts, and dark-mode aware through a
`prefers-color-scheme` block, because GitHub renders README images on both.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

WIDTH, HEIGHT = 820, 404
LEFT, RIGHT, TOP, BOTTOM = 268, 150, 96, 76

# Plain-language names. The CSV's `stage` column is written for someone who
# already knows what purged cross-validation is; a README is not that place.
STAGE_WORDS = {
    "Naive pipeline": "Written the ordinary way",
    "+ purged, embargoed CV": "Stop training on the future",
    "+ shifted trailing features": "Stop features seeing the event day",
    "+ point-in-time universe": "Stop using today's company list",
    "+ point-in-time entry": "Stop entering before the filing exists",
}


def load(path: Path) -> list[dict]:
    with path.open() as handle:
        return list(csv.DictReader(handle))


def render(rows: list[dict]) -> str:
    scores = [float(r["average_precision"]) for r in rows]
    impossible = [int(float(r["impossible_entries"])) for r in rows]
    top, floor = max(scores), 0.0
    span = top - floor or 1.0
    plot = WIDTH - LEFT - RIGHT
    step = (HEIGHT - TOP - BOTTOM) / max(len(rows) - 1, 1)

    def x(score: float) -> float:
        return LEFT + plot * (score - floor) / span

    bars = []
    for i, row in enumerate(rows):
        y = TOP + step * i
        score, count = scores[i], impossible[i]
        last = i == len(rows) - 1
        label = STAGE_WORDS.get(row["stage"], row["stage"])
        klass = "good" if last else ("bad" if i == 0 else "mid")
        bars.append(f"""
  <text class="stage" x="{LEFT - 16}" y="{y + 5}" text-anchor="end">{label}</text>
  <rect class="bar {klass}" x="{LEFT}" y="{y - 11}" width="{x(score) - LEFT:.1f}"
        height="22" rx="2"/>
  <text class="score {klass}" x="{x(score) + 10}" y="{y + 5}">{score:.3f}</text>
  <text class="count {'zero' if count == 0 else 'nonzero'}"
        x="{WIDTH - 20}" y="{y + 5}" text-anchor="end">{count:,}</text>""")

    fonts = "-apple-system,Segoe UI,Helvetica,Arial,sans-serif"
    # Spelled out for a screen reader, because the whole finding is in the two
    # numbers and an unlabelled chart hides it from anyone not looking at it.
    alt = (f"Average precision falls from {scores[0]:.3f} to {scores[-1]:.3f} as "
           f"four sources of hindsight are removed, and filings entered before "
           f"they existed fall from {impossible[0]:,} to {impossible[-1]:,}.")
    caption = ("The score moves erratically because each fix also changes which "
               "filings are measurable. The count on the right does not.")
    subtitle = "Same features, same model. Only what the pipeline was allowed to know."
    right_head = "ENTERED BEFORE THE FILING EXISTED"

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}"
     width="{WIDTH}" height="{HEIGHT}" font-family="{fonts}"
     role="img" aria-label="{alt}">
  <style>
    .bg {{ fill: #f5f4ef; }}
    .title {{ font-size: 17px; font-weight: 700; fill: #14202b; }}
    .sub {{ font-size: 12.5px; fill: #5f6f7a; }}
    .stage {{ font-size: 13px; fill: #14202b; }}
    .score {{ font-size: 14px; font-weight: 700; }}
    .count {{ font-size: 13px; font-variant-numeric: tabular-nums; }}
    .head {{ font-size: 10px; font-weight: 700; letter-spacing: .09em; fill: #84929c; }}
    .bar {{ opacity: .92; }}
    .bar.bad {{ fill: #a8382c; }}
    .bar.mid {{ fill: #9aa7b0; }}
    .bar.good {{ fill: #2258c9; }}
    .score.bad {{ fill: #a8382c; }}
    .score.mid {{ fill: #5f6f7a; }}
    .score.good {{ fill: #2258c9; }}
    .count.nonzero {{ fill: #a8382c; font-weight: 700; }}
    .count.zero {{ fill: #1d7a4f; font-weight: 700; }}
    @media (prefers-color-scheme: dark) {{
      .bg {{ fill: #11171b; }}
      .title, .stage {{ fill: #e9eef0; }}
      .sub, .score.mid {{ fill: #93a1a9; }}
      .bar.mid {{ fill: #46535c; }}
      .bar.good, .score.good {{ fill: #6ea4f7; }}
      .bar.bad, .score.bad, .count.nonzero {{ fill: #e0857a; }}
      .count.zero {{ fill: #5fc08c; }}
    }}
  </style>
  <rect class="bg" width="{WIDTH}" height="{HEIGHT}"/>
  <text class="title" x="20" y="30">Four ordinary shortcuts, and what each one was worth</text>
  <text class="sub" x="20" y="51">{subtitle}</text>
  <text class="head" x="{LEFT}" y="{TOP - 22}">SCORE</text>
  <text class="head" x="{WIDTH - 20}" y="{TOP - 22}" text-anchor="end">{right_head}</text>
{"".join(bars)}
  <text class="sub" x="20" y="{HEIGHT - 22}">{caption}</text>
</svg>
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", type=Path,
                        default=Path("evidence/real_run/leakage_study.csv"))
    parser.add_argument("--out", type=Path, default=Path("docs/leakage-ladder.svg"))
    args = parser.parse_args()
    if not args.evidence.exists():
        raise SystemExit(f"{args.evidence} is missing. Run `make evidence` first.")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(render(load(args.evidence)), encoding="utf-8")
    print(f"ladder chart -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

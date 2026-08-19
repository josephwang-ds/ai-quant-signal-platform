"""Static HTML report.

Self-contained: inline SVG, inline CSS, no scripts, no network. It opens from a
file:// URL in ten years, which is the point -- a dashboard that needs a running
server is a dashboard nobody looks at.

Every chart here carries one series, so identity is never encoded in colour
alone; the two colours in play distinguish *leaky* from *honest*, and both are
also spelled out in the labels and repeated in the tables beneath.
"""

from __future__ import annotations

import html
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

# Validated for both surfaces (adjacent CVD dE 21.6 light / 19.2 dark; contrast
# >= 3:1 in both). See dataviz palette reference.
PALETTE = {
    "light": {"surface": "#fcfcfb", "panel": "#ffffff", "ink": "#0b0b0b",
              "ink2": "#52514e", "muted": "#8a8984", "grid": "#e6e5e1",
              "accent": "#2a78d6", "alarm": "#e34948"},
    "dark": {"surface": "#1a1a19", "panel": "#222221", "ink": "#ffffff",
             "ink2": "#c3c2b7", "muted": "#8a8984", "grid": "#33322f",
             "accent": "#3987e5", "alarm": "#e66767"},
}


def render(result, study: pd.DataFrame, sweep: pd.DataFrame,
           output: str | Path = "data/build/report.html") -> Path:
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(_document(result, study, sweep), encoding="utf-8")
    return output


# --------------------------------------------------------------------------- #
def _document(result, study: pd.DataFrame, sweep: pd.DataFrame) -> str:
    metrics = result.metrics
    honest = study.iloc[-1]
    naive = study.iloc[0]

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Filing Triage</title>
<style>{_css()}</style>
</head>
<body>
<main class="wrap">

  <header class="hero">
    <p class="eyebrow">SEC 8-K disclosures &middot; point-in-time study</p>
    <h1>Which filings deserve a human read?</h1>
    <p class="lede">
      Forty 8-Ks land before breakfast and an analyst has time for five. This ranks
      them by how hard the market is about to react &mdash; <em>magnitude, not
      direction</em>. Predicting direction is a bet against people with faster data
      and better models. Predicting which disclosures matter is a triage problem,
      and triage is answerable.
    </p>
    {_stat_row(metrics, naive["average_precision"])}
  </header>

  <section>
    <h2>The result that mattered was a bug</h2>
    <p>
      The first version of this pipeline scored an average precision of
      <strong>{naive['average_precision']:.3f}</strong>. The version that survives
      its own audit scores <strong>{honest['average_precision']:.3f}</strong>, a
      {(naive['average_precision'] / honest['average_precision'] - 1):.0%} overstatement.
      Nothing about the
      features or the model changed between them &mdash; only whether the pipeline
      was allowed to see things it could not have known. Each bar below removes
      exactly one such privilege.
    </p>
    {_ladder_chart(study)}
    {_ladder_table(study)}
    <p class="note">
      Event counts differ by stage, and that is part of the finding: purged
      cross-validation discards events it cannot honestly train on, and a
      point-in-time universe restores issuers that a present-day index screen had
      quietly deleted. A metric computed on a sample that the bug itself selected
      is not comparable to one computed on the right sample &mdash; which is
      another way this class of error hides.
    </p>
  </section>

  <section>
    <h2>The bug no metric catches</h2>
    <p>
      Entering on the filing <em>date</em> instead of the acceptance
      <em>timestamp</em> barely moves the score &mdash; which is exactly why it
      ships. It is not a modelling error. It is a claim to have acted on news that
      had not been published yet.
    </p>
    {_integrity_panel(result, study)}
  </section>

  <section>
    <h2>How fast is it over?</h2>
    <p>
      If the ranking only works when you act instantly, it is describing the
      announcement rather than anything usable. Holding the model fixed and
      delaying the decision shows how much is left after the wait.
    </p>
    {_sweep_chart(sweep)}
  </section>

  <section>
    <h2>What the ranker leans on</h2>
    <p>
      Permutation importance, measured on average precision. The 8-K item code
      does most of the work: registrants tell you what kind of news it is before
      you read a word of it.
    </p>
    {_importance_chart(result.importance)}
  </section>

  <section>
    <h2>Does it hold up across time?</h2>
    <p>
      Walk-forward folds run in chronological order, so this doubles as a decay
      check. A ranker that only works in the first fold has not been validated,
      it has been fitted.
    </p>
    {_fold_table(result.by_fold)}
  </section>

  <section>
    <h2>The queue</h2>
    <p>What the system actually emits: one morning's filings, ranked.</p>
    {_queue_table(result.queue)}
  </section>

  <section>
    <h2>Leakage audit</h2>
    <p>
      These run on every pipeline execution and on every CI build. A failure is an
      exception, not a warning &mdash; a check that can be ignored is a comment.
    </p>
    {_audit_table(result.audit)}
  </section>

  <footer>
    <p>
      Generated {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC &middot;
      {result.config.describe_switches()}
    </p>
    <p class="note">
      Figures on this page come from the synthetic corpus that ships with the
      repository, so the project runs end to end with no SEC credentials and no
      network. <code>make ingest</code> swaps in real EDGAR filings and real
      prices; no pipeline code changes.
    </p>
  </footer>

</main>
</body>
</html>
"""


# --------------------------------------------------------------------------- #
# Panels
# --------------------------------------------------------------------------- #
def _stat_row(metrics: dict, naive_ap: float) -> str:
    tiles = [
        (f"{metrics.get('n_events', 0):,}", "filings ranked", "out of sample"),
        (f"{metrics.get('daily_lift_at_5', float('nan')):.1f}&times;",
         "better than reading five at random",
         f"top 5 of each session &middot; base rate {metrics.get('base_rate', 0):.0%}"),
        (f"{metrics.get('average_precision', float('nan')):.3f}",
         "average precision, audited",
         f"the naive pipeline claimed {naive_ap:.3f}"),
        (f"{metrics.get('daily_precision_at_5', float('nan')):.0%}",
         "of the daily top five actually moved",
         "material = top decile of reaction size"),
    ]
    cells = "".join(
        f'<div class="stat"><div class="stat-value">{value}</div>'
        f'<div class="stat-label">{label}</div>'
        f'<div class="stat-note">{note}</div></div>'
        for value, label, note in tiles)
    return f'<div class="stats">{cells}</div>'


def _ladder_chart(study: pd.DataFrame) -> str:
    labels = study["stage"].tolist()
    values = study["average_precision"].tolist()
    # Only the last stage is free of every bug; everything above it is still leaking.
    kinds = ["alarm"] * (len(values) - 1) + ["accent"]
    return _hbar(labels, values, kinds, fmt="{:.3f}", floor=0.0,
                 caption="Average precision by stage.",
                 legend=[("alarm", "still leaking"), ("accent", "audited clean")])


def _importance_chart(importance: pd.DataFrame) -> str:
    if importance.empty:
        return '<p class="note">Importance not computed for this run.</p>'
    top = importance.head(10)
    return _hbar(top["feature"].tolist(), top["importance"].tolist(),
                 ["accent"] * len(top), fmt="{:.3f}", floor=0.0,
                 caption="Drop in average precision when the column is shuffled.")


def _sweep_chart(sweep: pd.DataFrame) -> str:
    if sweep.empty:
        return ""
    labels = sweep["embargo"].tolist()
    values = sweep["average_precision"].tolist()
    return _hbar(labels, values, ["accent"] * len(values), fmt="{:.3f}", floor=0.0,
                 caption="Average precision as the delay between publication and "
                         "decision grows.")


def _integrity_panel(result, study: pd.DataFrame) -> str:
    naive = study.iloc[0]
    rows = [
        ("Entries that opened before the filing was public",
         f"{int(naive['impossible_entries']):,}",
         f"{naive['impossible_share']:.0%} of the sample", "bad"),
        ("Median hindsight granted by those entries",
         f"{naive['median_hindsight_hours']:.1f} h",
         "between the opening print and the filing", "bad"),
        ("Same figure, point-in-time entry",
         f"{result.integrity['impossible_entries']:,}",
         "the invariant the test suite pins", "good"),
    ]
    cells = "".join(
        f'<tr><td>{html.escape(label)}</td>'
        f'<td class="num {kind}">{value}</td>'
        f'<td class="muted">{html.escape(note)}</td></tr>'
        for label, value, note, kind in rows)
    return f'<table class="data"><tbody>{cells}</tbody></table>'


def _ladder_table(study: pd.DataFrame) -> str:
    head = ("<tr><th>Stage</th><th class='num'>Events</th><th class='num'>AUC</th>"
            "<th class='num'>Avg precision</th><th class='num'>Daily lift@5</th>"
            "<th class='num'>Checks failed</th><th>What changed</th></tr>")
    rows = "".join(
        f"<tr><td>{html.escape(r['stage'])}</td>"
        f"<td class='num'>{r['n_events']:,}</td>"
        f"<td class='num'>{r['roc_auc']:.3f}</td>"
        f"<td class='num'>{r['average_precision']:.3f}</td>"
        f"<td class='num'>{r['daily_lift_at_5']:.2f}&times;</td>"
        f"<td class='num {'bad' if r['checks_failed'] else 'good'}'>{r['checks_failed']}</td>"
        f"<td class='muted'>{html.escape(r['note'])}</td></tr>"
        for _, r in study.iterrows())
    return f'<div class="scroll"><table class="data"><thead>{head}</thead><tbody>{rows}</tbody></table></div>'


def _fold_table(by_fold: pd.DataFrame) -> str:
    if by_fold.empty:
        return ""
    head = "".join(f"<th class='num'>{html.escape(c)}</th>" for c in by_fold.columns)
    rows = "".join(
        "<tr>" + "".join(
            f"<td class='num'>{v:.3f}</td>" if isinstance(v, float)
            else f"<td class='num'>{v:,}</td>" for v in row) + "</tr>"
        for row in by_fold.itertuples(index=False))
    return (f'<div class="scroll"><table class="data"><thead><tr>{head}</tr></thead>'
            f'<tbody>{rows}</tbody></table></div>')


def _queue_table(queue: pd.DataFrame, sessions: int = 2, top: int = 6) -> str:
    if queue.empty:
        return ""
    picked = queue["entry_session"].drop_duplicates().tail(sessions)
    shown = queue[queue["entry_session"].isin(picked) & (queue["rank"] <= top)]
    head = ("<tr><th class='num'>#</th><th>Session</th><th>Ticker</th><th>Items</th>"
            "<th>Filed</th><th class='num'>Score</th><th>Reacted</th></tr>")
    rows = "".join(
        f"<tr><td class='num'>{int(r['rank'])}</td>"
        f"<td>{r['entry_session']}</td>"
        f"<td class='mono'>{html.escape(str(r['ticker']))}</td>"
        f"<td class='mono'>{html.escape(str(r['items']))}</td>"
        f"<td class='muted'>{r['acceptance_time']:%H:%M} ET &middot; {r['session_state']}</td>"
        f"<td class='num'>{r['score']:.3f}</td>"
        f"<td class='{'good' if r['label'] else 'muted'}'>"
        f"{'yes' if r['label'] else 'no'}</td></tr>"
        for _, r in shown.iterrows())
    return f'<div class="scroll"><table class="data"><thead>{head}</thead><tbody>{rows}</tbody></table></div>'


def _audit_table(audit) -> str:
    frame = audit.to_frame()
    rows = "".join(
        f"<tr><td>{html.escape(r['check'])}</td>"
        f"<td class='{'good' if r['status'] == 'pass' else 'bad'}'>{r['status']}</td>"
        f"<td class='num'>{r['violations']:,}</td>"
        f"<td class='muted'>{html.escape(r['detail'])}</td></tr>"
        for _, r in frame.iterrows())
    head = "<tr><th>Check</th><th>Status</th><th class='num'>Violations</th><th>Detail</th></tr>"
    return (f'<p class="summary">{html.escape(audit.summary())}</p>'
            f'<div class="scroll"><table class="data"><thead>{head}</thead>'
            f'<tbody>{rows}</tbody></table></div>')


# --------------------------------------------------------------------------- #
# SVG
# --------------------------------------------------------------------------- #
def _hbar(labels: list[str], values: list[float], kinds: list[str], *,
          fmt: str = "{:.3f}", floor: float = 0.0, caption: str = "",
          legend: list[tuple[str, str]] | None = None) -> str:
    """Horizontal bars: one series, magnitude by length, value direct-labelled.

    Bars are thin, separated by a surface gap, and anchored to the floor. Labels
    sit outside the mark in text ink, never in the series colour.
    """
    row_h, gap, bar_h = 34, 2, 18
    left, right, top = 210, 76, 6
    width = 760
    height = top + len(labels) * row_h + (34 if caption else 8)
    span = max(values + [floor]) - floor or 1.0
    plot = width - left - right

    parts = [
        f'<svg viewBox="0 0 {width} {height}" role="img" '
        f'aria-label="{html.escape(caption or "chart")}" class="chart">'
    ]
    for i, (label, value, kind) in enumerate(zip(labels, values, kinds)):
        y = top + i * row_h + (row_h - bar_h) / 2
        w = max(2.0, (value - floor) / span * plot)
        parts.append(
            f'<text x="{left - 12}" y="{y + bar_h / 2 + 4}" class="tick" '
            f'text-anchor="end">{html.escape(str(label))}</text>')
        parts.append(
            f'<rect x="{left}" y="{y}" width="{w - gap:.1f}" height="{bar_h}" '
            f'rx="4" class="bar {kind}"><title>{html.escape(str(label))}: '
            f'{fmt.format(value)}</title></rect>')
        parts.append(
            f'<text x="{left + w + 8:.1f}" y="{y + bar_h / 2 + 4}" class="value">'
            f'{fmt.format(value)}</text>')

    baseline_y = top + len(labels) * row_h
    parts.append(f'<line x1="{left}" y1="{top}" x2="{left}" y2="{baseline_y}" '
                 f'class="axis"/>')
    if caption:
        parts.append(f'<text x="{left}" y="{baseline_y + 22}" class="caption">'
                     f'{html.escape(caption)}{_floor_note(floor)}</text>')
    parts.append("</svg>")

    swatches = ""
    if legend:
        items = "".join(
            f'<span class="key"><span class="dot {kind}"></span>{html.escape(text)}</span>'
            for kind, text in legend)
        swatches = f'<div class="legend">{items}</div>'
    return f'<figure class="fig">{swatches}{"".join(parts)}</figure>'


def _floor_note(floor: float) -> str:
    return f"  (bars start at {floor:g})" if floor else ""


def _css() -> str:
    light, dark = PALETTE["light"], PALETTE["dark"]

    def variables(theme: dict) -> str:
        return "".join(f"--{k}:{v};" for k, v in theme.items())

    return f"""
:root {{ color-scheme: light; {variables(light)} }}
@media (prefers-color-scheme: dark) {{
  :root:not([data-theme="light"]) {{ color-scheme: dark; {variables(dark)} }}
}}
:root[data-theme="dark"] {{ color-scheme: dark; {variables(dark)} }}

* {{ box-sizing: border-box; }}
body {{
  margin: 0; background: var(--surface); color: var(--ink);
  font: 16px/1.65 ui-sans-serif, -apple-system, "Segoe UI", Inter, system-ui, sans-serif;
  -webkit-text-size-adjust: 100%;
}}
.wrap {{ max-width: 900px; margin: 0 auto; padding: 56px 24px 80px; }}

.eyebrow {{ text-transform: uppercase; letter-spacing: .1em; font-size: 12px;
  color: var(--muted); margin: 0 0 12px; font-weight: 600; }}
h1 {{ font-size: clamp(30px, 5vw, 44px); line-height: 1.15; margin: 0 0 16px;
  letter-spacing: -0.02em; }}
h2 {{ font-size: 22px; margin: 0 0 12px; letter-spacing: -0.01em; }}
.lede {{ font-size: 18px; color: var(--ink2); margin: 0 0 32px; max-width: 62ch; }}
p {{ max-width: 68ch; color: var(--ink2); }}
section {{ margin-top: 56px; }}
em {{ color: var(--ink); font-style: normal; font-weight: 600; }}

.stats {{ display: grid; gap: 12px; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
  margin: 32px 0 0; }}
.stat {{ background: var(--panel); border: 1px solid var(--grid); border-radius: 10px;
  padding: 18px 18px 16px; }}
.stat-value {{ font-size: 30px; font-weight: 650; letter-spacing: -0.02em;
  color: var(--ink); line-height: 1.1; }}
.stat-label {{ font-size: 13px; color: var(--ink2); margin-top: 6px; }}
.stat-note {{ font-size: 12px; color: var(--muted); margin-top: 6px; }}

.fig {{ margin: 24px 0 8px; }}
.chart {{ width: 100%; height: auto; display: block; }}
.bar.accent {{ fill: var(--accent); }}
.bar.alarm {{ fill: var(--alarm); }}
.axis {{ stroke: var(--grid); stroke-width: 1; }}
.tick {{ fill: var(--ink2); font-size: 12.5px; }}
.value {{ fill: var(--ink); font-size: 12.5px; font-weight: 600;
  font-variant-numeric: tabular-nums; }}
.caption {{ fill: var(--muted); font-size: 12px; }}

.legend {{ display: flex; gap: 18px; margin-bottom: 10px; font-size: 12.5px;
  color: var(--ink2); flex-wrap: wrap; }}
.key {{ display: inline-flex; align-items: center; gap: 7px; }}
.dot {{ width: 10px; height: 10px; border-radius: 3px; display: inline-block; }}
.dot.accent {{ background: var(--accent); }}
.dot.alarm {{ background: var(--alarm); }}

.scroll {{ overflow-x: auto; margin: 20px 0; }}
table.data {{ border-collapse: collapse; width: 100%; font-size: 13.5px; }}
table.data th, table.data td {{ text-align: left; padding: 9px 12px;
  border-bottom: 1px solid var(--grid); vertical-align: top; }}
table.data th {{ color: var(--muted); font-weight: 600; font-size: 12px;
  text-transform: uppercase; letter-spacing: .05em; white-space: nowrap; }}
td.num, th.num {{ text-align: right; font-variant-numeric: tabular-nums;
  white-space: nowrap; }}
td.muted {{ color: var(--muted); }}
td.mono, .mono {{ font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 12.5px; }}
td.good {{ color: var(--accent); font-weight: 600; }}
td.bad {{ color: var(--alarm); font-weight: 600; }}
.summary {{ font-weight: 600; color: var(--ink); }}
.note {{ font-size: 13.5px; color: var(--muted); }}
footer {{ margin-top: 72px; padding-top: 20px; border-top: 1px solid var(--grid); }}
footer p {{ font-size: 13px; color: var(--muted); }}
code {{ font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: .92em; }}
"""

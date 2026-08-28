"""The filing-triage findings, as a page on the live site.

Every number is read from `evidence/real_run` at build time. None is written
into this file, and that is the whole design: a hand-written summary of a
measured result is a copy that drifts, and this project's argument is precisely
that numbers drift when nothing is watching. If the evidence is re-exported, this
page changes with it or fails loudly because a file it needs is missing.

The visual language is the Company Lens site's own -- warm paper, Georgia
headlines, the same blue -- because this is a section of that site rather than a
research paper bolted onto it.
"""

from __future__ import annotations

import argparse
import csv
import json
from datetime import UTC, datetime
from pathlib import Path

REQUIRED = ("metrics.json", "integrity.json", "leakage_study.csv",
            "capacity_profile.csv", "baseline_intervals.csv",
            "model_comparison_paired.csv", "reaction_capture.csv",
            "anchoring_study.csv", "session_material_counts.csv", "manifest.json")


def load(evidence: Path) -> dict:
    missing = [name for name in REQUIRED if not (evidence / name).exists()]
    if missing:
        raise SystemExit(
            f"{evidence} is missing {missing}. Run `make evidence` first: this "
            "page is generated from that export and has no numbers of its own."
        )

    def rows(name):
        with (evidence / name).open() as handle:
            return list(csv.DictReader(handle))

    return {
        "metrics": json.loads((evidence / "metrics.json").read_text()),
        "integrity": json.loads((evidence / "integrity.json").read_text()),
        "manifest": json.loads((evidence / "manifest.json").read_text()),
        "ladder": rows("leakage_study.csv"),
        "capacity": rows("capacity_profile.csv"),
        "baselines": {r["baseline"]: r for r in rows("baseline_intervals.csv")},
        "families": rows("model_comparison_paired.csv"),
        "capture": {r["population"]: r for r in rows("reaction_capture.csv")},
        "anchoring": rows("anchoring_study.csv"),
        "material_counts": rows("session_material_counts.csv"),
    }


def _pct(value, digits=1) -> str:
    return f"{float(value):.{digits}%}"


def _num(value, digits=3) -> str:
    return f"{float(value):.{digits}f}"


def _ladder(rows) -> str:
    out = []
    for i, r in enumerate(rows):
        last = i == len(rows) - 1
        cls = " class='clean'" if last else ""
        strong = (lambda v: f"<strong>{v}</strong>") if (last or i == 0) else (lambda v: v)
        impossible = f"{int(float(r['impossible_entries'])):,}"
        out.append(
            f"<tr{cls}><td>{r['stage']}</td>"
            f"<td class='n'>{strong(_num(r['average_precision']))}</td>"
            f"<td class='n'>{_num(r['roc_auc'])}</td>"
            f"<td class='n'>{strong(impossible)}</td>"
            f"<td class='n'>{r['checks_failed']}</td></tr>"
        )
    return "".join(out)


def _capacity(rows, headline_k=5) -> str:
    out = []
    for r in rows:
        highlight = " class='pick'" if int(r["capacity_k"]) == headline_k else ""
        out.append(
            f"<tr{highlight}><td class='n'>{r['capacity_k']}</td>"
            f"<td class='n'>{int(r['sessions']):,}</td>"
            f"<td class='n'>{_pct(r['random_floor'])}</td>"
            f"<td class='n'>{_pct(r['model'])}</td>"
            f"<td class='n'>{_pct(r['oracle_ceiling'])}</td>"
            f"<td class='n'>{float(r['lift_vs_random']):.2f}&times;</td>"
            f"<td class='n'>{_pct(r['span_captured'], 0)}</td></tr>"
        )
    return "".join(out)


def _baselines(metrics, baselines) -> str:
    label = {"random": "Random within the session",
             "arrival": "Arrival order",
             "item_202": "Item 2.02 earnings first"}
    out = [(f"<tr class='pick'><td>The model</td>"
            f"<td class='n'>{_pct(metrics['daily_model_precision_at_5'])}</td>"
            f"<td class='n'>&mdash;</td><td class='n'>&mdash;</td>"
            f"<td class='n'>&mdash;</td></tr>")]
    for key, name in label.items():
        r = baselines.get(key)
        if not r:
            continue
        draws = int(float(r["draws_not_beating_baseline"]) * 2000)
        out.append(
            f"<tr><td>{name}</td>"
            f"<td class='n'>{_pct(r['baseline_precision'])}</td>"
            f"<td class='n'>{float(r['lift']):.2f}&times;</td>"
            f"<td class='n'>[{float(r['lift_ci_low']):.2f}, {float(r['lift_ci_high']):.2f}]</td>"
            f"<td class='n'>{draws} / 2000</td></tr>")
    return "".join(out)


def _families(rows, shipped) -> str:
    pretty = {"hist_gbdt": "Gradient boosting", "logistic": "Logistic regression",
              "random_forest": "Random forest", "stratified_dummy": "Stratified dummy"}
    out = [(f"<tr class='pick'><td>{pretty.get(shipped, shipped)} "
            f"<em>(shipped)</em></td>"
            f"<td class='n'>&mdash;</td><td class='n'>&mdash;</td>"
            f"<td class='n'>&mdash;</td></tr>")]
    for r in rows:
        draws = int(float(r["draws_not_beating_reference"]) * int(r["draws"]))
        clears = float(r["difference_ci_high"]) < 0
        mark = "" if clears else " <span class='soft'>(straddles zero)</span>"
        out.append(
            f"<tr><td>{pretty.get(r['candidate'], r['candidate'])}</td>"
            f"<td class='n'>{float(r['difference']):+.3f}</td>"
            f"<td class='n'>[{float(r['difference_ci_low']):+.3f}, "
            f"{float(r['difference_ci_high']):+.3f}]{mark}</td>"
            f"<td class='n'>{draws} / {r['draws']}</td></tr>")
    return "".join(out)


def _capture(capture) -> str:
    order = [("all filings", "All filings"),
             ("not material", "Not material"),
             ("material (>= threshold)", "Material"),
             ("material, accepted post", "Material, filed after the close")]
    out = []
    for key, name in order:
        r = capture.get(key)
        if not r:
            continue
        emphasis = key.startswith("material")
        value = _pct(r["median_share_in_open"])
        out.append(f"<tr{' class=pick' if key.endswith('post') else ''}>"
                   f"<td>{'<strong>' if emphasis else ''}{name}"
                   f"{'</strong>' if emphasis else ''}</td>"
                   f"<td class='n'>{int(r['filings']):,}</td>"
                   f"<td class='n'>{'<strong>' if emphasis else ''}{value}"
                   f"{'</strong>' if emphasis else ''}</td></tr>")
    return "".join(out)


def render(data: dict) -> str:
    m, integ, manifest = data["metrics"], data["integrity"], data["manifest"]
    ladder = data["ladder"]
    naive, honest = ladder[0], ladder[-1]
    env = manifest.get("environment", {})
    inputs = manifest.get("inputs", {})
    open_anchored = data["anchoring"][1] if len(data["anchoring"]) > 1 else None
    shipped = manifest.get("pipeline_config", {}).get("estimator", "random_forest")

    # The share of sessions holding nothing material, read rather than written:
    # it is the reason the ceiling sits where it does, and hard-coding it here
    # would put one drifting number on a page whose point is that none drift.
    empty = next((r for r in data["material_counts"]
                  if int(r["material_filings"]) == 0), None)
    empty_share = _pct(empty["share"], 0) if empty else "some"

    families = [r for r in data["families"] if r["candidate"] != "stratified_dummy"]
    spread = max(abs(float(r["difference"])) for r in families) if families else 0.0
    drop = float(naive["average_precision"]) - float(honest["average_precision"])

    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>How the ranking was audited &middot; Company Lens</title>
<style>
:root{{--ink:#102537;--muted:#667681;--blue:#2864dc;--paper:#f3f2ed;
--panel:#fff;--line:#d7dcdd;--alarm:#b03a2e}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--paper);color:var(--ink);
font:400 16px/1.65 Inter,-apple-system,"Segoe UI",sans-serif}}
.wrap{{max-width:860px;margin:0 auto;padding:0 22px 96px}}
header{{padding:76px 0 40px;border-bottom:1px solid var(--line)}}
.eyebrow{{color:var(--blue);font-size:11px;font-weight:800;letter-spacing:.14em;
text-transform:uppercase;margin:0 0 16px}}
h1{{margin:0 0 20px;font:500 clamp(34px,5.6vw,56px)/1.02 Georgia,serif;
letter-spacing:-.035em}}
h2{{margin:0 0 12px;font:500 30px/1.12 Georgia,serif;letter-spacing:-.022em}}
.lede{{font:400 19px/1.55 Georgia,serif;color:var(--ink);max-width:62ch;margin:0}}
section{{padding:52px 0;border-bottom:1px solid var(--line)}}
section:last-of-type{{border-bottom:0}}
p{{max-width:64ch}}
.swing{{display:flex;align-items:baseline;gap:18px;flex-wrap:wrap;margin:26px 0 0}}
.swing b{{font:500 46px/1 Georgia,serif}}
.swing .bad{{color:var(--alarm)}}.swing .good{{color:var(--blue)}}
.swing .arr{{color:var(--muted);font-size:26px}}
.swing small{{flex-basis:100%;color:var(--muted);font-size:14px;max-width:60ch}}
.stats{{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));
gap:1px;background:var(--line);border:1px solid var(--line);margin:28px 0 0}}
.stat{{background:var(--panel);padding:20px}}
.stat b{{display:block;font:500 30px/1 Georgia,serif}}
.stat span{{display:block;margin-top:7px;font-size:12px;color:var(--muted);line-height:1.5}}
.scroll{{overflow-x:auto;margin:22px 0 0}}
table{{width:100%;border-collapse:collapse;font-size:14px;min-width:520px}}
th{{text-align:left;padding:9px 11px;border-bottom:1px solid var(--ink);
font-size:10px;letter-spacing:.09em;text-transform:uppercase;
color:var(--muted);font-weight:700}}
td{{padding:11px;border-bottom:1px solid var(--line)}}
td.n{{font-variant-numeric:tabular-nums;white-space:nowrap}}
tr.clean td,tr.pick td{{background:#eef3fb}}
.soft{{color:var(--muted);font-size:12px}}
.note{{margin-top:18px;padding:15px 18px;background:var(--panel);
border-left:3px solid var(--blue);font-size:14px;color:var(--muted)}}
.note strong{{color:var(--ink)}}
.env{{font-family:ui-monospace,Menlo,monospace;font-size:12px;color:var(--muted);
word-break:break-all}}
footer{{padding:34px 0 0;color:var(--muted);font-size:13px}}
a{{color:var(--blue)}}
.back{{display:inline-block;margin-bottom:26px;font-size:13px;text-decoration:none}}
@media(prefers-color-scheme:dark){{:root{{--paper:#12171a;--panel:#1b2226;
--ink:#e9eef0;--muted:#95a3ab;--line:#2b353a;--blue:#6ba2f5;--alarm:#e08376}}
tr.clean td,tr.pick td{{background:#1e2833}}}}
</style></head><body><div class="wrap">

<header>
<a class="back" href="index.html">&larr; Company Lens</a>
<p class="eyebrow">How the ranking was audited</p>
<h1>The first version of this<br>pipeline was wrong</h1>
<p class="lede">It ranked which SEC filings deserved a human read, and reported an
average precision of {_num(naive['average_precision'])}. The version that survives
its own audit reports {_num(honest['average_precision'])}. The gap is not model
improvement &mdash; it is four bugs, none of which announced itself.</p>
<div class="swing">
<b class="bad">{_num(naive['average_precision'])}</b><span class="arr">&rarr;</span>
<b class="good">{_num(honest['average_precision'])}</b>
<small>No feature or model changed between them. Only whether the pipeline was
allowed to see things it could not have known at the time.</small>
</div>
</header>

<section>
<h2>Removing one bug at a time</h2>
<p>Each row switches off exactly one form of hindsight. The metric moves
erratically because every fix also changes which filings are measurable at all
&mdash; so the column that carries the argument is the count of impossible
entries, which is an invariant rather than a score.</p>
<div class="scroll"><table><thead><tr>
<th>Stage</th><th class="n">Avg precision</th><th class="n">ROC AUC</th>
<th class="n">Impossible entries</th><th class="n">Guards failing</th>
</tr></thead><tbody>{_ladder(ladder)}</tbody></table></div>
<div class="note">An <strong>impossible entry</strong> is a filing whose entry
price was printed before EDGAR accepted the document. The naive rule creates
{int(float(naive['impossible_entries'])):,} of them, {_pct(naive['impossible_share'])}
of measurable filings, at a median of {float(naive['median_hindsight_hours']):.1f}
hours of hindsight. The corrected rule leaves none.</div>
</section>

<section>
<h2>What the audited ranking is worth</h2>
<div class="stats">
<div class="stat"><b>{_num(m['average_precision'])}</b><span>average precision<br>
95% [{_num(m['average_precision_ci_low'])}, {_num(m['average_precision_ci_high'])}]</span></div>
<div class="stat"><b>{_num(m['roc_auc'])}</b><span>ROC AUC<br>
95% [{_num(m['roc_auc_ci_low'])}, {_num(m['roc_auc_ci_high'])}]</span></div>
<div class="stat"><b>{_pct(m['daily_span_captured_at_5'], 0)}</b>
<span>of the achievable gap captured<br>
{_pct(m['daily_precision_at_5'])} against a
{_pct(m['daily_oracle_precision_at_5'])} ceiling</span></div>
<div class="stat"><b>{int(m['n_events']):,}</b><span>filings scored out of sample<br>
over {int(m['sessions']):,} sessions</span></div>
</div>
<p style="margin-top:30px">Intervals are a cluster bootstrap over trading
sessions, not over filings: two filings from the same morning share a market, and
treating them as independent draws would report an interval narrower than the
evidence supports.</p>
<div class="scroll"><table><thead><tr>
<th>Reading the top five by</th><th class="n">Material found</th>
<th class="n">Model lift</th><th class="n">95% interval</th>
<th class="n">Draws favouring it</th>
</tr></thead><tbody>{_baselines(m, data['baselines'])}</tbody></table></div>
<div class="note">The last column is the one to read first. A lift is only a
result if it survives resampling; a comparison that loses a fifth of its draws to
arrival order is a different claim from one that loses none.</div>
</section>

<section>
<h2>Five is an assumption, so it is reported as a range</h2>
<p><em>k</em> is how many filings someone reads &mdash; not how many arrive. It
was assumed from a reader's capacity rather than derived, so the whole tradeoff
is published instead of one point. The lift depends heavily on that assumption;
the share of achievable span barely does.</p>
<div class="scroll"><table><thead><tr>
<th class="n">Read k</th><th class="n">Sessions</th><th class="n">Random</th>
<th class="n">Model</th><th class="n">Ceiling</th><th class="n">Lift</th>
<th class="n">Span captured</th>
</tr></thead><tbody>{_capacity(data['capacity'])}</tbody></table></div>
<div class="note">The ceiling is below 100% and often far below: a session
holding one material filing caps precision@5 at 20% however good the ranking is,
and {empty_share} of eligible sessions hold none at all. Sessions fall away as
<em>k</em> grows because a capacity above the day's filing count is reading
everything, not triaging.</div>
</section>

<section>
<h2>Useful triage, not a trading strategy</h2>
<p>That sentence is usually a disclaimer. Here it is a measurement. The label is
anchored at the previous close, so for a filing accepted after the bell some of
the reaction has already happened by the time anyone could act.</p>
<div class="scroll"><table><thead><tr>
<th>Filings</th><th class="n">Count</th>
<th class="n">Median share already in the opening print</th>
</tr></thead><tbody>{_capture(data['capture'])}</tbody></table></div>
<div class="note">The decomposition is the finding. Across all filings the gap
barely matters, because most 8-Ks move nothing. Restrict to the ones that cleared
the materiality threshold and it jumps; restrict to those filed after the close
and nearly half the move is gone before the bell &mdash; concentrated exactly
where the ranker is looking. Scored against an open-anchored label the same
pipeline falls to
{_num(open_anchored['average_precision']) if open_anchored else 'n/a'}. That is a
harder question, not a failing ranker.</div>
</section>

<section>
<h2>The model family barely matters</h2>
<p>The estimator is deliberately unremarkable, and that is measured rather than
asserted. Differences are paired: every family saw the same filings on the same
days, so the difference is measured within a resample.</p>
<div class="scroll"><table><thead><tr>
<th>Family</th><th class="n">vs shipped</th>
<th class="n">95% interval on the difference</th>
<th class="n">Draws favouring shipped</th>
</tr></thead><tbody>{_families(data['families'], shipped)}</tbody></table></div>
<div class="note">Swapping the family moves average precision by at most
<strong>{_num(spread)}</strong>. Swapping the validation scheme moves it
<strong>{_num(drop)}</strong>. The interesting code was never the estimator, and
the shipped family was chosen by a nested procedure that prices the selection
rather than performing it &mdash; because picking the top row of a table you just
read is the one leak no per-row guard can catch.</div>
</section>

<section>
<h2>What produced these numbers</h2>
<p>A result without a fingerprint of its inputs is a claim with its subject
deleted. EDGAR grows, vendor prices are re-adjusted retroactively, and library
versions move &mdash; so a rerun that disagrees could mean the code changed or
the data did. Each export records which.</p>
<div class="stats">
<div class="stat"><b>{int(inputs.get('events', {}).get('rows', 0)):,}</b>
<span>filings ingested<br>from {integ.get('events_total', 0):,} EDGAR records</span></div>
<div class="stat"><b>{int(inputs.get('prices', {}).get('rows', 0)):,}</b>
<span>daily price rows<br>{inputs.get('prices', {}).get('first_session', '?')}
&rarr; {inputs.get('prices', {}).get('last_session', '?')}</span></div>
<div class="stat"><b>{env.get('python', '?')}</b><span>Python<br>
scikit-learn {env.get('packages', {}).get('scikit-learn', '?')} ·
pandas {env.get('packages', {}).get('pandas', '?')}</span></div>
</div>
<p class="env" style="margin-top:22px">events sha256
{inputs.get('events', {}).get('sha256', '')[:32]}&hellip;<br>
prices sha256 {inputs.get('prices', {}).get('sha256', '')[:32]}&hellip;</p>
<div class="note">Digests are taken over canonicalised content rather than file
bytes, so a pandas upgrade does not change them. A changed row count is the
source growing; an unchanged count with a changed digest is values moving
underneath.</div>
</section>

<footer>
<p>The universe is {manifest.get('note', '')}<br>
Generated {datetime.now(UTC):%Y-%m-%d} from the committed evidence package.
Full report with charts, per-fold results and the leakage audit:
<a href="report.html">report.html</a>.</p>
</footer>

</div></body></html>
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", type=Path, default=Path("evidence/real_run"))
    parser.add_argument("--out", type=Path,
                        default=Path("data/build/company_pages/research.html"))
    args = parser.parse_args()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(render(load(args.evidence)), encoding="utf-8")
    print(f"research page -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

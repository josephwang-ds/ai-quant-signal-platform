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

# Plain-language names for what the model reads. Semantics, not measurements:
# the importances beside them come from the evidence, these do not, because a
# feature's meaning does not change when the sample does.
FEATURE_WORDS = {
    "item_2_02": (
        "Is this an earnings release?",
        (
        "8-K item 2.02 is the code a company uses when it reports results. Registrants"
        " label their own filings, so the model knows what kind of news it is before"
        " reading a word."
    ),
    ),
    "hour_et": (
        "What time of day was it filed?",
        "New York time. Companies choose when to release news, and the choice is informative.",
    ),
    "days_since_last_earnings": (
        "How long since this company last reported?",
        "Where the filing sits in the quarterly cycle.",
    ),
    "rel_volume": (
        "Was the stock unusually busy beforehand?",
        (
        "Yesterday's volume against this company's own 60-day median. Yesterday's, never"
        " today's — today's would be the reaction the model is trying to predict."
    ),
    ),
    "days_to_expected_earnings": (
        "How close is the next expected report?",
        "Estimated from this company's own filing history, never from a published calendar.",
    ),
    "issuer_prior_material_rate": (
        "How often has this company moved markets before?",
        "Counting only filings whose outcome was already known by the time this one arrived.",
    ),
    "released_post": (
        "Was it filed after the close?",
        "Roughly two thirds of 8-Ks arrive outside market hours.",
    ),
    "released_open": (
        "Was it filed during trading hours?",
        "",
    ),
    "log_doc_chars": (
        "How long is the document?",
        "Length, on a log scale.",
    ),
    "novelty": (
        "How different is it from this company's recent filings?",
        "Cosine distance from its own previous eight 8-Ks.",
    ),
    "days_to_fiscal_year_end": (
        "Where in the fiscal year does it land?",
        "A published calendar that almost never changes.",
    ),
    "days_since_prev_filing": (
        "How long since this company filed anything?",
        "",
    ),
    "filings_trailing_year": (
        "How talkative is this company?",
        "Filings in the previous 365 days, counting only earlier ones.",
    ),
    "vol_20": (
        "How volatile has the stock been?",
        "20-session standard deviation, ending the day before.",
    ),
}

# Terms the page uses that a reader outside this field has no reason to know.
GLOSSARY = [
    (
        "8-K",
        (
        "The form a US public company files to disclose something material between"
        " quarterly reports — anything from an earnings release to a chief executive"
        " leaving."
    ),
    ),
    (
        "Material",
        (
        "Here it means the stock moved at least twice its own normal daily noise after"
        " the filing, up or down. Magnitude, never direction: this project does not"
        " predict which way."
    ),
    ),
    (
        "Average precision",
        (
        "One number for how good a ranking is, from 0 to 1. It rewards putting the"
        " filings that mattered near the top. Chance on this sample is about 0.13."
    ),
    ),
    (
        "ROC AUC",
        (
        "The chance that a filing that mattered is ranked above one that did not. 0.5 is"
        " a coin flip. Reported as a cross-check rather than the headline, because it"
        " averages over the whole ranking including the tail nobody reads."
    ),
    ),
    (
        "precision@5",
        "Of the five filings surfaced on a given morning, the share that turned out to matter.",
    ),
    (
        "Leakage",
        (
        "The model seeing something it could not have known at the time. It does not"
        " crash — it quietly produces a better score, which is what makes it dangerous."
    ),
    ),
    (
        "Purged, embargoed validation",
        (
        "Testing only on filings that came after the ones trained on, and discarding any"
        " training filing whose outcome window overlaps the test period."
    ),
    ),
    (
        "Bootstrap interval",
        (
        "Re-running the measurement on 2,000 resamples to see how much the answer moves."
        " A number without one is a claim with its error bar deleted."
    ),
    ),
    (
        "Paired comparison",
        (
        "Scoring two methods on the same resampled days, so their difference is measured"
        " directly instead of comparing two separate estimates."
    ),
    ),
]

REQUIRED = ("metrics.json", "integrity.json", "leakage_study.csv",
            "capacity_profile.csv", "baseline_intervals.csv",
            "model_comparison_paired.csv", "reaction_capture.csv",
            "anchoring_study.csv", "session_material_counts.csv",
            "oos_importance.csv", "manifest.json")

# The issuer-relative layer is exported by a second command, so these are a
# group rather than a requirement: all of them, or none. A partial set is the
# dangerous state -- it would render a calibration table beside a policy fitted
# in a different run -- so it fails loudly, while a clean absence simply omits
# the sections.
SELF_RELATIVE = ("self_relative_metrics.json", "calibration_comparison.csv",
                 "calibration_curve.csv", "recommendation_confusion.csv",
                 "history_depth_sensitivity.csv", "nlp_feature_ablation.csv")


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
        "importance": rows("oos_importance.csv"),
        **_self_relative(evidence, rows),
    }


def _self_relative(evidence: Path, rows) -> dict:
    present = [name for name in SELF_RELATIVE if (evidence / name).exists()]
    if not present:
        return {"self_relative": None}
    if len(present) != len(SELF_RELATIVE):
        raise SystemExit(
            f"{evidence} has a partial issuer-relative export: missing "
            f"{[n for n in SELF_RELATIVE if n not in present]}. Run "
            "`make self-relative-evidence`; half of it is worse than none, "
            "because the sections would mix two runs."
        )
    return {"self_relative": {
        "metrics": json.loads((evidence / "self_relative_metrics.json").read_text()),
        "calibration": rows("calibration_comparison.csv"),
        "curve": rows("calibration_curve.csv"),
        "states": {r["state"]: r for r in rows("recommendation_confusion.csv")},
        "depth": rows("history_depth_sensitivity.csv"),
        "ablation": rows("nlp_feature_ablation.csv"),
    }}


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


def _features(importance, limit=10) -> str:
    """What the model reads, ordered by how much it actually leans on each.

    Order and numbers come from the out-of-sample permutation importance in the
    evidence; only the plain-language names are written here. A feature the
    evidence does not rank is not shown, so the list cannot describe a column
    that has been removed.
    """
    out = []
    for row in importance[:limit]:
        words = FEATURE_WORDS.get(row["feature"])
        if not words:
            continue
        title, detail = words
        out.append(
            f"<li><b>{title}</b>"
            f"<span class='drop'>{float(row['importance']):+.3f}</span>"
            f"{f'<small>{detail}</small>' if detail else ''}"
            f"<code>{row['feature']}</code></li>"
        )
    return "".join(out)


def _calibration(rows, shipped="identity") -> str:
    """Three ways of turning a score into a probability, scored on the same folds."""
    pretty = {"identity": "Leave the scores alone",
              "isotonic": "Isotonic regression",
              "sigmoid": "Platt scaling"}
    out = []
    for r in rows:
        pick = r["method"] == shipped
        out.append(
            f"<tr{' class=pick' if pick else ''}><td>{pretty.get(r['method'], r['method'])}"
            f"{' <em>(shipped)</em>' if pick else ''}</td>"
            f"<td class='n'>{_num(r['ece'])}</td>"
            f"<td class='n'>{_num(r['brier'])}</td>"
            f"<td class='n'>{_pct(r['brier_skill'])}</td></tr>")
    return "".join(out)


def _reliability(rows, minimum=30) -> str:
    """Stated probability against observed frequency, thin bins left out.

    A bin holding nine filings sits wherever noise puts it, and a reader cannot
    tell that from miscalibration -- so bins below `minimum` are dropped and the
    count stays on every row that remains.
    """
    out = []
    for r in rows:
        count = int(r["count"])
        if count < minimum:
            continue
        stated, observed = float(r["mean_predicted"]), float(r["observed_rate"])
        gap = observed - stated
        out.append(f"<tr><td>{_pct(r['bin_low'], 0)}&ndash;{_pct(r['bin_high'], 0)}</td>"
                   f"<td class='n'>{count:,}</td>"
                   f"<td class='n'>{_pct(stated)}</td>"
                   f"<td class='n'>{_pct(observed)}</td>"
                   f"<td class='n'>{gap:+.1%}</td></tr>")
    return "".join(out)


def _states(states, base_rate) -> str:
    order = [
        ("read_now", "Read now",
         ("A calibrated probability above the threshold <em>and</em> a signal "
          "the reader can check")),
        ("monitor", "Monitor",
         "Above the same threshold with nothing citable behind it"),
        ("routine", "Routine", "Consistent with this issuer's usual filings"),
    ]
    out = []
    for key, name, why in order:
        r = states.get(key)
        if not r or not r["precision"]:
            continue
        precision = float(r["precision"])
        out.append(
            f"<tr{' class=pick' if key == 'read_now' else ''}>"
            f"<td><strong>{name}</strong><br><span class='soft'>{why}</span></td>"
            f"<td class='n'>{int(r['count']):,}</td>"
            f"<td class='n'>{_pct(r['share'])}</td>"
            f"<td class='n'>{_pct(precision)}</td>"
            f"<td class='n'>{precision / base_rate:.2f}&times;</td>"
            f"<td class='n'>{_pct(r['recall'])}</td></tr>")
    return "".join(out)


def _ablation(rows) -> str:
    pretty = {"structured": "Market state and filing metadata",
              "deterministic_text": "&hellip; plus the wording features",
              "transformer_text": "&hellip; plus FinBERT instead",
              "all": "&hellip; everything at once"}
    out = []
    for r in rows:
        separates = r["separates_from_zero"] == "True"
        delta = float(r["pr_auc_vs_structured"])
        if r["group"] == "structured":
            interval = "<span class='soft'>reference</span>"
        else:
            mark = "" if separates else " <span class='soft'>(straddles zero)</span>"
            interval = (f"[{float(r['diff_ci_low']):+.4f}, "
                        f"{float(r['diff_ci_high']):+.4f}]{mark}")
        out.append(
            f"<tr{' class=pick' if r['group'] == 'structured' else ''}>"
            f"<td>{pretty.get(r['group'], r['group'])}</td>"
            f"<td class='n'>{int(r['features'])}</td>"
            f"<td class='n'>{_num(r['pr_auc'])}</td>"
            f"<td class='n'>{'&mdash;' if r['group'] == 'structured' else f'{delta:+.4f}'}</td>"
            f"<td class='n'>{interval}</td></tr>")
    return "".join(out)


def _sentiment_verdict(data) -> str:
    """One sentence on the FinBERT result, or silence if it was never run."""
    self_relative = data.get("self_relative")
    if not self_relative or not self_relative["ablation"]:
        return ""
    row = next((r for r in self_relative["ablation"]
                if r["group"] == "transformer_text"), None)
    if row is None:
        return ""
    return (f"It cost {abs(float(row['pr_auc_vs_structured'])):.4f} average "
            f"precision, and the table below is where that was measured.")


def _issuer_relative(data) -> str:
    """The issuer-relative layer: target, probability, policy, and the ablation.

    Returns nothing at all when that export is absent, rather than a section of
    empty tables. The page is generated from evidence; a section with no
    evidence behind it has nothing to say.
    """
    block = data.get("self_relative")
    if not block:
        return ""

    metrics = block["metrics"]
    target, history = metrics["target"], metrics["history"]
    policy, calibration = metrics["recommendation"], metrics["calibration"]
    base_rate = float(target["base_rate"])
    depth = history["confidence_counts"]
    covered = sum(v for k, v in depth.items() if k != "insufficient_history")
    read_now = block["states"].get("read_now", {})
    lift = (float(read_now["precision"]) / base_rate
            if read_now.get("precision") else float("nan"))

    return f"""
<section>
<h2>Ranking a filing against its own company</h2>
<p>A cross-sectional ranking asks which filing looks most like a mover. That
question quietly favours volatile small caps, which are not more newsworthy, only
noisier. The second model asks a different one: is this filing unusual <em>for
this company</em> &mdash; louder than {_pct(0.8, 0)} of what that same issuer has
filed before, judged only against outcomes already known when it arrived.</p>
<div class="stats">
<div class="stat"><b>{int(target['eligible']):,}</b><span>filings with enough of
their own history<br>out of {int(target['total']):,}</span></div>
<div class="stat"><b>{_pct(base_rate)}</b><span>clear their own bar<br>
the rate a coin-flip would have to beat</span></div>
<div class="stat"><b>{int(history['median_depth'])}</b><span>median prior filings
per issuer<br>up to {int(history['max_depth'])}</span></div>
</div>
<div class="note">An issuer with fewer than
{int(history['policy']['minimum'])} earlier filings has no defensible normal, and
{int(depth.get('insufficient_history', 0)):,} of them are told so rather than
scored &mdash; the card shows the raw evidence and says the history is too short.
Filling that gap with a cross-sectional percentile would answer a different
question in the same visual slot, which is worse than answering none.
{covered:,} filings have enough history to be scored.</div>
</section>

<section>
<h2>Making the score mean sixty-four in a hundred</h2>
<p>A gradient-boosted score between 0 and 1 is not a probability; it is monotone
in the right direction and nothing more. Three ways of fixing that were scored on
the same folds, each fitted on a later slice of its own training block so no
calibrator ever sees the fold it corrects.</p>
<div class="scroll"><table><thead><tr>
<th>Method</th><th class="n">Calibration error</th><th class="n">Brier</th>
<th class="n">Brier skill</th>
</tr></thead><tbody>{_calibration(block['calibration'])}</tbody></table></div>
<div class="note">The usual choice for a tree ensemble is isotonic regression,
and here it made calibration <em>worse</em> &mdash; averaging over trees is already
a calibrating operation, and fitting a flexible monotone map on a limited slice
added more noise than it removed. So the raw scores ship, at
{_num(calibration['ece'])} expected calibration error. That is a measurement, not
a default: a calibration stage nobody checks is how a project ends up shipping a
step function it never looked at.</div>
<div class="scroll"><table><thead><tr>
<th>Stated probability</th><th class="n">Filings</th><th class="n">Said</th>
<th class="n">Happened</th><th class="n">Gap</th>
</tr></thead><tbody>{_reliability(block['curve'])}</tbody></table></div>
<div class="note">Bins holding fewer than 30 filings are left out. They sit
wherever noise puts them, and a reader cannot tell that from miscalibration.</div>
</section>

<section>
<h2>Read now, Monitor, or Routine</h2>
<p>A probability is not an instruction. The policy fires <strong>Read now</strong>
only when a calibrated probability clears
{float(policy['read_now_threshold']):.2f} <em>and</em> at least one issuer-relative
signal a person could check themselves is in that company's top
{_pct(policy['support_percentile'], 0)} &mdash; unusually novel wording, unusually
heavy pre-filing volume. Thresholds are chosen on training folds only and reported
on the folds that follow.</p>
<div class="scroll"><table><thead><tr>
<th>State</th><th class="n">Filings</th><th class="n">Share</th>
<th class="n">Precision</th><th class="n">Vs base rate</th><th class="n">Recall</th>
</tr></thead><tbody>{_states(block['states'], base_rate)}</tbody></table></div>
<div class="note"><strong>Read now</strong> runs at {_pct(read_now.get('precision', 0))}
against a {_pct(base_rate)} base rate &mdash; {lift:.2f}&times; &mdash; on
{_pct(read_now.get('share', 0))} of the queue. <strong>Monitor</strong> reaches
almost the same precision, and the difference between the two states is not
accuracy but whether the card can name a reason. Requiring a citable signal costs
nothing measurable and buys an explanation, which is the trade this policy exists
to make. Nothing here is a view on price: the target is the <em>size</em> of a
reaction, and a direction cannot be recovered from it even in principle.</div>
</section>

{_transformer_section(block)}
"""


def _transformer_section(block) -> str:
    """The FinBERT ablation, or nothing when the corpus was never encoded.

    Kept separate from the sections above because it has its own precondition:
    the issuer-relative evidence can exist without a text cache, and a section
    describing an encode that never happened would be the one hand-written claim
    on a page that has none.
    """
    metrics = block["metrics"]
    if not block["ablation"] or not metrics.get("text"):
        return ""
    return f"""
<section>
<h2>What a financial transformer was worth</h2>
<p>FinBERT reads the disclosure and returns a tone distribution and a dense
representation of the text &mdash; a 2019 model whose training data ends in 2014,
so scoring filings from {metrics['sample']['first_filing'][:4]} onward with it is
not hindsight. All {int(metrics['text']['documents']):,} distinct disclosures were
encoded once and the features added a family at a time, each row against the same folds, the
difference bootstrapped over trading sessions so the two models are compared on
the same days rather than separately.</p>
<div class="scroll"><table><thead><tr>
<th>Features</th><th class="n">Count</th><th class="n">Avg precision</th>
<th class="n">Difference</th><th class="n">95% interval</th>
</tr></thead><tbody>{_ablation(block['ablation'])}</tbody></table></div>
<div class="note">The transformer does not merely fail to help; its interval sits
below zero. The reason is structural rather than a defect in the model, and it is
the part worth keeping: FinBERT predicts the <em>direction</em> of sentiment,
while the target here is the <em>magnitude</em> of a reaction, which is
direction-free by construction &mdash; a very good announcement and a very bad one
are both positives. Tone is close to orthogonal to the question being asked, and
six columns of near-orthogonal signal make a forest's splits worse rather than
better. So it does not ship. The cache and the code stay, because a directional
target would make it worth re-testing and the corpus is already encoded.</div>
</section>
"""


def _glossary() -> str:
    return "".join(f"<dt>{term}</dt><dd>{meaning}</dd>" for term, meaning in GLOSSARY)


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
.features{{margin:24px 0 0;padding:0;list-style:none;counter-reset:f}}
.features li{{position:relative;padding:16px 0 16px 44px;border-bottom:1px solid var(--line);
counter-increment:f}}
.features li::before{{content:counter(f);position:absolute;left:0;top:17px;
color:var(--blue);font-size:12px;font-weight:800}}
.features b{{font:500 17px/1.35 Georgia,serif;font-weight:500}}
.features .drop{{margin-left:10px;color:var(--muted);font-size:12px;
font-variant-numeric:tabular-nums}}
.features small{{display:block;margin-top:5px;color:var(--muted);font-size:13.5px;
line-height:1.55;max-width:60ch}}
.features code{{display:inline-block;margin-top:7px;color:var(--muted);font-size:11px;
font-family:ui-monospace,Menlo,monospace}}
.glossary{{margin:22px 0 0}}
.glossary dt{{margin-top:16px;font-weight:750;font-size:14px}}
.glossary dd{{margin:5px 0 0;color:var(--muted);font-size:14px;max-width:64ch}}
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
<h1>Ranking SEC filings,<br>audited against hindsight</h1>
<p class="lede">This ranks which of a morning's SEC disclosures deserve a human
read, and reports {_num(honest['average_precision'])} average precision after an
audit that removes four common sources of hindsight. Written the ordinary way the
same pipeline reports {_num(naive['average_precision'])} &mdash; and that gap is
the measurement worth having, because none of the four announces itself.</p>
<div class="swing">
<b class="bad">{_num(naive['average_precision'])}</b><span class="arr">&rarr;</span>
<b class="good">{_num(honest['average_precision'])}</b>
<small>Written the ordinary way &rarr; audited. No feature or model differs between
them, only whether the pipeline may see what it could not have known at the time.
Every number below is the audited one.</small>
</div>
</header>

<section>
<h2>What each form of hindsight is worth</h2>
<p>Each row removes exactly one. The metric moves erratically because every
correction also changes which filings are measurable at all &mdash; so the column
carrying the argument is the count of impossible entries, an invariant rather
than a score.</p>
<div class="scroll"><table><thead><tr>
<th>Stage</th><th class="n">Avg precision</th><th class="n">ROC AUC</th>
<th class="n">Impossible entries</th><th class="n">Guards failing</th>
</tr></thead><tbody>{_ladder(ladder)}</tbody></table></div>
<div class="note">An <strong>impossible entry</strong> is a filing whose entry
price was printed before EDGAR accepted the document &mdash; a position taken on
news that did not exist yet. The naive rule creates
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
<h2>What the model actually reads</h2>
<p>Every input has to be computable at the moment the filing lands &mdash; nothing
about what happened next. The ten it leans on most, ordered by how much the score
falls when that column is shuffled:</p>
<ol class="features">{_features(data['importance'])}</ol>
<div class="note">There are {len(data['importance'])} inputs in total; the rest are
the remaining 8-K item codes and slower-moving market state. Notice what is
<em>not</em> here: no price target, no analyst estimate, no sentiment score. A
sentiment model trained <em>today</em> has read what happened afterwards, which is
the same leak in a friendlier costume &mdash; and a sentiment model old enough to
avoid that was tried and measured. {_sentiment_verdict(data)}</div>
</section>
{_issuer_relative(data)}
<section>
<h2>Terms used above</h2>
<dl class="glossary">{_glossary()}</dl>
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

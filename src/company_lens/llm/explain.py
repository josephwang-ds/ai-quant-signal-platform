"""No-key fallback that obeys the same shape as a future LLM response."""

from __future__ import annotations

from company_lens.contracts import FilingBrief


def deterministic_explanation(
    ticker: str, performance: dict, filings: list[FilingBrief]
) -> dict:
    latest = filings[0] if filings else None
    comparison_change = (
        next(
            (
                change
                for change in latest.comparison.changes
                if change.current is not None
                and change.current.anchor
                in {passage.anchor for passage in latest.passages}
            ),
            None,
        )
        if latest and latest.comparison
        else None
    )
    if latest and comparison_change and latest.comparison:
        counts = latest.comparison.counts
        changed = {
            "text": (
                f"Against the prior comparable {latest.comparison.comparable_key}, the "
                f"primary document has {counts['changed']} changed, {counts['added']} added, "
                f"and {counts['removed']} removed meaningful sentences."
            ),
            "citations": [comparison_change.current.anchor],
        }
    elif latest and latest.passages:
        topic = latest.items[0]["label"].lower() if latest.items else "a corporate update"
        changed = {
            "text": f"The latest {latest.form} reports {topic}.",
            "citations": [latest.passages[0].anchor],
        }
    elif latest:
        topic = latest.items[0]["label"].lower() if latest.items else "a corporate update"
        changed = {
            "text": (
                f"{ticker}'s latest {latest.form} is categorized as {topic}. "
                "The cached primary document did not contain a substantive passage "
                "that the deterministic extractor could cite."
            ),
            "citations": [],
        }
    else:
        changed = {
            "text": "No filing is available for this company in the local dataset.",
            "citations": [],
        }

    asset = performance["asset"]
    why = {
        "text": (
            f"Over the selected historical period, {ticker} returned "
            f"{asset['total_return']:.1%} with a maximum drawdown of "
            f"{asset['max_drawdown']:.1%}. These are historical observations, not a forecast."
        ),
        "citations": ["metric:asset.total_return", "metric:asset.max_drawdown"],
    }
    uncertainty = {
        "text": (
            "This local snapshot covers 8-K filings and adjusted daily prices only. "
            "It does not establish valuation, future return, or an investment recommendation."
        ),
        "citations": [],
    }
    return {
        "mode": "deterministic_fallback",
        "what_changed": [changed],
        "why_it_matters": [why],
        "uncertainties": [uncertainty],
    }

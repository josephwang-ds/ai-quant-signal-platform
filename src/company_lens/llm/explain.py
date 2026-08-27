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
            "text_zh": (
                f"相对此前可比的 {latest.comparison.comparable_key}, 主文档有 "
                f"{counts['changed']} 处改动、{counts['added']} 处新增、"
                f"{counts['removed']} 处删除的有意义句子。"
            ),
            "citations": [comparison_change.current.anchor],
        }
    elif latest and latest.passages:
        topic = latest.items[0]["label"].lower() if latest.items else "a corporate update"
        topic_zh = (
            (latest.items[0].get("label_zh") or latest.items[0]["label"])
            if latest.items
            else "公司更新"
        )
        changed = {
            "text": f"The latest {latest.form} reports {topic}.",
            "text_zh": f"最新 {latest.form} 披露了{topic_zh}。",
            "citations": [latest.passages[0].anchor],
        }
    elif latest:
        topic = latest.items[0]["label"].lower() if latest.items else "a corporate update"
        topic_zh = (
            (latest.items[0].get("label_zh") or latest.items[0]["label"])
            if latest.items
            else "公司更新"
        )
        changed = {
            "text": (
                f"{ticker}'s latest {latest.form} is categorized as {topic}. "
                "The cached primary document did not contain a substantive passage "
                "that the deterministic extractor could cite."
            ),
            "text_zh": (
                f"{ticker} 最新 {latest.form} 归类为{topic_zh}。"
                "缓存主文档中没有确定性提取器可引用的实质性段落。"
            ),
            "citations": [],
        }
    else:
        changed = {
            "text": "No filing is available for this company in the local dataset.",
            "text_zh": "本地数据集中没有该公司的披露。",
            "citations": [],
        }

    asset = performance["asset"]
    why = {
        "text": (
            f"Over the selected historical period, {ticker} returned "
            f"{asset['total_return']:.1%} with a maximum drawdown of "
            f"{asset['max_drawdown']:.1%}. These are historical observations, not a forecast."
        ),
        "text_zh": (
            f"在所选历史期间, {ticker} 累计回报为 {asset['total_return']:.1%}, "
            f"最大回撤为 {asset['max_drawdown']:.1%}。这些是历史观测, 不是预测。"
        ),
        "citations": ["metric:asset.total_return", "metric:asset.max_drawdown"],
    }
    uncertainty = {
        "text": (
            "This local snapshot covers SEC disclosures, latest-restated annual Company "
            "Facts when available, and adjusted daily prices. It does not establish "
            "valuation, future return, or an investment recommendation."
        ),
        "text_zh": (
            "本地快照覆盖 SEC 披露、可用时的最新重述年度 Company Facts\uFF0C"
            "以及复权日线价格。它不构成估值、未来回报或投资建议。"
        ),
        "citations": [],
    }
    return {
        "mode": "deterministic_fallback",
        "what_changed": [changed],
        "why_it_matters": [why],
        "uncertainties": [uncertainty],
    }

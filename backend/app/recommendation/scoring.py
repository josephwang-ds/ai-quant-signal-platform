import pandas as pd

# 评分所需列（缺失则无法打分）
SCORING_COLUMNS = [
    "close",
    "ma20",
    "ma60",
    "return_20d",
    "return_60d",
    "volatility_20d",
    "rsi_14",
    "volume_change",
]

# 波动率上限：低于此值视为可接受范围
VOLATILITY_THRESHOLD = 0.45


def assign_signal_label(score: int) -> str:
    """
    将数值分数映射为 watchlist 风格标签（非买卖建议）。
    """
    if score >= 80:
        return "Strong Bullish Watchlist"
    if score >= 60:
        return "Bullish Watchlist"
    if score >= 40:
        return "Neutral"
    if score >= 20:
        return "Bearish Watchlist"
    return "High Risk / Avoid"


def calculate_signal_score(row) -> dict:
    """
    基于单行指标数据计算规则型信号分数（0–100）。

    每个维度最高 20 分，共 5 个维度：
    短期趋势、中期趋势、动量、RSI、波动率。

    返回:
        signal_score: 总分
        signal_label: watchlist 标签
        reasons: 各维度的文字说明（无论加分与否均记录）
        signal_components: 结构化评分维度明细
    """
    score = 0
    reasons: list[str] = []
    signal_components: list[dict] = []

    close = float(row["close"])
    ma20 = float(row["ma20"])
    ma60 = float(row["ma60"])
    return_20d = float(row["return_20d"])
    rsi_14 = float(row["rsi_14"])
    volatility_20d = float(row["volatility_20d"])

    # A. 短期趋势：收盘价 vs MA20
    short_term_passed = close > ma20
    short_term_desc = (
        "Price is above MA20, showing short-term trend strength."
        if short_term_passed
        else "Price is below MA20, suggesting weak short-term trend."
    )
    if short_term_passed:
        score += 20
    reasons.append(short_term_desc)
    signal_components.append(
        {
            "name": "Short-term trend",
            "passed": short_term_passed,
            "points": 20 if short_term_passed else 0,
            "description": short_term_desc,
        }
    )

    # B. 中期趋势：MA20 vs MA60
    medium_term_passed = ma20 > ma60
    medium_term_desc = (
        "MA20 is above MA60, indicating positive medium-term trend."
        if medium_term_passed
        else "MA20 is below MA60, indicating weaker trend structure."
    )
    if medium_term_passed:
        score += 20
    reasons.append(medium_term_desc)
    signal_components.append(
        {
            "name": "Medium-term trend",
            "passed": medium_term_passed,
            "points": 20 if medium_term_passed else 0,
            "description": medium_term_desc,
        }
    )

    # C. 动量：20 日收益率
    momentum_passed = return_20d > 0
    momentum_desc = (
        "20-day return is positive, suggesting recent momentum."
        if momentum_passed
        else "20-day return is negative, suggesting weak recent momentum."
    )
    if momentum_passed:
        score += 20
    reasons.append(momentum_desc)
    signal_components.append(
        {
            "name": "Momentum",
            "passed": momentum_passed,
            "points": 20 if momentum_passed else 0,
            "description": momentum_desc,
        }
    )

    # D. RSI：健康区间 40–70
    rsi_passed = 40 <= rsi_14 <= 70
    if rsi_passed:
        rsi_desc = (
            "RSI is in a healthy range, not extremely overbought or oversold."
        )
        score += 20
    elif rsi_14 > 70:
        rsi_desc = "RSI is above 70, suggesting possible overbought risk."
    else:
        rsi_desc = (
            "RSI is below 40, suggesting weak momentum or oversold conditions."
        )
    reasons.append(rsi_desc)
    signal_components.append(
        {
            "name": "RSI health",
            "passed": rsi_passed,
            "points": 20 if rsi_passed else 0,
            "description": rsi_desc,
        }
    )

    # E. 波动率：年化 20 日波动率
    volatility_passed = volatility_20d < VOLATILITY_THRESHOLD
    volatility_desc = (
        "20-day annualized volatility is within an acceptable range."
        if volatility_passed
        else "20-day annualized volatility is high, increasing risk."
    )
    if volatility_passed:
        score += 20
    reasons.append(volatility_desc)
    signal_components.append(
        {
            "name": "Volatility control",
            "passed": volatility_passed,
            "points": 20 if volatility_passed else 0,
            "description": volatility_desc,
        }
    )

    return {
        "signal_score": score,
        "signal_label": assign_signal_label(score),
        "reasons": reasons,
        "signal_components": signal_components,
    }


def _features_dict(row) -> dict:
    """提取最新行的特征快照，用于 API 响应（数值保留 6 位小数）。"""
    close = float(row["close"])
    ma20 = float(row["ma20"])
    ma60 = float(row["ma60"])

    return {
        "daily_return": round(float(row["daily_return"]), 6),
        "return_20d": round(float(row["return_20d"]), 6),
        "return_60d": round(float(row["return_60d"]), 6),
        "ma20": round(ma20, 6),
        "ma60": round(ma60, 6),
        "distance_to_ma20": round(close / ma20 - 1, 6),
        "distance_to_ma60": round(close / ma60 - 1, 6),
        "volatility_20d": round(float(row["volatility_20d"]), 6),
        "rsi_14": round(float(row["rsi_14"]), 6),
        "volume_change": round(float(row["volume_change"]), 6),
    }


def score_latest_signal(df: pd.DataFrame) -> dict:
    """
    对 DataFrame 最新一行计算信号分数。

    异常:
        ValueError: 指标数据不足，无法打分
    """
    clean_df = df.dropna(subset=SCORING_COLUMNS)

    if clean_df.empty:
        raise ValueError(
            "Not enough indicator data to calculate signal score."
        )

    latest = clean_df.iloc[-1]
    scoring = calculate_signal_score(latest)

    return {
        "ticker": str(latest["ticker"]),
        "date": latest["date"].strftime("%Y-%m-%d"),
        "last_price": round(float(latest["close"]), 2),
        "signal_score": scoring["signal_score"],
        "signal_label": scoring["signal_label"],
        "reasons": scoring["reasons"],
        "signal_components": scoring["signal_components"],
        "features": _features_dict(latest),
    }

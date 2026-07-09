"""回测实验持久化仓库（Experiments Persistence v1）。"""

from __future__ import annotations

import json
import logging
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Optional
from uuid import UUID

from psycopg.types.json import Json

from app.db.client import get_db_connection, is_database_configured

logger = logging.getLogger(__name__)


class DatabaseUnavailableError(RuntimeError):
    """数据库未配置或不可用。"""


def _require_database() -> None:
    if not is_database_configured():
        raise DatabaseUnavailableError(
            "Database is not configured. Set SUPABASE_DB_URL."
        )


def _json_safe(value: Any) -> Any:
    """将常见 Python 类型转为 JSON 可序列化结构。"""
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, UUID):
        return str(value)
    return value


def _serialize_row(row: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in row.items():
        if isinstance(value, UUID):
            result[key] = str(value)
        elif isinstance(value, datetime):
            result[key] = value.isoformat()
        elif isinstance(value, date):
            result[key] = value.isoformat()
        elif isinstance(value, Decimal):
            result[key] = float(value)
        elif isinstance(value, (dict, list)):
            result[key] = _json_safe(value)
        else:
            result[key] = value
    return result


def create_backtest_run(
    *,
    ticker: str,
    market: Optional[str],
    data_source: str,
    strategy: str,
    strategy_config: dict[str, Any],
    start_date: str,
    end_date: Optional[str],
    transaction_cost: Optional[float],
    metrics: dict[str, Any],
    notes: Optional[str],
    trades: list[dict[str, Any]],
) -> str:
    """在同一事务中写入 backtest_runs 与 backtest_trades，返回 run id。"""
    _require_database()

    try:
        with get_db_connection() as conn:
            with conn.transaction():
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        insert into backtest_runs (
                          ticker, market, data_source, strategy, strategy_config,
                          start_date, end_date, transaction_cost, metrics, notes
                        )
                        values (
                          %(ticker)s, %(market)s, %(data_source)s, %(strategy)s,
                          %(strategy_config)s, %(start_date)s, %(end_date)s,
                          %(transaction_cost)s, %(metrics)s, %(notes)s
                        )
                        returning id
                        """,
                        {
                            "ticker": ticker,
                            "market": market,
                            "data_source": data_source,
                            "strategy": strategy,
                            "strategy_config": Json(_json_safe(strategy_config)),
                            "start_date": start_date,
                            "end_date": end_date,
                            "transaction_cost": transaction_cost,
                            "metrics": Json(_json_safe(metrics)),
                            "notes": notes,
                        },
                    )
                    row = cur.fetchone()
                    if not row:
                        raise RuntimeError("Failed to insert backtest run")
                    run_id = row[0]

                    for trade in trades:
                        cur.execute(
                            """
                            insert into backtest_trades (
                              backtest_run_id, trade_date, action, price,
                              signal, position_after, reason
                            )
                            values (
                              %(backtest_run_id)s, %(trade_date)s, %(action)s,
                              %(price)s, %(signal)s, %(position_after)s, %(reason)s
                            )
                            """,
                            {
                                "backtest_run_id": run_id,
                                "trade_date": trade["trade_date"],
                                "action": trade["action"],
                                "price": trade.get("price"),
                                "signal": trade.get("signal"),
                                "position_after": trade.get("position_after"),
                                "reason": trade.get("reason"),
                            },
                        )

        return str(run_id)
    except DatabaseUnavailableError:
        raise
    except Exception as exc:
        logger.warning("create_backtest_run failed: %s", type(exc).__name__)
        raise DatabaseUnavailableError("Database connection failed.") from exc


def list_backtest_runs(*, limit: int = 50, offset: int = 0) -> list[dict[str, Any]]:
    """按创建时间倒序列出回测实验摘要。"""
    _require_database()
    limit = max(1, min(limit, 200))
    offset = max(0, offset)

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    select
                      r.id, r.ticker, r.market, r.data_source, r.strategy,
                      r.strategy_config, r.start_date, r.end_date,
                      r.transaction_cost, r.metrics, r.notes, r.created_at,
                      coalesce(t.trade_count, 0) as trade_count
                    from backtest_runs r
                    left join (
                      select backtest_run_id, count(*) as trade_count
                      from backtest_trades
                      group by backtest_run_id
                    ) t on t.backtest_run_id = r.id
                    order by r.created_at desc
                    limit %(limit)s offset %(offset)s
                    """,
                    {"limit": limit, "offset": offset},
                )
                columns = [desc.name for desc in cur.description]
                rows = cur.fetchall()

        results: list[dict[str, Any]] = []
        for row in rows:
            item = _serialize_row(dict(zip(columns, row)))
            metrics = item.get("metrics") or {}
            if isinstance(metrics, str):
                try:
                    metrics = json.loads(metrics)
                except json.JSONDecodeError:
                    metrics = {}
            item["metrics"] = metrics
            strategy_config = item.get("strategy_config") or {}
            if isinstance(strategy_config, str):
                try:
                    strategy_config = json.loads(strategy_config)
                except json.JSONDecodeError:
                    strategy_config = {}
            item["strategy_config"] = strategy_config
            item["trade_count"] = int(item.get("trade_count") or 0)
            results.append(item)

        return results
    except DatabaseUnavailableError:
        raise
    except Exception as exc:
        logger.warning("list_backtest_runs failed: %s", type(exc).__name__)
        raise DatabaseUnavailableError("Database connection failed.") from exc


def get_backtest_run(run_id: str) -> Optional[dict[str, Any]]:
    """获取单条回测实验详情（含交易日志）。"""
    _require_database()

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    select
                      id, ticker, market, data_source, strategy, strategy_config,
                      start_date, end_date, transaction_cost, metrics, notes, created_at
                    from backtest_runs
                    where id = %(run_id)s
                    """,
                    {"run_id": run_id},
                )
                row = cur.fetchone()
                if not row:
                    return None

                columns = [desc.name for desc in cur.description]
                run = _serialize_row(dict(zip(columns, row)))

                metrics = run.get("metrics") or {}
                if isinstance(metrics, str):
                    try:
                        metrics = json.loads(metrics)
                    except json.JSONDecodeError:
                        metrics = {}
                run["metrics"] = metrics

                strategy_config = run.get("strategy_config") or {}
                if isinstance(strategy_config, str):
                    try:
                        strategy_config = json.loads(strategy_config)
                    except json.JSONDecodeError:
                        strategy_config = {}
                run["strategy_config"] = strategy_config

                cur.execute(
                    """
                    select
                      id, trade_date, action, price, signal, position_after, reason, created_at
                    from backtest_trades
                    where backtest_run_id = %(run_id)s
                    order by trade_date asc, created_at asc
                    """,
                    {"run_id": run_id},
                )
                trade_columns = [desc.name for desc in cur.description]
                trades = [
                    _serialize_row(dict(zip(trade_columns, trade_row)))
                    for trade_row in cur.fetchall()
                ]

        run["trades"] = trades
        return run
    except DatabaseUnavailableError:
        raise
    except Exception as exc:
        logger.warning("get_backtest_run failed: %s", type(exc).__name__)
        raise DatabaseUnavailableError("Database connection failed.") from exc


def delete_backtest_run(run_id: str) -> bool:
    """删除回测实验（级联删除交易）。返回是否删除了行。"""
    _require_database()

    try:
        with get_db_connection() as conn:
            with conn.transaction():
                with conn.cursor() as cur:
                    cur.execute(
                        "delete from backtest_runs where id = %(run_id)s",
                        {"run_id": run_id},
                    )
                    return cur.rowcount > 0
    except DatabaseUnavailableError:
        raise
    except Exception as exc:
        logger.warning("delete_backtest_run failed: %s", type(exc).__name__)
        raise DatabaseUnavailableError("Database connection failed.") from exc

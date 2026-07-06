"""Supabase Postgres 连接客户端（Database Preparation v1）。"""

import logging
import os
from contextlib import contextmanager
from typing import Generator, Optional

import psycopg

logger = logging.getLogger(__name__)

DATABASE_NAME = "supabase_postgres"


def get_database_url() -> Optional[str]:
    """从环境变量读取数据库连接串；未配置时返回 None。"""
    url = os.getenv("SUPABASE_DB_URL", "").strip()
    return url or None


def is_database_configured() -> bool:
    """是否已设置 SUPABASE_DB_URL。"""
    return get_database_url() is not None


@contextmanager
def get_db_connection() -> Generator[psycopg.Connection, None, None]:
    """
    获取 psycopg 连接（上下文管理器）。

    Transaction Pooler 模式下禁用 prepared statements（prepare_threshold=None）。
  """
    url = get_database_url()
    if not url:
        raise RuntimeError("SUPABASE_DB_URL is not configured")

    conn = psycopg.connect(url, prepare_threshold=None)
    try:
        yield conn
    finally:
        conn.close()


def check_database_connection() -> dict:
    """
    检查数据库配置与连通性。

    不记录、不返回连接串或凭据。
    """
    if not is_database_configured():
        return {
            "configured": False,
            "connected": False,
            "message": "Database is not configured. Set SUPABASE_DB_URL.",
            "database": DATABASE_NAME,
        }

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("select 1 as ok")
                cur.fetchone()
        return {
            "configured": True,
            "connected": True,
            "message": "Database connection successful.",
            "database": DATABASE_NAME,
        }
    except Exception as exc:
        logger.warning("Database connection failed: %s", type(exc).__name__)
        return {
            "configured": True,
            "connected": False,
            "message": "Database connection failed.",
            "database": DATABASE_NAME,
        }

"""数据库状态 API。"""

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.db.client import check_database_connection

router = APIRouter(prefix="/api/database", tags=["database"])


@router.get("/status", response_model=None)
def get_database_status():
    """返回后端 Supabase Postgres 配置与连通性状态。"""
    result = check_database_connection()

    if result["configured"] and not result["connected"]:
        return JSONResponse(status_code=503, content=result)

    return result

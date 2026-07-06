import os

# 本地开发默认允许的前端来源
DEFAULT_LOCAL_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3001",
]


def get_allowed_origins() -> list[str]:
    """
    从环境变量 ALLOWED_ORIGINS 读取 CORS 白名单（逗号分隔）。
    未配置时回退到本地开发地址。
    """
    raw = os.getenv("ALLOWED_ORIGINS", "").strip()
    if not raw:
        return DEFAULT_LOCAL_ORIGINS

    origins = [origin.strip() for origin in raw.split(",") if origin.strip()]
    return origins or DEFAULT_LOCAL_ORIGINS

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
    未配置时回退到本地开发地址。显式来源会去除尾部斜杠并去重；
    通配符被拒绝，避免意外放宽浏览器访问边界。
    """
    raw = os.getenv("ALLOWED_ORIGINS", "").strip()
    if not raw:
        return list(DEFAULT_LOCAL_ORIGINS)

    origins: list[str] = []
    for value in raw.split(","):
        origin = value.strip().rstrip("/")
        if not origin:
            continue
        if origin == "*":
            raise ValueError("ALLOWED_ORIGINS must list explicit origins; '*' is not allowed.")
        if origin not in origins:
            origins.append(origin)

    return origins or list(DEFAULT_LOCAL_ORIGINS)

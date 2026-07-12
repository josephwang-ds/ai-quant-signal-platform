"""数据源状态端点 TestClient 测试。"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

STATUS_URL = "/api/data-sources/status"


def test_data_sources_status() -> None:
    response = client.get(STATUS_URL)

    assert response.status_code == 200
    payload = response.json()
    assert payload["active_provider"] == "auto"
    assert "fallback_chain" in payload

    providers = {item["name"]: item for item in payload["providers"]}
    assert providers["auto"]["status"] == "active"
    assert providers["stooq"]["status"] == "active"
    assert providers["yahoo"]["status"] == "active"
    assert providers["akshare"]["status"] in {"active", "degraded"}
    assert providers["coingecko"]["status"] == "planned"
    assert providers["csv"]["status"] == "planned"

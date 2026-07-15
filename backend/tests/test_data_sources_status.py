"""数据源状态端点 TestClient 测试。"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

STATUS_URL = "/api/data-sources/status"


def test_data_sources_status() -> None:
    response = client.get(STATUS_URL)

    assert response.status_code == 200
    payload = response.json()
    assert payload["routing_mode"] == "asset_class"

    providers = {item["name"]: item for item in payload["providers"]}
    assert providers["yahoo"]["installed"] is True
    assert providers["yahoo"]["configured"] is True
    assert "us_equity" in providers["yahoo"]["supported_assets"]
    assert providers["yahoo"]["live_health_checked"] is False

    akshare = providers["akshare"]
    assert akshare["installed"] == akshare["configured"]
    assert akshare["supported_assets"] == ["cn_equity"]
    assert akshare["live_health_checked"] is False

    assert "SPY" in payload["symbol_examples"]
    assert "600519.SH" in payload["symbol_examples"]

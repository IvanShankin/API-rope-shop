import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_login_rate_limiting(client_for_tests: AsyncClient, monkeypatch):
    from src.core.rate_limit import limiter

    # Временно включаем лимитер только для этого теста
    monkeypatch.setattr(limiter, "enabled", True)

    # Делаем 5 запросов — они проходят (или падают с 400/401, но не 429)
    for _ in range(5):
        await client_for_tests.post("/auth/login", data={"username": "a", "password": "b"})

    # 6-й запрос должен вернуть 429
    response = await client_for_tests.post("/auth/login", data={"username": "a", "password": "b"})
    assert response.status_code == 429
    assert "Rate limit exceeded" in response.json()["detail"]
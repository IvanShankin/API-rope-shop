import pytest
from httpx import AsyncClient


class TestsForCORS:

    @pytest.mark.asyncio
    async def test_cors_preflight_localhost(
        self,
        client_for_tests: AsyncClient,
    ) -> None:
        response = await client_for_tests.options(
            "/auth/login",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type,authorization",
            },
        )

        assert response.status_code == 200
        assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"
        assert response.headers.get("access-control-allow-credentials") == "true"
        assert "POST" in response.headers.get("access-control-allow-methods", "")

    @pytest.mark.asyncio
    async def test_cors_preflight_127_0_0_1(
        self,
        client_for_tests: AsyncClient,
    ) -> None:
        response = await client_for_tests.options(
            "/colors",
            headers={
                "Origin": "http://127.0.0.1:3000",
                "Access-Control-Request-Method": "GET",
            },
        )

        assert response.status_code == 200
        assert response.headers.get("access-control-allow-origin") == "http://127.0.0.1:3000"
        assert response.headers.get("access-control-allow-credentials") == "true"

    @pytest.mark.asyncio
    async def test_cors_request_allowed_origin(
        self,
        client_for_tests: AsyncClient,
    ) -> None:
        response = await client_for_tests.get(
            "/colors",
            headers={
                "Origin": "http://localhost:5173",
            },
        )

        assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"
        assert response.headers.get("access-control-allow-credentials") == "true"

    @pytest.mark.asyncio
    async def test_cors_disallowed_origin(
        self,
        client_for_tests: AsyncClient,
    ) -> None:
        response = await client_for_tests.options(
            "/colors",
            headers={
                "Origin": "https://unauthorized-domain.com",
                "Access-Control-Request-Method": "GET",
            },
        )

        assert "access-control-allow-origin" not in response.headers

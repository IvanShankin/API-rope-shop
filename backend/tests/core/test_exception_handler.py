import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_validation_error_handler_formats_string_detail(client_for_tests: AsyncClient):
    """
    Проверяет, что при ошибке валидации тела запроса (422)
    поле detail возвращается читаемой строкой, а не списком словарей,
    чтобы не ломать фронтенд (toast.error(error.response.data.detail)),
    при этом полный список ошибок доступен в ключе errors.
    """
    # Отправляем невалидный запрос в POST /reviews с пустым телом
    response = await client_for_tests.post("/reviews", json={})
    assert response.status_code == 422
    data = response.json()

    assert "detail" in data
    assert isinstance(data["detail"], str)
    assert len(data["detail"]) > 0

    assert "message" in data
    assert isinstance(data["message"], str)

    assert "errors" in data
    assert isinstance(data["errors"], list)
    assert len(data["errors"]) > 0

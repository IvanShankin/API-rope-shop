import pytest
from sqlalchemy import select

from src.modules.base.database_model import Language
from src.modules.users.models import UserRole
from tests.modules.users.fixtures.models_dto import CreateUserFixtureDTO
from tests.modules.colors.fixtures.models_dto import (
    CreateColorFixtureDTO,
    CreateColorTranslationFixtureDTO,
)
from tests.modules.rope_products.fixtures.models_dto import CreateRopeProductFixtureDTO
from tests.modules.rope_product_color.fixtures.models_dto import CreateRopeProductColorFixtureDTO
from src.modules.rope_product_color.models import ProductColor
from src.modules.rope_product_color.models_dto import (
    ProductColorCreate,
    ProductColorUpdateIndexDTO,
    ProductColorResponseDTO,
    ProductColorLocalizedResponseDTO,
)
from tests.helpers.functions import comparison_models


class TestsForSuccess:

    @pytest.mark.asyncio
    async def test_get_colors_by_product_id(
        self,
        client_for_tests,
        create_rope_product_fixture,
        create_color_fixture,
        create_rope_product_color_fixture,
    ):
        """Получение списка цветов товара с локализацией по умолчанию (ENG)."""
        product = await create_rope_product_fixture()
        color_1 = await create_color_fixture(
            CreateColorFixtureDTO(code="red_01", name="Red", index=1)
        )
        color_2 = await create_color_fixture(
            CreateColorFixtureDTO(code="blue_01", name="Blue", index=2)
        )

        link_1 = await create_rope_product_color_fixture(
            CreateRopeProductColorFixtureDTO(
                product_id=product.product_id,
                color_id=color_1.id,
                index=1,
            )
        )
        link_2 = await create_rope_product_color_fixture(
            CreateRopeProductColorFixtureDTO(
                product_id=product.product_id,
                color_id=color_2.id,
                index=2,
            )
        )

        response = await client_for_tests.get(
            f"/rope_product_colors/by-product/{product.product_id}"
        )
        assert response.status_code == 200

        data = [
            ProductColorLocalizedResponseDTO.model_validate(item)
            for item in response.json()
        ]
        assert len(data) == 2
        assert data[0].id == link_1.id
        assert data[0].index == 1
        assert data[0].color is not None
        assert data[0].color.code == "red_01"
        assert data[0].color.name == "Red"

        assert data[1].id == link_2.id
        assert data[1].index == 2
        assert data[1].color is not None
        assert data[1].color.code == "blue_01"
        assert data[1].color.name == "Blue"

    @pytest.mark.asyncio
    async def test_get_colors_by_product_id_locale(
        self,
        client_for_tests,
        create_rope_product_fixture,
        create_color_fixture,
        create_color_translation_fixture,
        create_rope_product_color_fixture,
    ):
        """Получение списка цветов товара с немецкой локализацией (GER)."""
        product = await create_rope_product_fixture()
        color = await create_color_fixture(
            CreateColorFixtureDTO(locale=Language.ENG, name="Green")
        )
        await create_color_translation_fixture(
            CreateColorTranslationFixtureDTO(
                color_id=color.id,
                locale=Language.GER,
                name="Grün",
            )
        )

        link = await create_rope_product_color_fixture(
            CreateRopeProductColorFixtureDTO(
                product_id=product.product_id,
                color_id=color.id,
                index=1,
            )
        )

        response = await client_for_tests.get(
            f"/rope_product_colors/by-product/{product.product_id}",
            params={"locale": "ger"},
        )
        assert response.status_code == 200

        data = [
            ProductColorLocalizedResponseDTO.model_validate(item)
            for item in response.json()
        ]
        assert len(data) == 1
        assert data[0].id == link.id
        assert data[0].color is not None
        assert data[0].color.name == "Grün"

    @pytest.mark.asyncio
    async def test_get_colors_by_product_id_empty(
        self,
        client_for_tests,
        create_rope_product_fixture,
    ):
        """Получение пустого списка цветов для товара без привязок."""
        product = await create_rope_product_fixture()

        response = await client_for_tests.get(
            f"/rope_product_colors/by-product/{product.product_id}"
        )
        assert response.status_code == 200

        data = [
            ProductColorLocalizedResponseDTO.model_validate(item)
            for item in response.json()
        ]
        assert data == []

    @pytest.mark.asyncio
    async def test_get_rope_product_color_by_id(
        self,
        client_for_tests,
        create_rope_product_color_fixture,
    ):
        """Получение привязки цвета по ID."""
        link = await create_rope_product_color_fixture()

        response = await client_for_tests.get(f"/rope_product_colors/{link.id}")
        assert response.status_code == 200

        resp_dto = ProductColorResponseDTO.model_validate(response.json())
        assert resp_dto.id == link.id
        assert resp_dto.product_id == link.product_id
        assert resp_dto.color_id == link.color_id
        assert resp_dto.index == link.index
        assert resp_dto.color is not None
        assert comparison_models(link, resp_dto, keys_not_checked=["color"])

    @pytest.mark.asyncio
    async def test_create_rope_product_color_first_item(
        self,
        session_db,
        client_for_tests,
        create_user_fixture,
        create_rope_product_fixture,
        create_color_fixture,
    ):
        """Создание первой привязки цвета к товару (индекс должен стать 1)."""
        admin_user, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        product = await create_rope_product_fixture()
        color = await create_color_fixture()

        req_data = ProductColorCreate(
            product_id=product.product_id,
            color_id=color.id,
        )

        response = await client_for_tests.post(
            "/rope_product_colors",
            headers={"Authorization": f"Bearer {access_token}"},
            json=req_data.model_dump(),
        )
        assert response.status_code == 201

        resp_dto = ProductColorResponseDTO.model_validate(response.json())
        assert resp_dto.product_id == product.product_id
        assert resp_dto.color_id == color.id
        assert resp_dto.index == 1
        assert resp_dto.color is not None
        assert resp_dto.color.id == color.id

        # Проверка в БД
        res = await session_db.execute(
            select(ProductColor).where(ProductColor.id == resp_dto.id)
        )
        db_item = res.scalar_one_or_none()
        assert db_item is not None
        assert db_item.product_id == product.product_id
        assert db_item.color_id == color.id
        assert db_item.index == 1

    @pytest.mark.asyncio
    async def test_create_rope_product_color_auto_increment_index(
        self,
        session_db,
        client_for_tests,
        create_user_fixture,
        create_rope_product_fixture,
        create_color_fixture,
        create_rope_product_color_fixture,
    ):
        """Создание второй привязки: индекс должен автоматически стать max_index + 1 (2)."""
        admin_user, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        product = await create_rope_product_fixture()
        color_1 = await create_color_fixture()
        color_2 = await create_color_fixture()

        await create_rope_product_color_fixture(
            CreateRopeProductColorFixtureDTO(
                product_id=product.product_id,
                color_id=color_1.id,
                index=1,
            )
        )

        req_data = ProductColorCreate(
            product_id=product.product_id,
            color_id=color_2.id,
        )

        response = await client_for_tests.post(
            "/rope_product_colors",
            headers={"Authorization": f"Bearer {access_token}"},
            json=req_data.model_dump(),
        )
        assert response.status_code == 201

        resp_dto = ProductColorResponseDTO.model_validate(response.json())
        assert resp_dto.product_id == product.product_id
        assert resp_dto.color_id == color_2.id
        assert resp_dto.index == 2

    @pytest.mark.asyncio
    async def test_update_rope_product_color_index_move_up(
        self,
        session_db,
        client_for_tests,
        create_user_fixture,
        create_rope_product_fixture,
        create_color_fixture,
        create_rope_product_color_fixture,
    ):
        """Перемещение индекса вперед/вверх (например, с 4 на 2): соседи 2 и 3 сдвигаются на +1."""
        admin_user, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        product = await create_rope_product_fixture()
        c1 = await create_color_fixture()
        c2 = await create_color_fixture()
        c3 = await create_color_fixture()
        c4 = await create_color_fixture()

        link_1 = await create_rope_product_color_fixture(
            CreateRopeProductColorFixtureDTO(
                product_id=product.product_id, color_id=c1.id, index=1
            )
        )
        link_2 = await create_rope_product_color_fixture(
            CreateRopeProductColorFixtureDTO(
                product_id=product.product_id, color_id=c2.id, index=2
            )
        )
        link_3 = await create_rope_product_color_fixture(
            CreateRopeProductColorFixtureDTO(
                product_id=product.product_id, color_id=c3.id, index=3
            )
        )
        link_4 = await create_rope_product_color_fixture(
            CreateRopeProductColorFixtureDTO(
                product_id=product.product_id, color_id=c4.id, index=4
            )
        )

        # Перемещаем link_4 с индекса 4 на индекс 2
        req_data = ProductColorUpdateIndexDTO(new_index=2)
        response = await client_for_tests.patch(
            f"/rope_product_colors/{link_4.id}/index",
            headers={"Authorization": f"Bearer {access_token}"},
            json=req_data.model_dump(),
        )
        assert response.status_code == 200

        updated_dto = ProductColorResponseDTO.model_validate(response.json())
        assert updated_dto.id == link_4.id
        assert updated_dto.index == 2

        session_db.expire_all()
        db_1 = (await session_db.execute(select(ProductColor).where(ProductColor.id == link_1.id))).scalar_one()
        db_2 = (await session_db.execute(select(ProductColor).where(ProductColor.id == link_2.id))).scalar_one()
        db_3 = (await session_db.execute(select(ProductColor).where(ProductColor.id == link_3.id))).scalar_one()
        db_4 = (await session_db.execute(select(ProductColor).where(ProductColor.id == link_4.id))).scalar_one()

        assert db_1.index == 1
        assert db_4.index == 2
        assert db_2.index == 3
        assert db_3.index == 4

    @pytest.mark.asyncio
    async def test_update_rope_product_color_index_move_down(
        self,
        session_db,
        client_for_tests,
        create_user_fixture,
        create_rope_product_fixture,
        create_color_fixture,
        create_rope_product_color_fixture,
    ):
        """Перемещение индекса назад/вниз (с 1 на 3): соседи 2 и 3 сдвигаются на -1."""
        admin_user, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        product = await create_rope_product_fixture()
        c1 = await create_color_fixture()
        c2 = await create_color_fixture()
        c3 = await create_color_fixture()

        link_1 = await create_rope_product_color_fixture(
            CreateRopeProductColorFixtureDTO(
                product_id=product.product_id, color_id=c1.id, index=1
            )
        )
        link_2 = await create_rope_product_color_fixture(
            CreateRopeProductColorFixtureDTO(
                product_id=product.product_id, color_id=c2.id, index=2
            )
        )
        link_3 = await create_rope_product_color_fixture(
            CreateRopeProductColorFixtureDTO(
                product_id=product.product_id, color_id=c3.id, index=3
            )
        )

        # Перемещаем link_1 с индекса 1 на индекс 3
        response = await client_for_tests.patch(
            f"/rope_product_colors/{link_1.id}/index",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"new_index": 3},
        )
        assert response.status_code == 200

        updated_dto = ProductColorResponseDTO.model_validate(response.json())
        assert updated_dto.id == link_1.id
        assert updated_dto.index == 3

        session_db.expire_all()
        db_1 = (await session_db.execute(select(ProductColor).where(ProductColor.id == link_1.id))).scalar_one()
        db_2 = (await session_db.execute(select(ProductColor).where(ProductColor.id == link_2.id))).scalar_one()
        db_3 = (await session_db.execute(select(ProductColor).where(ProductColor.id == link_3.id))).scalar_one()

        assert db_2.index == 1
        assert db_3.index == 2
        assert db_1.index == 3

    @pytest.mark.asyncio
    async def test_update_rope_product_color_index_same_value(
        self,
        client_for_tests,
        create_user_fixture,
        create_rope_product_color_fixture,
    ):
        """Перемещение индекса на то же самое значение (no-op)."""
        admin_user, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        link = await create_rope_product_color_fixture(
            CreateRopeProductColorFixtureDTO(index=5)
        )

        response = await client_for_tests.patch(
            f"/rope_product_colors/{link.id}/index",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"new_index": 5},
        )
        assert response.status_code == 200

        updated_dto = ProductColorResponseDTO.model_validate(response.json())
        assert updated_dto.index == 5

    @pytest.mark.asyncio
    async def test_delete_rope_product_color_and_shift(
        self,
        session_db,
        client_for_tests,
        create_user_fixture,
        create_rope_product_fixture,
        create_color_fixture,
        create_rope_product_color_fixture,
    ):
        """Удаление привязки и автоматический сдвиг последующих индексов на -1."""
        admin_user, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        product = await create_rope_product_fixture()
        c1 = await create_color_fixture()
        c2 = await create_color_fixture()
        c3 = await create_color_fixture()

        link_1 = await create_rope_product_color_fixture(
            CreateRopeProductColorFixtureDTO(
                product_id=product.product_id, color_id=c1.id, index=1
            )
        )
        link_2 = await create_rope_product_color_fixture(
            CreateRopeProductColorFixtureDTO(
                product_id=product.product_id, color_id=c2.id, index=2
            )
        )
        link_3 = await create_rope_product_color_fixture(
            CreateRopeProductColorFixtureDTO(
                product_id=product.product_id, color_id=c3.id, index=3
            )
        )

        # Удаляем link_2 (index 2)
        response = await client_for_tests.delete(
            f"/rope_product_colors/{link_2.id}",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 204

        session_db.expire_all()
        # Проверяем, что link_2 удален
        res_del = await session_db.execute(
            select(ProductColor).where(ProductColor.id == link_2.id)
        )
        assert res_del.scalar_one_or_none() is None

        # Проверяем оставшиеся индексы
        db_1 = (await session_db.execute(select(ProductColor).where(ProductColor.id == link_1.id))).scalar_one()
        db_3 = (await session_db.execute(select(ProductColor).where(ProductColor.id == link_3.id))).scalar_one()

        assert db_1.index == 1
        assert db_3.index == 2


class TestsForErrors:

    @pytest.mark.asyncio
    async def test_get_colors_by_product_not_found(
        self,
        client_for_tests,
    ):
        """Запрос цветов для несуществующего товара."""
        response = await client_for_tests.get("/rope_product_colors/by-product/99999")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(
        self,
        client_for_tests,
    ):
        """Запрос несуществующей привязки по ID."""
        response = await client_for_tests.get("/rope_product_colors/99999")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_create_forbidden(
        self,
        client_for_tests,
        create_user_fixture,
        create_rope_product_fixture,
        create_color_fixture,
    ):
        """Попытка создания привязки обычным пользователем (роль USER)."""
        regular_user, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.USER)
        )
        product = await create_rope_product_fixture()
        color = await create_color_fixture()

        response = await client_for_tests.post(
            "/rope_product_colors",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"product_id": product.product_id, "color_id": color.id},
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_create_unauthorized(
        self,
        client_for_tests,
        create_rope_product_fixture,
        create_color_fixture,
    ):
        """Попытка создания без авторизации."""
        product = await create_rope_product_fixture()
        color = await create_color_fixture()

        response = await client_for_tests.post(
            "/rope_product_colors",
            json={"product_id": product.product_id, "color_id": color.id},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_create_product_not_found(
        self,
        client_for_tests,
        create_user_fixture,
        create_color_fixture,
    ):
        """Создание привязки с несуществующим product_id."""
        admin_user, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        color = await create_color_fixture()

        response = await client_for_tests.post(
            "/rope_product_colors",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"product_id": 99999, "color_id": color.id},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_create_color_not_found(
        self,
        client_for_tests,
        create_user_fixture,
        create_rope_product_fixture,
    ):
        """Создание привязки с несуществующим color_id."""
        admin_user, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        product = await create_rope_product_fixture()

        response = await client_for_tests.post(
            "/rope_product_colors",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"product_id": product.product_id, "color_id": 99999},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_create_already_exists(
        self,
        client_for_tests,
        create_user_fixture,
        create_rope_product_fixture,
        create_color_fixture,
        create_rope_product_color_fixture,
    ):
        """Повторная привязка того же цвета к товару."""
        admin_user, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        product = await create_rope_product_fixture()
        color = await create_color_fixture()

        await create_rope_product_color_fixture(
            CreateRopeProductColorFixtureDTO(
                product_id=product.product_id,
                color_id=color.id,
            )
        )

        response = await client_for_tests.post(
            "/rope_product_colors",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"product_id": product.product_id, "color_id": color.id},
        )
        assert response.status_code == 409

    @pytest.mark.asyncio
    async def test_update_index_forbidden(
        self,
        client_for_tests,
        create_user_fixture,
        create_rope_product_color_fixture,
    ):
        """Обновление индекса обычным пользователем (роль USER)."""
        regular_user, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.USER)
        )
        link = await create_rope_product_color_fixture()

        response = await client_for_tests.patch(
            f"/rope_product_colors/{link.id}/index",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"new_index": 2},
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_update_index_unauthorized(
        self,
        client_for_tests,
        create_rope_product_color_fixture,
    ):
        """Обновление индекса без авторизации."""
        link = await create_rope_product_color_fixture()

        response = await client_for_tests.patch(
            f"/rope_product_colors/{link.id}/index",
            json={"new_index": 2},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_update_index_not_found(
        self,
        client_for_tests,
        create_user_fixture,
    ):
        """Обновление индекса несуществующей привязки."""
        admin_user, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )

        response = await client_for_tests.patch(
            "/rope_product_colors/99999/index",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"new_index": 2},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_index_validation_error(
        self,
        client_for_tests,
        create_user_fixture,
        create_rope_product_color_fixture,
    ):
        """Валидация отрицательного индекса (new_index: -1)."""
        admin_user, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        link = await create_rope_product_color_fixture()

        response = await client_for_tests.patch(
            f"/rope_product_colors/{link.id}/index",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"new_index": -1},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_delete_forbidden(
        self,
        client_for_tests,
        create_user_fixture,
        create_rope_product_color_fixture,
    ):
        """Удаление обычным пользователем (роль USER)."""
        regular_user, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.USER)
        )
        link = await create_rope_product_color_fixture()

        response = await client_for_tests.delete(
            f"/rope_product_colors/{link.id}",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_delete_unauthorized(
        self,
        client_for_tests,
        create_rope_product_color_fixture,
    ):
        """Удаление без авторизации."""
        link = await create_rope_product_color_fixture()

        response = await client_for_tests.delete(
            f"/rope_product_colors/{link.id}",
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_delete_not_found(
        self,
        client_for_tests,
        create_user_fixture,
    ):
        """Удаление несуществующей привязки."""
        admin_user, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )

        response = await client_for_tests.delete(
            "/rope_product_colors/99999",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 404

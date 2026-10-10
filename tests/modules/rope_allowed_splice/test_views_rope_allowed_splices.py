import pytest
from sqlalchemy import select

from src.modules.base.database_model import Language
from src.modules.users.models import UserRole
from tests.modules.users.fixtures.models_dto import CreateUserFixtureDTO
from tests.modules.splice_types.fixtures.models_dto import (
    CreateSpliceTypeFixtureDTO,
    CreateSpliceTypeTranslationFixtureDTO,
)
from tests.modules.rope_products.fixtures.models_dto import CreateRopeProductFixtureDTO
from tests.modules.rope_allowed_splice.fixtures.models_dto import CreateRopeAllowedSpliceFixtureDTO
from src.modules.rope_allowed_splice.models import RopeAllowedSplice
from src.modules.rope_allowed_splice.models_dto import (
    RopeAllowedSpliceCreate,
    RopeAllowedSpliceBulkSetDTO,
    RopeAllowedSpliceResponseDTO,
    RopeAllowedSpliceLocalizedResponseDTO,
)
from tests.helpers.functions import comparison_models


class TestsForSuccess:

    @pytest.mark.asyncio
    async def test_get_allowed_splices_by_product_id(
        self,
        client_for_tests,
        create_rope_product_fixture,
        create_splice_type_fixture,
        create_rope_allowed_splice_fixture,
    ):
        """Получение списка разрешенных сращиваний товара с локализацией по умолчанию (ENG)."""
        product = await create_rope_product_fixture()
        splice_1 = await create_splice_type_fixture(
            CreateSpliceTypeFixtureDTO(code="loop_01", name="Loop Splice", index=1)
        )
        splice_2 = await create_splice_type_fixture(
            CreateSpliceTypeFixtureDTO(code="endless_01", name="Endless Splice", index=2)
        )

        await create_rope_allowed_splice_fixture(
            CreateRopeAllowedSpliceFixtureDTO(
                rope_product_id=product.product_id,
                splice_type_id=splice_1.id,
            )
        )
        await create_rope_allowed_splice_fixture(
            CreateRopeAllowedSpliceFixtureDTO(
                rope_product_id=product.product_id,
                splice_type_id=splice_2.id,
            )
        )

        response = await client_for_tests.get(
            f"/rope_allowed_splices/by-product/{product.product_id}"
        )
        assert response.status_code == 200

        data = [
            RopeAllowedSpliceLocalizedResponseDTO.model_validate(item)
            for item in response.json()
        ]
        assert len(data) == 2
        assert data[0].rope_product_id == product.product_id
        assert data[0].splice_type_id == splice_1.id
        assert data[0].splice_type is not None
        assert data[0].splice_type.code == "loop_01"
        assert data[0].splice_type.name == "Loop Splice"

        assert data[1].rope_product_id == product.product_id
        assert data[1].splice_type_id == splice_2.id
        assert data[1].splice_type is not None
        assert data[1].splice_type.code == "endless_01"
        assert data[1].splice_type.name == "Endless Splice"

    @pytest.mark.asyncio
    async def test_get_allowed_splices_by_product_id_locale(
        self,
        client_for_tests,
        create_rope_product_fixture,
        create_splice_type_fixture,
        create_splice_type_translation_fixture,
        create_rope_allowed_splice_fixture,
    ):
        """Получение списка разрешенных сращиваний товара с немецкой локализацией (GER)."""
        product = await create_rope_product_fixture()
        splice = await create_splice_type_fixture(
            CreateSpliceTypeFixtureDTO(locale=Language.ENG, name="Eye Splice")
        )
        await create_splice_type_translation_fixture(
            CreateSpliceTypeTranslationFixtureDTO(
                splice_type_id=splice.id,
                locale=Language.GER,
                name="Augspleiß",
                description="Beschreibung",
            )
        )

        await create_rope_allowed_splice_fixture(
            CreateRopeAllowedSpliceFixtureDTO(
                rope_product_id=product.product_id,
                splice_type_id=splice.id,
            )
        )

        response = await client_for_tests.get(
            f"/rope_allowed_splices/by-product/{product.product_id}",
            params={"locale": "ger"},
        )
        assert response.status_code == 200

        data = [
            RopeAllowedSpliceLocalizedResponseDTO.model_validate(item)
            for item in response.json()
        ]
        assert len(data) == 1
        assert data[0].splice_type is not None
        assert data[0].splice_type.name == "Augspleiß"
        assert data[0].splice_type.description == "Beschreibung"

    @pytest.mark.asyncio
    async def test_get_allowed_splices_by_product_id_empty(
        self,
        client_for_tests,
        create_rope_product_fixture,
    ):
        """Получение пустого списка разрешенных сращиваний для товара без привязок."""
        product = await create_rope_product_fixture()

        response = await client_for_tests.get(
            f"/rope_allowed_splices/by-product/{product.product_id}"
        )
        assert response.status_code == 200

        data = [
            RopeAllowedSpliceLocalizedResponseDTO.model_validate(item)
            for item in response.json()
        ]
        assert data == []

    @pytest.mark.asyncio
    async def test_get_rope_allowed_splice_by_composite_key(
        self,
        client_for_tests,
        create_rope_allowed_splice_fixture,
    ):
        """Получение привязки сращивания по составному ключу."""
        link = await create_rope_allowed_splice_fixture()

        response = await client_for_tests.get(
            f"/rope_allowed_splices/{link.rope_product_id}/{link.splice_type_id}"
        )
        assert response.status_code == 200

        resp_dto = RopeAllowedSpliceResponseDTO.model_validate(response.json())
        assert resp_dto.rope_product_id == link.rope_product_id
        assert resp_dto.splice_type_id == link.splice_type_id
        assert resp_dto.splice_type is not None
        assert comparison_models(link, resp_dto, keys_not_checked=["splice_type"])

    @pytest.mark.asyncio
    async def test_create_rope_allowed_splice(
        self,
        session_db,
        client_for_tests,
        create_user_fixture,
        create_rope_product_fixture,
        create_splice_type_fixture,
    ):
        """Создание привязки разрешенного типа сращивания к товару администратором."""
        admin_user, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        product = await create_rope_product_fixture()
        splice = await create_splice_type_fixture()

        req_data = RopeAllowedSpliceCreate(
            rope_product_id=product.product_id,
            splice_type_id=splice.id,
        )

        response = await client_for_tests.post(
            "/rope_allowed_splices",
            headers={"Authorization": f"Bearer {access_token}"},
            json=req_data.model_dump(),
        )
        assert response.status_code == 201

        resp_dto = RopeAllowedSpliceResponseDTO.model_validate(response.json())
        assert resp_dto.rope_product_id == product.product_id
        assert resp_dto.splice_type_id == splice.id
        assert resp_dto.splice_type is not None
        assert resp_dto.splice_type.id == splice.id

        # Проверка в БД
        res = await session_db.execute(
            select(RopeAllowedSplice).where(
                RopeAllowedSplice.rope_product_id == product.product_id,
                RopeAllowedSplice.splice_type_id == splice.id,
            )
        )
        db_item = res.scalar_one_or_none()
        assert db_item is not None
        assert db_item.rope_product_id == product.product_id
        assert db_item.splice_type_id == splice.id

    @pytest.mark.asyncio
    async def test_set_allowed_splices_for_product(
        self,
        session_db,
        client_for_tests,
        create_user_fixture,
        create_rope_product_fixture,
        create_splice_type_fixture,
        create_rope_allowed_splice_fixture,
    ):
        """Пакетная установка (перезапись) разрешенных сращиваний для товара."""
        admin_user, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        product = await create_rope_product_fixture()
        old_splice = await create_splice_type_fixture()
        new_splice_1 = await create_splice_type_fixture()
        new_splice_2 = await create_splice_type_fixture()

        # Старая привязка, которая должна быть удалена
        await create_rope_allowed_splice_fixture(
            CreateRopeAllowedSpliceFixtureDTO(
                rope_product_id=product.product_id,
                splice_type_id=old_splice.id,
            )
        )

        bulk_data = RopeAllowedSpliceBulkSetDTO(
            splice_type_ids=[new_splice_1.id, new_splice_2.id]
        )

        response = await client_for_tests.put(
            f"/rope_allowed_splices/by-product/{product.product_id}",
            headers={"Authorization": f"Bearer {access_token}"},
            json=bulk_data.model_dump(),
        )
        assert response.status_code == 200

        resp_list = [
            RopeAllowedSpliceResponseDTO.model_validate(item)
            for item in response.json()
        ]
        assert len(resp_list) == 2
        assigned_ids = {item.splice_type_id for item in resp_list}
        assert assigned_ids == {new_splice_1.id, new_splice_2.id}

        # Проверка в БД: старого нет, новые есть
        res = await session_db.execute(
            select(RopeAllowedSplice).where(
                RopeAllowedSplice.rope_product_id == product.product_id
            )
        )
        db_items = res.scalars().all()
        assert len(db_items) == 2
        assert {item.splice_type_id for item in db_items} == {new_splice_1.id, new_splice_2.id}

    @pytest.mark.asyncio
    async def test_delete_rope_allowed_splice(
        self,
        session_db,
        client_for_tests,
        create_user_fixture,
        create_rope_allowed_splice_fixture,
    ):
        """Удаление привязки сращивания администратором."""
        admin_user, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        link = await create_rope_allowed_splice_fixture()

        response = await client_for_tests.delete(
            f"/rope_allowed_splices/{link.rope_product_id}/{link.splice_type_id}",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 204

        # Проверка в БД
        res = await session_db.execute(
            select(RopeAllowedSplice).where(
                RopeAllowedSplice.rope_product_id == link.rope_product_id,
                RopeAllowedSplice.splice_type_id == link.splice_type_id,
            )
        )
        assert res.scalar_one_or_none() is None


class TestsForFailures:

    @pytest.mark.asyncio
    async def test_create_rope_allowed_splice_unauthorized(
        self,
        client_for_tests,
        create_rope_product_fixture,
        create_splice_type_fixture,
    ):
        """Попытка создания привязки без токена -> 401."""
        product = await create_rope_product_fixture()
        splice = await create_splice_type_fixture()

        req_data = RopeAllowedSpliceCreate(
            rope_product_id=product.product_id,
            splice_type_id=splice.id,
        )

        response = await client_for_tests.post(
            "/rope_allowed_splices",
            json=req_data.model_dump(),
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_create_rope_allowed_splice_forbidden(
        self,
        client_for_tests,
        create_user_fixture,
        create_rope_product_fixture,
        create_splice_type_fixture,
    ):
        """Попытка создания привязки обычным пользователем -> 403."""
        user, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.USER)
        )
        product = await create_rope_product_fixture()
        splice = await create_splice_type_fixture()

        req_data = RopeAllowedSpliceCreate(
            rope_product_id=product.product_id,
            splice_type_id=splice.id,
        )

        response = await client_for_tests.post(
            "/rope_allowed_splices",
            headers={"Authorization": f"Bearer {access_token}"},
            json=req_data.model_dump(),
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_create_rope_allowed_splice_product_not_found(
        self,
        client_for_tests,
        create_user_fixture,
        create_splice_type_fixture,
    ):
        """Попытка привязки к несуществующему товару -> 404."""
        admin_user, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        splice = await create_splice_type_fixture()

        req_data = RopeAllowedSpliceCreate(
            rope_product_id=999999,
            splice_type_id=splice.id,
        )

        response = await client_for_tests.post(
            "/rope_allowed_splices",
            headers={"Authorization": f"Bearer {access_token}"},
            json=req_data.model_dump(),
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_create_rope_allowed_splice_splice_type_not_found(
        self,
        client_for_tests,
        create_user_fixture,
        create_rope_product_fixture,
    ):
        """Попытка привязки несуществующего типа сращивания -> 404."""
        admin_user, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        product = await create_rope_product_fixture()

        req_data = RopeAllowedSpliceCreate(
            rope_product_id=product.product_id,
            splice_type_id=999999,
        )

        response = await client_for_tests.post(
            "/rope_allowed_splices",
            headers={"Authorization": f"Bearer {access_token}"},
            json=req_data.model_dump(),
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_create_rope_allowed_splice_already_exists(
        self,
        client_for_tests,
        create_user_fixture,
        create_rope_allowed_splice_fixture,
    ):
        """Попытка повторного связывания той же пары -> 409."""
        admin_user, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        link = await create_rope_allowed_splice_fixture()

        req_data = RopeAllowedSpliceCreate(
            rope_product_id=link.rope_product_id,
            splice_type_id=link.splice_type_id,
        )

        response = await client_for_tests.post(
            "/rope_allowed_splices",
            headers={"Authorization": f"Bearer {access_token}"},
            json=req_data.model_dump(),
        )
        assert response.status_code == 409

    @pytest.mark.asyncio
    async def test_get_allowed_splices_product_not_found(
        self,
        client_for_tests,
    ):
        """Запрос разрешенных сращиваний для несуществующего товара -> 404."""
        response = await client_for_tests.get("/rope_allowed_splices/by-product/999999")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_rope_allowed_splice_not_found(
        self,
        client_for_tests,
    ):
        """Запрос несуществующей пары привязки -> 404."""
        response = await client_for_tests.get("/rope_allowed_splices/999999/999999")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_rope_allowed_splice_unauthorized(
        self,
        client_for_tests,
        create_rope_allowed_splice_fixture,
    ):
        """Попытка удаления без авторизации -> 401."""
        link = await create_rope_allowed_splice_fixture()

        response = await client_for_tests.delete(
            f"/rope_allowed_splices/{link.rope_product_id}/{link.splice_type_id}"
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_delete_rope_allowed_splice_forbidden(
        self,
        client_for_tests,
        create_user_fixture,
        create_rope_allowed_splice_fixture,
    ):
        """Попытка удаления обычным пользователем -> 403."""
        user, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.USER)
        )
        link = await create_rope_allowed_splice_fixture()

        response = await client_for_tests.delete(
            f"/rope_allowed_splices/{link.rope_product_id}/{link.splice_type_id}",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_delete_rope_allowed_splice_not_found(
        self,
        client_for_tests,
        create_user_fixture,
    ):
        """Попытка удаления несуществующей привязки -> 404."""
        admin_user, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )

        response = await client_for_tests.delete(
            "/rope_allowed_splices/999999/999999",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_set_allowed_splices_product_not_found(
        self,
        client_for_tests,
        create_user_fixture,
        create_splice_type_fixture,
    ):
        """Пакетная установка для несуществующего товара -> 404."""
        admin_user, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        splice = await create_splice_type_fixture()

        bulk_data = RopeAllowedSpliceBulkSetDTO(splice_type_ids=[splice.id])

        response = await client_for_tests.put(
            "/rope_allowed_splices/by-product/999999",
            headers={"Authorization": f"Bearer {access_token}"},
            json=bulk_data.model_dump(),
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_set_allowed_splices_splice_type_not_found(
        self,
        client_for_tests,
        create_user_fixture,
        create_rope_product_fixture,
    ):
        """Пакетная установка с несуществующим типом сращивания -> 404."""
        admin_user, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        product = await create_rope_product_fixture()

        bulk_data = RopeAllowedSpliceBulkSetDTO(splice_type_ids=[999999])

        response = await client_for_tests.put(
            f"/rope_allowed_splices/by-product/{product.product_id}",
            headers={"Authorization": f"Bearer {access_token}"},
            json=bulk_data.model_dump(),
        )
        assert response.status_code == 404

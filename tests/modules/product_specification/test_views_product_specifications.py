import pytest
from sqlalchemy import select

from src.modules.base.database_model import Language
from src.modules.product_specification.models import (
    ProductSpecification,
    ProductSpecificationTranslation,
)
from src.modules.product_specification.models_dto import (
    ProductSpecificationBatchCreate,
    ProductSpecificationBatchDelete,
    ProductSpecificationBatchDeleteResponseDTO,
    ProductSpecificationBatchSync,
    ProductSpecificationBatchUpdate,
    ProductSpecificationCreate,
    ProductSpecificationItemCreate,
    ProductSpecificationLocalizedResponseDTO,
    ProductSpecificationResponseDTO,
    ProductSpecificationTranslationCreate,
    ProductSpecificationTranslationResponseDTO,
    ProductSpecificationTranslationUpdate,
    ProductSpecificationUpdate,
    ProductSpecificationUpdateIndexDTO,
)
from src.modules.users.models import UserRole
from tests.helpers.functions import comparison_models
from tests.modules.product_specification.fixtures.models_dto import (
    CreateProductSpecificationFixtureDTO,
    CreateProductSpecificationTranslationFixtureDTO,
)
from tests.modules.products.fixtures.models_dto import CreateProductFixtureDTO
from tests.modules.users.fixtures.models_dto import CreateUserFixtureDTO


class TestsForSuccess:

    @pytest.mark.asyncio
    async def test_get_specifications_by_product_id(
        self,
        client_for_tests,
        create_product_fixture,
        create_product_specification_fixture,
    ):
        """Получение характеристик товара с локализацией по умолчанию (ENG)."""
        product = await create_product_fixture()
        spec_1 = await create_product_specification_fixture(
            CreateProductSpecificationFixtureDTO(
                product_id=product.id,
                index=0,
                name="Manufacturer",
                value="LIROS",
                locale=Language.ENG,
            )
        )
        spec_2 = await create_product_specification_fixture(
            CreateProductSpecificationFixtureDTO(
                product_id=product.id,
                index=1,
                name="Core",
                value="Dyneema SK78",
                locale=Language.ENG,
            )
        )

        response = await client_for_tests.get(
            f"/product_specifications/by-product/{product.id}?locale=eng"
        )
        assert response.status_code == 200

        data = [
            ProductSpecificationLocalizedResponseDTO.model_validate(item)
            for item in response.json()
        ]
        assert len(data) == 2
        assert data[0].id == spec_1.id
        assert data[0].name == "Manufacturer"
        assert data[0].value == "LIROS"

        assert data[1].id == spec_2.id
        assert data[1].name == "Core"
        assert data[1].value == "Dyneema SK78"

    @pytest.mark.asyncio
    async def test_get_specifications_without_locale_returns_full(
        self,
        client_for_tests,
        create_product_fixture,
        create_product_specification_fixture,
    ):
        """Без передачи locale возвращается полный список с объектами переводов."""
        product = await create_product_fixture()
        spec = await create_product_specification_fixture(
            CreateProductSpecificationFixtureDTO(
                product_id=product.id,
                name="Material",
                value="Polyester",
            )
        )

        response = await client_for_tests.get(
            f"/product_specifications/by-product/{product.id}"
        )
        assert response.status_code == 200

        data = [
            ProductSpecificationResponseDTO.model_validate(item)
            for item in response.json()
        ]
        assert len(data) == 1
        assert data[0].id == spec.id
        assert len(data[0].translations) >= 1

    @pytest.mark.asyncio
    async def test_batch_create_specifications(
        self,
        client_for_tests,
        create_user_fixture,
        create_product_fixture,
        session_db,
    ):
        """Пакетное создание характеристик для товара."""
        _, admin_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        product = await create_product_fixture()

        payload = {
            "items": [
                {
                    "translations": [
                        {"locale": "eng", "name": "Diameter", "value": "10 mm"},
                        {"locale": "rus", "name": "Диаметр", "value": "10 мм"},
                    ]
                },
                {
                    "translations": [
                        {"locale": "eng", "name": "Strength", "value": "2500 daN"},
                        {"locale": "rus", "name": "Прочность", "value": "2500 даН"},
                    ]
                },
            ]
        }

        response = await client_for_tests.post(
            f"/product_specifications/by-product/{product.id}/batch",
            json=payload,
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 201

        data = [
            ProductSpecificationResponseDTO.model_validate(item)
            for item in response.json()
        ]
        assert len(data) == 2
        assert data[0].index == 0
        assert data[1].index == 1
        assert len(data[0].translations) == 2
        assert len(data[1].translations) == 2

        # Проверяем в БД
        specs = (
            await session_db.execute(
                select(ProductSpecification).where(
                    ProductSpecification.product_id == product.id
                )
            )
        ).scalars().all()
        assert len(specs) == 2

    @pytest.mark.asyncio
    async def test_batch_update_specifications(
        self,
        client_for_tests,
        create_user_fixture,
        create_product_fixture,
        create_product_specification_fixture,
    ):
        """Пакетное обновление характеристик товара."""
        _, admin_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        product = await create_product_fixture()
        spec_1 = await create_product_specification_fixture(
            CreateProductSpecificationFixtureDTO(
                product_id=product.id,
                name="Old Name 1",
                value="Old Val 1",
            )
        )
        spec_2 = await create_product_specification_fixture(
            CreateProductSpecificationFixtureDTO(
                product_id=product.id,
                name="Old Name 2",
                value="Old Val 2",
            )
        )

        payload = {
            "items": [
                {
                    "id": spec_1.id,
                    "index": 10,
                    "translations": [
                        {"locale": "eng", "name": "Updated Name 1", "value": "Updated Val 1"},
                    ],
                },
                {
                    "id": spec_2.id,
                    "index": 11,
                    "translations": [
                        {"locale": "eng", "name": "Updated Name 2", "value": "Updated Val 2"},
                    ],
                },
            ]
        }

        response = await client_for_tests.put(
            f"/product_specifications/by-product/{product.id}/batch",
            json=payload,
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200

        data = [
            ProductSpecificationResponseDTO.model_validate(item)
            for item in response.json()
        ]
        assert len(data) == 2
        assert data[0].id == spec_1.id
        assert data[0].index == 10
        assert data[0].translations[0].name == "Updated Name 1"

        assert data[1].id == spec_2.id
        assert data[1].index == 11
        assert data[1].translations[0].name == "Updated Name 2"

    @pytest.mark.asyncio
    async def test_batch_delete_specifications(
        self,
        client_for_tests,
        create_user_fixture,
        create_product_fixture,
        create_product_specification_fixture,
        session_db,
    ):
        """Пакетное удаление характеристик товара."""
        _, admin_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        product = await create_product_fixture()
        spec_1 = await create_product_specification_fixture(
            CreateProductSpecificationFixtureDTO(product_id=product.id, index=0)
        )
        spec_2 = await create_product_specification_fixture(
            CreateProductSpecificationFixtureDTO(product_id=product.id, index=1)
        )
        spec_3 = await create_product_specification_fixture(
            CreateProductSpecificationFixtureDTO(product_id=product.id, index=2)
        )

        payload = {"specification_ids": [spec_1.id, spec_2.id]}

        response = await client_for_tests.request(
            method="DELETE",
            url=f"/product_specifications/by-product/{product.id}/batch",
            json=payload,
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200

        res_dto = ProductSpecificationBatchDeleteResponseDTO.model_validate(
            response.json()
        )
        assert res_dto.deleted_count == 2
        assert spec_1.id in res_dto.deleted_ids
        assert spec_2.id in res_dto.deleted_ids

        # Оставшаяся характеристика должна быть переиндексирована в 0
        rem_specs = (
            await session_db.execute(
                select(ProductSpecification).where(
                    ProductSpecification.product_id == product.id
                )
            )
        ).scalars().all()
        assert len(rem_specs) == 1
        assert rem_specs[0].id == spec_3.id
        assert rem_specs[0].index == 0

    @pytest.mark.asyncio
    async def test_sync_batch_specifications(
        self,
        client_for_tests,
        create_user_fixture,
        create_product_fixture,
        create_product_specification_fixture,
        session_db,
    ):
        """Полная синхронизация списка характеристик (create, update, delete)."""
        _, admin_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        product = await create_product_fixture()
        spec_keep = await create_product_specification_fixture(
            CreateProductSpecificationFixtureDTO(
                product_id=product.id,
                name="Keep Spec",
                value="Keep Val",
            )
        )
        spec_delete = await create_product_specification_fixture(
            CreateProductSpecificationFixtureDTO(
                product_id=product.id,
                name="Delete Spec",
                value="Delete Val",
            )
        )

        payload = {
            "items": [
                {
                    "id": spec_keep.id,
                    "translations": [
                        {"locale": "eng", "name": "Keep Spec Updated", "value": "Updated Val"},
                    ],
                },
                {
                    # New specification
                    "translations": [
                        {"locale": "eng", "name": "Brand New", "value": "Brand New Val"},
                    ],
                },
            ]
        }

        response = await client_for_tests.put(
            f"/product_specifications/by-product/{product.id}/sync",
            json=payload,
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200

        data = [
            ProductSpecificationResponseDTO.model_validate(item)
            for item in response.json()
        ]
        assert len(data) == 2
        # spec_delete должен быть удален
        found_ids = [d.id for d in data]
        assert spec_keep.id in found_ids
        assert spec_delete.id not in found_ids

        # Проверяем в БД
        deleted_check = await session_db.get(ProductSpecification, spec_delete.id)
        assert deleted_check is None

    @pytest.mark.asyncio
    async def test_single_crud_specification(
        self,
        client_for_tests,
        create_user_fixture,
        create_product_fixture,
        session_db,
    ):
        """Тестирование одиночных операций CRUD для спецификации."""
        _, admin_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        product = await create_product_fixture()

        # 1. Create
        create_payload = {
            "product_id": product.id,
            "index": 0,
            "translations": [
                {"locale": "eng", "name": "Color", "value": "White"},
            ],
        }
        res_create = await client_for_tests.post(
            "/product_specifications",
            json=create_payload,
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert res_create.status_code == 201
        created_dto = ProductSpecificationResponseDTO.model_validate(res_create.json())
        spec_id = created_dto.id

        # 2. Get by ID
        res_get = await client_for_tests.get(f"/product_specifications/{spec_id}")
        assert res_get.status_code == 200
        get_dto = ProductSpecificationResponseDTO.model_validate(res_get.json())
        assert get_dto.id == spec_id

        # 3. Patch translations
        patch_payload = {
            "translations": [
                {"locale": "eng", "name": "Color", "value": "Black"},
                {"locale": "rus", "name": "Цвет", "value": "Черный"},
            ]
        }
        res_patch = await client_for_tests.patch(
            f"/product_specifications/{spec_id}",
            json=patch_payload,
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert res_patch.status_code == 200
        patched_dto = ProductSpecificationResponseDTO.model_validate(res_patch.json())
        assert len(patched_dto.translations) == 2

        # 4. Reorder
        res_reorder = await client_for_tests.patch(
            f"/product_specifications/{spec_id}/index",
            json={"new_index": 5},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert res_reorder.status_code == 200
        reorder_dto = ProductSpecificationResponseDTO.model_validate(res_reorder.json())
        assert reorder_dto.index == 5

        # 5. Delete
        res_del = await client_for_tests.delete(
            f"/product_specifications/{spec_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert res_del.status_code == 204

        res_check = await client_for_tests.get(f"/product_specifications/{spec_id}")
        assert res_check.status_code == 404

    @pytest.mark.asyncio
    async def test_translations_crud(
        self,
        client_for_tests,
        create_user_fixture,
        create_product_specification_fixture,
    ):
        """Тестирование CRUD для переводов спецификации."""
        _, admin_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        spec = await create_product_specification_fixture(
            CreateProductSpecificationFixtureDTO(
                locale=Language.ENG,
                name="Weight",
                value="50 g/m",
            )
        )

        # 1. Add translation
        add_payload = {
            "locale": "ger",
            "name": "Gewicht",
            "value": "50 g/m",
        }
        res_add = await client_for_tests.post(
            f"/product_specifications/{spec.id}/translations",
            json=add_payload,
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert res_add.status_code == 201
        added_dto = ProductSpecificationTranslationResponseDTO.model_validate(res_add.json())
        assert added_dto.locale == Language.GER
        assert added_dto.name == "Gewicht"

        # 2. Update translation
        update_payload = {"name": "Gewicht pro Meter"}
        res_upd = await client_for_tests.patch(
            f"/product_specifications/{spec.id}/translations/ger",
            json=update_payload,
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert res_upd.status_code == 200
        upd_dto = ProductSpecificationTranslationResponseDTO.model_validate(res_upd.json())
        assert upd_dto.name == "Gewicht pro Meter"

        # 3. Delete translation
        res_del = await client_for_tests.delete(
            f"/product_specifications/{spec.id}/translations/ger",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert res_del.status_code == 204

        # 4. Delete last translation should fail with 400
        res_del_last = await client_for_tests.delete(
            f"/product_specifications/{spec.id}/translations/eng",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert res_del_last.status_code == 400


class TestsForErrors:

    @pytest.mark.asyncio
    async def test_forbidden_for_non_admin(
        self,
        client_for_tests,
        create_user_fixture,
        create_product_fixture,
    ):
        """Обычный пользователь не имеет права управлять спецификациями."""
        _, user_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.USER)
        )
        product = await create_product_fixture()

        payload = {
            "items": [
                {
                    "translations": [
                        {"locale": "eng", "name": "Name", "value": "Val"},
                    ]
                }
            ]
        }
        response = await client_for_tests.post(
            f"/product_specifications/by-product/{product.id}/batch",
            json=payload,
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_product_not_found(
        self,
        client_for_tests,
        create_user_fixture,
    ):
        """Ошибка 404 если товар не существует при батч-операции."""
        _, admin_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        non_existent_id = 999999

        response = await client_for_tests.post(
            f"/product_specifications/by-product/{non_existent_id}/batch",
            json={"items": [{"translations": [{"locale": "eng", "name": "N", "value": "V"}]}]},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_batch_update_foreign_specification(
        self,
        client_for_tests,
        create_user_fixture,
        create_product_fixture,
        create_product_specification_fixture,
    ):
        """Ошибка 404 при попытке обновить спецификацию, принадлежащую другому товару."""
        _, admin_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        product_1 = await create_product_fixture()
        product_2 = await create_product_fixture()
        spec_for_prod2 = await create_product_specification_fixture(
            CreateProductSpecificationFixtureDTO(product_id=product_2.id)
        )

        payload = {
            "items": [
                {
                    "id": spec_for_prod2.id,
                    "translations": [{"locale": "eng", "name": "Hacked", "value": "Val"}],
                }
            ]
        }
        # Пытаемся обновить её под product_1
        response = await client_for_tests.put(
            f"/product_specifications/by-product/{product_1.id}/batch",
            json=payload,
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 404

from pathlib import Path
from typing import Callable
import pytest
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.core.config.config import Config
from src.modules.base.database_model import Language
from src.modules.users.models import UserRole
from tests.modules.users.fixtures.models_dto import CreateUserFixtureDTO
from tests.modules.splice_types.fixtures.models_dto import (
    CreateSpliceTypeFixtureDTO,
    CreateSpliceTypeTranslationFixtureDTO,
)
from tests.modules.splice_materials.fixtures.models_dto import CreateSpliceMaterialFixtureDTO
from tests.modules.splice_prices.fixtures.models_dto import CreateSplicePriceRuleFixtureDTO
from src.modules.splice_types.models import (
    SpliceType,
    SpliceTypeTranslation,
    SpliceCategory,
    SpliceVisualType,
)
from src.modules.splice_types.models_dto import (
    SpliceTypeResponseDTO,
    SpliceTypeLocalizedResponseDTO,
    SpliceTypeCreate,
    SpliceTypeUpdate,
    SpliceTypeTranslationCreate,
    SpliceTypeTranslationUpdate,
    SpliceTypeTranslationResponseDTO,
)
from tests.helpers.functions import comparison_models


class TestsForSuccess:

    @pytest.mark.asyncio
    async def test_get_all_splice_types(
        self,
        client_for_tests,
        create_splice_type_fixture,
    ):
        type_1 = await create_splice_type_fixture(
            CreateSpliceTypeFixtureDTO(code="type_1", name="Type One")
        )
        type_2 = await create_splice_type_fixture(
            CreateSpliceTypeFixtureDTO(code="type_2", name="Type Two")
        )

        response = await client_for_tests.get("/splice_types")
        assert response.status_code == 200

        data = [
            SpliceTypeLocalizedResponseDTO.model_validate(item)
            for item in response.json()
        ]
        assert len(data) >= 2

        ids = [item.id for item in data]
        assert type_1.id in ids
        assert type_2.id in ids

        found = next(item for item in data if item.id == type_1.id)
        assert found.code == "type_1"
        assert found.name == "Type One"

    @pytest.mark.asyncio
    async def test_get_splice_types_filter_category(
        self,
        client_for_tests,
        create_splice_type_fixture,
    ):
        loop_type = await create_splice_type_fixture(
            CreateSpliceTypeFixtureDTO(category=SpliceCategory.LOOP)
        )
        splice_type = await create_splice_type_fixture(
            CreateSpliceTypeFixtureDTO(category=SpliceCategory.SPLICE)
        )

        response = await client_for_tests.get("/splice_types", params={"category": "loop"})
        assert response.status_code == 200

        data = [
            SpliceTypeLocalizedResponseDTO.model_validate(item)
            for item in response.json()
        ]
        ids = [item.id for item in data]
        assert loop_type.id in ids
        assert splice_type.id not in ids

    @pytest.mark.asyncio
    async def test_get_splice_types_filter_is_active(
        self,
        client_for_tests,
        create_splice_type_fixture,
    ):
        active_type = await create_splice_type_fixture(
            CreateSpliceTypeFixtureDTO(is_active=True)
        )
        inactive_type = await create_splice_type_fixture(
            CreateSpliceTypeFixtureDTO(is_active=False)
        )

        resp_active = await client_for_tests.get("/splice_types", params={"is_active": "true"})
        assert resp_active.status_code == 200
        active_items = [
            SpliceTypeLocalizedResponseDTO.model_validate(item)
            for item in resp_active.json()
        ]
        active_ids = [item.id for item in active_items]
        assert active_type.id in active_ids
        assert inactive_type.id not in active_ids

        resp_inactive = await client_for_tests.get("/splice_types", params={"is_active": "false"})
        assert resp_inactive.status_code == 200
        inactive_items = [
            SpliceTypeLocalizedResponseDTO.model_validate(item)
            for item in resp_inactive.json()
        ]
        inactive_ids = [item.id for item in inactive_items]
        assert inactive_type.id in inactive_ids
        assert active_type.id not in inactive_ids

    @pytest.mark.asyncio
    async def test_get_splice_types_locale(
        self,
        client_for_tests,
        create_splice_type_fixture,
        create_splice_type_translation_fixture,
    ):
        st = await create_splice_type_fixture(
            CreateSpliceTypeFixtureDTO(locale=Language.ENG, name="English Name")
        )
        await create_splice_type_translation_fixture(
            CreateSpliceTypeTranslationFixtureDTO(
                splice_type_id=st.id,
                locale=Language.GER,
                name="Deutscher Name",
            )
        )

        response = await client_for_tests.get("/splice_types", params={"locale": "ger"})
        assert response.status_code == 200

        data = [
            SpliceTypeLocalizedResponseDTO.model_validate(item)
            for item in response.json()
        ]
        found = next(item for item in data if item.id == st.id)
        assert found.name == "Deutscher Name"

    @pytest.mark.asyncio
    async def test_create_splice_type(
        self,
        session_db,
        client_for_tests,
        create_user_fixture,
    ):
        admin_user, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )

        create_data = SpliceTypeCreate(
            code="new_unique_code",
            category=SpliceCategory.LOOP,
            visual_type=SpliceVisualType.AUG_SPLICE,
            index=10,
            is_active=True,
            translations=[
                SpliceTypeTranslationCreate(
                    locale=Language.ENG,
                    name="Aug Splice Loop",
                    description="Standard aug splice",
                ),
                SpliceTypeTranslationCreate(
                    locale=Language.GER,
                    name="Augspleiss Schlaufe",
                    description="Standard Augspleiss",
                ),
            ],
        )

        response = await client_for_tests.post(
            "/splice_types",
            headers={"Authorization": f"Bearer {access_token}"},
            json=create_data.model_dump(mode="json"),
        )
        assert response.status_code == 201

        resp_dto = SpliceTypeResponseDTO.model_validate(response.json())
        assert resp_dto.code == "new_unique_code"
        assert resp_dto.category == SpliceCategory.LOOP
        assert resp_dto.visual_type == SpliceVisualType.AUG_SPLICE
        assert len(resp_dto.translations) == 2

        # Проверяем запись в БД
        res = await session_db.execute(
            select(SpliceType)
            .where(SpliceType.id == resp_dto.id)
            .options(selectinload(SpliceType.translations))
        )
        type_from_db = res.scalar_one_or_none()
        assert type_from_db is not None
        assert comparison_models(resp_dto, type_from_db, keys_not_checked=["translations"])
        assert len(type_from_db.translations) == 2

    @pytest.mark.asyncio
    async def test_update_splice_type(
        self,
        session_db,
        client_for_tests,
        create_user_fixture,
        create_splice_type_fixture,
    ):
        admin_user, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        st = await create_splice_type_fixture(CreateSpliceTypeFixtureDTO(index=1))

        update_data = SpliceTypeUpdate(
            index=99,
            category=SpliceCategory.SPLICE,
            is_active=False,
        )

        response = await client_for_tests.patch(
            f"/splice_types/{st.id}",
            headers={"Authorization": f"Bearer {access_token}"},
            json=update_data.model_dump(exclude_unset=True, mode="json"),
        )
        assert response.status_code == 200

        updated_dto = SpliceTypeResponseDTO.model_validate(response.json())
        assert updated_dto.index == 99
        assert updated_dto.category == SpliceCategory.SPLICE
        assert updated_dto.is_active is False

        res = await session_db.execute(select(SpliceType).where(SpliceType.id == st.id))
        db_item = res.scalar_one_or_none()
        assert db_item is not None
        assert db_item.index == 99
        assert db_item.category == SpliceCategory.SPLICE
        assert db_item.is_active is False

    @pytest.mark.asyncio
    async def test_upload_and_delete_image(
        self,
        session_db,
        client_for_tests,
        create_user_fixture,
        create_splice_type_fixture,
        create_image_bytes_fixture: Callable[..., bytes],
        config_fix: Config,
    ):
        admin_user, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        st = await create_splice_type_fixture(CreateSpliceTypeFixtureDTO())

        img_bytes = create_image_bytes_fixture(format_="PNG", size=(300, 300), color="blue")

        # 1. Загрузка изображения
        response_upload = await client_for_tests.post(
            f"/splice_types/{st.id}/image",
            headers={"Authorization": f"Bearer {access_token}"},
            files={"file": ("photo.png", img_bytes, "image/png")},
        )
        assert response_upload.status_code == 200

        uploaded_dto = SpliceTypeResponseDTO.model_validate(response_upload.json())
        assert uploaded_dto.image_url is not None
        assert uploaded_dto.image_url.startswith("/media/")

        # Проверяем наличие файла на диске
        rel_path = uploaded_dto.image_url.removeprefix("/media/")
        saved_file = config_fix.paths.media / rel_path
        assert saved_file.exists()

        # 2. Удаление изображения
        response_delete = await client_for_tests.delete(
            f"/splice_types/{st.id}/image",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response_delete.status_code == 200

        deleted_dto = SpliceTypeResponseDTO.model_validate(response_delete.json())
        assert deleted_dto.image_url is None

        # Проверяем удаление файла с диска
        assert not saved_file.exists()
        if saved_file.parent.exists():
            saved_file.parent.rmdir()

    @pytest.mark.asyncio
    async def test_delete_splice_type(
        self,
        session_db,
        client_for_tests,
        create_user_fixture,
        create_splice_type_fixture,
    ):
        admin_user, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        st = await create_splice_type_fixture(CreateSpliceTypeFixtureDTO())

        response = await client_for_tests.delete(
            f"/splice_types/{st.id}",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 204

        res = await session_db.execute(select(SpliceType).where(SpliceType.id == st.id))
        assert res.scalar_one_or_none() is None

        # Проверяем каскадное удаление переводов
        res_trans = await session_db.execute(
            select(SpliceTypeTranslation).where(SpliceTypeTranslation.splice_type_id == st.id)
        )
        assert len(res_trans.scalars().all()) == 0

    @pytest.mark.asyncio
    async def test_add_translation(
        self,
        session_db,
        client_for_tests,
        create_user_fixture,
        create_splice_type_fixture,
    ):
        admin_user, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        st = await create_splice_type_fixture(CreateSpliceTypeFixtureDTO(locale=Language.ENG))

        trans_data = SpliceTypeTranslationCreate(
            locale=Language.GER,
            name="Deutscher Name",
            description="Deutsche Beschreibung",
        )

        response = await client_for_tests.post(
            f"/splice_types/{st.id}/translations",
            headers={"Authorization": f"Bearer {access_token}"},
            json=trans_data.model_dump(mode="json"),
        )
        assert response.status_code == 201

        resp_dto = SpliceTypeTranslationResponseDTO.model_validate(response.json())
        assert resp_dto.locale == Language.GER
        assert resp_dto.name == "Deutscher Name"
        assert resp_dto.splice_type_id == st.id

        # Проверяем в БД
        res = await session_db.execute(
            select(SpliceTypeTranslation).where(SpliceTypeTranslation.id == resp_dto.id)
        )
        assert res.scalar_one_or_none() is not None

    @pytest.mark.asyncio
    async def test_update_translation(
        self,
        session_db,
        client_for_tests,
        create_user_fixture,
        create_splice_type_fixture,
    ):
        admin_user, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        st = await create_splice_type_fixture(CreateSpliceTypeFixtureDTO(name="Original"))
        trans_id = st.translations[0].id

        update_data = SpliceTypeTranslationUpdate(
            name="Updated Name",
            description="Updated Description",
        )

        response = await client_for_tests.patch(
            f"/splice_types/translations/{trans_id}",
            headers={"Authorization": f"Bearer {access_token}"},
            json=update_data.model_dump(exclude_unset=True),
        )
        assert response.status_code == 200

        updated_dto = SpliceTypeTranslationResponseDTO.model_validate(response.json())
        assert updated_dto.name == "Updated Name"
        assert updated_dto.description == "Updated Description"

        res = await session_db.execute(
            select(SpliceTypeTranslation).where(SpliceTypeTranslation.id == trans_id)
        )
        db_trans = res.scalar_one_or_none()
        assert db_trans is not None
        assert db_trans.name == "Updated Name"

    @pytest.mark.asyncio
    async def test_delete_translation(
        self,
        session_db,
        client_for_tests,
        create_user_fixture,
        create_splice_type_fixture,
        create_splice_type_translation_fixture,
    ):
        admin_user, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        st = await create_splice_type_fixture(CreateSpliceTypeFixtureDTO(locale=Language.ENG))
        extra_trans = await create_splice_type_translation_fixture(
            CreateSpliceTypeTranslationFixtureDTO(splice_type_id=st.id, locale=Language.GER)
        )

        response = await client_for_tests.delete(
            f"/splice_types/translations/{extra_trans.id}",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 204

        res = await session_db.execute(
            select(SpliceTypeTranslation).where(SpliceTypeTranslation.id == extra_trans.id)
        )
        assert res.scalar_one_or_none() is None


class TestsForErrors:

    @pytest.mark.asyncio
    async def test_create_splice_type_forbidden(
        self,
        client_for_tests,
        create_user_fixture,
    ):
        regular_user, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.USER)
        )

        create_data = SpliceTypeCreate(
            code="test_code",
            category=SpliceCategory.LOOP,
            visual_type=SpliceVisualType.GENERIC,
            index=1,
            translations=[
                SpliceTypeTranslationCreate(locale=Language.ENG, name="Test"),
            ],
        )

        response = await client_for_tests.post(
            "/splice_types",
            headers={"Authorization": f"Bearer {access_token}"},
            json=create_data.model_dump(mode="json"),
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_create_splice_type_unauthorized(
        self,
        client_for_tests,
    ):
        create_data = SpliceTypeCreate(
            code="test_code",
            category=SpliceCategory.LOOP,
            visual_type=SpliceVisualType.GENERIC,
            index=1,
            translations=[
                SpliceTypeTranslationCreate(locale=Language.ENG, name="Test"),
            ],
        )

        response = await client_for_tests.post(
            "/splice_types",
            json=create_data.model_dump(mode="json"),
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_create_splice_type_without_translations(
        self,
        client_for_tests,
        create_user_fixture,
    ):
        admin_user, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )

        create_data = {
            "code": "no_trans_code",
            "category": "loop",
            "visual_type": "generic",
            "index": 1,
            "translations": [],
        }

        response = await client_for_tests.post(
            "/splice_types",
            headers={"Authorization": f"Bearer {access_token}"},
            json=create_data,
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_create_splice_type_duplicate_code(
        self,
        client_for_tests,
        create_user_fixture,
        create_splice_type_fixture,
    ):
        admin_user, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        await create_splice_type_fixture(CreateSpliceTypeFixtureDTO(code="duplicate_code"))

        create_data = SpliceTypeCreate(
            code="duplicate_code",
            category=SpliceCategory.LOOP,
            visual_type=SpliceVisualType.GENERIC,
            index=2,
            translations=[
                SpliceTypeTranslationCreate(locale=Language.ENG, name="Test"),
            ],
        )

        response = await client_for_tests.post(
            "/splice_types",
            headers={"Authorization": f"Bearer {access_token}"},
            json=create_data.model_dump(mode="json"),
        )
        assert response.status_code == 409

    @pytest.mark.asyncio
    async def test_update_splice_type_not_found(
        self,
        client_for_tests,
        create_user_fixture,
    ):
        admin_user, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )

        response = await client_for_tests.patch(
            "/splice_types/99999",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"index": 5},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_splice_type_not_found(
        self,
        client_for_tests,
        create_user_fixture,
    ):
        admin_user, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )

        response = await client_for_tests.delete(
            "/splice_types/99999",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_splice_type_has_dependencies(
        self,
        client_for_tests,
        create_user_fixture,
        create_splice_type_fixture,
        create_splice_material_fixture,
        create_splice_price_rule_fixture,
    ):
        """Попытка удаления типа сращивания при наличии связанных ценовых правил -> 400 Bad Request."""
        admin_user, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        st = await create_splice_type_fixture(CreateSpliceTypeFixtureDTO())
        material = await create_splice_material_fixture(CreateSpliceMaterialFixtureDTO())
        await create_splice_price_rule_fixture(
            CreateSplicePriceRuleFixtureDTO(
                splice_type_id=st.id,
                splice_material_id=material.id,
            )
        )

        response = await client_for_tests.delete(
            f"/splice_types/{st.id}",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 400
        assert "referenced by splice price rules or rope products" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_upload_image_not_found(
        self,
        client_for_tests,
        create_user_fixture,
        create_image_bytes_fixture: Callable[..., bytes],
    ):
        admin_user, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        img_bytes = create_image_bytes_fixture(format_="PNG")

        response = await client_for_tests.post(
            "/splice_types/99999/image",
            headers={"Authorization": f"Bearer {access_token}"},
            files={"file": ("photo.png", img_bytes, "image/png")},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_image_not_found(
        self,
        client_for_tests,
        create_user_fixture,
    ):
        admin_user, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )

        response = await client_for_tests.delete(
            "/splice_types/99999/image",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_add_translation_duplicate_locale(
        self,
        client_for_tests,
        create_user_fixture,
        create_splice_type_fixture,
    ):
        admin_user, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        st = await create_splice_type_fixture(CreateSpliceTypeFixtureDTO(locale=Language.ENG))

        trans_data = SpliceTypeTranslationCreate(
            locale=Language.ENG,
            name="Duplicate English",
        )

        response = await client_for_tests.post(
            f"/splice_types/{st.id}/translations",
            headers={"Authorization": f"Bearer {access_token}"},
            json=trans_data.model_dump(mode="json"),
        )
        assert response.status_code == 409

    @pytest.mark.asyncio
    async def test_add_translation_type_not_found(
        self,
        client_for_tests,
        create_user_fixture,
    ):
        admin_user, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )

        trans_data = SpliceTypeTranslationCreate(
            locale=Language.GER,
            name="German Name",
        )

        response = await client_for_tests.post(
            "/splice_types/99999/translations",
            headers={"Authorization": f"Bearer {access_token}"},
            json=trans_data.model_dump(mode="json"),
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_translation_not_found(
        self,
        client_for_tests,
        create_user_fixture,
    ):
        admin_user, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )

        response = await client_for_tests.patch(
            "/splice_types/translations/99999",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"name": "New Name"},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_translation_not_found(
        self,
        client_for_tests,
        create_user_fixture,
    ):
        admin_user, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )

        response = await client_for_tests.delete(
            "/splice_types/translations/99999",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_last_translation_error(
        self,
        client_for_tests,
        create_user_fixture,
        create_splice_type_fixture,
    ):
        admin_user, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        st = await create_splice_type_fixture(CreateSpliceTypeFixtureDTO())
        only_trans_id = st.translations[0].id

        response = await client_for_tests.delete(
            f"/splice_types/translations/{only_trans_id}",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 400

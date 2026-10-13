from typing import Callable
from pathlib import Path
import pytest
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.core.config.config import Config
from src.modules.base.database_model import Language
from src.modules.products.models import Product
from src.modules.users.models import UserRole
from tests.modules.users.fixtures.models_dto import CreateUserFixtureDTO
from tests.modules.categories.fixtures.models_dto import (
    CreateCategoryFixtureDTO,
    CreateCategoryTranslationFixtureDTO,
)
from src.modules.categories.models import Category, CategoryTranslation
from src.modules.categories.models_dto import (
    CategoryResponseDTO,
    CategoryLocalizedResponseDTO,
    CategoryCreate,
    CategoryUpdate,
    CategoryUpdateIndexDTO,
    CategoryTranslationCreate,
    CategoryTranslationUpdate,
    CategoryTranslationResponseDTO,
)
from tests.helpers.functions import comparison_models


class TestsForSuccess:

    @pytest.mark.asyncio
    async def test_get_all_categories(
        self,
        client_for_tests,
        create_category_fixture,
    ):
        cat_1 = await create_category_fixture(
            CreateCategoryFixtureDTO(slug="yachting-ropes", name="Yachting Ropes")
        )
        cat_2 = await create_category_fixture(
            CreateCategoryFixtureDTO(slug="climbing-ropes", name="Climbing Ropes")
        )

        response = await client_for_tests.get("/categories")
        assert response.status_code == 200

        data = [
            CategoryLocalizedResponseDTO.model_validate(item)
            for item in response.json()
        ]
        assert len(data) >= 2

        ids = [item.id for item in data]
        assert cat_1.id in ids
        assert cat_2.id in ids

        found = next(item for item in data if item.id == cat_1.id)
        assert found.slug == "yachting-ropes"
        assert found.name == "Yachting Ropes"
        assert found.products_count == 0

    @pytest.mark.asyncio
    async def test_get_all_categories_filter_is_active(
        self,
        client_for_tests,
        create_category_fixture,
    ):
        active_cat = await create_category_fixture(
            CreateCategoryFixtureDTO(is_active=True)
        )
        inactive_cat = await create_category_fixture(
            CreateCategoryFixtureDTO(is_active=False)
        )

        resp_active = await client_for_tests.get("/categories", params={"is_active": "true"})
        assert resp_active.status_code == 200
        active_items = [
            CategoryLocalizedResponseDTO.model_validate(item)
            for item in resp_active.json()
        ]
        active_ids = [item.id for item in active_items]
        assert active_cat.id in active_ids
        assert inactive_cat.id not in active_ids

        resp_inactive = await client_for_tests.get("/categories", params={"is_active": "false"})
        assert resp_inactive.status_code == 200
        inactive_items = [
            CategoryLocalizedResponseDTO.model_validate(item)
            for item in resp_inactive.json()
        ]
        inactive_ids = [item.id for item in inactive_items]
        assert inactive_cat.id in inactive_ids
        assert active_cat.id not in inactive_ids

    @pytest.mark.asyncio
    async def test_get_all_categories_pagination(
        self,
        client_for_tests,
        create_category_fixture,
    ):
        await create_category_fixture(CreateCategoryFixtureDTO(index=1))
        await create_category_fixture(CreateCategoryFixtureDTO(index=2))
        await create_category_fixture(CreateCategoryFixtureDTO(index=3))

        resp_limit = await client_for_tests.get("/categories", params={"limit": 2, "offset": 0})
        assert resp_limit.status_code == 200
        items_limit = resp_limit.json()
        assert len(items_limit) == 2

        resp_offset = await client_for_tests.get("/categories", params={"limit": 2, "offset": 2})
        assert resp_offset.status_code == 200
        items_offset = resp_offset.json()
        assert len(items_offset) >= 1

    @pytest.mark.asyncio
    async def test_get_all_categories_locale(
        self,
        client_for_tests,
        create_category_fixture,
        create_category_translation_fixture,
    ):
        cat = await create_category_fixture(
            CreateCategoryFixtureDTO(locale=Language.ENG, name="Tow Ropes")
        )
        await create_category_translation_fixture(
            CreateCategoryTranslationFixtureDTO(
                category_id=cat.id,
                locale=Language.GER,
                name="Schleppseile",
            )
        )

        response = await client_for_tests.get("/categories", params={"locale": "ger"})
        assert response.status_code == 200

        data = [
            CategoryLocalizedResponseDTO.model_validate(item)
            for item in response.json()
        ]
        found = next(item for item in data if item.id == cat.id)
        assert found.name == "Schleppseile"

    @pytest.mark.asyncio
    async def test_get_category_by_id(
        self,
        client_for_tests,
        create_category_fixture,
    ):
        cat = await create_category_fixture(
            CreateCategoryFixtureDTO(slug="marine-lines", name="Marine Lines")
        )

        response = await client_for_tests.get(f"/categories/{cat.id}")
        assert response.status_code == 200

        resp_dto = CategoryResponseDTO.model_validate(response.json())
        assert resp_dto.id == cat.id
        assert resp_dto.slug == "marine-lines"
        assert len(resp_dto.translations) >= 1
        assert resp_dto.products_count == 0

    @pytest.mark.asyncio
    async def test_get_category_by_slug(
        self,
        client_for_tests,
        create_category_fixture,
    ):
        cat = await create_category_fixture(
            CreateCategoryFixtureDTO(slug="industrial-cords", name="Industrial Cords")
        )

        response = await client_for_tests.get("/categories/by-slug/industrial-cords")
        assert response.status_code == 200

        resp_dto = CategoryResponseDTO.model_validate(response.json())
        assert resp_dto.id == cat.id
        assert resp_dto.slug == "industrial-cords"
        assert resp_dto.translations[0].name == "Industrial Cords"

    @pytest.mark.asyncio
    async def test_create_category(
        self,
        session_db,
        client_for_tests,
        create_user_fixture,
    ):
        admin_user, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )

        create_data = CategoryCreate(
            slug="safety-harnesses",
            image_url="https://example.com/safety.jpg",
            index=3,
            is_active=True,
            translations=[
                CategoryTranslationCreate(
                    locale=Language.ENG,
                    name="Safety Harnesses",
                ),
                CategoryTranslationCreate(
                    locale=Language.GER,
                    name="Sicherheitsgurte",
                ),
            ],
        )

        response = await client_for_tests.post(
            "/categories",
            headers={"Authorization": f"Bearer {access_token}"},
            json=create_data.model_dump(mode="json"),
        )
        assert response.status_code == 201

        resp_dto = CategoryResponseDTO.model_validate(response.json())
        assert resp_dto.slug == "safety-harnesses"
        assert resp_dto.image_url == "https://example.com/safety.jpg"
        assert resp_dto.index == 3
        assert resp_dto.is_active is True
        assert len(resp_dto.translations) == 2

        # Проверяем в БД
        res = await session_db.execute(
            select(Category)
            .where(Category.id == resp_dto.id)
            .options(selectinload(Category.translations))
        )
        cat_from_db = res.scalar_one_or_none()
        assert cat_from_db is not None
        assert comparison_models(resp_dto, cat_from_db, keys_not_checked=["translations", "products_count"])
        assert len(cat_from_db.translations) == 2

    @pytest.mark.asyncio
    async def test_update_category(
        self,
        session_db,
        client_for_tests,
        create_user_fixture,
        create_category_fixture,
    ):
        admin_user, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        cat = await create_category_fixture(CreateCategoryFixtureDTO(slug="old-slug", index=1))

        update_data = CategoryUpdate(
            slug="updated-slug",
            is_active=False,
        )

        response = await client_for_tests.patch(
            f"/categories/{cat.id}",
            headers={"Authorization": f"Bearer {access_token}"},
            json=update_data.model_dump(exclude_unset=True, mode="json"),
        )
        assert response.status_code == 200

        updated_dto = CategoryResponseDTO.model_validate(response.json())
        assert updated_dto.slug == "updated-slug"
        assert updated_dto.index == 1
        assert updated_dto.is_active is False

        session_db.expire_all()
        res = await session_db.execute(select(Category).where(Category.id == cat.id))
        db_item = res.scalar_one_or_none()
        assert db_item is not None
        assert db_item.slug == "updated-slug"
        assert db_item.is_active is False

    @pytest.mark.asyncio
    async def test_update_category_index(
        self,
        session_db,
        client_for_tests,
        create_user_fixture,
        create_category_fixture,
    ):
        """Тест перемещения индекса (reorder) с автоматическим сдвигом соседей."""
        admin_user, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )

        c0 = await create_category_fixture(CreateCategoryFixtureDTO(slug="c0", index=0))
        c1 = await create_category_fixture(CreateCategoryFixtureDTO(slug="c1", index=1))
        c2 = await create_category_fixture(CreateCategoryFixtureDTO(slug="c2", index=2))
        c3 = await create_category_fixture(CreateCategoryFixtureDTO(slug="c3", index=3))

        # Перемещаем c3 (был index=3) на index=1
        req_data = CategoryUpdateIndexDTO(new_index=1)
        response = await client_for_tests.patch(
            f"/categories/{c3.id}/index",
            headers={"Authorization": f"Bearer {access_token}"},
            json=req_data.model_dump(),
        )
        assert response.status_code == 200

        updated_dto = CategoryResponseDTO.model_validate(response.json())
        assert updated_dto.id == c3.id
        assert updated_dto.index == 1

        session_db.expire_all()
        db_c0 = (await session_db.execute(select(Category).where(Category.id == c0.id))).scalar_one()
        db_c1 = (await session_db.execute(select(Category).where(Category.id == c1.id))).scalar_one()
        db_c2 = (await session_db.execute(select(Category).where(Category.id == c2.id))).scalar_one()
        db_c3 = (await session_db.execute(select(Category).where(Category.id == c3.id))).scalar_one()

        assert db_c0.index == 0
        assert db_c3.index == 1
        assert db_c1.index == 2
        assert db_c2.index == 3

    @pytest.mark.asyncio
    async def test_update_category_index_same_value(
        self,
        session_db,
        client_for_tests,
        create_user_fixture,
        create_category_fixture,
    ):
        admin_user, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        cat = await create_category_fixture(CreateCategoryFixtureDTO(index=4))

        response = await client_for_tests.patch(
            f"/categories/{cat.id}/index",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"new_index": 4},
        )
        assert response.status_code == 200

        updated_dto = CategoryResponseDTO.model_validate(response.json())
        assert updated_dto.index == 4

    @pytest.mark.asyncio
    async def test_upload_and_delete_image(
        self,
        session_db,
        client_for_tests,
        create_user_fixture,
        create_category_fixture,
        create_image_bytes_fixture: Callable[..., bytes],
        config_fix: Config,
    ):
        admin_user, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        cat = await create_category_fixture(CreateCategoryFixtureDTO())

        img_bytes = create_image_bytes_fixture(format_="PNG", size=(300, 300), color="blue")

        # 1. Загрузка изображения
        response_upload = await client_for_tests.post(
            f"/categories/{cat.id}/image",
            headers={"Authorization": f"Bearer {access_token}"},
            files={"file": ("category.png", img_bytes, "image/png")},
        )
        assert response_upload.status_code == 200

        uploaded_dto = CategoryResponseDTO.model_validate(response_upload.json())
        assert uploaded_dto.image_url is not None
        assert uploaded_dto.image_url.startswith("/media/")

        rel_path = uploaded_dto.image_url.removeprefix("/media/")
        saved_file = config_fix.paths.media / rel_path
        assert saved_file.exists()

        # 2. Удаление изображения
        response_delete = await client_for_tests.delete(
            f"/categories/{cat.id}/image",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response_delete.status_code == 200

        deleted_dto = CategoryResponseDTO.model_validate(response_delete.json())
        assert deleted_dto.image_url is None

        assert not saved_file.exists()
        if saved_file.parent.exists():
            saved_file.parent.rmdir()

    @pytest.mark.asyncio
    async def test_delete_category(
        self,
        session_db,
        client_for_tests,
        create_user_fixture,
        create_category_fixture,
    ):
        admin_user, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        cat = await create_category_fixture(CreateCategoryFixtureDTO())

        response = await client_for_tests.delete(
            f"/categories/{cat.id}",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 204

        res = await session_db.execute(select(Category).where(Category.id == cat.id))
        assert res.scalar_one_or_none() is None

        # Проверяем каскадное удаление переводов
        res_trans = await session_db.execute(
            select(CategoryTranslation).where(CategoryTranslation.category_id == cat.id)
        )
        assert len(res_trans.scalars().all()) == 0

    @pytest.mark.asyncio
    async def test_add_translation(
        self,
        session_db,
        client_for_tests,
        create_user_fixture,
        create_category_fixture,
    ):
        admin_user, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        cat = await create_category_fixture(CreateCategoryFixtureDTO(locale=Language.ENG))

        trans_data = CategoryTranslationCreate(
            locale=Language.GER,
            name="Deutscher Name",
        )

        response = await client_for_tests.post(
            f"/categories/{cat.id}/translations",
            headers={"Authorization": f"Bearer {access_token}"},
            json=trans_data.model_dump(mode="json"),
        )
        assert response.status_code == 201

        resp_dto = CategoryTranslationResponseDTO.model_validate(response.json())
        assert resp_dto.locale == Language.GER
        assert resp_dto.name == "Deutscher Name"
        assert resp_dto.category_id == cat.id

        res = await session_db.execute(
            select(CategoryTranslation).where(CategoryTranslation.id == resp_dto.id)
        )
        assert res.scalar_one_or_none() is not None

    @pytest.mark.asyncio
    async def test_update_translation(
        self,
        session_db,
        client_for_tests,
        create_user_fixture,
        create_category_fixture,
    ):
        admin_user, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        cat = await create_category_fixture(CreateCategoryFixtureDTO(name="Original Name"))
        trans_id = cat.translations[0].id

        update_data = CategoryTranslationUpdate(
            name="Updated Name",
        )

        response = await client_for_tests.patch(
            f"/categories/translations/{trans_id}",
            headers={"Authorization": f"Bearer {access_token}"},
            json=update_data.model_dump(exclude_unset=True),
        )
        assert response.status_code == 200

        updated_dto = CategoryTranslationResponseDTO.model_validate(response.json())
        assert updated_dto.name == "Updated Name"

        res = await session_db.execute(
            select(CategoryTranslation).where(CategoryTranslation.id == trans_id)
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
        create_category_fixture,
        create_category_translation_fixture,
    ):
        admin_user, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        cat = await create_category_fixture(CreateCategoryFixtureDTO(locale=Language.ENG))
        extra_trans = await create_category_translation_fixture(
            CreateCategoryTranslationFixtureDTO(category_id=cat.id, locale=Language.GER)
        )

        response = await client_for_tests.delete(
            f"/categories/translations/{extra_trans.id}",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 204

        res = await session_db.execute(
            select(CategoryTranslation).where(CategoryTranslation.id == extra_trans.id)
        )
        assert res.scalar_one_or_none() is None


class TestsForErrors:

    @pytest.mark.asyncio
    async def test_create_category_forbidden(
        self,
        client_for_tests,
        create_user_fixture,
    ):
        regular_user, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.USER)
        )

        create_data = CategoryCreate(
            slug="forbidden-category",
            index=1,
            translations=[
                CategoryTranslationCreate(locale=Language.ENG, name="Test"),
            ],
        )

        response = await client_for_tests.post(
            "/categories",
            headers={"Authorization": f"Bearer {access_token}"},
            json=create_data.model_dump(mode="json"),
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_create_category_unauthorized(
        self,
        client_for_tests,
    ):
        create_data = CategoryCreate(
            slug="unauth-category",
            index=1,
            translations=[
                CategoryTranslationCreate(locale=Language.ENG, name="Test"),
            ],
        )

        response = await client_for_tests.post(
            "/categories",
            json=create_data.model_dump(mode="json"),
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_create_category_without_translations(
        self,
        client_for_tests,
        create_user_fixture,
    ):
        admin_user, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )

        create_data = {
            "slug": "no-trans-cat",
            "index": 1,
            "translations": [],
        }

        response = await client_for_tests.post(
            "/categories",
            headers={"Authorization": f"Bearer {access_token}"},
            json=create_data,
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_category_duplicate_slug(
        self,
        client_for_tests,
        create_user_fixture,
        create_category_fixture,
    ):
        admin_user, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        await create_category_fixture(CreateCategoryFixtureDTO(slug="existing-slug"))

        create_data = CategoryCreate(
            slug="existing-slug",
            index=2,
            translations=[
                CategoryTranslationCreate(locale=Language.ENG, name="Test"),
            ],
        )

        response = await client_for_tests.post(
            "/categories",
            headers={"Authorization": f"Bearer {access_token}"},
            json=create_data.model_dump(mode="json"),
        )
        assert response.status_code == 409

    @pytest.mark.asyncio
    async def test_get_category_not_found(
        self,
        client_for_tests,
    ):
        response = await client_for_tests.get("/categories/99999")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_category_by_slug_not_found(
        self,
        client_for_tests,
    ):
        response = await client_for_tests.get("/categories/by-slug/non-existent-slug")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_category_not_found(
        self,
        client_for_tests,
        create_user_fixture,
    ):
        admin_user, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )

        response = await client_for_tests.patch(
            "/categories/99999",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"slug": "new-slug"},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_category_duplicate_slug(
        self,
        client_for_tests,
        create_user_fixture,
        create_category_fixture,
    ):
        admin_user, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        cat_1 = await create_category_fixture(CreateCategoryFixtureDTO(slug="slug-one"))
        cat_2 = await create_category_fixture(CreateCategoryFixtureDTO(slug="slug-two"))

        response = await client_for_tests.patch(
            f"/categories/{cat_2.id}",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"slug": "slug-one"},
        )
        assert response.status_code == 409

    @pytest.mark.asyncio
    async def test_update_category_index_forbidden(
        self,
        client_for_tests,
        create_user_fixture,
        create_category_fixture,
    ):
        regular_user, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.USER)
        )
        cat = await create_category_fixture(CreateCategoryFixtureDTO())

        response = await client_for_tests.patch(
            f"/categories/{cat.id}/index",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"new_index": 2},
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_update_category_index_unauthorized(
        self,
        client_for_tests,
        create_category_fixture,
    ):
        cat = await create_category_fixture(CreateCategoryFixtureDTO())

        response = await client_for_tests.patch(
            f"/categories/{cat.id}/index",
            json={"new_index": 2},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_update_category_index_not_found(
        self,
        client_for_tests,
        create_user_fixture,
    ):
        admin_user, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )

        response = await client_for_tests.patch(
            "/categories/99999/index",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"new_index": 2},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_category_index_validation_error(
        self,
        client_for_tests,
        create_user_fixture,
        create_category_fixture,
    ):
        admin_user, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        cat = await create_category_fixture(CreateCategoryFixtureDTO())

        response = await client_for_tests.patch(
            f"/categories/{cat.id}/index",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"new_index": -1},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_delete_category_not_found(
        self,
        client_for_tests,
        create_user_fixture,
    ):
        admin_user, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )

        response = await client_for_tests.delete(
            "/categories/99999",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_category_has_dependencies(
        self,
        session_db,
        client_for_tests,
        create_user_fixture,
        create_category_fixture,
    ):
        """Попытка удаления категории, к которой привязан товар -> 400 Bad Request."""
        admin_user, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        cat = await create_category_fixture(CreateCategoryFixtureDTO())

        # Создаем товар с этой категорией
        product = Product(category_id=cat.id)
        session_db.add(product)
        await session_db.commit()

        response = await client_for_tests.delete(
            f"/categories/{cat.id}",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 400
        assert "referenced by products" in response.json()["detail"]

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
            "/categories/99999/image",
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
            "/categories/99999/image",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_add_translation_category_not_found(
        self,
        client_for_tests,
        create_user_fixture,
    ):
        admin_user, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )

        trans_data = CategoryTranslationCreate(
            locale=Language.GER,
            name="German Name",
        )

        response = await client_for_tests.post(
            "/categories/99999/translations",
            headers={"Authorization": f"Bearer {access_token}"},
            json=trans_data.model_dump(mode="json"),
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_add_translation_duplicate_locale(
        self,
        client_for_tests,
        create_user_fixture,
        create_category_fixture,
    ):
        admin_user, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        cat = await create_category_fixture(CreateCategoryFixtureDTO(locale=Language.ENG))

        trans_data = CategoryTranslationCreate(
            locale=Language.ENG,
            name="Duplicate English",
        )

        response = await client_for_tests.post(
            f"/categories/{cat.id}/translations",
            headers={"Authorization": f"Bearer {access_token}"},
            json=trans_data.model_dump(mode="json"),
        )
        assert response.status_code == 409

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
            "/categories/translations/99999",
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
            "/categories/translations/99999",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_last_translation_error(
        self,
        client_for_tests,
        create_user_fixture,
        create_category_fixture,
    ):
        admin_user, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        cat = await create_category_fixture(CreateCategoryFixtureDTO())
        only_trans_id = cat.translations[0].id

        response = await client_for_tests.delete(
            f"/categories/translations/{only_trans_id}",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 400

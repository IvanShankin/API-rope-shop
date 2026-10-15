import pytest
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.modules.base.database_model import Language
from src.modules.product_images.models import ProductImage
from src.modules.rope_products.models import RopeConfiguratorSetting
from src.modules.products.models import Product, ProductTranslation, ProductType
from src.modules.products.models_dto import (
    ProductCreate,
    ProductLocalizedResponseDTO,
    ProductResponseDTO,
    ProductTranslationCreate,
    ProductTranslationResponseDTO,
    ProductTranslationUpdate,
    ProductUpdate,
    ProductUpdateIndexDTO,
)
from src.modules.users.models import UserRole
from tests.helpers.functions import comparison_models
from tests.modules.categories.fixtures.models_dto import CreateCategoryFixtureDTO
from tests.modules.products.fixtures.models_dto import (
    CreateProductFixtureDTO,
    CreateProductTranslationFixtureDTO,
)
from tests.modules.users.fixtures.models_dto import CreateUserFixtureDTO


class TestsForSuccess:

    @pytest.mark.asyncio
    async def test_get_all_products(
        self,
        client_for_tests,
        create_category_fixture,
        create_product_fixture,
    ):
        cat = await create_category_fixture()
        p1 = await create_product_fixture(
            CreateProductFixtureDTO(
                category_id=cat.id,
                slug="racer-xtr",
                name="Racer XTR",
                description="Racing line",
            )
        )
        p2 = await create_product_fixture(
            CreateProductFixtureDTO(
                category_id=cat.id,
                slug="cruiser-pro",
                name="Cruiser Pro",
                description="Cruising line",
            )
        )

        response = await client_for_tests.get("/products")
        assert response.status_code == 200

        data = [
            ProductLocalizedResponseDTO.model_validate(item)
            for item in response.json()
        ]
        assert len(data) >= 2

        ids = [item.id for item in data]
        assert p1.id in ids
        assert p2.id in ids

        found = next(item for item in data if item.id == p1.id)
        assert found.slug == "racer-xtr"
        assert found.name == "Racer XTR"
        assert found.description == "Racing line"

    @pytest.mark.asyncio
    async def test_get_all_products_filter_by_category_id(
        self,
        client_for_tests,
        create_category_fixture,
        create_product_fixture,
    ):
        cat1 = await create_category_fixture()
        cat2 = await create_category_fixture()

        p1 = await create_product_fixture(CreateProductFixtureDTO(category_id=cat1.id))
        p2 = await create_product_fixture(CreateProductFixtureDTO(category_id=cat2.id))

        resp = await client_for_tests.get("/products", params={"category_id": cat1.id})
        assert resp.status_code == 200

        items = [ProductLocalizedResponseDTO.model_validate(i) for i in resp.json()]
        ids = [i.id for i in items]
        assert p1.id in ids
        assert p2.id not in ids

    @pytest.mark.asyncio
    async def test_get_all_products_filter_by_category_slug(
        self,
        client_for_tests,
        create_category_fixture,
        create_product_fixture,
    ):
        cat1 = await create_category_fixture(CreateCategoryFixtureDTO(slug="yachting"))
        cat2 = await create_category_fixture(CreateCategoryFixtureDTO(slug="climbing"))

        p1 = await create_product_fixture(CreateProductFixtureDTO(category_id=cat1.id))
        p2 = await create_product_fixture(CreateProductFixtureDTO(category_id=cat2.id))

        resp = await client_for_tests.get("/products", params={"category_slug": "yachting"})
        assert resp.status_code == 200

        items = [ProductLocalizedResponseDTO.model_validate(i) for i in resp.json()]
        ids = [i.id for i in items]
        assert p1.id in ids
        assert p2.id not in ids

    @pytest.mark.asyncio
    async def test_get_all_products_filter_by_product_type(
        self,
        client_for_tests,
        create_product_fixture,
    ):
        p_rope = await create_product_fixture(
            CreateProductFixtureDTO(product_type=ProductType.ROPE.value)
        )
        p_hw = await create_product_fixture(
            CreateProductFixtureDTO(product_type=ProductType.HARDWARE.value)
        )

        resp = await client_for_tests.get("/products", params={"product_type": "hardware"})
        assert resp.status_code == 200

        items = [ProductLocalizedResponseDTO.model_validate(i) for i in resp.json()]
        ids = [i.id for i in items]
        assert p_hw.id in ids
        assert p_rope.id not in ids

    @pytest.mark.asyncio
    async def test_get_all_products_filter_by_is_active(
        self,
        client_for_tests,
        create_product_fixture,
    ):
        p_active = await create_product_fixture(CreateProductFixtureDTO(is_active=True))
        p_inactive = await create_product_fixture(CreateProductFixtureDTO(is_active=False))

        resp_active = await client_for_tests.get("/products", params={"is_active": "true"})
        assert resp_active.status_code == 200
        active_ids = [i["id"] for i in resp_active.json()]
        assert p_active.id in active_ids
        assert p_inactive.id not in active_ids

        resp_inactive = await client_for_tests.get("/products", params={"is_active": "false"})
        assert resp_inactive.status_code == 200
        inactive_ids = [i["id"] for i in resp_inactive.json()]
        assert p_inactive.id in inactive_ids
        assert p_active.id not in inactive_ids

    @pytest.mark.asyncio
    async def test_get_all_products_pagination(
        self,
        client_for_tests,
        create_product_fixture,
    ):
        await create_product_fixture(CreateProductFixtureDTO(index=1))
        await create_product_fixture(CreateProductFixtureDTO(index=2))
        await create_product_fixture(CreateProductFixtureDTO(index=3))

        resp_limit = await client_for_tests.get("/products", params={"limit": 2, "skip": 0})
        assert resp_limit.status_code == 200
        assert len(resp_limit.json()) == 2

        resp_skip = await client_for_tests.get("/products", params={"limit": 2, "skip": 2})
        assert resp_skip.status_code == 200
        assert len(resp_skip.json()) >= 1

    @pytest.mark.asyncio
    async def test_get_all_products_locale(
        self,
        client_for_tests,
        create_product_fixture,
        create_product_translation_fixture,
    ):
        prod = await create_product_fixture(
            CreateProductFixtureDTO(
                locale=Language.ENG,
                name="Tow Rope",
                description="Heavy duty",
            )
        )
        await create_product_translation_fixture(
            CreateProductTranslationFixtureDTO(
                product_id=prod.id,
                locale=Language.GER,
                name="Schleppseil",
                description="Schwere Ausführung",
            )
        )

        resp = await client_for_tests.get("/products", params={"locale": "ger"})
        assert resp.status_code == 200

        data = [ProductLocalizedResponseDTO.model_validate(i) for i in resp.json()]
        found = next(i for i in data if i.id == prod.id)
        assert found.name == "Schleppseil"
        assert found.description == "Schwere Ausführung"

    @pytest.mark.asyncio
    async def test_get_product_by_id(
        self,
        client_for_tests,
        create_product_fixture,
    ):
        prod = await create_product_fixture(
            CreateProductFixtureDTO(slug="marine-cord", name="Marine Cord")
        )

        response = await client_for_tests.get(f"/products/{prod.id}")
        assert response.status_code == 200

        resp_dto = ProductResponseDTO.model_validate(response.json())
        assert resp_dto.id == prod.id
        assert resp_dto.slug == "marine-cord"
        assert len(resp_dto.translations) >= 1
        assert resp_dto.translations[0].name == "Marine Cord"

    @pytest.mark.asyncio
    async def test_get_product_by_slug(
        self,
        client_for_tests,
        create_product_fixture,
    ):
        prod = await create_product_fixture(
            CreateProductFixtureDTO(slug="super-line", name="Super Line")
        )

        response = await client_for_tests.get("/products/by-slug/super-line")
        assert response.status_code == 200

        resp_dto = ProductResponseDTO.model_validate(response.json())
        assert resp_dto.id == prod.id
        assert resp_dto.slug == "super-line"

    @pytest.mark.asyncio
    async def test_create_product(
        self,
        session_db,
        client_for_tests,
        create_user_fixture,
        create_category_fixture,
    ):
        admin_user, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        cat = await create_category_fixture()

        create_data = ProductCreate(
            category_id=cat.id,
            slug="new-racing-line",
            product_type=ProductType.ROPE.value,
            index=2,
            is_active=True,
            translations=[
                ProductTranslationCreate(
                    locale=Language.ENG,
                    name="New Racing Line",
                    description="High tech rope",
                ),
                ProductTranslationCreate(
                    locale=Language.GER,
                    name="Neue Regattaleine",
                    description="High-Tech Tauwerk",
                ),
            ],
        )

        response = await client_for_tests.post(
            "/products",
            headers={"Authorization": f"Bearer {access_token}"},
            json=create_data.model_dump(mode="json"),
        )
        assert response.status_code == 201

        resp_dto = ProductResponseDTO.model_validate(response.json())
        assert resp_dto.category_id == cat.id
        assert resp_dto.slug == "new-racing-line"
        assert resp_dto.product_type == "rope"
        assert resp_dto.index == 2
        assert resp_dto.is_active is True
        assert len(resp_dto.translations) == 2

        # Проверяем в БД
        res = await session_db.execute(
            select(Product)
            .where(Product.id == resp_dto.id)
            .options(selectinload(Product.translations))
        )
        db_prod = res.scalar_one_or_none()
        assert db_prod is not None
        assert comparison_models(
            resp_dto,
            db_prod,
            keys_not_checked=["translations", "main_image_url"],
        )
        assert len(db_prod.translations) == 2

    @pytest.mark.asyncio
    async def test_update_product(
        self,
        session_db,
        client_for_tests,
        create_user_fixture,
        create_category_fixture,
        create_product_fixture,
    ):
        admin_user, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        cat_new = await create_category_fixture()
        prod = await create_product_fixture(CreateProductFixtureDTO(slug="orig-slug"))

        update_data = ProductUpdate(
            category_id=cat_new.id,
            slug="updated-prod-slug",
            product_type=ProductType.FINISHED_PRODUCT.value,
            is_active=False,
        )

        response = await client_for_tests.patch(
            f"/products/{prod.id}",
            headers={"Authorization": f"Bearer {access_token}"},
            json=update_data.model_dump(exclude_unset=True, mode="json"),
        )
        assert response.status_code == 200

        updated_dto = ProductResponseDTO.model_validate(response.json())
        assert updated_dto.category_id == cat_new.id
        assert updated_dto.slug == "updated-prod-slug"
        assert updated_dto.product_type == "finished_product"
        assert updated_dto.is_active is False

        session_db.expire_all()
        res = await session_db.execute(select(Product).where(Product.id == prod.id))
        db_item = res.scalar_one_or_none()
        assert db_item is not None
        assert db_item.slug == "updated-prod-slug"
        assert db_item.product_type == "finished_product"
        assert db_item.is_active is False

    @pytest.mark.asyncio
    async def test_update_product_index(
        self,
        session_db,
        client_for_tests,
        create_user_fixture,
        create_product_fixture,
    ):
        """Тест перемещения индекса (reorder) с автоматическим сдвигом соседей."""
        admin_user, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )

        p0 = await create_product_fixture(CreateProductFixtureDTO(slug="p0", index=0))
        p1 = await create_product_fixture(CreateProductFixtureDTO(slug="p1", index=1))
        p2 = await create_product_fixture(CreateProductFixtureDTO(slug="p2", index=2))
        p3 = await create_product_fixture(CreateProductFixtureDTO(slug="p3", index=3))

        # Перемещаем p3 (был index=3) на index=1
        req_data = ProductUpdateIndexDTO(new_index=1)
        response = await client_for_tests.patch(
            f"/products/{p3.id}/index",
            headers={"Authorization": f"Bearer {access_token}"},
            json=req_data.model_dump(),
        )
        assert response.status_code == 200

        updated_dto = ProductResponseDTO.model_validate(response.json())
        assert updated_dto.id == p3.id
        assert updated_dto.index == 1

        session_db.expire_all()
        db_p0 = (await session_db.execute(select(Product).where(Product.id == p0.id))).scalar_one()
        db_p1 = (await session_db.execute(select(Product).where(Product.id == p1.id))).scalar_one()
        db_p2 = (await session_db.execute(select(Product).where(Product.id == p2.id))).scalar_one()
        db_p3 = (await session_db.execute(select(Product).where(Product.id == p3.id))).scalar_one()

        assert db_p0.index == 0
        assert db_p3.index == 1
        assert db_p1.index == 2
        assert db_p2.index == 3

    @pytest.mark.asyncio
    async def test_update_product_index_same_value(
        self,
        client_for_tests,
        create_user_fixture,
        create_product_fixture,
    ):
        admin_user, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        prod = await create_product_fixture(CreateProductFixtureDTO(index=4))

        response = await client_for_tests.patch(
            f"/products/{prod.id}/index",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"new_index": 4},
        )
        assert response.status_code == 200

        updated_dto = ProductResponseDTO.model_validate(response.json())
        assert updated_dto.index == 4

    @pytest.mark.asyncio
    async def test_delete_product(
        self,
        session_db,
        client_for_tests,
        create_user_fixture,
        create_product_fixture,
    ):
        admin_user, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        prod = await create_product_fixture(CreateProductFixtureDTO())

        response = await client_for_tests.delete(
            f"/products/{prod.id}",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 204

        res = await session_db.execute(select(Product).where(Product.id == prod.id))
        assert res.scalar_one_or_none() is None

        # Проверяем каскадное удаление переводов
        res_trans = await session_db.execute(
            select(ProductTranslation).where(ProductTranslation.product_id == prod.id)
        )
        assert len(res_trans.scalars().all()) == 0

    @pytest.mark.asyncio
    async def test_add_translation(
        self,
        session_db,
        client_for_tests,
        create_user_fixture,
        create_product_fixture,
    ):
        admin_user, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        prod = await create_product_fixture(CreateProductFixtureDTO(locale=Language.ENG))

        trans_data = ProductTranslationCreate(
            locale=Language.GER,
            name="Deutscher Name",
            description="Deutsche Beschreibung",
        )

        response = await client_for_tests.post(
            f"/products/{prod.id}/translations",
            headers={"Authorization": f"Bearer {access_token}"},
            json=trans_data.model_dump(mode="json"),
        )
        assert response.status_code == 201

        resp_dto = ProductTranslationResponseDTO.model_validate(response.json())
        assert resp_dto.locale == Language.GER
        assert resp_dto.name == "Deutscher Name"
        assert resp_dto.description == "Deutsche Beschreibung"
        assert resp_dto.product_id == prod.id

        res = await session_db.execute(
            select(ProductTranslation).where(ProductTranslation.id == resp_dto.id)
        )
        assert res.scalar_one_or_none() is not None

    @pytest.mark.asyncio
    async def test_update_translation(
        self,
        session_db,
        client_for_tests,
        create_user_fixture,
        create_product_fixture,
    ):
        admin_user, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        prod = await create_product_fixture(CreateProductFixtureDTO(name="Original Name"))
        trans_id = prod.translations[0].id

        update_data = ProductTranslationUpdate(
            name="Updated Name",
            description="Updated Description",
        )

        response = await client_for_tests.patch(
            f"/products/translations/{trans_id}",
            headers={"Authorization": f"Bearer {access_token}"},
            json=update_data.model_dump(exclude_unset=True),
        )
        assert response.status_code == 200

        updated_dto = ProductTranslationResponseDTO.model_validate(response.json())
        assert updated_dto.name == "Updated Name"
        assert updated_dto.description == "Updated Description"

        res = await session_db.execute(
            select(ProductTranslation).where(ProductTranslation.id == trans_id)
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
        create_product_fixture,
        create_product_translation_fixture,
    ):
        admin_user, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        prod = await create_product_fixture(CreateProductFixtureDTO(locale=Language.ENG))
        extra_trans = await create_product_translation_fixture(
            CreateProductTranslationFixtureDTO(product_id=prod.id, locale=Language.GER)
        )

        response = await client_for_tests.delete(
            f"/products/translations/{extra_trans.id}",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 204

        res = await session_db.execute(
            select(ProductTranslation).where(ProductTranslation.id == extra_trans.id)
        )
        assert res.scalar_one_or_none() is None


class TestsForErrors:

    @pytest.mark.asyncio
    async def test_create_product_forbidden(
        self,
        client_for_tests,
        create_user_fixture,
        create_category_fixture,
    ):
        regular_user, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.USER)
        )
        cat = await create_category_fixture()

        create_data = ProductCreate(
            category_id=cat.id,
            slug="forbidden-product",
            index=1,
            translations=[
                ProductTranslationCreate(locale=Language.ENG, name="Test"),
            ],
        )

        response = await client_for_tests.post(
            "/products",
            headers={"Authorization": f"Bearer {access_token}"},
            json=create_data.model_dump(mode="json"),
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_create_product_unauthorized(
        self,
        client_for_tests,
    ):
        create_data = {
            "category_id": 1,
            "slug": "unauth-prod",
            "translations": [
                {"locale": "eng", "name": "Test"},
            ],
        }

        response = await client_for_tests.post(
            "/products",
            json=create_data,
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_create_product_without_translations(
        self,
        client_for_tests,
        create_user_fixture,
        create_category_fixture,
    ):
        admin_user, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        cat = await create_category_fixture()

        create_data = {
            "category_id": cat.id,
            "slug": "no-trans-prod",
            "translations": [],
        }

        response = await client_for_tests.post(
            "/products",
            headers={"Authorization": f"Bearer {access_token}"},
            json=create_data,
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_product_category_not_found(
        self,
        client_for_tests,
        create_user_fixture,
    ):
        admin_user, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )

        create_data = ProductCreate(
            category_id=99999,
            slug="orphan-product",
            translations=[
                ProductTranslationCreate(locale=Language.ENG, name="Test"),
            ],
        )

        response = await client_for_tests.post(
            "/products",
            headers={"Authorization": f"Bearer {access_token}"},
            json=create_data.model_dump(mode="json"),
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_create_product_duplicate_slug(
        self,
        client_for_tests,
        create_user_fixture,
        create_category_fixture,
        create_product_fixture,
    ):
        admin_user, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        cat = await create_category_fixture()
        await create_product_fixture(CreateProductFixtureDTO(slug="existing-prod-slug"))

        create_data = ProductCreate(
            category_id=cat.id,
            slug="existing-prod-slug",
            translations=[
                ProductTranslationCreate(locale=Language.ENG, name="Test"),
            ],
        )

        response = await client_for_tests.post(
            "/products",
            headers={"Authorization": f"Bearer {access_token}"},
            json=create_data.model_dump(mode="json"),
        )
        assert response.status_code == 409

    @pytest.mark.asyncio
    async def test_get_product_not_found(
        self,
        client_for_tests,
    ):
        response = await client_for_tests.get("/products/99999")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_product_by_slug_not_found(
        self,
        client_for_tests,
    ):
        response = await client_for_tests.get("/products/by-slug/non-existent-slug")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_product_not_found(
        self,
        client_for_tests,
        create_user_fixture,
    ):
        admin_user, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )

        response = await client_for_tests.patch(
            "/products/99999",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"slug": "new-slug"},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_product_category_not_found(
        self,
        client_for_tests,
        create_user_fixture,
        create_product_fixture,
    ):
        admin_user, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        prod = await create_product_fixture()

        response = await client_for_tests.patch(
            f"/products/{prod.id}",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"category_id": 99999},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_product_duplicate_slug(
        self,
        client_for_tests,
        create_user_fixture,
        create_product_fixture,
    ):
        admin_user, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        p1 = await create_product_fixture(CreateProductFixtureDTO(slug="slug-one"))
        p2 = await create_product_fixture(CreateProductFixtureDTO(slug="slug-two"))

        response = await client_for_tests.patch(
            f"/products/{p2.id}",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"slug": "slug-one"},
        )
        assert response.status_code == 409

    @pytest.mark.asyncio
    async def test_update_product_index_forbidden(
        self,
        client_for_tests,
        create_user_fixture,
        create_product_fixture,
    ):
        regular_user, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.USER)
        )
        prod = await create_product_fixture()

        response = await client_for_tests.patch(
            f"/products/{prod.id}/index",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"new_index": 2},
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_update_product_index_unauthorized(
        self,
        client_for_tests,
        create_product_fixture,
    ):
        prod = await create_product_fixture()

        response = await client_for_tests.patch(
            f"/products/{prod.id}/index",
            json={"new_index": 2},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_update_product_index_not_found(
        self,
        client_for_tests,
        create_user_fixture,
    ):
        admin_user, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )

        response = await client_for_tests.patch(
            "/products/99999/index",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"new_index": 2},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_product_index_validation_error(
        self,
        client_for_tests,
        create_user_fixture,
        create_product_fixture,
    ):
        admin_user, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        prod = await create_product_fixture()

        response = await client_for_tests.patch(
            f"/products/{prod.id}/index",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"new_index": -1},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_delete_product_not_found(
        self,
        client_for_tests,
        create_user_fixture,
    ):
        admin_user, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )

        response = await client_for_tests.delete(
            "/products/99999",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_product_has_dependencies_rope(
        self,
        session_db,
        client_for_tests,
        create_user_fixture,
        create_product_fixture,
        create_material_group_fixture,
        create_splice_material_fixture,
    ):
        """Попытка удаления товара, к которому привязан Product -> 400 Bad Request."""
        admin_user, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        prod = await create_product_fixture()
        mg = await create_material_group_fixture()
        sm = await create_splice_material_fixture()

        rope_prod = RopeConfiguratorSetting(
            product_id=prod.id,
            material_group_id=mg.id,
            splice_material_id=sm.id,
        )
        session_db.add(rope_prod)
        await session_db.commit()

        response = await client_for_tests.delete(
            f"/products/{prod.id}",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 400
        assert "referenced by other entities" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_delete_product_has_dependencies_image(
        self,
        session_db,
        client_for_tests,
        create_user_fixture,
        create_product_fixture,
    ):
        """Попытка удаления товара, к которому привязано изображение -> 400 Bad Request."""
        admin_user, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        prod = await create_product_fixture()

        img = ProductImage(
            product_id=prod.id,
            image_url="/media/products/photo.webp",
            index=1,
            is_main=True,
        )
        session_db.add(img)
        await session_db.commit()

        response = await client_for_tests.delete(
            f"/products/{prod.id}",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 400
        assert "referenced by other entities" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_add_translation_product_not_found(
        self,
        client_for_tests,
        create_user_fixture,
    ):
        admin_user, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )

        trans_data = ProductTranslationCreate(
            locale=Language.GER,
            name="German Name",
        )

        response = await client_for_tests.post(
            "/products/99999/translations",
            headers={"Authorization": f"Bearer {access_token}"},
            json=trans_data.model_dump(mode="json"),
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_add_translation_duplicate_locale(
        self,
        client_for_tests,
        create_user_fixture,
        create_product_fixture,
    ):
        admin_user, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        prod = await create_product_fixture(CreateProductFixtureDTO(locale=Language.ENG))

        trans_data = ProductTranslationCreate(
            locale=Language.ENG,
            name="Duplicate English",
        )

        response = await client_for_tests.post(
            f"/products/{prod.id}/translations",
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
            "/products/translations/99999",
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
            "/products/translations/99999",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_last_translation_error(
        self,
        client_for_tests,
        create_user_fixture,
        create_product_fixture,
    ):
        admin_user, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        prod = await create_product_fixture(CreateProductFixtureDTO())
        only_trans_id = prod.translations[0].id

        response = await client_for_tests.delete(
            f"/products/translations/{only_trans_id}",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 400

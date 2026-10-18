import pytest
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.modules.base.database_model import Language
from src.modules.product_images.models import ProductImage
from src.modules.rope_products.models import RopeConfiguratorSetting
from src.modules.products.models import Product, ProductTranslation, ProductType
from src.modules.products.models_dto import (
    ProductCreate,
    ProductDetailResponseDTO,
    ProductListResponseDTO,
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
from tests.modules.material_groups.fixtures.models_dto import CreateMaterialGroupFixtureDTO
from tests.modules.materials.fixtures.models_dto import CreateMaterialFixtureDTO
from tests.modules.product_application.fixtures.models_dto import (
    CreateProductApplicationFixtureDTO,
    CreateProductAssignedApplicationFixtureDTO,
)
from tests.modules.product_specification.fixtures.models_dto import (
    CreateProductSpecificationFixtureDTO,
)
from tests.modules.products.fixtures.models_dto import (
    CreateProductFixtureDTO,
    CreateProductTranslationFixtureDTO,
)
from tests.modules.rope_products.fixtures.models_dto import (
    CreateRopeProductFixtureDTO,
    CreateRopeVariantFixtureDTO,
)
from tests.modules.splice_materials.fixtures.models_dto import (
    CreateSpliceMaterialFixtureDTO,
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

        list_dto = ProductListResponseDTO.model_validate(response.json())
        data = list_dto.items
        assert list_dto.total >= 2
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

        list_dto = ProductListResponseDTO.model_validate(resp.json())
        items = list_dto.items
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

        list_dto = ProductListResponseDTO.model_validate(resp.json())
        items = list_dto.items
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

        list_dto = ProductListResponseDTO.model_validate(resp.json())
        items = list_dto.items
        ids = [i.id for i in items]
        assert p_hw.id in ids
        assert p_rope.id not in ids

    @pytest.mark.asyncio
    async def test_get_all_products_filter_by_construction_type(
        self,
        client_for_tests,
        create_product_fixture,
    ):
        p_hollow = await create_product_fixture(
            CreateProductFixtureDTO(construction_type="hollow")
        )
        p_core = await create_product_fixture(
            CreateProductFixtureDTO(construction_type="hm_core")
        )

        resp = await client_for_tests.get("/products", params={"construction_type": "hollow"})
        assert resp.status_code == 200

        list_dto = ProductListResponseDTO.model_validate(resp.json())
        items = list_dto.items
        ids = [i.id for i in items]
        assert p_hollow.id in ids
        assert p_core.id not in ids

    @pytest.mark.asyncio
    async def test_get_all_products_filter_by_material_id(
        self,
        client_for_tests,
        create_product_fixture,
        create_material_group_fixture,
        create_material_fixture,
        create_splice_material_fixture,
        create_rope_product_fixture,
    ):
        mg = await create_material_group_fixture()
        mat1 = await create_material_fixture(CreateMaterialFixtureDTO(material_group_id=mg.id))
        mat2 = await create_material_fixture(CreateMaterialFixtureDTO(material_group_id=mg.id))
        sm = await create_splice_material_fixture()

        p1 = await create_product_fixture()
        p2 = await create_product_fixture()

        await create_rope_product_fixture(
            CreateRopeProductFixtureDTO(
                product_id=p1.id,
                material_group_id=mg.id,
                material_id=mat1.id,
                splice_material_id=sm.id,
            )
        )
        await create_rope_product_fixture(
            CreateRopeProductFixtureDTO(
                product_id=p2.id,
                material_group_id=mg.id,
                material_id=mat2.id,
                splice_material_id=sm.id,
            )
        )

        resp = await client_for_tests.get("/products", params={"material_id": mat1.id})
        assert resp.status_code == 200

        list_dto = ProductListResponseDTO.model_validate(resp.json())
        items = list_dto.items
        ids = [i.id for i in items]
        assert p1.id in ids
        assert p2.id not in ids

    @pytest.mark.asyncio
    async def test_get_all_products_filter_by_application_codes(
        self,
        client_for_tests,
        create_product_fixture,
        create_product_application_fixture,
        create_product_assigned_application_fixture,
    ):
        app_winch = await create_product_application_fixture(
            CreateProductApplicationFixtureDTO(code="winch_test")
        )
        app_sheet = await create_product_application_fixture(
            CreateProductApplicationFixtureDTO(code="sheet_test")
        )

        p1 = await create_product_fixture()
        p2 = await create_product_fixture()

        await create_product_assigned_application_fixture(
            CreateProductAssignedApplicationFixtureDTO(product_id=p1.id, application_id=app_winch.id)
        )
        await create_product_assigned_application_fixture(
            CreateProductAssignedApplicationFixtureDTO(product_id=p2.id, application_id=app_sheet.id)
        )

        resp = await client_for_tests.get("/products", params={"application_codes": "winch_test"})
        assert resp.status_code == 200

        list_dto = ProductListResponseDTO.model_validate(resp.json())
        items = list_dto.items
        ids = [i.id for i in items]
        assert p1.id in ids
        assert p2.id not in ids

    @pytest.mark.asyncio
    async def test_get_all_products_filter_by_diameter(
        self,
        client_for_tests,
        create_product_fixture,
        create_rope_variant_fixture,
    ):
        p_thin = await create_product_fixture()
        p_thick = await create_product_fixture()

        await create_rope_variant_fixture(
            CreateRopeVariantFixtureDTO(product_id=p_thin.id, size_value=4.0, price=10.0)
        )
        await create_rope_variant_fixture(
            CreateRopeVariantFixtureDTO(product_id=p_thick.id, size_value=12.0, price=20.0)
        )

        resp = await client_for_tests.get("/products", params={"diameter_min": 10.0})
        assert resp.status_code == 200
        list_dto = ProductListResponseDTO.model_validate(resp.json())
        items = list_dto.items
        ids = [i.id for i in items]
        assert p_thick.id in ids
        assert p_thin.id not in ids

        resp_max = await client_for_tests.get("/products", params={"diameter_max": 6.0})
        assert resp_max.status_code == 200
        list_dto_max = ProductListResponseDTO.model_validate(resp_max.json())
        items_max = list_dto_max.items
        ids_max = [i.id for i in items_max]
        assert p_thin.id in ids_max
        assert p_thick.id not in ids_max

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
        list_active = ProductListResponseDTO.model_validate(resp_active.json())
        active_ids = [i.id for i in list_active.items]
        assert p_active.id in active_ids
        assert p_inactive.id not in active_ids

        resp_inactive = await client_for_tests.get("/products", params={"is_active": "false"})
        assert resp_inactive.status_code == 200
        list_inactive = ProductListResponseDTO.model_validate(resp_inactive.json())
        inactive_ids = [i.id for i in list_inactive.items]
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
        dto_limit = ProductListResponseDTO.model_validate(resp_limit.json())
        assert len(dto_limit.items) == 2
        assert dto_limit.total >= 3
        assert dto_limit.skip == 0
        assert dto_limit.limit == 2

        resp_skip = await client_for_tests.get("/products", params={"limit": 2, "skip": 2})
        assert resp_skip.status_code == 200
        dto_skip = ProductListResponseDTO.model_validate(resp_skip.json())
        assert len(dto_skip.items) >= 1
        assert dto_skip.skip == 2

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

        list_dto = ProductListResponseDTO.model_validate(resp.json())
        data = list_dto.items
        found = next(i for i in data if i.id == prod.id)
        assert found.name == "Schleppseil"
        assert found.description == "Schwere Ausführung"

    @pytest.mark.asyncio
    async def test_get_product_by_id(
        self,
        client_for_tests,
        create_product_fixture,
        create_product_specification_fixture,
        create_product_application_fixture,
        create_product_assigned_application_fixture,
        create_rope_variant_fixture,
    ):
        prod = await create_product_fixture(
            CreateProductFixtureDTO(slug="marine-cord", name="Marine Cord")
        )
        await create_product_specification_fixture(
            CreateProductSpecificationFixtureDTO(
                product_id=prod.id,
                name="Material",
                value="Polyester",
            )
        )
        app = await create_product_application_fixture(
            CreateProductApplicationFixtureDTO(code="sheet_app", name="Sheet")
        )
        await create_product_assigned_application_fixture(
            CreateProductAssignedApplicationFixtureDTO(
                product_id=prod.id,
                application_id=app.id,
            )
        )
        await create_rope_variant_fixture(
            CreateRopeVariantFixtureDTO(
                product_id=prod.id,
                variant_name="8 mm",
                size_value=8.0,
                price=5.50,
            )
        )

        # 1. Full Response (without locale)
        response = await client_for_tests.get(f"/products/{prod.id}")
        assert response.status_code == 200

        resp_dto = ProductResponseDTO.model_validate(response.json())
        assert resp_dto.id == prod.id
        assert resp_dto.slug == "marine-cord"
        assert len(resp_dto.translations) >= 1
        assert resp_dto.translations[0].name == "Marine Cord"
        assert len(resp_dto.specifications) == 1
        assert resp_dto.specifications[0].translations[0].name == "Material"
        assert len(resp_dto.assigned_applications) == 1
        assert resp_dto.assigned_applications[0].application is not None
        assert len(resp_dto.applications) == 1
        assert resp_dto.applications[0].code == "sheet_app"
        assert len(resp_dto.variants) == 1
        assert resp_dto.price_from == 5.50
        assert resp_dto.variants_count == 1

        # 2. Localized Response (with locale)
        loc_resp = await client_for_tests.get(f"/products/{prod.id}", params={"locale": "eng"})
        assert loc_resp.status_code == 200
        loc_dto = ProductLocalizedResponseDTO.model_validate(loc_resp.json())
        assert loc_dto.id == prod.id
        assert loc_dto.name == "Marine Cord"
        assert len(loc_dto.specifications) == 1
        assert loc_dto.specifications[0].name == "Material"
        assert loc_dto.specifications[0].value == "Polyester"
        assert len(loc_dto.applications) == 1
        assert loc_dto.applications[0].code == "sheet_app"
        assert loc_dto.price_from == 5.50
        assert loc_dto.variants_count == 1

    @pytest.mark.asyncio
    async def test_get_product_by_slug(
        self,
        client_for_tests,
        create_product_fixture,
        create_product_specification_fixture,
        create_product_application_fixture,
        create_product_assigned_application_fixture,
    ):
        prod = await create_product_fixture(
            CreateProductFixtureDTO(slug="super-line", name="Super Line")
        )
        await create_product_specification_fixture(
            CreateProductSpecificationFixtureDTO(
                product_id=prod.id,
                name="Core",
                value="Dyneema",
            )
        )
        app = await create_product_application_fixture(
            CreateProductApplicationFixtureDTO(code="halyard_app", name="Halyard")
        )
        await create_product_assigned_application_fixture(
            CreateProductAssignedApplicationFixtureDTO(
                product_id=prod.id,
                application_id=app.id,
            )
        )

        # 1. Full Response (without locale)
        response = await client_for_tests.get("/products/by-slug/super-line")
        assert response.status_code == 200

        resp_dto = ProductResponseDTO.model_validate(response.json())
        assert resp_dto.id == prod.id
        assert resp_dto.slug == "super-line"
        assert len(resp_dto.specifications) == 1
        assert len(resp_dto.applications) == 1

        # 2. Localized Response (with locale)
        loc_response = await client_for_tests.get("/products/by-slug/super-line", params={"locale": "eng"})
        assert loc_response.status_code == 200

        loc_dto = ProductLocalizedResponseDTO.model_validate(loc_response.json())
        assert loc_dto.id == prod.id
        assert loc_dto.slug == "super-line"
        assert loc_dto.name == "Super Line"
        assert len(loc_dto.specifications) == 1
        assert loc_dto.specifications[0].name == "Core"
        assert len(loc_dto.applications) == 1
        assert loc_dto.applications[0].code == "halyard_app"

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
            keys_not_checked=[
                "translations",
                "main_image_url",
                "price_from",
                "size_min",
                "size_max",
                "variants_count",
                "images",
                "specifications",
                "assigned_applications",
                "applications",
                "variants",
                "colors",
            ],
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
    async def test_delete_product_with_dependencies_rope(
        self,
        session_db,
        client_for_tests,
        create_user_fixture,
        create_product_fixture,
        create_material_group_fixture,
        create_splice_material_fixture,
    ):
        """Удаление товара, у которого есть RopeConfiguratorSetting -> 204 No Content."""
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
        assert response.status_code == 204

        res = await session_db.execute(select(Product).where(Product.id == prod.id))
        assert res.scalar_one_or_none() is None

        res_rope = await session_db.execute(
            select(RopeConfiguratorSetting).where(RopeConfiguratorSetting.product_id == prod.id)
        )
        assert res_rope.scalar_one_or_none() is None

    @pytest.mark.asyncio
    async def test_delete_product_with_dependencies_image(
        self,
        session_db,
        client_for_tests,
        create_user_fixture,
        create_product_fixture,
        config_fix,
    ):
        """Удаление товара с изображением и файлом на диске -> 204 No Content."""
        admin_user, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        prod = await create_product_fixture()

        # Создаем физический файл изображения на диске
        prod_dir = config_fix.paths.products / str(prod.id)
        prod_dir.mkdir(parents=True, exist_ok=True)
        test_file = prod_dir / "photo.webp"
        test_file.write_text("fake image content")
        assert test_file.exists()

        img = ProductImage(
            product_id=prod.id,
            image_url=f"/{config_fix.paths.media.name}/{config_fix.paths.products.name}/{prod.id}/photo.webp",
            index=1,
            is_main=True,
        )
        session_db.add(img)
        await session_db.commit()

        response = await client_for_tests.delete(
            f"/products/{prod.id}",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 204

        res = await session_db.execute(select(Product).where(Product.id == prod.id))
        assert res.scalar_one_or_none() is None

        res_img = await session_db.execute(
            select(ProductImage).where(ProductImage.product_id == prod.id)
        )
        assert res_img.scalar_one_or_none() is None

        # Проверяем, что файл и папка удалены с диска
        assert not test_file.exists()
        assert not prod_dir.exists()

    @pytest.mark.asyncio
    async def test_delete_product_with_quote_rope_item(
        self,
        session_db,
        client_for_tests,
        create_user_fixture,
        create_product_fixture,
        create_quote_request_fixture,
        create_quote_rope_item_fixture,
    ):
        """Удаление товара с позицией в заявке QuoteRopeItem -> 204, FK обнуляется (SET NULL)."""
        from src.modules.quote_requests.models import QuoteRopeItem
        from tests.modules.quote_requests.fixtures.models_dto import (
            CreateQuoteRopeItemFixtureDTO,
        )

        admin_user, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        prod = await create_product_fixture()

        qr = await create_quote_request_fixture()
        item = await create_quote_rope_item_fixture(
            quote_request_id=qr.id,
            new_item=CreateQuoteRopeItemFixtureDTO(product_id=prod.id),
        )

        response = await client_for_tests.delete(
            f"/products/{prod.id}",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 204

        res = await session_db.execute(select(Product).where(Product.id == prod.id))
        assert res.scalar_one_or_none() is None

        item_id = item.id
        expected_snapshot = item.product_name_snapshot
        session_db.expire_all()
        res_item = await session_db.execute(
            select(QuoteRopeItem).where(QuoteRopeItem.id == item_id)
        )
        db_item = res_item.scalar_one()
        assert db_item.product_id is None
        assert db_item.product_name_snapshot == expected_snapshot

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

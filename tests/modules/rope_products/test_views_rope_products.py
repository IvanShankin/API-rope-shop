import pytest
from sqlalchemy import select

from src.modules.users.models import UserRole
from tests.modules.users.fixtures.models_dto import CreateUserFixtureDTO
from tests.modules.splice_materials.fixtures.models_dto import CreateSpliceMaterialFixtureDTO
from tests.modules.colors.fixtures.models_dto import CreateColorFixtureDTO
from tests.modules.rope_product_color.fixtures.models_dto import CreateRopeProductColorFixtureDTO
from tests.modules.splice_types.fixtures.models_dto import CreateSpliceTypeFixtureDTO
from tests.modules.rope_allowed_splice.fixtures.models_dto import CreateRopeAllowedSpliceFixtureDTO
from tests.modules.rope_products.fixtures.models_dto import (
    CreateRopeProductFixtureDTO,
    CreateRopeVariantFixtureDTO,
)
from src.modules.rope_products.models import RopeConfiguratorSetting, ProductVariant
from src.modules.rope_products.models_dto import (
    RopeConfiguratorSettingCreate,
    RopeConfiguratorSettingUpdate,
    RopeConfiguratorSettingResponseDTO,
    RopeConfiguratorSettingDetailResponseDTO,
    ProductVariantCreate,
    ProductVariantCreateForProduct,
    ProductVariantUpdate,
    ProductVariantUpdateIndexDTO,
    ProductVariantResponseDTO,
)
from tests.helpers.functions import comparison_models


class TestsForSuccess:

    @pytest.mark.asyncio
    async def test_list_rope_products(
        self,
        client_for_tests,
        create_rope_product_fixture,
    ):
        """Получение списка товаров-веревок с фильтрацией."""
        p1 = await create_rope_product_fixture(CreateRopeProductFixtureDTO(can_be_spliced=True))
        p2 = await create_rope_product_fixture(CreateRopeProductFixtureDTO(can_be_spliced=False))

        response = await client_for_tests.get("/rope_products")
        assert response.status_code == 200

        data = [RopeConfiguratorSettingResponseDTO.model_validate(item) for item in response.json()]
        assert len(data) >= 2
        product_ids = [item.product_id for item in data]
        assert p1.product_id in product_ids
        assert p2.product_id in product_ids

        # Фильтр can_be_spliced=True
        resp_filtered = await client_for_tests.get("/rope_products", params={"can_be_spliced": True})
        assert resp_filtered.status_code == 200
        filtered_data = [RopeConfiguratorSettingResponseDTO.model_validate(item) for item in resp_filtered.json()]
        assert all(item.can_be_spliced is True for item in filtered_data)

    @pytest.mark.asyncio
    async def test_get_rope_product_detail(
        self,
        client_for_tests,
        create_rope_product_fixture,
        create_rope_variant_fixture,
    ):
        """Получение детальной информации о товаре со связанными сущностями."""
        product = await create_rope_product_fixture()
        var_1 = await create_rope_variant_fixture(
            CreateRopeVariantFixtureDTO(
                product_id=product.product_id,
                variant_name="8 мм",
                size_value=8.0,
                price=4.0,
                index=1,
            )
        )
        var_2 = await create_rope_variant_fixture(
            CreateRopeVariantFixtureDTO(
                product_id=product.product_id,
                variant_name="10 мм",
                size_value=10.0,
                price=5.0,
                index=2,
            )
        )

        response = await client_for_tests.get(f"/rope_products/{product.product_id}")
        assert response.status_code == 200

        data = RopeConfiguratorSettingDetailResponseDTO.model_validate(response.json())
        assert data.product_id == product.product_id
        assert len(data.variants) == 2
        assert data.variants[0].variant_name == "8 мм"
        assert float(data.variants[0].size_value) == 8.0
        assert data.variants[1].variant_name == "10 мм"
        assert float(data.variants[1].size_value) == 10.0
        assert data.splice_material is not None
        assert data.splice_material.id == product.splice_material_id

    @pytest.mark.asyncio
    async def test_create_rope_product_auto_id(
        self,
        session_db,
        client_for_tests,
        create_user_fixture,
        create_splice_material_fixture,
        create_rope_product_fixture,
    ):
        """Создание товара-веревки без указания product_id (создается автоматически)."""
        admin_user, access_token = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.ADMIN))
        dummy = await create_rope_product_fixture()

        req_data = RopeConfiguratorSettingCreate(
            material_group_id=dummy.material_group_id,
            splice_material_id=dummy.splice_material_id,
            construction="12-Strand Braid",
            can_be_spliced=True,
        )

        response = await client_for_tests.post(
            "/rope_products",
            headers={"Authorization": f"Bearer {access_token}"},
            json=req_data.model_dump(),
        )
        assert response.status_code == 201

        resp_dto = RopeConfiguratorSettingResponseDTO.model_validate(response.json())
        assert resp_dto.product_id is not None
        assert resp_dto.construction == "12-Strand Braid"
        assert resp_dto.can_be_spliced is True

        res = await session_db.execute(
            select(RopeConfiguratorSetting).where(RopeConfiguratorSetting.product_id == resp_dto.product_id)
        )
        assert res.scalar_one_or_none() is not None

    @pytest.mark.asyncio
    async def test_update_rope_product(
        self,
        session_db,
        client_for_tests,
        create_user_fixture,
        create_rope_product_fixture,
    ):
        """Обновление характеристик товара-веревки администратором."""
        admin_user, access_token = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.ADMIN))
        product = await create_rope_product_fixture()

        update_data = RopeConfiguratorSettingUpdate(
            construction="Updated Construction",
            can_be_spliced=False,
        )

        response = await client_for_tests.patch(
            f"/rope_products/{product.product_id}",
            headers={"Authorization": f"Bearer {access_token}"},
            json=update_data.model_dump(exclude_unset=True),
        )
        assert response.status_code == 200

        resp_dto = RopeConfiguratorSettingResponseDTO.model_validate(response.json())
        assert resp_dto.construction == "Updated Construction"
        assert resp_dto.can_be_spliced is False

    @pytest.mark.asyncio
    async def test_delete_rope_product(
        self,
        session_db,
        client_for_tests,
        create_user_fixture,
        create_rope_product_fixture,
    ):
        """Удаление товара-веревки администратором."""
        admin_user, access_token = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.ADMIN))
        product = await create_rope_product_fixture()

        response = await client_for_tests.delete(
            f"/rope_products/{product.product_id}",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 204

        res = await session_db.execute(
            select(RopeConfiguratorSetting).where(RopeConfiguratorSetting.product_id == product.product_id)
        )
        assert res.scalar_one_or_none() is None

    @pytest.mark.asyncio
    async def test_create_variant_auto_index(
        self,
        session_db,
        client_for_tests,
        create_user_fixture,
        create_rope_product_fixture,
    ):
        """Создание вариантов с автоприсвоением индекса (max_index + 1)."""
        admin_user, access_token = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.ADMIN))
        product = await create_rope_product_fixture()

        v1_data = ProductVariantCreateForProduct(
            variant_name="6 мм",
            size_value=6.0,
            breaking_load_dan=1200.0,
            weight_g=28.0,
            price=2.50,
        )
        res1 = await client_for_tests.post(
            f"/rope_products/{product.product_id}/variants",
            headers={"Authorization": f"Bearer {access_token}"},
            json=v1_data.model_dump(),
        )
        assert res1.status_code == 201
        dto1 = ProductVariantResponseDTO.model_validate(res1.json())
        assert dto1.index == 1
        assert dto1.variant_name == "6 мм"
        assert float(dto1.size_value) == 6.0

        v2_data = ProductVariantCreate(
            product_id=product.product_id,
            variant_name="8 мм",
            size_value=8.0,
            breaking_load_dan=2100.0,
            weight_g=45.0,
            price=3.80,
        )
        res2 = await client_for_tests.post(
            "/rope_variants",
            headers={"Authorization": f"Bearer {access_token}"},
            json=v2_data.model_dump(),
        )
        assert res2.status_code == 201
        dto2 = ProductVariantResponseDTO.model_validate(res2.json())
        assert dto2.index == 2
        assert dto2.variant_name == "8 мм"
        assert float(dto2.size_value) == 8.0

    @pytest.mark.asyncio
    async def test_list_product_variants(
        self,
        client_for_tests,
        create_rope_product_fixture,
        create_rope_variant_fixture,
    ):
        """Получение списка вариантов товара по порядку index."""
        product = await create_rope_product_fixture()
        v1 = await create_rope_variant_fixture(
            CreateRopeVariantFixtureDTO(
                product_id=product.product_id,
                variant_name="10 мм",
                size_value=10.0,
                price=5.0,
                index=1,
            )
        )
        v2 = await create_rope_variant_fixture(
            CreateRopeVariantFixtureDTO(
                product_id=product.product_id,
                variant_name="12 мм",
                size_value=12.0,
                price=6.0,
                index=2,
            )
        )

        response = await client_for_tests.get(f"/rope_products/{product.product_id}/variants")
        assert response.status_code == 200

        data = [ProductVariantResponseDTO.model_validate(item) for item in response.json()]
        assert len(data) == 2
        assert data[0].id == v1.id
        assert data[1].id == v2.id

    @pytest.mark.asyncio
    async def test_get_variant_by_id(
        self,
        client_for_tests,
        create_rope_variant_fixture,
    ):
        """Получение варианта по ID."""
        variant = await create_rope_variant_fixture()

        response = await client_for_tests.get(f"/rope_variants/{variant.id}")
        assert response.status_code == 200

        dto = ProductVariantResponseDTO.model_validate(response.json())
        assert dto.id == variant.id
        assert float(dto.size_value) == float(variant.size_value)
        assert float(dto.price) == float(variant.price)

    @pytest.mark.asyncio
    async def test_update_variant(
        self,
        client_for_tests,
        create_user_fixture,
        create_rope_variant_fixture,
    ):
        """Обновление характеристик варианта."""
        admin_user, access_token = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.ADMIN))
        variant = await create_rope_variant_fixture(
            CreateRopeVariantFixtureDTO(
                variant_name="10 мм",
                size_value=10.0,
                price=5.0,
            )
        )

        update_data = ProductVariantUpdate(price=6.50, is_active=False)
        response = await client_for_tests.patch(
            f"/rope_variants/{variant.id}",
            headers={"Authorization": f"Bearer {access_token}"},
            json=update_data.model_dump(exclude_unset=True),
        )
        assert response.status_code == 200

        dto = ProductVariantResponseDTO.model_validate(response.json())
        assert float(dto.price) == 6.50
        assert dto.is_active is False

    @pytest.mark.asyncio
    async def test_reorder_variant(
        self,
        client_for_tests,
        create_user_fixture,
        create_rope_product_fixture,
        create_rope_variant_fixture,
    ):
        """Перемещение варианта с пересчетом индексов соседей."""
        admin_user, access_token = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.ADMIN))
        product = await create_rope_product_fixture()
        v1 = await create_rope_variant_fixture(
            CreateRopeVariantFixtureDTO(
                product_id=product.product_id,
                variant_name="6 мм",
                size_value=6.0,
                price=3.0,
                index=1,
            )
        )
        v2 = await create_rope_variant_fixture(
            CreateRopeVariantFixtureDTO(
                product_id=product.product_id,
                variant_name="8 мм",
                size_value=8.0,
                price=4.0,
                index=2,
            )
        )
        v3 = await create_rope_variant_fixture(
            CreateRopeVariantFixtureDTO(
                product_id=product.product_id,
                variant_name="10 мм",
                size_value=10.0,
                price=5.0,
                index=3,
            )
        )

        # Перемещаем v3 на позицию 1
        response = await client_for_tests.patch(
            f"/rope_variants/{v3.id}/index",
            headers={"Authorization": f"Bearer {access_token}"},
            json=ProductVariantUpdateIndexDTO(new_index=1).model_dump(),
        )
        assert response.status_code == 200

        resp_list = await client_for_tests.get(f"/rope_products/{product.product_id}/variants")
        variants = [ProductVariantResponseDTO.model_validate(i) for i in resp_list.json()]
        assert variants[0].id == v3.id
        assert variants[0].index == 1
        assert variants[1].id == v1.id
        assert variants[1].index == 2
        assert variants[2].id == v2.id
        assert variants[2].index == 3

    @pytest.mark.asyncio
    async def test_delete_variant_collapses_indexes(
        self,
        client_for_tests,
        create_user_fixture,
        create_rope_product_fixture,
        create_rope_variant_fixture,
    ):
        """Удаление варианта со сдвигом последующих индексов без пробелов."""
        admin_user, access_token = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.ADMIN))
        product = await create_rope_product_fixture()
        v1 = await create_rope_variant_fixture(
            CreateRopeVariantFixtureDTO(
                product_id=product.product_id,
                variant_name="6 мм",
                size_value=6.0,
                price=3.0,
                index=1,
            )
        )
        v2 = await create_rope_variant_fixture(
            CreateRopeVariantFixtureDTO(
                product_id=product.product_id,
                variant_name="8 мм",
                size_value=8.0,
                price=4.0,
                index=2,
            )
        )
        v3 = await create_rope_variant_fixture(
            CreateRopeVariantFixtureDTO(
                product_id=product.product_id,
                variant_name="10 мм",
                size_value=10.0,
                price=5.0,
                index=3,
            )
        )

        # Удаляем v2 (индекс 2)
        response = await client_for_tests.delete(
            f"/rope_variants/{v2.id}",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 204

        resp_list = await client_for_tests.get(f"/rope_products/{product.product_id}/variants")
        variants = [ProductVariantResponseDTO.model_validate(i) for i in resp_list.json()]
        assert len(variants) == 2
        assert variants[0].id == v1.id
        assert variants[0].index == 1
        assert variants[1].id == v3.id
        assert variants[1].index == 2


class TestsForFailures:

    @pytest.mark.asyncio
    async def test_create_rope_product_unauthorized(
        self,
        client_for_tests,
        create_rope_product_fixture,
    ):
        """Создание без токена -> 401."""
        dummy = await create_rope_product_fixture()
        req_data = RopeConfiguratorSettingCreate(
            material_group_id=dummy.material_group_id,
            splice_material_id=dummy.splice_material_id,
        )
        response = await client_for_tests.post("/rope_products", json=req_data.model_dump())
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_create_rope_product_forbidden(
        self,
        client_for_tests,
        create_user_fixture,
        create_rope_product_fixture,
    ):
        """Создание обычным юзером -> 403."""
        user, access_token = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.USER))
        dummy = await create_rope_product_fixture()
        req_data = RopeConfiguratorSettingCreate(
            material_group_id=dummy.material_group_id,
            splice_material_id=dummy.splice_material_id,
        )
        response = await client_for_tests.post(
            "/rope_products",
            headers={"Authorization": f"Bearer {access_token}"},
            json=req_data.model_dump(),
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_create_rope_product_already_exists(
        self,
        client_for_tests,
        create_user_fixture,
        create_rope_product_fixture,
    ):
        """Создание с уже занятым product_id -> 409."""
        admin_user, access_token = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.ADMIN))
        dummy = await create_rope_product_fixture()

        req_data = RopeConfiguratorSettingCreate(
            product_id=dummy.product_id,
            material_group_id=dummy.material_group_id,
            splice_material_id=dummy.splice_material_id,
        )
        response = await client_for_tests.post(
            "/rope_products",
            headers={"Authorization": f"Bearer {access_token}"},
            json=req_data.model_dump(),
        )
        assert response.status_code == 409

    @pytest.mark.asyncio
    async def test_create_rope_product_material_group_not_found(
        self,
        client_for_tests,
        create_user_fixture,
        create_rope_product_fixture,
    ):
        """Создание с несуществующей material_group_id -> 404."""
        admin_user, access_token = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.ADMIN))
        dummy = await create_rope_product_fixture()

        req_data = RopeConfiguratorSettingCreate(
            material_group_id=999999,
            splice_material_id=dummy.splice_material_id,
        )
        response = await client_for_tests.post(
            "/rope_products",
            headers={"Authorization": f"Bearer {access_token}"},
            json=req_data.model_dump(),
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_rope_product_not_found(
        self,
        client_for_tests,
    ):
        """Запрос несуществующего товара -> 404."""
        response = await client_for_tests.get("/rope_products/999999")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_rope_product_has_dependencies_variant(
        self,
        client_for_tests,
        create_user_fixture,
        create_rope_product_fixture,
        create_rope_variant_fixture,
    ):
        """Попытка удаления товара-веревки с привязанными вариантами -> 400 Bad Request."""
        admin_user, access_token = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.ADMIN))
        product = await create_rope_product_fixture()
        await create_rope_variant_fixture(
            CreateRopeVariantFixtureDTO(product_id=product.product_id)
        )

        response = await client_for_tests.delete(
            f"/rope_products/{product.product_id}",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 400
        assert "associated variants, colors, or splices" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_delete_rope_product_has_dependencies_color(
        self,
        client_for_tests,
        create_user_fixture,
        create_rope_product_fixture,
        create_color_fixture,
        create_rope_product_color_fixture,
    ):
        """Попытка удаления товара-веревки с привязанными цветами -> 400 Bad Request."""
        admin_user, access_token = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.ADMIN))
        product = await create_rope_product_fixture()
        color = await create_color_fixture(CreateColorFixtureDTO())
        await create_rope_product_color_fixture(
            CreateRopeProductColorFixtureDTO(
                product_id=product.product_id,
                color_id=color.id,
            )
        )

        response = await client_for_tests.delete(
            f"/rope_products/{product.product_id}",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 400
        assert "associated variants, colors, or splices" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_delete_rope_product_has_dependencies_splice(
        self,
        client_for_tests,
        create_user_fixture,
        create_rope_product_fixture,
        create_splice_type_fixture,
        create_rope_allowed_splice_fixture,
    ):
        """Попытка удаления товара-веревки с разрешенными типами сращивания -> 400 Bad Request."""
        admin_user, access_token = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.ADMIN))
        product = await create_rope_product_fixture()
        splice_type = await create_splice_type_fixture(CreateSpliceTypeFixtureDTO())
        await create_rope_allowed_splice_fixture(
            CreateRopeAllowedSpliceFixtureDTO(
                product_id=product.product_id,
                splice_type_id=splice_type.id,
            )
        )

        response = await client_for_tests.delete(
            f"/rope_products/{product.product_id}",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 400
        assert "associated variants, colors, or splices" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_create_variant_duplicate_diameter(
        self,
        client_for_tests,
        create_user_fixture,
        create_rope_product_fixture,
        create_rope_variant_fixture,
    ):
        """Попытка создания дубликата размера для той же веревки -> 409."""
        admin_user, access_token = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.ADMIN))
        product = await create_rope_product_fixture()
        await create_rope_variant_fixture(
            CreateRopeVariantFixtureDTO(
                product_id=product.product_id,
                variant_name="10 мм",
                size_value=10.0,
                price=5.0,
            )
        )

        req_data = ProductVariantCreate(
            product_id=product.product_id,
            variant_name="10 мм",
            size_value=10.0,
            price=6.0,
        )
        response = await client_for_tests.post(
            "/rope_variants",
            headers={"Authorization": f"Bearer {access_token}"},
            json=req_data.model_dump(),
        )
        assert response.status_code == 409

    @pytest.mark.asyncio
    async def test_get_variant_not_found(
        self,
        client_for_tests,
    ):
        """Запрос несуществующего варианта -> 404."""
        response = await client_for_tests.get("/rope_variants/999999")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_variant_not_found(
        self,
        client_for_tests,
        create_user_fixture,
    ):
        """Удаление несуществующего варианта -> 404."""
        admin_user, access_token = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.ADMIN))
        response = await client_for_tests.delete(
            "/rope_variants/999999",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 404

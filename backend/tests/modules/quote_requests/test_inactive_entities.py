import pytest
from src.modules.base.database_model import Language
from src.modules.quote_requests.models import ConfiguratorType
from src.modules.quote_requests.models_dto import QuoteRequestCreate, QuoteRopeItemCreate
from tests.modules.configurator_setting.fixtures.models_dto import CreateConfiguratorSettingFixtureDTO
from tests.modules.splice_materials.fixtures.models_dto import CreateSpliceMaterialFixtureDTO
from tests.modules.material_groups.fixtures.models_dto import CreateMaterialGroupFixtureDTO
from tests.modules.colors.fixtures.models_dto import CreateColorFixtureDTO
from tests.modules.splice_types.fixtures.models_dto import CreateSpliceTypeFixtureDTO
from tests.modules.splice_prices.fixtures.models_dto import CreateSplicePriceRuleFixtureDTO
from tests.modules.rope_products.fixtures.models_dto import (
    CreateRopeProductFixtureDTO,
    CreateRopeVariantFixtureDTO,
)
from tests.modules.rope_product_color.fixtures.models_dto import CreateRopeProductColorFixtureDTO
from tests.modules.rope_allowed_splice.fixtures.models_dto import CreateRopeAllowedSpliceFixtureDTO


@pytest.mark.asyncio
async def test_quote_request_rejects_inactive_variant(
    client_for_tests,
    create_configurator_setting_fixture,
    create_splice_material_fixture,
    create_material_group_fixture,
    create_color_fixture,
    create_splice_type_fixture,
    create_rope_product_fixture,
    create_rope_variant_fixture,
    create_rope_product_color_fixture,
    create_rope_allowed_splice_fixture,
    create_splice_price_rule_fixture,
):
    await create_configurator_setting_fixture(CreateConfiguratorSettingFixtureDTO())
    splice_mat = await create_splice_material_fixture(CreateSpliceMaterialFixtureDTO())
    mat_group = await create_material_group_fixture(CreateMaterialGroupFixtureDTO())
    color = await create_color_fixture(CreateColorFixtureDTO())
    splice = await create_splice_type_fixture(CreateSpliceTypeFixtureDTO())

    product = await create_rope_product_fixture(
        CreateRopeProductFixtureDTO(
            material_group_id=mat_group.id,
            splice_material_id=splice_mat.id,
            can_be_spliced=True,
        )
    )

    # Inactive variant
    await create_rope_variant_fixture(
        CreateRopeVariantFixtureDTO(
            product_id=product.product_id,
            variant_name="10 мм",
            size_value=10.0,
            price=4.50,
            is_active=False,
        )
    )

    await create_rope_product_color_fixture(
        CreateRopeProductColorFixtureDTO(
            product_id=product.product_id,
            color_id=color.id,
        )
    )

    await create_rope_allowed_splice_fixture(
        CreateRopeAllowedSpliceFixtureDTO(
            product_id=product.product_id,
            splice_type_id=splice.id,
        )
    )

    await create_splice_price_rule_fixture(
        CreateSplicePriceRuleFixtureDTO(
            splice_type_id=splice.id,
            splice_material_id=splice_mat.id,
            diameter_from_mm=8.0,
            diameter_to_mm=12.0,
            price=20.00,
        )
    )

    payload = {
        "configurator_type": "rope_with_splice",
        "name": "Test Customer",
        "email": "customer@example.com",
        "locale": "ger",
        "rope_items": [
            {
                "product_id": product.product_id,
                "color_id": color.id,
                "diameter_mm": 10.0,
                "length_m": 5.0,
                "quantity": 1,
            }
        ],
    }

    response = await client_for_tests.post("/quote_requests", json=payload)
    assert response.status_code == 400
    assert "inactive" in response.json()["detail"].lower()

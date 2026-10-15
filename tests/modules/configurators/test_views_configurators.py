import pytest

from src.modules.base.database_model import Language
from src.modules.quote_requests.models import ConfiguratorType
from src.modules.configurator_extra.models import BillingType
from src.modules.splice_types.models import SpliceCategory
from src.modules.configurators.models_dto import ConfiguratorDataResponseDTO
from tests.modules.configurator_setting.fixtures.models_dto import CreateConfiguratorSettingFixtureDTO
from tests.modules.configurator_extra.fixtures.models_dto import (
    CreateConfiguratorExtraFixtureDTO,
    CreateConfiguratorExtraTranslationFixtureDTO,
)
from tests.modules.splice_materials.fixtures.models_dto import CreateSpliceMaterialFixtureDTO
from tests.modules.splice_types.fixtures.models_dto import (
    CreateSpliceTypeFixtureDTO,
    CreateSpliceTypeTranslationFixtureDTO,
)
from tests.modules.splice_prices.fixtures.models_dto import CreateSplicePriceRuleFixtureDTO
from tests.modules.material_groups.fixtures.models_dto import CreateMaterialGroupFixtureDTO
from tests.modules.colors.fixtures.models_dto import CreateColorFixtureDTO
from tests.modules.rope_products.fixtures.models_dto import (
    CreateRopeProductFixtureDTO,
    CreateRopeVariantFixtureDTO,
)
from tests.modules.rope_product_color.fixtures.models_dto import CreateRopeProductColorFixtureDTO
from tests.modules.rope_allowed_splice.fixtures.models_dto import CreateRopeAllowedSpliceFixtureDTO


class TestsForSuccess:

    @pytest.mark.asyncio
    async def test_get_configurators_empty_db(
        self,
        client_for_tests,
    ):
        """Эндпоинт успешно отрабатывает при пустом каталоге, возвращая валидную DTO схему."""
        response = await client_for_tests.get("/configurators")
        assert response.status_code == 200

        data = response.json()
        dto = ConfiguratorDataResponseDTO.model_validate(data)
        assert dto.configurator_type is None
        assert dto.locale == Language.ENG
        assert dto.extras == []
        assert dto.splice_materials == []
        assert dto.splice_types == []
        assert dto.splice_price_rules == []
        assert dto.rope_products == []

    @pytest.mark.asyncio
    async def test_get_configurators_all_data(
        self,
        client_for_tests,
        create_configurator_setting_fixture,
        create_configurator_extra_fixture,
        create_splice_material_fixture,
        create_splice_type_fixture,
        create_splice_price_rule_fixture,
        create_material_group_fixture,
        create_color_fixture,
        create_rope_product_fixture,
        create_rope_variant_fixture,
        create_rope_product_color_fixture,
        create_rope_allowed_splice_fixture,
    ):
        """Без передачи configurator_type отдается полный сводный пакет всех сущностей и настроек."""
        # Настройки
        await create_configurator_setting_fixture(
            CreateConfiguratorSettingFixtureDTO(min_length_m=5.0, max_length_m=500.0)
        )

        # Доп. опция
        await create_configurator_extra_fixture(
            CreateConfiguratorExtraFixtureDTO(
                code="CERTIFICATE",
                name="Certificate of Conformity",
                price=15.0,
                billing_type=BillingType.FIXED,
            )
        )

        # Материал заделки
        mat = await create_splice_material_fixture(
            CreateSpliceMaterialFixtureDTO(code="dyneema", name="Dyneema High-Tech")
        )

        # Типы заделок (LOOP и SPLICE)
        st_loop = await create_splice_type_fixture(
            CreateSpliceTypeFixtureDTO(
                code="aug_splice",
                name="Eye Splice",
                category=SpliceCategory.LOOP,
            )
        )
        st_splice = await create_splice_type_fixture(
            CreateSpliceTypeFixtureDTO(
                code="endless",
                name="Endless Splice",
                category=SpliceCategory.SPLICE,
            )
        )

        # Правила цен
        await create_splice_price_rule_fixture(
            CreateSplicePriceRuleFixtureDTO(
                splice_type_id=st_loop.id,
                splice_material_id=mat.id,
                diameter_from_mm=8.0,
                diameter_to_mm=12.0,
                price=25.0,
            )
        )
        await create_splice_price_rule_fixture(
            CreateSplicePriceRuleFixtureDTO(
                splice_type_id=st_splice.id,
                splice_material_id=mat.id,
                diameter_from_mm=8.0,
                diameter_to_mm=12.0,
                price=35.0,
            )
        )

        # Канат с вариантом, цветом и заделкой
        mg = await create_material_group_fixture(
            CreateMaterialGroupFixtureDTO(code="polyester", name="Polyester Group")
        )

        color = await create_color_fixture(
            CreateColorFixtureDTO(code="navy_blue", name="Navy Blue", hex="#000080")
        )

        rope = await create_rope_product_fixture(
            CreateRopeProductFixtureDTO(
                material_group_id=mg.id,
                splice_material_id=mat.id,
                construction="12-strand braided",
            )
        )
        await create_rope_variant_fixture(
            CreateRopeVariantFixtureDTO(
                product_id=rope.product_id,
                variant_name="10 мм",
                size_value=10.0,
                price=3.5,
            )
        )
        await create_rope_product_color_fixture(
            CreateRopeProductColorFixtureDTO(product_id=rope.product_id, color_id=color.id)
        )
        await create_rope_allowed_splice_fixture(
            CreateRopeAllowedSpliceFixtureDTO(product_id=rope.product_id, splice_type_id=st_loop.id)
        )

        # Вызов API
        response = await client_for_tests.get("/configurators")
        assert response.status_code == 200

        dto = ConfiguratorDataResponseDTO.model_validate(response.json())
        assert dto.configurator_type is None
        assert dto.settings is not None
        assert dto.settings.min_length_m == 5.0
        assert len(dto.extras) == 1
        assert dto.extras[0].name == "Certificate of Conformity"
        assert len(dto.splice_materials) == 1
        assert dto.splice_materials[0].code == "dyneema"
        assert len(dto.splice_types) == 2
        assert len(dto.splice_price_rules) == 2
        assert dto.rope_products is not None
        assert len(dto.rope_products) == 1
        assert dto.rope_products[0].construction == "12-strand braided"
        assert dto.rope_products[0].material_group_name == "Polyester Group"
        assert len(dto.rope_products[0].variants) == 1
        assert dto.rope_products[0].variants[0].variant_name == "10 мм"
        assert float(dto.rope_products[0].variants[0].size_value) == 10.0
        assert len(dto.rope_products[0].colors) == 1
        assert dto.rope_products[0].colors[0].color.name == "Navy Blue"
        assert len(dto.rope_products[0].allowed_splices) == 1
        assert dto.rope_products[0].allowed_splices[0].splice_type.name == "Eye Splice"

    @pytest.mark.asyncio
    async def test_get_configurators_filter_rope_with_splice(
        self,
        client_for_tests,
        create_configurator_setting_fixture,
        create_configurator_extra_fixture,
        create_splice_material_fixture,
        create_splice_type_fixture,
        create_material_group_fixture,
        create_rope_product_fixture,
        create_rope_variant_fixture,
    ):
        """Фильтр rope_with_splice возвращает канатный каталог и полный список опций."""
        await create_configurator_setting_fixture(CreateConfiguratorSettingFixtureDTO())
        await create_configurator_extra_fixture(
            CreateConfiguratorExtraFixtureDTO(
                code="PER_M_EXTRA",
                name="Coating per meter",
                billing_type=BillingType.PER_METER,
                price=0.5,
            )
        )

        mat = await create_splice_material_fixture(CreateSpliceMaterialFixtureDTO())
        await create_splice_type_fixture(
            CreateSpliceTypeFixtureDTO(name="Loop", category=SpliceCategory.LOOP)
        )

        mg = await create_material_group_fixture(CreateMaterialGroupFixtureDTO())
        rope = await create_rope_product_fixture(
            CreateRopeProductFixtureDTO(material_group_id=mg.id, splice_material_id=mat.id)
        )
        await create_rope_variant_fixture(
            CreateRopeVariantFixtureDTO(
                product_id=rope.product_id,
                variant_name="8 мм",
                size_value=8.0,
                price=2.0,
            )
        )

        response = await client_for_tests.get("/configurators?configurator_type=rope_with_splice")
        assert response.status_code == 200

        dto = ConfiguratorDataResponseDTO.model_validate(response.json())
        assert dto.configurator_type == ConfiguratorType.ROPE_WITH_SPLICE
        assert len(dto.extras) == 1
        assert dto.extras[0].code == "PER_M_EXTRA"
        assert dto.rope_products is not None
        assert len(dto.rope_products) == 1

    @pytest.mark.asyncio
    async def test_get_configurators_filter_loop_only(
        self,
        client_for_tests,
        create_configurator_extra_fixture,
        create_splice_material_fixture,
        create_splice_type_fixture,
        create_splice_price_rule_fixture,
        create_material_group_fixture,
        create_rope_product_fixture,
    ):
        """
        Фильтр loop_only:
        - Возвращает только типы заделок категории LOOP.
        - Исключает опции с типом BillingType.PER_METER.
        - Поле rope_products равно None (клиент заказывает петли на свой канат).
        """
        # 1 опция FIXED, 1 опция PER_METER
        await create_configurator_extra_fixture(
            CreateConfiguratorExtraFixtureDTO(
                code="PACKAGING",
                name="Eco Packaging",
                billing_type=BillingType.FIXED,
                price=5.0,
            )
        )
        await create_configurator_extra_fixture(
            CreateConfiguratorExtraFixtureDTO(
                code="COATING",
                name="Coating",
                billing_type=BillingType.PER_METER,
                price=1.0,
            )
        )

        mat = await create_splice_material_fixture(CreateSpliceMaterialFixtureDTO())

        st_loop = await create_splice_type_fixture(
            CreateSpliceTypeFixtureDTO(code="eye_loop", name="Eye Loop", category=SpliceCategory.LOOP)
        )
        st_splice = await create_splice_type_fixture(
            CreateSpliceTypeFixtureDTO(code="endless_splice", name="Endless", category=SpliceCategory.SPLICE)
        )

        await create_splice_price_rule_fixture(
            CreateSplicePriceRuleFixtureDTO(splice_type_id=st_loop.id, splice_material_id=mat.id, price=20.0)
        )
        await create_splice_price_rule_fixture(
            CreateSplicePriceRuleFixtureDTO(splice_type_id=st_splice.id, splice_material_id=mat.id, price=30.0)
        )

        # Создаем канат (не должен попасть в ответ)
        mg = await create_material_group_fixture(CreateMaterialGroupFixtureDTO())
        await create_rope_product_fixture(
            CreateRopeProductFixtureDTO(material_group_id=mg.id, splice_material_id=mat.id)
        )

        response = await client_for_tests.get("/configurators?configurator_type=loop_only")
        assert response.status_code == 200

        dto = ConfiguratorDataResponseDTO.model_validate(response.json())
        assert dto.configurator_type == ConfiguratorType.LOOP_ONLY
        assert dto.rope_products is None

        # Проверка опций: только FIXED остался, PER_METER отфильтрован
        assert len(dto.extras) == 1
        assert dto.extras[0].code == "PACKAGING"

        # Проверка типов заделок: только LOOP
        assert len(dto.splice_types) == 1
        assert dto.splice_types[0].category == SpliceCategory.LOOP
        assert dto.splice_types[0].code == "eye_loop"

        # Проверка матрицы цен: только правила для LOOP
        assert len(dto.splice_price_rules) == 1
        assert dto.splice_price_rules[0].splice_type_id == st_loop.id

    @pytest.mark.asyncio
    async def test_get_configurators_filter_splice_only(
        self,
        client_for_tests,
        create_splice_material_fixture,
        create_splice_type_fixture,
        create_splice_price_rule_fixture,
    ):
        """Фильтр splice_only возвращает только услуги категории SPLICE и правила для них."""
        mat = await create_splice_material_fixture(CreateSpliceMaterialFixtureDTO())

        st_loop = await create_splice_type_fixture(
            CreateSpliceTypeFixtureDTO(code="eye_loop_2", name="Eye Loop", category=SpliceCategory.LOOP)
        )
        st_splice = await create_splice_type_fixture(
            CreateSpliceTypeFixtureDTO(code="takling_2", name="Takling", category=SpliceCategory.SPLICE)
        )

        await create_splice_price_rule_fixture(
            CreateSplicePriceRuleFixtureDTO(splice_type_id=st_loop.id, splice_material_id=mat.id, price=15.0)
        )
        await create_splice_price_rule_fixture(
            CreateSplicePriceRuleFixtureDTO(splice_type_id=st_splice.id, splice_material_id=mat.id, price=2.5)
        )

        response = await client_for_tests.get("/configurators?configurator_type=splice_only")
        assert response.status_code == 200

        dto = ConfiguratorDataResponseDTO.model_validate(response.json())
        assert dto.configurator_type == ConfiguratorType.SPLICE_ONLY
        assert dto.rope_products is None

        assert len(dto.splice_types) == 1
        assert dto.splice_types[0].category == SpliceCategory.SPLICE
        assert dto.splice_types[0].code == "takling_2"

        assert len(dto.splice_price_rules) == 1
        assert dto.splice_price_rules[0].splice_type_id == st_splice.id

    @pytest.mark.asyncio
    async def test_get_configurators_localization(
        self,
        client_for_tests,
        create_configurator_extra_fixture,
        create_configurator_extra_translation_fixture,
        create_splice_type_fixture,
        create_splice_type_translation_fixture,
    ):
        """Проверка локализации: при запросе с locale=rus или locale=ger отдаются соответствующие переводы."""
        extra = await create_configurator_extra_fixture(
            CreateConfiguratorExtraFixtureDTO(code="WARRANTY", name="Extended Warranty")
        )
        await create_configurator_extra_translation_fixture(
            CreateConfiguratorExtraTranslationFixtureDTO(
                extra_id=extra.id,
                locale=Language.RUS,
                name="Расширенная гарантия",
            )
        )

        splice_type = await create_splice_type_fixture(
            CreateSpliceTypeFixtureDTO(code="leather_prot", name="Leather Protection")
        )
        await create_splice_type_translation_fixture(
            CreateSpliceTypeTranslationFixtureDTO(
                splice_type_id=splice_type.id,
                locale=Language.RUS,
                name="Кожаный протектор",
            )
        )

        # Запрос на русском языке
        resp_rus = await client_for_tests.get("/configurators?locale=rus")
        assert resp_rus.status_code == 200
        dto_rus = ConfiguratorDataResponseDTO.model_validate(resp_rus.json())
        assert dto_rus.locale == Language.RUS

        extra_rus = next(e for e in dto_rus.extras if e.id == extra.id)
        assert extra_rus.name == "Расширенная гарантия"

        st_rus = next(s for s in dto_rus.splice_types if s.id == splice_type.id)
        assert st_rus.name == "Кожаный протектор"

        # Запрос на немецком языке (fallback на код или английский если нет немецкого)
        resp_ger = await client_for_tests.get("/configurators?locale=ger")
        assert resp_ger.status_code == 200
        dto_ger = ConfiguratorDataResponseDTO.model_validate(resp_ger.json())
        assert dto_ger.locale == Language.GER
        extra_ger = next(e for e in dto_ger.extras if e.id == extra.id)
        assert extra_ger.name == "Extended Warranty"

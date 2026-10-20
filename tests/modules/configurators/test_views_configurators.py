import pytest

from src.core.config import Config
from src.modules.base.database_model import Language
from src.modules.quote_requests.models import ConfiguratorType
from src.modules.configurator_extra.models import BillingType
from src.modules.splice_types.models import SpliceCategory
from src.modules.configurators.models_dto import (
    ConfiguratorDataResponseDTO,
    SplicePriceCalculationResponseDTO,
)
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
from tests.modules.products.fixtures.models_dto import (
    CreateProductFixtureDTO,
    CreateProductTranslationFixtureDTO,
)
from tests.modules.product_images.fixtures.models_dto import CreateProductImageFixtureDTO


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

    @pytest.mark.asyncio
    async def test_get_configurators_rope_product_name_and_image_localization(
        self,
        client_for_tests,
        create_product_fixture,
        create_product_translation_fixture,
        create_product_image_fixture,
        create_material_group_fixture,
        create_splice_material_fixture,
        create_rope_product_fixture,
        config_fix: Config,
    ):
        """Проверка наличия name, slug, main_image_url, subtitle и их корректной локализации в ConfiguratorRopeProductResponseDTO."""
        mg = await create_material_group_fixture(CreateMaterialGroupFixtureDTO(name="Dyneema Group"))
        sm = await create_splice_material_fixture(CreateSpliceMaterialFixtureDTO(code="core"))

        # Создаем продукт с английским переводом (по умолчанию)
        prod = await create_product_fixture(
            CreateProductFixtureDTO(
                slug="magic-race-rope",
                name="Magic Race EN",
                subtitle="High performance EN",
                locale=Language.ENG,
            )
        )

        # Добавляем русский перевод
        await create_product_translation_fixture(
            CreateProductTranslationFixtureDTO(
                product_id=prod.id,
                locale=Language.RUS,
                name="Мэджик Рейс РУ",
                subtitle="Высокая прочность РУ",
            )
        )

        # Добавляем немецкий перевод
        await create_product_translation_fixture(
            CreateProductTranslationFixtureDTO(
                product_id=prod.id,
                locale=Language.GER,
                name="Magic Race DE",
                subtitle="Hochleistung DE",
            )
        )

        test_image_url = f"/{config_fix.paths.media.name}/{config_fix.paths.products.name}/{prod.id}/magic_race.webp"

        # Добавляем главное изображение к продукту
        await create_product_image_fixture(
            CreateProductImageFixtureDTO(
                product_id=prod.id,
                image_url=test_image_url,
                is_main=True,
                is_active=True,
            )
        )

        # Привязываем канат к конфигуратору
        await create_rope_product_fixture(
            CreateRopeProductFixtureDTO(
                product_id=prod.id,
                material_group_id=mg.id,
                splice_material_id=sm.id,
                construction="12-strand braided",
            )
        )

        # 1. Запрос с русской локалью
        resp_rus = await client_for_tests.get("/configurators?locale=rus")
        assert resp_rus.status_code == 200
        dto_rus = ConfiguratorDataResponseDTO.model_validate(resp_rus.json())
        assert dto_rus.rope_products is not None
        assert len(dto_rus.rope_products) == 1
        rope_rus = dto_rus.rope_products[0]
        assert rope_rus.product_id == prod.id
        assert rope_rus.name == "Мэджик Рейс РУ"
        assert rope_rus.subtitle == "Высокая прочность РУ"
        assert rope_rus.slug == "magic-race-rope"
        assert rope_rus.main_image_url == test_image_url

        # 2. Запрос с немецкой локалью
        resp_ger = await client_for_tests.get("/configurators?locale=ger")
        assert resp_ger.status_code == 200
        dto_ger = ConfiguratorDataResponseDTO.model_validate(resp_ger.json())
        assert dto_ger.rope_products is not None
        rope_ger = dto_ger.rope_products[0]
        assert rope_ger.name == "Magic Race DE"
        assert rope_ger.subtitle == "Hochleistung DE"
        assert rope_ger.slug == "magic-race-rope"
        assert rope_ger.main_image_url == test_image_url

        # 3. Запрос с английской локалью (по умолчанию)
        resp_eng = await client_for_tests.get("/configurators")
        assert resp_eng.status_code == 200
        dto_eng = ConfiguratorDataResponseDTO.model_validate(resp_eng.json())
        assert dto_eng.rope_products is not None
        rope_eng = dto_eng.rope_products[0]
        assert rope_eng.name == "Magic Race EN"
        assert rope_eng.subtitle == "High performance EN"
        assert rope_eng.slug == "magic-race-rope"
        assert rope_eng.main_image_url == test_image_url

    @pytest.mark.asyncio
    async def test_calculate_splice_price_success(
        self,
        client_for_tests,
        create_splice_material_fixture,
        create_splice_type_fixture,
        create_splice_price_rule_fixture,
    ):
        """Расчет стоимости заделки по material_id, splice_type_id и diameter_mm."""
        sm = await create_splice_material_fixture(CreateSpliceMaterialFixtureDTO(code="core_calc"))
        st = await create_splice_type_fixture(CreateSpliceTypeFixtureDTO(code="eye_splice_calc"))
        await create_splice_price_rule_fixture(
            CreateSplicePriceRuleFixtureDTO(
                splice_material_id=sm.id,
                splice_type_id=st.id,
                diameter_from_mm=4.0,
                diameter_to_mm=8.0,
                price=32.50,
            )
        )

        resp = await client_for_tests.get(
            "/configurators/price",
            params={
                "material_id": sm.id,
                "splice_type_id": st.id,
                "diameter_mm": 6.0,
            },
        )
        assert resp.status_code == 200
        dto = SplicePriceCalculationResponseDTO.model_validate(resp.json())
        assert dto.price == 32.50
        assert dto.currency == "EUR"
        assert dto.material_id == sm.id
        assert dto.splice_type_id == st.id
        assert dto.diameter_mm == 6.0

    @pytest.mark.asyncio
    async def test_calculate_splice_price_not_found(
        self,
        client_for_tests,
        create_splice_material_fixture,
        create_splice_type_fixture,
    ):
        """Если подходящее правило не найдено, возвращается ошибка."""
        sm = await create_splice_material_fixture(CreateSpliceMaterialFixtureDTO(code="mat_unmatched"))
        st = await create_splice_type_fixture(CreateSpliceTypeFixtureDTO(code="type_unmatched"))

        resp = await client_for_tests.get(
            "/configurators/price",
            params={
                "material_id": sm.id,
                "splice_type_id": st.id,
                "diameter_mm": 50.0,
            },
        )
        assert resp.status_code in (400, 404)


    @pytest.mark.asyncio
    async def test_get_configurator_excludes_inactive_color_and_splice_and_variant(
        self,
        client_for_tests,
        create_material_group_fixture,
        create_splice_material_fixture,
        create_color_fixture,
        create_splice_type_fixture,
        create_rope_product_fixture,
        create_rope_variant_fixture,
        create_rope_product_color_fixture,
        create_rope_allowed_splice_fixture,
    ):
        """Неактивные цвета, заделки и варианты исключаются из каната, color и splice_type не могут быть null."""
        mg = await create_material_group_fixture(CreateMaterialGroupFixtureDTO(code="mg_contract"))
        sm = await create_splice_material_fixture(CreateSpliceMaterialFixtureDTO(code="sm_contract"))

        active_color = await create_color_fixture(
            CreateColorFixtureDTO(code="c_active", name="Active Color", hex="#111111", is_active=True)
        )
        inactive_color = await create_color_fixture(
            CreateColorFixtureDTO(code="c_inactive", name="Inactive Color", hex="#222222", is_active=False)
        )

        active_st = await create_splice_type_fixture(
            CreateSpliceTypeFixtureDTO(code="st_active", name="Active Splice", is_active=True)
        )
        inactive_st = await create_splice_type_fixture(
            CreateSpliceTypeFixtureDTO(code="st_inactive", name="Inactive Splice", is_active=False)
        )

        rope = await create_rope_product_fixture(
            CreateRopeProductFixtureDTO(material_group_id=mg.id, splice_material_id=sm.id)
        )

        await create_rope_variant_fixture(
            CreateRopeVariantFixtureDTO(product_id=rope.product_id, variant_name="Active Var", is_active=True)
        )
        await create_rope_variant_fixture(
            CreateRopeVariantFixtureDTO(product_id=rope.product_id, variant_name="Inactive Var", is_active=False)
        )

        await create_rope_product_color_fixture(
            CreateRopeProductColorFixtureDTO(product_id=rope.product_id, color_id=active_color.id)
        )
        await create_rope_product_color_fixture(
            CreateRopeProductColorFixtureDTO(product_id=rope.product_id, color_id=inactive_color.id)
        )

        await create_rope_allowed_splice_fixture(
            CreateRopeAllowedSpliceFixtureDTO(product_id=rope.product_id, splice_type_id=active_st.id)
        )
        await create_rope_allowed_splice_fixture(
            CreateRopeAllowedSpliceFixtureDTO(product_id=rope.product_id, splice_type_id=inactive_st.id)
        )

        response = await client_for_tests.get("/configurators")
        assert response.status_code == 200
        dto = ConfiguratorDataResponseDTO.model_validate(response.json())

        target_rope = next(r for r in dto.rope_products if r.product_id == rope.product_id)

        # Проверка вариантов
        assert len(target_rope.variants) == 1
        assert target_rope.variants[0].variant_name == "Active Var"

        # Проверка цветов: только активный, color не null
        assert len(target_rope.colors) == 1
        assert target_rope.colors[0].color_id == active_color.id
        assert target_rope.colors[0].color is not None
        assert target_rope.colors[0].color.code == "c_active"
        color_ids = [c.color_id for c in target_rope.colors]
        assert inactive_color.id not in color_ids

        # Проверка заделок: только активная, splice_type не null
        assert len(target_rope.allowed_splices) == 1
        assert target_rope.allowed_splices[0].splice_type_id == active_st.id
        assert target_rope.allowed_splices[0].splice_type is not None
        assert target_rope.allowed_splices[0].splice_type.code == "st_active"
        splice_ids = [s.splice_type_id for s in target_rope.allowed_splices]
        assert inactive_st.id not in splice_ids

    @pytest.mark.asyncio
    async def test_get_configurator_excludes_price_rules_for_inactive_splice_type(
        self,
        client_for_tests,
        create_splice_material_fixture,
        create_splice_type_fixture,
        create_splice_price_rule_fixture,
    ):
        """Матрица ценовых правил не должна включать правила для отключённых типов заделок."""
        sm = await create_splice_material_fixture(CreateSpliceMaterialFixtureDTO(code="sm_rules_test"))

        st_active = await create_splice_type_fixture(
            CreateSpliceTypeFixtureDTO(code="st_rule_act", is_active=True)
        )
        st_inactive = await create_splice_type_fixture(
            CreateSpliceTypeFixtureDTO(code="st_rule_inact", is_active=False)
        )

        rule_active = await create_splice_price_rule_fixture(
            CreateSplicePriceRuleFixtureDTO(
                splice_type_id=st_active.id,
                splice_material_id=sm.id,
                price=10.0,
                is_active=True,
            )
        )
        rule_inactive_st = await create_splice_price_rule_fixture(
            CreateSplicePriceRuleFixtureDTO(
                splice_type_id=st_inactive.id,
                splice_material_id=sm.id,
                price=20.0,
                is_active=True,  # Правило активно, но сам тип заделки выключен!
            )
        )

        response = await client_for_tests.get("/configurators")
        assert response.status_code == 200
        dto = ConfiguratorDataResponseDTO.model_validate(response.json())

        # Заделки: только активная
        st_ids = [st.id for st in dto.splice_types]
        assert st_active.id in st_ids
        assert st_inactive.id not in st_ids

        # Ценовые правила: правило для отключённой заделки должно быть исключено
        rule_ids = [r.id for r in dto.splice_price_rules]
        assert rule_active.id in rule_ids
        assert rule_inactive_st.id not in rule_ids

    @pytest.mark.asyncio
    async def test_calculate_splice_price_inactive_splice_type_returns_404(
        self,
        client_for_tests,
        create_splice_material_fixture,
        create_splice_type_fixture,
        create_splice_price_rule_fixture,
    ):
        """Расчёт цены заделки возвращает 404, если связанный тип заделки отключён."""
        sm = await create_splice_material_fixture(CreateSpliceMaterialFixtureDTO(code="sm_calc_test"))

        st_active = await create_splice_type_fixture(
            CreateSpliceTypeFixtureDTO(code="st_calc_act", is_active=True)
        )
        st_inactive = await create_splice_type_fixture(
            CreateSpliceTypeFixtureDTO(code="st_calc_inact", is_active=False)
        )

        await create_splice_price_rule_fixture(
            CreateSplicePriceRuleFixtureDTO(
                splice_type_id=st_active.id,
                splice_material_id=sm.id,
                diameter_from_mm=8.0,
                diameter_to_mm=12.0,
                price=30.0,
                is_active=True,
            )
        )
        await create_splice_price_rule_fixture(
            CreateSplicePriceRuleFixtureDTO(
                splice_type_id=st_inactive.id,
                splice_material_id=sm.id,
                diameter_from_mm=8.0,
                diameter_to_mm=12.0,
                price=50.0,
                is_active=True,
            )
        )

        # Для активной заделки -> 200 OK
        resp_act = await client_for_tests.get(
            "/configurators/price",
            params={
                "material_id": sm.id,
                "splice_type_id": st_active.id,
                "diameter_mm": 10.0,
            },
        )
        assert resp_act.status_code == 200
        assert resp_act.json()["price"] == 30.0

        # Для отключённой заделки -> 404 Not Found (нельзя посчитать цену на выключенную услугу)
        resp_inact = await client_for_tests.get(
            "/configurators/price",
            params={
                "material_id": sm.id,
                "splice_type_id": st_inactive.id,
                "diameter_mm": 10.0,
            },
        )
        assert resp_inact.status_code == 404

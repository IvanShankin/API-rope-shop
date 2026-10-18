import asyncio
import os
import sys
from pathlib import Path
from sqlalchemy import delete

# Добавляем корневую директорию проекта в sys.path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(BASE_DIR))

# Устанавливаем окружение для использования базы данных из .env
# Если файла нет, будет использоваться .env по умолчанию
if not os.getenv("CONFIG_NAME_ENV"):
    os.environ["CONFIG_NAME_ENV"] = ".env"

from src.core.config.config import Config
from src.modules.categories.models import Category, CategoryTranslation
from src.modules.colors.models import Color, ColorTranslation
from src.modules.configurator_extra.models import (
    BillingType,
    ConfiguratorExtra,
    ConfiguratorExtraTranslation,
)
from src.modules.configurator_setting.models import ConfiguratorSetting, Currency
from src.modules.material_groups.models import MaterialGroup, MaterialGroupTranslation
from src.modules.materials.models import Material, MaterialTranslation
from src.modules.products.models import Product
from src.modules.rope_products.models import RopeConfiguratorSetting, ProductVariant
from src.modules.quote_requests.models import (
    ConfiguratorType,
    QuoteExtraItem,
    QuoteRequest,
    QuoteRequestStatus,
    QuoteRopeItem,
    QuoteServiceItem,
)
from src.modules.refresh_tokens.models import RefreshToken
from src.modules.rope_allowed_splice.models import RopeAllowedSplice
from src.modules.rope_product_color.models import ProductColor
from src.modules.splice_materials.models import SpliceMaterial
from src.modules.splice_prices.models import SplicePriceRule
from src.modules.splice_types.models import (
    SpliceCategory,
    SpliceType,
    SpliceTypeTranslation,
    SpliceVisualType,
)
from src.modules.users.models import User, UserRole

# Импортируем фикстуры напрямую из tests/fixturs/__init__.py
from tests.fixturs import (
    create_color_fixture,
    create_color_translation_fixture,
    create_configurator_extra_fixture,
    create_configurator_extra_translation_fixture,
    create_configurator_setting_fixture,
    create_material_fixture,
    create_material_group_fixture,
    create_material_group_translation_fixture,
    create_material_translation_fixture,
    create_rope_allowed_splice_fixture,
    create_rope_product_color_fixture,
    create_rope_product_fixture,
    create_rope_variant_fixture,
    create_splice_material_fixture,
    create_splice_price_rule_fixture,
    create_splice_type_fixture,
    create_splice_type_translation_fixture,
    create_user_fixture,
    create_quote_request_fixture,
)
from tests.modules.colors.fixtures.models_dto import (
    CreateColorFixtureDTO,
    CreateColorTranslationFixtureDTO,
)
from tests.modules.configurator_extra.fixtures.models_dto import (
    CreateConfiguratorExtraFixtureDTO,
    CreateConfiguratorExtraTranslationFixtureDTO,
)
from tests.modules.configurator_setting.fixtures.models_dto import (
    CreateConfiguratorSettingFixtureDTO,
)
from tests.modules.material_groups.fixtures.models_dto import (
    CreateMaterialGroupFixtureDTO,
    CreateMaterialGroupTranslationFixtureDTO,
)
from tests.modules.materials.fixtures.models_dto import (
    CreateMaterialFixtureDTO,
    CreateMaterialTranslationFixtureDTO,
)
from tests.modules.quote_requests.fixtures.models_dto import (
    CreateQuoteExtraItemFixtureDTO,
    CreateQuoteRequestFixtureDTO,
    CreateQuoteRopeItemFixtureDTO,
    CreateQuoteServiceItemFixtureDTO,
)
from tests.modules.rope_allowed_splice.fixtures.models_dto import (
    CreateRopeAllowedSpliceFixtureDTO,
)
from tests.modules.rope_product_color.fixtures.models_dto import (
    CreateRopeProductColorFixtureDTO,
)
from tests.modules.rope_products.fixtures.models_dto import (
    CreateRopeProductFixtureDTO,
    CreateRopeVariantFixtureDTO,
)
from tests.modules.splice_materials.fixtures.models_dto import (
    CreateSpliceMaterialFixtureDTO,
)
from tests.modules.splice_prices.fixtures.models_dto import (
    CreateSplicePriceRuleFixtureDTO,
)
from tests.modules.splice_types.fixtures.models_dto import (
    CreateSpliceTypeFixtureDTO,
    CreateSpliceTypeTranslationFixtureDTO,
)
from tests.modules.users.fixtures.models_dto import CreateUserFixtureDTO


async def clear_database(conf: Config):
    """Очистка всех таблиц в правильном порядке зависимостей foreign keys."""
    print("Clearing old data from database...")
    async with conf.db_connection.session_local() as session:
        await session.execute(delete(QuoteRopeItem))
        await session.execute(delete(QuoteServiceItem))
        await session.execute(delete(QuoteExtraItem))
        await session.execute(delete(QuoteRequest))
        await session.execute(delete(ConfiguratorSetting))
        await session.execute(delete(ConfiguratorExtraTranslation))
        await session.execute(delete(ConfiguratorExtra))
        await session.execute(delete(RopeAllowedSplice))
        await session.execute(delete(ProductColor))
        await session.execute(delete(ProductVariant))
        await session.execute(delete(RopeConfiguratorSetting))
        await session.execute(delete(Product))
        await session.execute(delete(MaterialTranslation))
        await session.execute(delete(Material))
        await session.execute(delete(MaterialGroupTranslation))
        await session.execute(delete(MaterialGroup))
        await session.execute(delete(RefreshToken))
        await session.execute(delete(User))
        await session.execute(delete(SplicePriceRule))
        await session.execute(delete(SpliceMaterial))
        await session.execute(delete(SpliceTypeTranslation))
        await session.execute(delete(SpliceType))
        await session.execute(delete(ColorTranslation))
        await session.execute(delete(Color))
        await session.commit()
    print("Database cleared successfully.")


async def fill_data(conf: Config):
    """Заполнение базы тестовыми данными."""
    print("Starting database population with test data...")

    async with conf.db_connection.session_local() as session:
        # Создаем фабрики
        f = {
            "user": await create_user_fixture(session),
            "color": await create_color_fixture(session),
            "color_trans": await create_color_translation_fixture(session),
            "mat_group": await create_material_group_fixture(session),
            "mat_group_trans": await create_material_group_translation_fixture(session),
            "material": await create_material_fixture(session),
            "material_trans": await create_material_translation_fixture(session),
            "splice_mat": await create_splice_material_fixture(session),
            "splice_type": await create_splice_type_fixture(session),
            "splice_type_trans": await create_splice_type_translation_fixture(session),
            "splice_price": await create_splice_price_rule_fixture(session),
            "extra": await create_configurator_extra_fixture(session),
            "extra_trans": await create_configurator_extra_translation_fixture(session),
            "setting": await create_configurator_setting_fixture(session),
            "rope_product": await create_rope_product_fixture(session),
            "rope_variant": await create_rope_variant_fixture(session),
            "rope_color": await create_rope_product_color_fixture(session),
            "rope_allowed_splice": await create_rope_allowed_splice_fixture(session),
            "quote_request": await create_quote_request_fixture(session),
        }

        # 1. Пользователи
        print("  -> Creating Users...")
        admin, _ = await f["user"](
            CreateUserFixtureDTO(
                email="admin@rope-expert.com",
                password="adminpassword123",
                role=UserRole.ADMIN,
            )
        )
        user_client, _ = await f["user"](
            CreateUserFixtureDTO(
                email="client@yacht-club.de",
                password="clientpassword123",
                role=UserRole.USER,
            )
        )

        # 2. Цвета канатов
        print("  -> Creating Colors...")
        c_navy = await f["color"](CreateColorFixtureDTO(code="navy_blue", hex="#000080", index=1))
        await f["color_trans"](CreateColorTranslationFixtureDTO(color_id=c_navy.id, locale="rus", name="Темно-синий"))
        await f["color_trans"](CreateColorTranslationFixtureDTO(color_id=c_navy.id, locale="ger", name="Marineblau"))

        c_white = await f["color"](CreateColorFixtureDTO(code="white", hex="#FFFFFF", index=2))
        await f["color_trans"](CreateColorTranslationFixtureDTO(color_id=c_white.id, locale="rus", name="Белый"))
        await f["color_trans"](CreateColorTranslationFixtureDTO(color_id=c_white.id, locale="ger", name="Weiß"))

        c_black = await f["color"](CreateColorFixtureDTO(code="black", hex="#000000", index=3))
        await f["color_trans"](CreateColorTranslationFixtureDTO(color_id=c_black.id, locale="rus", name="Черный"))
        await f["color_trans"](CreateColorTranslationFixtureDTO(color_id=c_black.id, locale="ger", name="Schwarz"))

        c_red = await f["color"](CreateColorFixtureDTO(code="red_flecks", hex="#FF0000", index=4))
        await f["color_trans"](CreateColorTranslationFixtureDTO(color_id=c_red.id, locale="rus", name="Белый с красными крапинками"))
        await f["color_trans"](CreateColorTranslationFixtureDTO(color_id=c_red.id, locale="ger", name="Weiß mit roten Flecken"))

        # 3. Группы материалов
        print("  -> Creating Material Groups...")
        mg_poly = await f["mat_group"](CreateMaterialGroupFixtureDTO(code="polyester", index=1))
        await f["mat_group_trans"](CreateMaterialGroupTranslationFixtureDTO(material_group_id=mg_poly.id, locale="rus", name="Полиэстер"))
        await f["mat_group_trans"](CreateMaterialGroupTranslationFixtureDTO(material_group_id=mg_poly.id, locale="ger", name="Polyester"))

        mg_dyneema = await f["mat_group"](CreateMaterialGroupFixtureDTO(code="dyneema", index=2))
        await f["mat_group_trans"](CreateMaterialGroupTranslationFixtureDTO(material_group_id=mg_dyneema.id, locale="rus", name="Дайнима (Dyneema)"))
        await f["mat_group_trans"](CreateMaterialGroupTranslationFixtureDTO(material_group_id=mg_dyneema.id, locale="ger", name="Dyneema SK78/99"))

        # 4. Материалы внутри групп
        print("  -> Creating Materials...")
        m_pes_standard = await f["material"](CreateMaterialFixtureDTO(material_group_id=mg_poly.id, code="pes_standard", index=1))
        await f["material_trans"](CreateMaterialTranslationFixtureDTO(material_id=m_pes_standard.id, locale="rus", name="Высокопрочный полиэстер"))
        await f["material_trans"](CreateMaterialTranslationFixtureDTO(material_id=m_pes_standard.id, locale="ger", name="Hochfestes Polyester"))

        m_dyn_sk78 = await f["material"](CreateMaterialFixtureDTO(material_group_id=mg_dyneema.id, code="sk78", index=2))
        await f["material_trans"](CreateMaterialTranslationFixtureDTO(material_id=m_dyn_sk78.id, locale="rus", name="Dyneema SK78"))
        await f["material_trans"](CreateMaterialTranslationFixtureDTO(material_id=m_dyn_sk78.id, locale="ger", name="Dyneema SK78"))

        # 5. Материалы заделок (Splice Materials)
        print("  -> Creating Splice Materials...")
        sm_standard = await f["splice_mat"](CreateSpliceMaterialFixtureDTO(code="standard_core", name="Kern-Mantel Standard"))
        sm_hightech = await f["splice_mat"](CreateSpliceMaterialFixtureDTO(code="high_tech_dyneema", name="High-Tech Dyneema Hohlgeflecht"))

        # 6. Типы заделок (Splice Types)
        print("  -> Creating Splice Types...")
        st_aug = await f["splice_type"](
            CreateSpliceTypeFixtureDTO(
                code="aug_splice",
                category=SpliceCategory.LOOP,
                visual_type=SpliceVisualType.AUG_SPLICE,
                image_url="/assets/splices/aug_splice.png",
                index=1,
            )
        )
        await f["splice_type_trans"](
            CreateSpliceTypeTranslationFixtureDTO(
                splice_type_id=st_aug.id,
                locale="rus",
                name="Огон (Петля со сплайсом)",
                description="Классический огон с надежной заделкой свободного конца",
            )
        )
        await f["splice_type_trans"](
            CreateSpliceTypeTranslationFixtureDTO(
                splice_type_id=st_aug.id,
                locale="ger",
                name="Augspleiß",
                description="Klassischer Augspleiß für Tauwerk",
            )
        )

        st_endless = await f["splice_type"](
            CreateSpliceTypeFixtureDTO(
                code="endless_splice",
                category=SpliceCategory.SPLICE,
                visual_type=SpliceVisualType.ENDLESS_SPLICE,
                image_url="/assets/splices/endless.png",
                index=2,
            )
        )
        await f["splice_type_trans"](
            CreateSpliceTypeTranslationFixtureDTO(
                splice_type_id=st_endless.id,
                locale="rus",
                name="Бесконечное сращивание (Endless Splice)",
                description="Сращивание концов каната в единое неразрывное кольцо",
            )
        )
        await f["splice_type_trans"](
            CreateSpliceTypeTranslationFixtureDTO(
                splice_type_id=st_endless.id,
                locale="ger",
                name="Endlosspleiß",
                description="Verbindung von zwei Enden zu einer geschlossenen Schlinge",
            )
        )

        st_takling = await f["splice_type"](
            CreateSpliceTypeFixtureDTO(
                code="takling",
                category=SpliceCategory.LOOP,
                visual_type=SpliceVisualType.TAKLING,
                image_url="/assets/splices/takling.png",
                index=3,
            )
        )
        await f["splice_type_trans"](
            CreateSpliceTypeTranslationFixtureDTO(
                splice_type_id=st_takling.id,
                locale="rus",
                name="Марка прошивная (Takling)",
                description="Плотная марка плетеной нитью для защиты конца каната от распускания",
            )
        )
        await f["splice_type_trans"](
            CreateSpliceTypeTranslationFixtureDTO(
                splice_type_id=st_takling.id,
                locale="ger",
                name="Takling genäht",
                description="Genähter Takling zur Sicherung des Tauendes",
            )
        )

        st_soft_shackle = await f["splice_type"](
            CreateSpliceTypeFixtureDTO(
                code="soft_shackle",
                category=SpliceCategory.LOOP,
                visual_type=SpliceVisualType.SOFT_SHACKLE,
                image_url="/assets/splices/soft_shackle.png",
                index=4,
            )
        )
        await f["splice_type_trans"](
            CreateSpliceTypeTranslationFixtureDTO(
                splice_type_id=st_soft_shackle.id,
                locale="rus",
                name="Мягкая мочка (Soft Shackle)",
                description="Изготовление высокопрочной мягкой скобы из Dyneema",
            )
        )
        await f["splice_type_trans"](
            CreateSpliceTypeTranslationFixtureDTO(
                splice_type_id=st_soft_shackle.id,
                locale="ger",
                name="Softschäkel",
                description="Leichter und extrem stabiler Dyneema-Schäkel",
            )
        )

        # 7. Правила цен (Splice Price Rules)
        print("  -> Creating Splice Price Rules...")
        # Augspleiss Standard (0-14mm = 15 EUR, 14-20mm = 22 EUR, 20-30mm = 35 EUR)
        await f["splice_price"](
            CreateSplicePriceRuleFixtureDTO(
                splice_type_id=st_aug.id,
                splice_material_id=sm_standard.id,
                diameter_from_mm=0.0,
                diameter_to_mm=14.0,
                price=15.00,
            )
        )
        await f["splice_price"](
            CreateSplicePriceRuleFixtureDTO(
                splice_type_id=st_aug.id,
                splice_material_id=sm_standard.id,
                diameter_from_mm=14.0,
                diameter_to_mm=20.0,
                price=22.00,
            )
        )
        await f["splice_price"](
            CreateSplicePriceRuleFixtureDTO(
                splice_type_id=st_aug.id,
                splice_material_id=sm_standard.id,
                diameter_from_mm=20.0,
                diameter_to_mm=30.0,
                price=35.00,
            )
        )

        # Augspleiss High-Tech Dyneema (0-14mm = 30 EUR, 14-20mm = 45 EUR)
        await f["splice_price"](
            CreateSplicePriceRuleFixtureDTO(
                splice_type_id=st_aug.id,
                splice_material_id=sm_hightech.id,
                diameter_from_mm=0.0,
                diameter_to_mm=14.0,
                price=30.00,
            )
        )
        await f["splice_price"](
            CreateSplicePriceRuleFixtureDTO(
                splice_type_id=st_aug.id,
                splice_material_id=sm_hightech.id,
                diameter_from_mm=14.0,
                diameter_to_mm=20.0,
                price=45.00,
            )
        )

        # Endless Splice (Standard: 35 EUR, High-Tech: 60 EUR)
        await f["splice_price"](
            CreateSplicePriceRuleFixtureDTO(
                splice_type_id=st_endless.id,
                splice_material_id=sm_standard.id,
                diameter_from_mm=0.0,
                diameter_to_mm=20.0,
                price=35.00,
            )
        )
        await f["splice_price"](
            CreateSplicePriceRuleFixtureDTO(
                splice_type_id=st_endless.id,
                splice_material_id=sm_hightech.id,
                diameter_from_mm=0.0,
                diameter_to_mm=20.0,
                price=60.00,
            )
        )

        # Takling (Standard: 5 EUR, High-Tech: 8 EUR)
        await f["splice_price"](
            CreateSplicePriceRuleFixtureDTO(
                splice_type_id=st_takling.id,
                splice_material_id=sm_standard.id,
                diameter_from_mm=0.0,
                diameter_to_mm=30.0,
                price=5.00,
            )
        )
        await f["splice_price"](
            CreateSplicePriceRuleFixtureDTO(
                splice_type_id=st_takling.id,
                splice_material_id=sm_hightech.id,
                diameter_from_mm=0.0,
                diameter_to_mm=30.0,
                price=8.00,
            )
        )

        # Soft Shackle (High-Tech Dyneema: 25 EUR)
        await f["splice_price"](
            CreateSplicePriceRuleFixtureDTO(
                splice_type_id=st_soft_shackle.id,
                splice_material_id=sm_hightech.id,
                diameter_from_mm=0.0,
                diameter_to_mm=20.0,
                price=25.00,
            )
        )

        # 8. Дополнительные опции (Configurator Extras)
        print("  -> Creating Configurator Extras...")
        extra_leather = await f["extra"](
            CreateConfiguratorExtraFixtureDTO(
                code="leather_protection",
                billing_type=BillingType.FIXED,
                price=18.50,
                currency=Currency.EUR,
                index=1,
            )
        )
        await f["extra_trans"](
            CreateConfiguratorExtraTranslationFixtureDTO(
                extra_id=extra_leather.id,
                locale="rus",
                name="Кожаная оплетка для огона",
                description="Защита петли натуральной морской кожей от перетирания в клюзе",
            )
        )
        await f["extra_trans"](
            CreateConfiguratorExtraTranslationFixtureDTO(
                extra_id=extra_leather.id,
                locale="ger",
                name="Leder-Kauschschutz",
                description="Echtes Segelleder zum Schutz des Auges vor Scheuerstellen",
            )
        )

        extra_chafe = await f["extra"](
            CreateConfiguratorExtraFixtureDTO(
                code="chafe_sleeve",
                billing_type=BillingType.PER_METER,
                price=6.00,
                currency=Currency.EUR,
                index=2,
            )
        )
        await f["extra_trans"](
            CreateConfiguratorExtraTranslationFixtureDTO(
                extra_id=extra_chafe.id,
                locale="rus",
                name="Защитный чехол от истирания (за метр)",
                description="Сверхпрочный скользящий чехол из Cordura или Dyneema",
            )
        )
        await f["extra_trans"](
            CreateConfiguratorExtraTranslationFixtureDTO(
                extra_id=extra_chafe.id,
                locale="ger",
                name="Scheuerschutz-Schlauch (pro Meter)",
                description="Geflochtener Scheuerschutz aus Dyneema oder Cordura",
            )
        )

        extra_cert = await f["extra"](
            CreateConfiguratorExtraFixtureDTO(
                code="break_load_cert",
                billing_type=BillingType.FIXED,
                price=30.00,
                currency=Currency.EUR,
                index=3,
            )
        )
        await f["extra_trans"](
            CreateConfiguratorExtraTranslationFixtureDTO(
                extra_id=extra_cert.id,
                locale="rus",
                name="Сертификат испытания на разрыв",
                description="Протокол заводских испытаний готового изделия на стенде",
            )
        )
        await f["extra_trans"](
            CreateConfiguratorExtraTranslationFixtureDTO(
                extra_id=extra_cert.id,
                locale="ger",
                name="Prüfzeugnis / Zugtest-Zertifikat",
                description="Offizielles Messprotokoll der Bruchlastprüfung auf der Prüfbank",
            )
        )

        # 9. Настройки конфигуратора (Configurator Settings)
        print("  -> Creating Configurator Settings...")
        await f["setting"](
            CreateConfiguratorSettingFixtureDTO(
                min_length_m=1.0,
                max_length_m=300.0,
                splice_allowance_until_mm=12.0,
                splice_allowance_until_m=0.6,
                splice_allowance_over_m=1.0,
                urgent_surcharge_per_splice=10.00,
                urgent_max_splices=10,
                standard_turnaround_hours=72,
                urgent_turnaround_hours=24,
                currency=Currency.EUR,
                vat_rate=19.0,
                vat_note="inkl. 19% MwSt.",
            )
        )

        # 10. Товары-канаты, модификации и связи
        print("  -> Creating Rope Products, Variants and Relations...")
        # Канат 1: Cruising Rope (Standard Polyester)
        rope_1 = await f["rope_product"](
            CreateRopeProductFixtureDTO(
                material_group_id=mg_poly.id,
                splice_material_id=sm_standard.id,
                construction="16-plait braided core with cover",
                core_description="High tenacity polyester core",
                cover_description="Abrasion resistant polyester cover",
                can_be_spliced=True,
            )
        )
        await f["rope_variant"](
            CreateRopeVariantFixtureDTO(
                product_id=rope_1.product_id,
                variant_name="10 мм",
                size_value=10.0,
                price=2.50,
                breaking_load_dan=2300.0,
                working_load_dan=460.0,
                weight_g=65.0,
                index=1,
                is_active=True,
            )
        )
        await f["rope_variant"](
            CreateRopeVariantFixtureDTO(
                product_id=rope_1.product_id,
                variant_name="12 мм",
                size_value=12.0,
                price=3.80,
                breaking_load_dan=3200.0,
                working_load_dan=640.0,
                weight_g=90.0,
                index=2,
                is_active=True,
            )
        )
        await f["rope_variant"](
            CreateRopeVariantFixtureDTO(
                product_id=rope_1.product_id,
                variant_name="14 мм",
                size_value=14.0,
                price=5.20,
                breaking_load_dan=4400.0,
                working_load_dan=880.0,
                weight_g=125.0,
                index=3,
                is_active=True,
            )
        )
        await f["rope_color"](
            CreateRopeProductColorFixtureDTO(
                product_id=rope_1.product_id,
                color_id=c_navy.id,
                index=1,
            )
        )
        await f["rope_color"](
            CreateRopeProductColorFixtureDTO(
                product_id=rope_1.product_id,
                color_id=c_white.id,
                index=2,
            )
        )
        await f["rope_color"](
            CreateRopeProductColorFixtureDTO(
                product_id=rope_1.product_id,
                color_id=c_black.id,
                index=3,
            )
        )
        await f["rope_allowed_splice"](
            CreateRopeAllowedSpliceFixtureDTO(
                product_id=rope_1.product_id,
                splice_type_id=st_aug.id,
            )
        )
        await f["rope_allowed_splice"](
            CreateRopeAllowedSpliceFixtureDTO(
                product_id=rope_1.product_id,
                splice_type_id=st_endless.id,
            )
        )
        await f["rope_allowed_splice"](
            CreateRopeAllowedSpliceFixtureDTO(
                product_id=rope_1.product_id,
                splice_type_id=st_takling.id,
            )
        )

        # Канат 2: Dyneema Rope (High-Tech)
        rope_2 = await f["rope_product"](
            CreateRopeProductFixtureDTO(
                material_group_id=mg_dyneema.id,
                splice_material_id=sm_hightech.id,
                construction="12-strand braided core with Technora/Polyester cover",
                core_description="Dyneema SK78 12-strand coated core",
                cover_description="50/50 Technora / Polyester braid",
                can_be_spliced=True,
            )
        )
        await f["rope_variant"](
            CreateRopeVariantFixtureDTO(
                product_id=rope_2.product_id,
                variant_name="8 мм",
                size_value=8.0,
                price=4.50,
                breaking_load_dan=3500.0,
                working_load_dan=1100.0,
                weight_g=45.0,
                index=1,
                is_active=True,
            )
        )
        await f["rope_variant"](
            CreateRopeVariantFixtureDTO(
                product_id=rope_2.product_id,
                variant_name="10 мм",
                size_value=10.0,
                price=6.80,
                breaking_load_dan=5000.0,
                working_load_dan=1600.0,
                weight_g=60.0,
                index=2,
                is_active=True,
            )
        )
        await f["rope_variant"](
            CreateRopeVariantFixtureDTO(
                product_id=rope_2.product_id,
                variant_name="12 мм",
                size_value=12.0,
                price=9.50,
                breaking_load_dan=7200.0,
                working_load_dan=2300.0,
                weight_g=85.0,
                index=3,
                is_active=True,
            )
        )
        await f["rope_color"](
            CreateRopeProductColorFixtureDTO(
                product_id=rope_2.product_id,
                color_id=c_navy.id,
                index=1,
            )
        )
        await f["rope_color"](
            CreateRopeProductColorFixtureDTO(
                product_id=rope_2.product_id,
                color_id=c_red.id,
                index=2,
            )
        )
        await f["rope_allowed_splice"](
            CreateRopeAllowedSpliceFixtureDTO(
                product_id=rope_2.product_id,
                splice_type_id=st_aug.id,
            )
        )
        await f["rope_allowed_splice"](
            CreateRopeAllowedSpliceFixtureDTO(
                product_id=rope_2.product_id,
                splice_type_id=st_soft_shackle.id,
            )
        )
        await f["rope_allowed_splice"](
            CreateRopeAllowedSpliceFixtureDTO(
                product_id=rope_2.product_id,
                splice_type_id=st_endless.id,
            )
        )

        # 11. Пример готовой заявки (Quote Request)
        print("  -> Creating Example Quote Requests...")
        await f["quote_request"](
            CreateQuoteRequestFixtureDTO(
                request_number="RPL-2026-0001",
                configurator_type=ConfiguratorType.ROPE_WITH_SPLICE,
                name="Hans Schmidt",
                email="schmidt@baltic-yachting.de",
                phone="+49 170 1234567",
                comment="Foresheet for 40ft cruiser/racer",
                currency=Currency.EUR,
                total_price=125.60,
                vat_rate=19.0,
                is_urgent=False,
                status=QuoteRequestStatus.NEW,
                rope_items=[
                    CreateQuoteRopeItemFixtureDTO(
                        product_id=rope_1.product_id,
                        color_id=c_navy.id,
                        product_name_snapshot="Cruising 16-plait Polyester",
                        color_name_snapshot="Marineblau",
                        diameter_mm=10.0,
                        length_m=30.0,
                        quantity=1,
                        price_per_meter_snapshot=2.50,
                        total_rope_cost=75.00,
                        end_a_type_id=st_aug.id,
                        end_a_name_snapshot="Augspleiß",
                        end_a_eye_size_cm=15.0,
                        end_a_cost=15.00,
                        end_b_type_id=st_takling.id,
                        end_b_name_snapshot="Takling genäht",
                        end_b_cost=5.00,
                    )
                ],
                extra_items=[
                    CreateQuoteExtraItemFixtureDTO(
                        extra_id=extra_leather.id,
                        extra_code_snapshot="leather_protection",
                        extra_name_snapshot="Leder-Kauschschutz",
                        billing_type_snapshot=BillingType.FIXED,
                        unit_price_snapshot=18.50,
                        calculated_cost=18.50,
                    )
                ],
            )
        )

        await f["quote_request"](
            CreateQuoteRequestFixtureDTO(
                request_number="RPL-2026-0002",
                configurator_type=ConfiguratorType.LOOP_ONLY,
                name="Markus Weber",
                email="m.weber@north-sea-rigging.com",
                phone="+49 151 9876543",
                comment="Rigging refit: 4 soft shackles for halyard blocks",
                currency=Currency.EUR,
                total_price=100.00,
                vat_rate=19.0,
                is_urgent=True,
                status=QuoteRequestStatus.IN_PROGRESS,
                service_items=[
                    CreateQuoteServiceItemFixtureDTO(
                        splice_type_id=st_soft_shackle.id,
                        splice_material_id=sm_hightech.id,
                        service_name_snapshot="Softschäkel",
                        material_name_snapshot="High-Tech Dyneema Hohlgeflecht",
                        diameter_mm=8.0,
                        eye_size_cm=12.0,
                        quantity=4,
                        unit_price_snapshot=25.00,
                        total_cost=100.00,
                    )
                ],
            )
        )

    print("\n[OK] Test data population successfully completed!")


async def main():
    conf = Config()
    await clear_database(conf)
    await fill_data(conf)


if __name__ == "__main__":
    asyncio.run(main())

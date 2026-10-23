import asyncio
import os
import sys
from pathlib import Path

# Add project root directory to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Ensure environment uses .env
if not os.getenv("CONFIG_NAME_ENV"):
    os.environ["CONFIG_NAME_ENV"] = ".env"

from passlib.context import CryptContext
from sqlalchemy import delete, text

from src.core.config.config import Config
from src.modules.base.database_model import Language
from src.modules.configurator_extra.models import BillingType
from src.modules.configurator_setting.models import Currency
from src.modules.db_models import (
    Category,
    CategoryTranslation,
    CharityPhoto,
    CharityPhotoTranslation,
    Color,
    ColorTranslation,
    ConfiguratorExtra,
    ConfiguratorExtraTranslation,
    ConfiguratorSetting,
    ContactRequest,
    ContentBlock,
    ContentBlockTranslation,
    Material,
    MaterialGroup,
    MaterialGroupTranslation,
    MaterialTranslation,
    Product,
    ProductApplication,
    ProductApplicationTranslation,
    ProductAssignedApplication,
    ProductColor,
    ProductImage,
    ProductSpecification,
    ProductSpecificationTranslation,
    ProductTranslation,
    ProductVariant,
    QuoteExtraItem,
    QuoteRequest,
    QuoteRopeItem,
    QuoteServiceItem,
    RefreshToken,
    Review,
    ReviewTranslation,
    RopeAllowedSplice,
    RopeConfiguratorSetting,
    Settings,
    SpliceMaterial,
    SplicePriceRule,
    SpliceType,
    SpliceTypeTranslation,
    User,
    WorkPhoto,
    WorkPhotoTranslation,
)
from src.modules.quote_requests.models import ConfiguratorType, QuoteRequestStatus
from src.modules.splice_types.models import SpliceCategory, SpliceVisualType
from src.modules.users.models import UserRole

# Import test factories and fixture DTOs
from tests.modules.categories.fixtures.factory import (
    create_category_factory,
    create_category_translation_factory,
)
from tests.modules.categories.fixtures.models_dto import (
    CreateCategoryFixtureDTO,
    CreateCategoryTranslationFixtureDTO,
)
from tests.modules.colors.fixtures.factory import (
    create_color_factory,
    create_color_translation_factory,
)
from tests.modules.colors.fixtures.models_dto import (
    CreateColorFixtureDTO,
    CreateColorTranslationFixtureDTO,
)
from tests.modules.configurator_extra.fixtures.factory import (
    create_configurator_extra_factory,
    create_configurator_extra_translation_factory,
)
from tests.modules.configurator_extra.fixtures.models_dto import (
    CreateConfiguratorExtraFixtureDTO,
    CreateConfiguratorExtraTranslationFixtureDTO,
)
from tests.modules.configurator_setting.fixtures.factory import (
    create_configurator_setting_factory,
)
from tests.modules.configurator_setting.fixtures.models_dto import (
    CreateConfiguratorSettingFixtureDTO,
)
from tests.modules.material_groups.fixtures.factory import (
    create_material_group_factory,
    create_material_group_translation_factory,
)
from tests.modules.material_groups.fixtures.models_dto import (
    CreateMaterialGroupFixtureDTO,
    CreateMaterialGroupTranslationFixtureDTO,
)
from tests.modules.materials.fixtures.factory import (
    create_material_factory,
    create_material_translation_factory,
)
from tests.modules.materials.fixtures.models_dto import (
    CreateMaterialFixtureDTO,
    CreateMaterialTranslationFixtureDTO,
)
from tests.modules.products.fixtures.factory import (
    create_product_factory,
    create_product_translation_factory,
)
from tests.modules.products.fixtures.models_dto import (
    CreateProductFixtureDTO,
    CreateProductTranslationFixtureDTO,
)
from tests.modules.quote_requests.fixtures.factory import (
    create_quote_request_factory,
)
from tests.modules.quote_requests.fixtures.models_dto import (
    CreateQuoteExtraItemFixtureDTO,
    CreateQuoteRequestFixtureDTO,
    CreateQuoteRopeItemFixtureDTO,
    CreateQuoteServiceItemFixtureDTO,
)
from tests.modules.rope_allowed_splice.fixtures.factory import (
    create_rope_allowed_splice_factory,
)
from tests.modules.rope_allowed_splice.fixtures.models_dto import (
    CreateRopeAllowedSpliceFixtureDTO,
)
from tests.modules.rope_product_color.fixtures.factory import (
    create_rope_product_color_factory,
)
from tests.modules.rope_product_color.fixtures.models_dto import (
    CreateRopeProductColorFixtureDTO,
)
from tests.modules.rope_products.fixtures.factory import (
    create_rope_product_factory,
    create_rope_variant_factory,
)
from tests.modules.rope_products.fixtures.models_dto import (
    CreateRopeProductFixtureDTO,
    CreateRopeVariantFixtureDTO,
)
from tests.modules.splice_materials.fixtures.factory import (
    create_splice_material_factory,
)
from tests.modules.splice_materials.fixtures.models_dto import (
    CreateSpliceMaterialFixtureDTO,
)
from tests.modules.splice_prices.fixtures.factory import (
    create_splice_price_rule_factory,
)
from tests.modules.splice_prices.fixtures.models_dto import (
    CreateSplicePriceRuleFixtureDTO,
)
from tests.modules.splice_types.fixtures.factory import (
    create_splice_type_factory,
    create_splice_type_translation_factory,
)
from tests.modules.splice_types.fixtures.models_dto import (
    CreateSpliceTypeFixtureDTO,
    CreateSpliceTypeTranslationFixtureDTO,
)
from tests.modules.users.fixtures.factory import (
    create_user_factory,
)
from tests.modules.users.fixtures.models_dto import (
    CreateUserFixtureDTO,
)


async def clear_database(conf: Config):
    """Очистка всех таблиц в правильном порядке зависимостей foreign keys."""
    print("Clearing old data from database...")
    async with conf.db_connection.session_local() as session:
        await session.execute(delete(Settings))
        await session.execute(delete(ContactRequest))
        await session.execute(delete(ContentBlockTranslation))
        await session.execute(delete(ContentBlock))
        await session.execute(delete(WorkPhotoTranslation))
        await session.execute(delete(WorkPhoto))
        await session.execute(delete(CharityPhotoTranslation))
        await session.execute(delete(CharityPhoto))
        await session.execute(delete(ReviewTranslation))
        await session.execute(delete(Review))
        await session.execute(delete(QuoteRopeItem))
        await session.execute(delete(QuoteServiceItem))
        await session.execute(delete(QuoteExtraItem))
        await session.execute(delete(QuoteRequest))
        await session.execute(text("ALTER SEQUENCE IF EXISTS quote_request_number_seq RESTART WITH 1;"))
        await session.execute(delete(ConfiguratorSetting))
        await session.execute(delete(ConfiguratorExtraTranslation))
        await session.execute(delete(ConfiguratorExtra))
        await session.execute(delete(RopeAllowedSplice))
        await session.execute(delete(ProductColor))
        await session.execute(delete(ProductVariant))
        await session.execute(delete(RopeConfiguratorSetting))
        await session.execute(delete(ProductSpecificationTranslation))
        await session.execute(delete(ProductSpecification))
        await session.execute(delete(ProductAssignedApplication))
        await session.execute(delete(ProductApplicationTranslation))
        await session.execute(delete(ProductApplication))
        await session.execute(delete(ProductImage))
        await session.execute(delete(ProductTranslation))
        await session.execute(delete(Product))
        await session.execute(delete(CategoryTranslation))
        await session.execute(delete(Category))
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
    """Заполнение базы тестовыми данными с помощью фабрик."""
    print("Starting database population with test factories...")
    crypto_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    async with conf.db_connection.session_local() as session:
        # 1. Пользователи
        print("  -> Creating Users...")
        await create_user_factory(
            session,
            crypto_context,
            CreateUserFixtureDTO(
                email="admin@rope-expert.com",
                username="admin",
                password="adminpassword123",
                role=UserRole.ADMIN,
            ),
        )
        await create_user_factory(
            session,
            crypto_context,
            CreateUserFixtureDTO(
                email="client@yacht-club.de",
                username="client_yacht",
                password="clientpassword123",
                role=UserRole.USER,
            ),
        )

        # 2. Цвета канатов
        print("  -> Creating Colors...")
        c_navy = await create_color_factory(
            session,
            CreateColorFixtureDTO(
                code="navy_blue",
                hex="#000080",
                index=1,
                locale=Language.ENG,
                name="Navy Blue",
            ),
        )
        await create_color_translation_factory(
            session,
            CreateColorTranslationFixtureDTO(color_id=c_navy.id, locale=Language.RUS, name="Темно-синий"),
        )
        await create_color_translation_factory(
            session,
            CreateColorTranslationFixtureDTO(color_id=c_navy.id, locale=Language.GER, name="Marineblau"),
        )

        c_white = await create_color_factory(
            session,
            CreateColorFixtureDTO(
                code="white",
                hex="#FFFFFF",
                index=2,
                locale=Language.ENG,
                name="White",
            ),
        )
        await create_color_translation_factory(
            session,
            CreateColorTranslationFixtureDTO(color_id=c_white.id, locale=Language.RUS, name="Белый"),
        )
        await create_color_translation_factory(
            session,
            CreateColorTranslationFixtureDTO(color_id=c_white.id, locale=Language.GER, name="Weiß"),
        )

        c_black = await create_color_factory(
            session,
            CreateColorFixtureDTO(
                code="black",
                hex="#000000",
                index=3,
                locale=Language.ENG,
                name="Black",
            ),
        )
        await create_color_translation_factory(
            session,
            CreateColorTranslationFixtureDTO(color_id=c_black.id, locale=Language.RUS, name="Черный"),
        )
        await create_color_translation_factory(
            session,
            CreateColorTranslationFixtureDTO(color_id=c_black.id, locale=Language.GER, name="Schwarz"),
        )

        c_red = await create_color_factory(
            session,
            CreateColorFixtureDTO(
                code="red_flecks",
                hex="#FF0000",
                index=4,
                locale=Language.ENG,
                name="White with red flecks",
            ),
        )
        await create_color_translation_factory(
            session,
            CreateColorTranslationFixtureDTO(
                color_id=c_red.id,
                locale=Language.RUS,
                name="Белый с красными крапинками",
            ),
        )
        await create_color_translation_factory(
            session,
            CreateColorTranslationFixtureDTO(
                color_id=c_red.id,
                locale=Language.GER,
                name="Weiß mit roten Flecken",
            ),
        )

        # 3. Группы материалов
        print("  -> Creating Material Groups...")
        mg_poly = await create_material_group_factory(
            session,
            CreateMaterialGroupFixtureDTO(
                code="polyester",
                index=1,
                locale=Language.ENG,
                name="Polyester",
            ),
        )
        await create_material_group_translation_factory(
            session,
            CreateMaterialGroupTranslationFixtureDTO(
                material_group_id=mg_poly.id,
                locale=Language.RUS,
                name="Полиэстер",
            ),
        )
        await create_material_group_translation_factory(
            session,
            CreateMaterialGroupTranslationFixtureDTO(
                material_group_id=mg_poly.id,
                locale=Language.GER,
                name="Polyester",
            ),
        )

        mg_dyneema = await create_material_group_factory(
            session,
            CreateMaterialGroupFixtureDTO(
                code="dyneema",
                index=2,
                locale=Language.ENG,
                name="Dyneema",
            ),
        )
        await create_material_group_translation_factory(
            session,
            CreateMaterialGroupTranslationFixtureDTO(
                material_group_id=mg_dyneema.id,
                locale=Language.RUS,
                name="Дайнима (Dyneema)",
            ),
        )
        await create_material_group_translation_factory(
            session,
            CreateMaterialGroupTranslationFixtureDTO(
                material_group_id=mg_dyneema.id,
                locale=Language.GER,
                name="Dyneema SK78/99",
            ),
        )

        # 4. Материалы внутри групп
        print("  -> Creating Materials...")
        m_pes_standard = await create_material_factory(
            session,
            CreateMaterialFixtureDTO(
                material_group_id=mg_poly.id,
                code="pes_standard",
                index=1,
                locale=Language.ENG,
                name="High-tenacity Polyester",
            ),
        )
        await create_material_translation_factory(
            session,
            CreateMaterialTranslationFixtureDTO(
                material_id=m_pes_standard.id,
                locale=Language.RUS,
                name="Высокопрочный полиэстер",
            ),
        )
        await create_material_translation_factory(
            session,
            CreateMaterialTranslationFixtureDTO(
                material_id=m_pes_standard.id,
                locale=Language.GER,
                name="Hochfestes Polyester",
            ),
        )

        m_dyn_sk78 = await create_material_factory(
            session,
            CreateMaterialFixtureDTO(
                material_group_id=mg_dyneema.id,
                code="sk78",
                index=2,
                locale=Language.ENG,
                name="Dyneema SK78",
            ),
        )
        await create_material_translation_factory(
            session,
            CreateMaterialTranslationFixtureDTO(
                material_id=m_dyn_sk78.id,
                locale=Language.RUS,
                name="Dyneema SK78",
            ),
        )
        await create_material_translation_factory(
            session,
            CreateMaterialTranslationFixtureDTO(
                material_id=m_dyn_sk78.id,
                locale=Language.GER,
                name="Dyneema SK78",
            ),
        )

        # 5. Материалы заделок (Splice Materials)
        print("  -> Creating Splice Materials...")
        sm_standard = await create_splice_material_factory(
            session,
            CreateSpliceMaterialFixtureDTO(
                code="standard_core",
                name="Kern-Mantel Standard",
            ),
        )
        sm_hightech = await create_splice_material_factory(
            session,
            CreateSpliceMaterialFixtureDTO(
                code="high_tech_dyneema",
                name="High-Tech Dyneema Hohlgeflecht",
            ),
        )

        # 6. Типы заделок (Splice Types)
        print("  -> Creating Splice Types...")
        st_aug = await create_splice_type_factory(
            session,
            CreateSpliceTypeFixtureDTO(
                code="aug_splice",
                category=SpliceCategory.LOOP,
                visual_type=SpliceVisualType.AUG_SPLICE,
                image_url="/assets/splices/aug_splice.png",
                index=1,
                locale=Language.ENG,
                name="Eye Splice",
                description="Classic eye splice with secure finish",
            ),
        )
        await create_splice_type_translation_factory(
            session,
            CreateSpliceTypeTranslationFixtureDTO(
                splice_type_id=st_aug.id,
                locale=Language.RUS,
                name="Огон (Петля со сплайсом)",
                description="Классический огон с надежной заделкой свободного конца",
            ),
        )
        await create_splice_type_translation_factory(
            session,
            CreateSpliceTypeTranslationFixtureDTO(
                splice_type_id=st_aug.id,
                locale=Language.GER,
                name="Augspleiß",
                description="Klassischer Augspleiß für Tauwerk",
            ),
        )

        st_endless = await create_splice_type_factory(
            session,
            CreateSpliceTypeFixtureDTO(
                code="endless_splice",
                category=SpliceCategory.SPLICE,
                visual_type=SpliceVisualType.ENDLESS_SPLICE,
                image_url="/assets/splices/endless.png",
                index=2,
                locale=Language.ENG,
                name="Endless Splice",
                description="Continuous loop splicing of rope ends",
            ),
        )
        await create_splice_type_translation_factory(
            session,
            CreateSpliceTypeTranslationFixtureDTO(
                splice_type_id=st_endless.id,
                locale=Language.RUS,
                name="Бесконечное сращивание (Endless Splice)",
                description="Сращивание концов каната в единое неразрывное кольцо",
            ),
        )
        await create_splice_type_translation_factory(
            session,
            CreateSpliceTypeTranslationFixtureDTO(
                splice_type_id=st_endless.id,
                locale=Language.GER,
                name="Endlosspleiß",
                description="Verbindung von zwei Enden zu einer geschlossenen Schlinge",
            ),
        )

        st_takling = await create_splice_type_factory(
            session,
            CreateSpliceTypeFixtureDTO(
                code="takling",
                category=SpliceCategory.LOOP,
                visual_type=SpliceVisualType.TAKLING,
                image_url="/assets/splices/takling.png",
                index=3,
                locale=Language.ENG,
                name="Whipped End (Takling)",
                description="Sewn whipping to protect rope end from fraying",
            ),
        )
        await create_splice_type_translation_factory(
            session,
            CreateSpliceTypeTranslationFixtureDTO(
                splice_type_id=st_takling.id,
                locale=Language.RUS,
                name="Марка прошивная (Takling)",
                description="Плотная марка плетеной нитью для защиты конца каната от распускания",
            ),
        )
        await create_splice_type_translation_factory(
            session,
            CreateSpliceTypeTranslationFixtureDTO(
                splice_type_id=st_takling.id,
                locale=Language.GER,
                name="Takling genäht",
                description="Genähter Takling zur Sicherung des Tauendes",
            ),
        )

        st_soft_shackle = await create_splice_type_factory(
            session,
            CreateSpliceTypeFixtureDTO(
                code="soft_shackle",
                category=SpliceCategory.LOOP,
                visual_type=SpliceVisualType.SOFT_SHACKLE,
                image_url="/assets/splices/soft_shackle.png",
                index=4,
                locale=Language.ENG,
                name="Soft Shackle",
                description="Lightweight high-strength Dyneema soft shackle",
            ),
        )
        await create_splice_type_translation_factory(
            session,
            CreateSpliceTypeTranslationFixtureDTO(
                splice_type_id=st_soft_shackle.id,
                locale=Language.RUS,
                name="Мягкая мочка (Soft Shackle)",
                description="Изготовление высокопрочной мягкой скобы из Dyneema",
            ),
        )
        await create_splice_type_translation_factory(
            session,
            CreateSpliceTypeTranslationFixtureDTO(
                splice_type_id=st_soft_shackle.id,
                locale=Language.GER,
                name="Softschäkel",
                description="Leichter und extrem stabiler Dyneema-Schäkel",
            ),
        )

        # 7. Правила цен (Splice Price Rules)
        print("  -> Creating Splice Price Rules...")
        # Augspleiss Standard (0-14mm = 15 EUR, 14-20mm = 22 EUR, 20-30mm = 35 EUR)
        await create_splice_price_rule_factory(
            session,
            CreateSplicePriceRuleFixtureDTO(
                splice_type_id=st_aug.id,
                splice_material_id=sm_standard.id,
                diameter_from_mm=0.0,
                diameter_to_mm=14.0,
                price=15.00,
            ),
        )
        await create_splice_price_rule_factory(
            session,
            CreateSplicePriceRuleFixtureDTO(
                splice_type_id=st_aug.id,
                splice_material_id=sm_standard.id,
                diameter_from_mm=14.0,
                diameter_to_mm=20.0,
                price=22.00,
            ),
        )
        await create_splice_price_rule_factory(
            session,
            CreateSplicePriceRuleFixtureDTO(
                splice_type_id=st_aug.id,
                splice_material_id=sm_standard.id,
                diameter_from_mm=20.0,
                diameter_to_mm=30.0,
                price=35.00,
            ),
        )

        # Augspleiss High-Tech Dyneema (0-14mm = 30 EUR, 14-20mm = 45 EUR)
        await create_splice_price_rule_factory(
            session,
            CreateSplicePriceRuleFixtureDTO(
                splice_type_id=st_aug.id,
                splice_material_id=sm_hightech.id,
                diameter_from_mm=0.0,
                diameter_to_mm=14.0,
                price=30.00,
            ),
        )
        await create_splice_price_rule_factory(
            session,
            CreateSplicePriceRuleFixtureDTO(
                splice_type_id=st_aug.id,
                splice_material_id=sm_hightech.id,
                diameter_from_mm=14.0,
                diameter_to_mm=20.0,
                price=45.00,
            ),
        )

        # Endless Splice (Standard: 35 EUR, High-Tech: 60 EUR)
        await create_splice_price_rule_factory(
            session,
            CreateSplicePriceRuleFixtureDTO(
                splice_type_id=st_endless.id,
                splice_material_id=sm_standard.id,
                diameter_from_mm=0.0,
                diameter_to_mm=20.0,
                price=35.00,
            ),
        )
        await create_splice_price_rule_factory(
            session,
            CreateSplicePriceRuleFixtureDTO(
                splice_type_id=st_endless.id,
                splice_material_id=sm_hightech.id,
                diameter_from_mm=0.0,
                diameter_to_mm=20.0,
                price=60.00,
            ),
        )

        # Takling (Standard: 5 EUR, High-Tech: 8 EUR)
        await create_splice_price_rule_factory(
            session,
            CreateSplicePriceRuleFixtureDTO(
                splice_type_id=st_takling.id,
                splice_material_id=sm_standard.id,
                diameter_from_mm=0.0,
                diameter_to_mm=30.0,
                price=5.00,
            ),
        )
        await create_splice_price_rule_factory(
            session,
            CreateSplicePriceRuleFixtureDTO(
                splice_type_id=st_takling.id,
                splice_material_id=sm_hightech.id,
                diameter_from_mm=0.0,
                diameter_to_mm=30.0,
                price=8.00,
            ),
        )

        # Soft Shackle (High-Tech Dyneema: 25 EUR)
        await create_splice_price_rule_factory(
            session,
            CreateSplicePriceRuleFixtureDTO(
                splice_type_id=st_soft_shackle.id,
                splice_material_id=sm_hightech.id,
                diameter_from_mm=0.0,
                diameter_to_mm=20.0,
                price=25.00,
            ),
        )

        # 8. Дополнительные опции (Configurator Extras)
        print("  -> Creating Configurator Extras...")
        extra_leather = await create_configurator_extra_factory(
            session,
            CreateConfiguratorExtraFixtureDTO(
                code="leather_protection",
                billing_type=BillingType.FIXED,
                price=18.50,
                currency=Currency.EUR,
                index=1,
                locale=Language.ENG,
                name="Leather eye protection",
                description="Natural marine leather eye protection from abrasion in chocks",
            ),
        )
        await create_configurator_extra_translation_factory(
            session,
            CreateConfiguratorExtraTranslationFixtureDTO(
                extra_id=extra_leather.id,
                locale=Language.RUS,
                name="Кожаная оплетка для огона",
                description="Защита петли натуральной морской кожей от перетирания в клюзе",
            ),
        )
        await create_configurator_extra_translation_factory(
            session,
            CreateConfiguratorExtraTranslationFixtureDTO(
                extra_id=extra_leather.id,
                locale=Language.GER,
                name="Leder-Kauschschutz",
                description="Echtes Segelleder zum Schutz des Auges vor Scheuerstellen",
            ),
        )

        extra_chafe = await create_configurator_extra_factory(
            session,
            CreateConfiguratorExtraFixtureDTO(
                code="chafe_sleeve",
                billing_type=BillingType.PER_METER,
                price=6.00,
                currency=Currency.EUR,
                index=2,
                locale=Language.ENG,
                name="Chafe protection sleeve (per meter)",
                description="Heavy-duty sliding chafe sleeve made of Cordura or Dyneema",
            ),
        )
        await create_configurator_extra_translation_factory(
            session,
            CreateConfiguratorExtraTranslationFixtureDTO(
                extra_id=extra_chafe.id,
                locale=Language.RUS,
                name="Защитный чехол от истирания (за метр)",
                description="Сверхпрочный скользящий чехол из Cordura или Dyneema",
            ),
        )
        await create_configurator_extra_translation_factory(
            session,
            CreateConfiguratorExtraTranslationFixtureDTO(
                extra_id=extra_chafe.id,
                locale=Language.GER,
                name="Scheuerschutz-Schlauch (pro Meter)",
                description="Geflochtener Scheuerschutz aus Dyneema oder Cordura",
            ),
        )

        extra_cert = await create_configurator_extra_factory(
            session,
            CreateConfiguratorExtraFixtureDTO(
                code="break_load_cert",
                billing_type=BillingType.FIXED,
                price=30.00,
                currency=Currency.EUR,
                index=3,
                locale=Language.ENG,
                name="Break load test certificate",
                description="Official test certificate from the tensile test bench",
            ),
        )
        await create_configurator_extra_translation_factory(
            session,
            CreateConfiguratorExtraTranslationFixtureDTO(
                extra_id=extra_cert.id,
                locale=Language.RUS,
                name="Сертификат испытания на разрыв",
                description="Протокол заводских испытаний готового изделия на стенде",
            ),
        )
        await create_configurator_extra_translation_factory(
            session,
            CreateConfiguratorExtraTranslationFixtureDTO(
                extra_id=extra_cert.id,
                locale=Language.GER,
                name="Prüfzeugnis / Zugtest-Zertifikat",
                description="Offizielles Messprotokoll der Bruchlastprüfung auf der Prüfbank",
            ),
        )

        # 9. Настройки конфигуратора (Configurator Settings)
        print("  -> Creating Configurator Settings...")
        await create_configurator_setting_factory(
            session,
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
            ),
        )

        # 10. Категории, товары-канаты, модификации и связи
        print("  -> Creating Categories, Rope Products, Variants and Relations...")
        cat_ropes = await create_category_factory(
            session,
            CreateCategoryFixtureDTO(
                slug="ropes",
                index=1,
                locale=Language.ENG,
                name="Ropes & Cordage",
            ),
        )
        await create_category_translation_factory(
            session,
            CreateCategoryTranslationFixtureDTO(
                category_id=cat_ropes.id,
                locale=Language.RUS,
                name="Канаты и тросы",
            ),
        )
        await create_category_translation_factory(
            session,
            CreateCategoryTranslationFixtureDTO(
                category_id=cat_ropes.id,
                locale=Language.GER,
                name="Tauwerk & Seile",
            ),
        )

        # Канат 1: Cruising Rope (Standard Polyester)
        prod_cruising = await create_product_factory(
            session,
            CreateProductFixtureDTO(
                category_id=cat_ropes.id,
                slug="cruising-polyester-16",
                price_unit="meter",
                has_configurator=True,
                index=1,
                locale=Language.ENG,
                name="Cruising Polyester 16-plait",
                subtitle="Durable all-round cruising rope",
                description="High quality polyester rope for halyards and sheets on cruising yachts.",
            ),
        )
        await create_product_translation_factory(
            session,
            CreateProductTranslationFixtureDTO(
                product_id=prod_cruising.id,
                locale=Language.RUS,
                name="Cruising Полиэстер 16-прядный",
                subtitle="Надежный универсальный канат для круизных яхт",
                description="Высококачественный канат из полиэстера для фалов и шкотов.",
            ),
        )
        await create_product_translation_factory(
            session,
            CreateProductTranslationFixtureDTO(
                product_id=prod_cruising.id,
                locale=Language.GER,
                name="Cruising Polyester 16-fach geflochten",
                subtitle="Langlebiges Universaltauwerk für Fahrtensegler",
                description="Hochwertiges Polyester-Tauwerk für Fallen und Schoten auf Fahrtenyachten.",
            ),
        )

        await create_rope_product_factory(
            session,
            CreateRopeProductFixtureDTO(
                product_id=prod_cruising.id,
                material_group_id=mg_poly.id,
                material_id=m_pes_standard.id,
                splice_material_id=sm_standard.id,
                construction="16-plait braided core with cover",
                core_description="High tenacity polyester core",
                cover_description="Abrasion resistant polyester cover",
                can_be_spliced=True,
            ),
        )

        await create_rope_variant_factory(
            session,
            CreateRopeVariantFixtureDTO(
                product_id=prod_cruising.id,
                variant_name="10 мм",
                size_value=10.0,
                price=2.50,
                breaking_load_dan=2300.0,
                working_load_dan=460.0,
                weight_g=65.0,
                index=1,
                is_active=True,
            ),
        )
        await create_rope_variant_factory(
            session,
            CreateRopeVariantFixtureDTO(
                product_id=prod_cruising.id,
                variant_name="12 мм",
                size_value=12.0,
                price=3.80,
                breaking_load_dan=3200.0,
                working_load_dan=640.0,
                weight_g=90.0,
                index=2,
                is_active=True,
            ),
        )
        await create_rope_variant_factory(
            session,
            CreateRopeVariantFixtureDTO(
                product_id=prod_cruising.id,
                variant_name="14 мм",
                size_value=14.0,
                price=5.20,
                breaking_load_dan=4400.0,
                working_load_dan=880.0,
                weight_g=125.0,
                index=3,
                is_active=True,
            ),
        )

        await create_rope_product_color_factory(
            session,
            CreateRopeProductColorFixtureDTO(
                product_id=prod_cruising.id,
                color_id=c_navy.id,
                index=1,
            ),
        )
        await create_rope_product_color_factory(
            session,
            CreateRopeProductColorFixtureDTO(
                product_id=prod_cruising.id,
                color_id=c_white.id,
                index=2,
            ),
        )
        await create_rope_product_color_factory(
            session,
            CreateRopeProductColorFixtureDTO(
                product_id=prod_cruising.id,
                color_id=c_black.id,
                index=3,
            ),
        )

        await create_rope_allowed_splice_factory(
            session,
            CreateRopeAllowedSpliceFixtureDTO(
                product_id=prod_cruising.id,
                splice_type_id=st_aug.id,
            ),
        )
        await create_rope_allowed_splice_factory(
            session,
            CreateRopeAllowedSpliceFixtureDTO(
                product_id=prod_cruising.id,
                splice_type_id=st_endless.id,
            ),
        )
        await create_rope_allowed_splice_factory(
            session,
            CreateRopeAllowedSpliceFixtureDTO(
                product_id=prod_cruising.id,
                splice_type_id=st_takling.id,
            ),
        )

        # Канат 2: Dyneema Rope (High-Tech)
        prod_dyneema = await create_product_factory(
            session,
            CreateProductFixtureDTO(
                category_id=cat_ropes.id,
                slug="dyneema-sk78-racing",
                price_unit="meter",
                has_configurator=True,
                index=2,
                locale=Language.ENG,
                name="Dyneema SK78 Racing Braid",
                subtitle="Ultra low stretch performance line",
                description="Racing performance line with Dyneema SK78 core and Technora cover.",
            ),
        )
        await create_product_translation_factory(
            session,
            CreateProductTranslationFixtureDTO(
                product_id=prod_dyneema.id,
                locale=Language.RUS,
                name="Dyneema SK78 Racing",
                subtitle="Канат с минимальным растяжением для гонок",
                description="Высокотехнологичный канат с сердечником Dyneema SK78 и защитной оплеткой.",
            ),
        )
        await create_product_translation_factory(
            session,
            CreateProductTranslationFixtureDTO(
                product_id=prod_dyneema.id,
                locale=Language.GER,
                name="Dyneema SK78 Racing-Tauwerk",
                subtitle="Extrem dehnungsarmes Hochleistungstauwerk",
                description="Regattatauerk mit Dyneema SK78 Kern und abriebfestem Mantel.",
            ),
        )

        await create_rope_product_factory(
            session,
            CreateRopeProductFixtureDTO(
                product_id=prod_dyneema.id,
                material_group_id=mg_dyneema.id,
                material_id=m_dyn_sk78.id,
                splice_material_id=sm_hightech.id,
                construction="12-strand braided core with Technora/Polyester cover",
                core_description="Dyneema SK78 12-strand coated core",
                cover_description="50/50 Technora / Polyester braid",
                can_be_spliced=True,
            ),
        )

        await create_rope_variant_factory(
            session,
            CreateRopeVariantFixtureDTO(
                product_id=prod_dyneema.id,
                variant_name="8 мм",
                size_value=8.0,
                price=4.50,
                breaking_load_dan=3500.0,
                working_load_dan=1100.0,
                weight_g=45.0,
                index=1,
                is_active=True,
            ),
        )
        await create_rope_variant_factory(
            session,
            CreateRopeVariantFixtureDTO(
                product_id=prod_dyneema.id,
                variant_name="10 мм",
                size_value=10.0,
                price=6.80,
                breaking_load_dan=5000.0,
                working_load_dan=1600.0,
                weight_g=60.0,
                index=2,
                is_active=True,
            ),
        )
        await create_rope_variant_factory(
            session,
            CreateRopeVariantFixtureDTO(
                product_id=prod_dyneema.id,
                variant_name="12 мм",
                size_value=12.0,
                price=9.50,
                breaking_load_dan=7200.0,
                working_load_dan=2300.0,
                weight_g=85.0,
                index=3,
                is_active=True,
            ),
        )

        await create_rope_product_color_factory(
            session,
            CreateRopeProductColorFixtureDTO(
                product_id=prod_dyneema.id,
                color_id=c_navy.id,
                index=1,
            ),
        )
        await create_rope_product_color_factory(
            session,
            CreateRopeProductColorFixtureDTO(
                product_id=prod_dyneema.id,
                color_id=c_red.id,
                index=2,
            ),
        )

        await create_rope_allowed_splice_factory(
            session,
            CreateRopeAllowedSpliceFixtureDTO(
                product_id=prod_dyneema.id,
                splice_type_id=st_aug.id,
            ),
        )
        await create_rope_allowed_splice_factory(
            session,
            CreateRopeAllowedSpliceFixtureDTO(
                product_id=prod_dyneema.id,
                splice_type_id=st_soft_shackle.id,
            ),
        )
        await create_rope_allowed_splice_factory(
            session,
            CreateRopeAllowedSpliceFixtureDTO(
                product_id=prod_dyneema.id,
                splice_type_id=st_endless.id,
            ),
        )

        # 11. Пример готовых заявок (Quote Requests)
        print("  -> Creating Example Quote Requests...")
        await create_quote_request_factory(
            session,
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
                        product_id=prod_cruising.id,
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
                        name_snapshot="Leder-Kauschschutz",
                        billing_type_snapshot="fixed",
                        quantity=1,
                        unit_price_snapshot=18.50,
                        total_cost=18.50,
                    )
                ],
            ),
        )

        await create_quote_request_factory(
            session,
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
            ),
        )

    print("\n[OK] Test data population successfully completed!")


async def main():
    conf = Config()
    await clear_database(conf)
    await fill_data(conf)


if __name__ == "__main__":
    asyncio.run(main())

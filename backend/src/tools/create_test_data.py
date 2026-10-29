import asyncio
import os
import sys
from pathlib import Path

# Add project and backend root directories to sys.path
_current = Path(__file__).resolve()
BASE_DIR = _current.parent.parent.parent
for _p in (_current.parent.parent.parent, _current.parent.parent.parent.parent):
    if _p.exists() and str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

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
from src.modules.reviews.models import ReviewsStatus
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
from tests.modules.charity_photos.fixtures.factory import (
    create_charity_photo_factory,
)
from tests.modules.charity_photos.fixtures.models_dto import (
    CreateCharityPhotoFixtureDTO,
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
from tests.modules.contact_requests.fixtures.factory import (
    create_contact_request_factory,
)
from tests.modules.contact_requests.fixtures.models_dto import (
    CreateContactRequestFixtureDTO,
)
from tests.modules.content_blocks.fixtures.factory import (
    create_content_block_factory,
    create_content_block_translation_factory,
)
from tests.modules.content_blocks.fixtures.models_dto import (
    CreateContentBlockFixtureDTO,
    CreateContentBlockTranslationFixtureDTO,
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
from tests.modules.product_application.fixtures.factory import (
    create_product_application_factory,
    create_product_application_translation_factory,
    create_product_assigned_application_factory,
)
from tests.modules.product_application.fixtures.models_dto import (
    CreateProductApplicationFixtureDTO,
    CreateProductApplicationTranslationFixtureDTO,
    CreateProductAssignedApplicationFixtureDTO,
)
from tests.modules.product_images.fixtures.factory import (
    create_product_image_factory,
)
from tests.modules.product_images.fixtures.models_dto import (
    CreateProductImageFixtureDTO,
)
from tests.modules.product_specification.fixtures.factory import (
    create_product_specification_factory,
    create_product_specification_translation_factory,
)
from tests.modules.product_specification.fixtures.models_dto import (
    CreateProductSpecificationFixtureDTO,
    CreateProductSpecificationTranslationFixtureDTO,
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
from tests.modules.reviews.fixtures.factory import (
    create_review_factory,
    create_review_translation_factory,
)
from tests.modules.reviews.fixtures.models_dto import (
    CreateReviewFixtureDTO,
    CreateReviewTranslationFixtureDTO,
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
from tests.modules.work_photos.fixtures.factory import (
    create_work_photo_factory,
)
from tests.modules.work_photos.fixtures.models_dto import (
    CreateWorkPhotoFixtureDTO,
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
        # ==========================================
        # 1. Системные настройки (Settings)
        # ==========================================
        print("  -> Creating Settings...")
        settings_record = Settings(
            company_name="Nordic Rigging & Rope Works",
            contact_email="service@nordic-ropes.com",
            contact_phone="+49 (40) 890-1234",
            site_url="https://nordic-ropes.com",
            telegram_chat_id="-100192837465",
            telegram_notifications_enabled=True,
            email_notifications_enabled=True,
            manager_notification_email="orders@nordic-ropes.com",
            manager_email_notifications_enabled=True,
        )
        session.add(settings_record)
        await session.commit()

        # ==========================================
        # 2. Пользователи (Users)
        # ==========================================
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
                email="rigging.master@rope-expert.com",
                username="master_klaus",
                password="masterpassword123",
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
        await create_user_factory(
            session,
            crypto_context,
            CreateUserFixtureDTO(
                email="skipper.alex@baltic-sail.org",
                username="skipper_alex",
                password="skipperpassword123",
                role=UserRole.USER,
            ),
        )
        await create_user_factory(
            session,
            crypto_context,
            CreateUserFixtureDTO(
                email="anna.berg@hamburg-rigging.de",
                username="anna_berg",
                password="annapassword123",
                role=UserRole.USER,
            ),
        )

        # ==========================================
        # 3. Цвета канатов (Colors + Translations)
        # ==========================================
        print("  -> Creating Colors...")
        colors_meta = [
            ("navy_blue", "#000080", 1, "Navy Blue", "Темно-синий", "Marineblau"),
            ("white", "#FFFFFF", 2, "White", "Белый", "Weiß"),
            ("black", "#000000", 3, "Black", "Черный", "Schwarz"),
            ("red_flecks", "#FF4500", 4, "White with red flecks", "Белый с красными крапинками", "Weiß mit roten Flecken"),
            ("solid_red", "#D62828", 5, "Solid Red", "Ярко-красный", "Rot"),
            ("silver_grey", "#A8B2B7", 6, "Silver Grey", "Серебристо-серый", "Silbergrau"),
            ("racing_green", "#2D6A4F", 7, "Racing Green", "Гоночный зеленый", "Racing-Grün"),
            ("navy_yellow_flecks", "#1D3557", 8, "Navy with yellow flecks", "Синий с желтыми крапинками", "Marineblau mit gelben Flecken"),
            ("signal_orange", "#F77F00", 9, "Signal Orange", "Сигнальный оранжевый", "Signalorange"),
            ("anthracite", "#2F3542", 10, "Anthracite", "Антрацит", "Anthrazit"),
            ("ocean_blue", "#0077B6", 11, "Ocean Blue", "Океанский синий", "Ozeanblau"),
            ("classic_hemp", "#D4A373", 12, "Classic Hemp / Spunflex", "Классическая пенька", "Klassik Hanfoptik"),
        ]
        created_colors = {}
        for code, hex_val, idx, name_en, name_ru, name_de in colors_meta:
            c = await create_color_factory(
                session,
                CreateColorFixtureDTO(
                    code=code,
                    hex=hex_val,
                    index=idx,
                    locale=Language.ENG,
                    name=name_en,
                ),
            )
            await create_color_translation_factory(
                session,
                CreateColorTranslationFixtureDTO(color_id=c.id, locale=Language.RUS, name=name_ru),
            )
            await create_color_translation_factory(
                session,
                CreateColorTranslationFixtureDTO(color_id=c.id, locale=Language.GER, name=name_de),
            )
            created_colors[code] = c

        # ==========================================
        # 4. Группы материалов (Material Groups)
        # ==========================================
        print("  -> Creating Material Groups...")
        material_groups_meta = [
            ("polyester", 1, "Polyester", "Полиэстер", "Polyester"),
            ("dyneema", 2, "Dyneema (HMPE)", "Дайнима (Dyneema HMPE)", "Dyneema (HMPE)"),
            ("polyamide", 3, "Polyamide (Nylon)", "Полиамид (Нейлон)", "Polyamid (Nylon)"),
            ("aramid_technora", 4, "Technora / Aramid", "Технора и Арамид", "Technora / Aramid"),
            ("polypropylene", 5, "Polypropylene (Floating)", "Полипропилен (Плавающий)", "Schwimmfähiges Polypropylen"),
        ]
        created_mg = {}
        for code, idx, name_en, name_ru, name_de in material_groups_meta:
            mg = await create_material_group_factory(
                session,
                CreateMaterialGroupFixtureDTO(
                    code=code,
                    index=idx,
                    locale=Language.ENG,
                    name=name_en,
                ),
            )
            await create_material_group_translation_factory(
                session,
                CreateMaterialGroupTranslationFixtureDTO(material_group_id=mg.id, locale=Language.RUS, name=name_ru),
            )
            await create_material_group_translation_factory(
                session,
                CreateMaterialGroupTranslationFixtureDTO(material_group_id=mg.id, locale=Language.GER, name=name_de),
            )
            created_mg[code] = mg

        # ==========================================
        # 5. Материалы внутри групп (Materials)
        # ==========================================
        print("  -> Creating Materials...")
        materials_meta = [
            ("pes_standard", "polyester", 1, "High-tenacity Polyester", "Высокопрочный полиэстер", "Hochfestes Polyester"),
            ("pes_low_stretch", "polyester", 2, "Heat-set Low-Stretch Polyester", "Термофиксированный полиэстер", "Vorgerecktes Polyester"),
            ("sk78", "dyneema", 3, "Dyneema SK78", "Dyneema SK78", "Dyneema SK78"),
            ("sk99", "dyneema", 4, "Dyneema SK99 Ultra-Modulus", "Dyneema SK99 Ультра-модуль", "Dyneema SK99 Ultra-Modul"),
            ("pa_nylon66", "polyamide", 5, "High-Elastic Polyamide 6.6", "Высокоэластичный полиамид 6.6", "Hochelastisches Polyamid 6.6"),
            ("technora_blend", "aramid_technora", 6, "Technora Aramid Hybrid", "Композит Technora Aramid", "Technora-Aramid-Gewebe"),
            ("pp_multitwist", "polypropylene", 7, "Lightweight Floating Polypropylene", "Легкий плавающий полипропилен", "Leichtes schwimmfähiges PP"),
        ]
        created_materials = {}
        for code, mg_code, idx, name_en, name_ru, name_de in materials_meta:
            m = await create_material_factory(
                session,
                CreateMaterialFixtureDTO(
                    material_group_id=created_mg[mg_code].id,
                    code=code,
                    index=idx,
                    locale=Language.ENG,
                    name=name_en,
                ),
            )
            await create_material_translation_factory(
                session,
                CreateMaterialTranslationFixtureDTO(material_id=m.id, locale=Language.RUS, name=name_ru),
            )
            await create_material_translation_factory(
                session,
                CreateMaterialTranslationFixtureDTO(material_id=m.id, locale=Language.GER, name=name_de),
            )
            created_materials[code] = m

        # ==========================================
        # 6. Материалы заделок (Splice Materials)
        # ==========================================
        print("  -> Creating Splice Materials...")
        splice_materials_meta = [
            ("standard_core", "Kern-Mantel Standard Polyester"),
            ("high_tech_dyneema", "High-Tech Dyneema Hohlgeflecht"),
            ("polyester_3strand", "3-Kardelig Polyester geschlagen"),
            ("octoplait_polyamide", "8-plait Squareline Polyamid"),
            ("technora_heat", "Technora Heat-Resistant Cover"),
        ]
        created_sm = {}
        for code, name in splice_materials_meta:
            sm = await create_splice_material_factory(
                session,
                CreateSpliceMaterialFixtureDTO(
                    code=code,
                    name=name,
                ),
            )
            created_sm[code] = sm

        # ==========================================
        # 7. Типы заделок (Splice Types + Translations)
        # ==========================================
        print("  -> Creating Splice Types...")
        splice_types_meta = [
            (
                "aug_splice",
                SpliceCategory.LOOP,
                SpliceVisualType.AUG_SPLICE,
                "/assets/splices/aug_splice.webp",
                1,
                "Eye Splice",
                "Classic eye splice with secure finish",
                "Огон (Петля со сплайсом)",
                "Классический огон с надежной заделкой свободного конца",
                "Augspleiß",
                "Klassischer Augspleiß für festen Halt und hohe Bruchlast",
            ),
            (
                "endless_splice",
                SpliceCategory.SPLICE,
                SpliceVisualType.ENDLESS_SPLICE,
                "/assets/splices/endless.webp",
                2,
                "Endless Splice",
                "Continuous loop splicing of rope ends",
                "Бесконечное сращивание (Endless Splice)",
                "Сращивание концов каната в единое неразрывное кольцо для закруток",
                "Endlosspleiß",
                "Verbindung von zwei Enden zu einer geschlossenen Schlinge für Endlosroller",
            ),
            (
                "takling",
                SpliceCategory.LOOP,
                SpliceVisualType.TAKLING,
                "/assets/splices/takling.webp",
                3,
                "Whipped End (Takling)",
                "Sewn whipping to protect rope end from fraying",
                "Марка прошивная (Takling)",
                "Плотная марка плетеной нитью для защиты конца каната от распускания",
                "Takling genäht",
                "Solider genähter Takling zur Sicherung des Tauwerkendes vor Aufdrehen",
            ),
            (
                "soft_shackle",
                SpliceCategory.LOOP,
                SpliceVisualType.SOFT_SHACKLE,
                "/assets/splices/soft_shackle.webp",
                4,
                "Soft Shackle",
                "Lightweight high-strength Dyneema soft shackle with diamond knot",
                "Мягкая мочка (Soft Shackle)",
                "Высокопрочная сверхлегкая скоба из Dyneema с алмазным узлом",
                "Softschäkel",
                "Leichter und extrem stabiler Dyneema-Schäkel mit Diamantknoten",
            ),
            (
                "kausche_splice",
                SpliceCategory.LOOP,
                SpliceVisualType.KAUSCHE,
                "/assets/splices/kausche.webp",
                5,
                "Eye Splice with SS Thimble",
                "Heavy-duty eye splice enclosing a marine-grade AISI 316 stainless steel thimble",
                "Огон с коушем из нержавеющей стали",
                "Усиленный огон с запрессовкой нержавеющего коуша AISI 316 для швартовов и якорей",
                "Kauschspleiß mit Edelstahlkausche",
                "Professioneller Kauschspleiß mit eingelegter Edelstahlkausche V4A",
            ),
            (
                "pilotauge",
                SpliceCategory.LOOP,
                SpliceVisualType.PILOTAUGE,
                "/assets/splices/pilotauge.webp",
                6,
                "Messenger Pilot Loop",
                "Small eye splice at halyard tail to attach reeving lines easily inside the mast",
                "Огон-проводник для мачты",
                "Компактный мини-огон на хвостовой части фала для затягивания проводника в мачту",
                "Pilotauge / Einziehspleiß",
                "Kleines Auge am Fallende zum problemlosen Einziehen mit einer Pilotleine",
            ),
            (
                "friction_ring_splice",
                SpliceCategory.LOOP,
                SpliceVisualType.FRICTION_RING,
                "/assets/splices/friction_ring.webp",
                7,
                "Low Friction Ring Splice",
                "High-performance loop splicing around an anodized hard-lube low friction ring",
                "Сплайс с кольцом низкого трения",
                "Сплайс из Dyneema с кольцом низкого трения для оттяжек и барбер-чаулеров",
                "Low-Friction-Ring Spleiß",
                "Spleiß mit integriertem Aluminium Low-Friction-Ring für moderne Trimmsysteme",
            ),
        ]
        created_st = {}
        for code, cat, vis_type, img, idx, n_en, d_en, n_ru, d_ru, n_de, d_de in splice_types_meta:
            st = await create_splice_type_factory(
                session,
                CreateSpliceTypeFixtureDTO(
                    code=code,
                    category=cat,
                    visual_type=vis_type,
                    image_url=img,
                    index=idx,
                    locale=Language.ENG,
                    name=n_en,
                    description=d_en,
                ),
            )
            await create_splice_type_translation_factory(
                session,
                CreateSpliceTypeTranslationFixtureDTO(
                    splice_type_id=st.id,
                    locale=Language.RUS,
                    name=n_ru,
                    description=d_ru,
                ),
            )
            await create_splice_type_translation_factory(
                session,
                CreateSpliceTypeTranslationFixtureDTO(
                    splice_type_id=st.id,
                    locale=Language.GER,
                    name=n_de,
                    description=d_de,
                ),
            )
            created_st[code] = st

        # ==========================================
        # 8. Правила цен (Splice Price Rules)
        # ==========================================
        print("  -> Creating Splice Price Rules...")
        # (splice_type, splice_mat, d_from, d_to, price)
        price_rules_data = [
            # Eye Splice - Standard
            ("aug_splice", "standard_core", 0.0, 12.0, 15.00),
            ("aug_splice", "standard_core", 12.0, 18.0, 22.00),
            ("aug_splice", "standard_core", 18.0, 30.0, 35.00),
            # Eye Splice - High Tech Dyneema
            ("aug_splice", "high_tech_dyneema", 0.0, 10.0, 25.00),
            ("aug_splice", "high_tech_dyneema", 10.0, 16.0, 38.00),
            ("aug_splice", "high_tech_dyneema", 16.0, 30.0, 52.00),
            # Eye Splice - 3-Strand Polyester
            ("aug_splice", "polyester_3strand", 0.0, 16.0, 14.00),
            ("aug_splice", "polyester_3strand", 16.0, 30.0, 24.00),
            # Eye Splice - 8-plait Squareline
            ("aug_splice", "octoplait_polyamide", 0.0, 16.0, 22.00),
            ("aug_splice", "octoplait_polyamide", 16.0, 30.0, 34.00),

            # Endless Splice
            ("endless_splice", "standard_core", 0.0, 14.0, 35.00),
            ("endless_splice", "standard_core", 14.0, 24.0, 48.00),
            ("endless_splice", "high_tech_dyneema", 0.0, 14.0, 60.00),
            ("endless_splice", "high_tech_dyneema", 14.0, 24.0, 85.00),

            # Whipped End (Takling)
            ("takling", "standard_core", 0.0, 30.0, 6.00),
            ("takling", "high_tech_dyneema", 0.0, 30.0, 9.00),
            ("takling", "polyester_3strand", 0.0, 30.0, 5.00),
            ("takling", "octoplait_polyamide", 0.0, 30.0, 7.00),

            # Soft Shackle
            ("soft_shackle", "high_tech_dyneema", 0.0, 10.0, 22.00),
            ("soft_shackle", "high_tech_dyneema", 10.0, 18.0, 32.00),

            # Kausche Splice (with Thimble)
            ("kausche_splice", "standard_core", 0.0, 14.0, 26.00),
            ("kausche_splice", "standard_core", 14.0, 24.0, 38.00),
            ("kausche_splice", "polyester_3strand", 0.0, 16.0, 20.00),
            ("kausche_splice", "polyester_3strand", 16.0, 30.0, 32.00),
            ("kausche_splice", "octoplait_polyamide", 0.0, 16.0, 28.00),
            ("kausche_splice", "octoplait_polyamide", 16.0, 30.0, 42.00),

            # Pilotauge
            ("pilotauge", "standard_core", 0.0, 30.0, 10.00),
            ("pilotauge", "high_tech_dyneema", 0.0, 30.0, 14.00),

            # Friction Ring Splice
            ("friction_ring_splice", "high_tech_dyneema", 0.0, 14.0, 45.00),
            ("friction_ring_splice", "high_tech_dyneema", 14.0, 24.0, 65.00),
        ]
        for st_code, sm_code, d_from, d_to, pr in price_rules_data:
            await create_splice_price_rule_factory(
                session,
                CreateSplicePriceRuleFixtureDTO(
                    splice_type_id=created_st[st_code].id,
                    splice_material_id=created_sm[sm_code].id,
                    diameter_from_mm=d_from,
                    diameter_to_mm=d_to,
                    price=pr,
                ),
            )

        # ==========================================
        # 9. Дополнительные опции (Configurator Extras)
        # ==========================================
        print("  -> Creating Configurator Extras...")
        extras_meta = [
            (
                "leather_protection",
                BillingType.FIXED,
                18.50,
                1,
                "Leather eye protection",
                "Natural marine leather eye protection from abrasion in chocks",
                "Кожаная оплетка для огона",
                "Защита петли натуральной морской кожей от перетирания в клюзе",
                "Leder-Kauschschutz",
                "Echtes Segelleder zum Schutz des Auges vor Scheuerstellen in Klüsen",
            ),
            (
                "chafe_sleeve",
                BillingType.PER_METER,
                6.50,
                2,
                "Chafe protection sleeve (per meter)",
                "Heavy-duty sliding chafe sleeve made of Cordura or Dyneema",
                "Защитный чехол от истирания (за метр)",
                "Сверхпрочный скользящий чехол из Cordura или Dyneema",
                "Scheuerschutz-Schlauch (pro Meter)",
                "Geflochtener Scheuerschutz aus Dyneema oder Cordura für Festmacher und Fallen",
            ),
            (
                "break_load_cert",
                BillingType.FIXED,
                35.00,
                3,
                "Break load test certificate",
                "Official calibrated test bench certificate of breaking strength",
                "Сертификат испытания на разрыв",
                "Протокол заводских испытаний готового изделия на сертифицированном стенде",
                "Prüfzeugnis / Zugtest-Zertifikat",
                "Offizielles kalibriertes Messprotokoll der Bruchlastprüfung auf der Prüfbank",
            ),
            (
                "stainless_thimble",
                BillingType.FIXED,
                12.00,
                4,
                "Marine Stainless Steel Thimble AISI 316",
                "High polish AISI 316 heavy stainless steel thimble for eye splice",
                "Коуш из нержавеющей стали AISI 316",
                "Усиленный полированный коуш из морской нержавеющей стали для огона",
                "Edelstahlkausche AISI 316",
                "Hochglanzpolierte schwere Edelstahlkausche für Augspleiße",
            ),
            (
                "custom_laser_label",
                BillingType.FIXED,
                7.50,
                5,
                "Custom Heat-Shrink Identity Label",
                "Durable clear heat-shrink tubing printed with line name, yacht name, or length",
                "Индивидуальная маркировка термоусадкой",
                "Термоусадочная маркировка с указанием фала, длины или названия яхты",
                "Individueller Beschriftungsschlauch",
                "Transparenter Schrumpfschlauch mit individuellem Druck (z.B. Fall-Name, Bootsname)",
            ),
            (
                "pu_waterproof_coating",
                BillingType.PER_METER,
                3.20,
                6,
                "PU UV & Abrasion Protection Dip (per meter)",
                "Polyurethane immersion treatment enhancing UV durability and water repulsion",
                "Полиуретановая защитная пропитка (за метр)",
                "Глубокая пропитка полиуретановым лаком для защиты от соли, влаги и УФ",
                "PU-Schutzbeschichtung (pro Meter)",
                "Flüssige Polyurethan-Versiegelung gegen Abrieb, UV und Salzwasseraufnahme",
            ),
        ]
        created_extras = {}
        for code, b_type, price, idx, n_en, d_en, n_ru, d_ru, n_de, d_de in extras_meta:
            ex = await create_configurator_extra_factory(
                session,
                CreateConfiguratorExtraFixtureDTO(
                    code=code,
                    billing_type=b_type,
                    price=price,
                    currency=Currency.EUR,
                    index=idx,
                    locale=Language.ENG,
                    name=n_en,
                    description=d_en,
                ),
            )
            await create_configurator_extra_translation_factory(
                session,
                CreateConfiguratorExtraTranslationFixtureDTO(
                    extra_id=ex.id,
                    locale=Language.RUS,
                    name=n_ru,
                    description=d_ru,
                ),
            )
            await create_configurator_extra_translation_factory(
                session,
                CreateConfiguratorExtraTranslationFixtureDTO(
                    extra_id=ex.id,
                    locale=Language.GER,
                    name=n_de,
                    description=d_de,
                ),
            )
            created_extras[code] = ex

        # ==========================================
        # 10. Настройки конфигуратора (Configurator Settings)
        # ==========================================
        print("  -> Creating Configurator Settings...")
        await create_configurator_setting_factory(
            session,
            CreateConfiguratorSettingFixtureDTO(
                min_length_m=1.0,
                max_length_m=350.0,
                splice_allowance_until_mm=12.0,
                splice_allowance_until_m=0.6,
                splice_allowance_over_m=1.0,
                urgent_surcharge_per_splice=12.50,
                urgent_max_splices=12,
                standard_turnaround_hours=72,
                urgent_turnaround_hours=24,
                currency=Currency.EUR,
                vat_rate=19.0,
                vat_note="inkl. 19% MwSt.",
            ),
        )

        # ==========================================
        # 11. Назначения товаров (Product Applications)
        # ==========================================
        print("  -> Creating Product Applications...")
        apps_meta = [
            ("halyard", 1, "Halyards (Main, Jib, Gennaker)", "Фалы (Грот, Стаксель, Генакер)", "Fallen (Groß, Genua, Spinnaker)"),
            ("sheet", 2, "Sheets & Guys", "Шкоты и брассы", "Schoten & Achterholer"),
            ("mooring", 3, "Mooring & Dock Lines", "Швартовные концы", "Festmacherleinen"),
            ("anchor", 4, "Anchor Rode & Warps", "Якорные канаты", "Ankerleinen"),
            ("control_line", 5, "Control Lines & Outhauls", "Оттяжки и рифы", "Trimm- & Reffleinen"),
            ("runner", 6, "Runners & Checkstays", "Бакштаги и оттяжки", "Backstagen & Checkstagen"),
        ]
        created_apps = {}
        for code, idx, n_en, n_ru, n_de in apps_meta:
            app_obj = await create_product_application_factory(
                session,
                CreateProductApplicationFixtureDTO(
                    code=code,
                    index=idx,
                    is_active=True,
                    locale=Language.ENG,
                    name=n_en,
                ),
            )
            await create_product_application_translation_factory(
                session,
                CreateProductApplicationTranslationFixtureDTO(
                    application_id=app_obj.id,
                    locale=Language.RUS,
                    name=n_ru,
                ),
            )
            await create_product_application_translation_factory(
                session,
                CreateProductApplicationTranslationFixtureDTO(
                    application_id=app_obj.id,
                    locale=Language.GER,
                    name=n_de,
                ),
            )
            created_apps[code] = app_obj

        # ==========================================
        # 12. Категории каталога (Categories)
        # ==========================================
        print("  -> Creating Categories...")
        categories_meta = [
            ("cruising-ropes", 1, "Cruising Cordage", "Круизные канаты", "Cruising Tauwerk"),
            ("racing-ropes", 2, "Racing & Performance Lines", "Гоночные канаты", "Regatta- & Racingtauwerk"),
            ("mooring-anchor", 3, "Mooring & Anchor Lines", "Швартовные и якорные канаты", "Festmacher & Ankerleinen"),
            ("dinghy-sport", 4, "Dinghy & Sports Lines", "Швертботы и спорт", "Jollen & Sportboot Tauwerk"),
        ]
        created_cats = {}
        for slug, idx, n_en, n_ru, n_de in categories_meta:
            cat = await create_category_factory(
                session,
                CreateCategoryFixtureDTO(
                    slug=slug,
                    index=idx,
                    locale=Language.ENG,
                    name=n_en,
                ),
            )
            await create_category_translation_factory(
                session,
                CreateCategoryTranslationFixtureDTO(
                    category_id=cat.id,
                    locale=Language.RUS,
                    name=n_ru,
                ),
            )
            await create_category_translation_factory(
                session,
                CreateCategoryTranslationFixtureDTO(
                    category_id=cat.id,
                    locale=Language.GER,
                    name=n_de,
                ),
            )
            created_cats[slug] = cat

        # ==========================================
        # 13. Товары, спецификации, изображения, связи
        # ==========================================
        print("  -> Creating Rope Products, Variants, Specs, Images and Relations...")

        # Вспомогательная функция для назначения характеристик товару
        async def add_product_specs(prod_id: int, specs_list):
            for s_idx, (s_name_en, s_val_en, s_name_ru, s_val_ru, s_name_de, s_val_de) in enumerate(specs_list, start=1):
                spec = await create_product_specification_factory(
                    session,
                    CreateProductSpecificationFixtureDTO(
                        product_id=prod_id,
                        index=s_idx,
                        locale=Language.ENG,
                        name=s_name_en,
                        value=s_val_en,
                    ),
                )
                await create_product_specification_translation_factory(
                    session,
                    CreateProductSpecificationTranslationFixtureDTO(
                        specification_id=spec.id,
                        locale=Language.RUS,
                        name=s_name_ru,
                        value=s_val_ru,
                    ),
                )
                await create_product_specification_translation_factory(
                    session,
                    CreateProductSpecificationTranslationFixtureDTO(
                        specification_id=spec.id,
                        locale=Language.GER,
                        name=s_name_de,
                        value=s_val_de,
                    ),
                )

        # ---------------------------------------------------------
        # Товар 1: Cruising Polyester 16-plait (Круизный полиэстер)
        # ---------------------------------------------------------
        p1 = await create_product_factory(
            session,
            CreateProductFixtureDTO(
                category_id=created_cats["cruising-ropes"].id,
                slug="cruising-polyester-16",
                price_unit="meter",
                has_configurator=True,
                construction_type="polyester_core",
                index=1,
                locale=Language.ENG,
                name="Cruising Polyester 16-plait",
                subtitle="Durable all-round cruising rope for halyards and sheets",
                description="High tenacity 16-plait polyester line with outstanding grip on winches and clutches. Perfectly balanced for cruising yachts.",
            ),
        )
        await create_product_translation_factory(
            session,
            CreateProductTranslationFixtureDTO(
                product_id=p1.id,
                locale=Language.RUS,
                name="Cruising Полиэстер 16-прядный",
                subtitle="Надежный универсальный круизный канат для фалов и шкотов",
                description="Высокопрочный 16-прядный плетеный канат из полиэстера. Отлично держит в кулачковых и клавишных стопорах, комфортен для рук.",
            ),
        )
        await create_product_translation_factory(
            session,
            CreateProductTranslationFixtureDTO(
                product_id=p1.id,
                locale=Language.GER,
                name="Cruising Polyester 16-fach",
                subtitle="Langlebiges Universaltauwerk für Fallen und Schoten",
                description="Hochfestes 16-fach geflochtenes Polyestertauwerk mit exzellentem Halt in Klemmen und auf Winschen. Ideal für Fahrtensegler.",
            ),
        )
        await create_rope_product_factory(
            session,
            CreateRopeProductFixtureDTO(
                product_id=p1.id,
                material_group_id=created_mg["polyester"].id,
                material_id=created_materials["pes_standard"].id,
                splice_material_id=created_sm["standard_core"].id,
                construction="16-plait braided core with abrasion-resistant braided cover",
                core_description="High-tenacity 100% PES core",
                cover_description="Durable UV-stabilized PES 16-braid",
                can_be_spliced=True,
            ),
        )
        # Варианты диаметров
        p1_variants = [
            ("8 мм", 8.0, 1.85, 1750.0, 350.0, 4.2, 50.0, "PES16-08", 1),
            ("10 мм", 10.0, 2.60, 2600.0, 520.0, 4.0, 72.0, "PES16-10", 2),
            ("12 мм", 12.0, 3.90, 3700.0, 740.0, 3.8, 105.0, "PES16-12", 3),
            ("14 мм", 14.0, 5.20, 4900.0, 980.0, 3.6, 140.0, "PES16-14", 4),
            ("16 мм", 16.0, 6.80, 6300.0, 1260.0, 3.5, 185.0, "PES16-16", 5),
        ]
        for v_name, s_val, pr, bl, wl, st, w_g, sku, idx in p1_variants:
            await create_rope_variant_factory(
                session,
                CreateRopeVariantFixtureDTO(
                    product_id=p1.id,
                    variant_name=v_name,
                    size_value=s_val,
                    price=pr,
                    breaking_load_dan=bl,
                    working_load_dan=wl,
                    working_stretch_percent=st,
                    weight_g=w_g,
                    sku=sku,
                    index=idx,
                    is_active=True,
                ),
            )
        # Цвета
        for col_idx, col_code in enumerate(["navy_blue", "white", "black", "red_flecks", "racing_green"], start=1):
            await create_rope_product_color_factory(
                session,
                CreateRopeProductColorFixtureDTO(product_id=p1.id, color_id=created_colors[col_code].id, index=col_idx),
            )
        # Разрешенные заделки
        for st_code in ["aug_splice", "takling", "endless_splice", "pilotauge"]:
            await create_rope_allowed_splice_factory(
                session,
                CreateRopeAllowedSpliceFixtureDTO(product_id=p1.id, splice_type_id=created_st[st_code].id),
            )
        # Назначения
        for app_code in ["halyard", "sheet", "control_line"]:
            await create_product_assigned_application_factory(
                session,
                CreateProductAssignedApplicationFixtureDTO(product_id=p1.id, application_id=created_apps[app_code].id),
            )
        # Спецификации
        await add_product_specs(
            p1.id,
            [
                ("Core Material", "100% High-Tenacity Polyester", "Материал сердечника", "100% высокопрочный полиэстер", "Kernmaterial", "100% hochfestes Polyester"),
                ("Cover Material", "16-plait UV-Stabilized Polyester", "Материал оплетки", "16-прядный полиэстер с УФ-защитой", "Mantelmaterial", "16-fach UV-stabilisiertes Polyester"),
                ("Working Stretch", "< 4% at 20% breaking load", "Рабочее удлинение", "< 4% при 20% рабочей нагрузки", "Arbeitsdehnung", "< 4% bei 20% Bruchlast"),
                ("Buoyancy", "Sinking line (Specific gravity 1.38)", "Плавучесть", "Тонущий (удельный вес 1.38)", "Schwimmfähigkeit", "Sinkend (spezifisches Gewicht 1.38)"),
            ],
        )
        # Фото
        await create_product_image_factory(
            session,
            CreateProductImageFixtureDTO(product_id=p1.id, image_url="/assets/products/cruising_pes_1.webp", is_main=True, index=1, is_active=True),
        )
        await create_product_image_factory(
            session,
            CreateProductImageFixtureDTO(product_id=p1.id, image_url="/assets/products/cruising_pes_2.webp", is_main=False, index=2, is_active=True),
        )

        # ---------------------------------------------------------
        # Товар 2: Dyneema SK78 Racing Braid (Гоночный Dyneema)
        # ---------------------------------------------------------
        p2 = await create_product_factory(
            session,
            CreateProductFixtureDTO(
                category_id=created_cats["racing-ropes"].id,
                slug="dyneema-sk78-racing",
                price_unit="meter",
                has_configurator=True,
                construction_type="hm_core",
                index=2,
                locale=Language.ENG,
                name="Dyneema SK78 Racing Braid",
                subtitle="Ultra-low stretch racing performance line",
                description="Engineered for high load applications. Features a 12-strand coated Dyneema SK78 core with an abrasion-resistant Technora/Polyester cover.",
            ),
        )
        await create_product_translation_factory(
            session,
            CreateProductTranslationFixtureDTO(
                product_id=p2.id,
                locale=Language.RUS,
                name="Dyneema SK78 Racing Braid",
                subtitle="Гоночный канат с ультранизким растяжением",
                description="Специально разработан для высоких динамических нагрузок. Сердечник из 12-прядной Dyneema SK78 с оплеткой из Technora и полиэстера.",
            ),
        )
        await create_product_translation_factory(
            session,
            CreateProductTranslationFixtureDTO(
                product_id=p2.id,
                locale=Language.GER,
                name="Dyneema SK78 Racing-Tauwerk",
                subtitle="Extrem dehnungsarmes Hochleistungstauwerk für Regattasegler",
                description="Maximale Festigkeit und minimale Dehnung. 12-fach geflochtener Dyneema SK78 Kern mit griffigem Technora/Polyester-Mantel.",
            ),
        )
        await create_rope_product_factory(
            session,
            CreateRopeProductFixtureDTO(
                product_id=p2.id,
                material_group_id=created_mg["dyneema"].id,
                material_id=created_materials["sk78"].id,
                splice_material_id=created_sm["high_tech_dyneema"].id,
                construction="12-strand braided pre-stretched Dyneema core with 24-plait hybrid cover",
                core_description="Dyneema SK78 polyurethane impregnated",
                cover_description="50/50 Technora / High-tenacity Polyester",
                can_be_spliced=True,
            ),
        )
        p2_variants = [
            ("6 мм", 6.0, 3.40, 2400.0, 750.0, 1.2, 28.0, "DYN78-06", 1),
            ("8 мм", 8.0, 5.10, 4200.0, 1300.0, 1.1, 46.0, "DYN78-08", 2),
            ("10 мм", 10.0, 7.80, 6800.0, 2100.0, 0.9, 70.0, "DYN78-10", 3),
            ("12 мм", 12.0, 11.20, 9500.0, 3000.0, 0.8, 102.0, "DYN78-12", 4),
            ("14 мм", 14.0, 15.60, 13200.0, 4200.0, 0.8, 138.0, "DYN78-14", 5),
        ]
        for v_name, s_val, pr, bl, wl, st, w_g, sku, idx in p2_variants:
            await create_rope_variant_factory(
                session,
                CreateRopeVariantFixtureDTO(
                    product_id=p2.id,
                    variant_name=v_name,
                    size_value=s_val,
                    price=pr,
                    breaking_load_dan=bl,
                    working_load_dan=wl,
                    working_stretch_percent=st,
                    weight_g=w_g,
                    sku=sku,
                    index=idx,
                    is_active=True,
                ),
            )
        for col_idx, col_code in enumerate(["navy_blue", "solid_red", "ocean_blue", "anthracite"], start=1):
            await create_rope_product_color_factory(
                session,
                CreateRopeProductColorFixtureDTO(product_id=p2.id, color_id=created_colors[col_code].id, index=col_idx),
            )
        for st_code in ["aug_splice", "soft_shackle", "takling", "friction_ring_splice", "pilotauge"]:
            await create_rope_allowed_splice_factory(
                session,
                CreateRopeAllowedSpliceFixtureDTO(product_id=p2.id, splice_type_id=created_st[st_code].id),
            )
        for app_code in ["halyard", "sheet", "runner", "control_line"]:
            await create_product_assigned_application_factory(
                session,
                CreateProductAssignedApplicationFixtureDTO(product_id=p2.id, application_id=created_apps[app_code].id),
            )
        await add_product_specs(
            p2.id,
            [
                ("Core Material", "100% Dyneema SK78 Pre-stretched", "Материал сердечника", "100% Dyneema SK78 преднатянутая", "Kernmaterial", "100% Dyneema SK78 verstreckt"),
                ("Cover Material", "Technora / High-Tenacity Polyester", "Материал оплетки", "Комбинация Technora и полиэстера", "Mantelmaterial", "Technora / HT-Polyester Mischung"),
                ("Working Stretch", "< 1% at working load", "Рабочее удлинение", "< 1% при рабочей нагрузке", "Arbeitsdehnung", "< 1% bei Arbeitslast"),
                ("Heat Resistance", "Cover resistant up to 300°C", "Термостойкость", "Оплетка устойчива до 300°C на лебедках", "Hitzebeständigkeit", "Mantel hitzefest bis 300°C"),
            ],
        )
        await create_product_image_factory(
            session,
            CreateProductImageFixtureDTO(product_id=p2.id, image_url="/assets/products/dyneema_sk78_1.webp", is_main=True, index=1, is_active=True),
        )
        await create_product_image_factory(
            session,
            CreateProductImageFixtureDTO(product_id=p2.id, image_url="/assets/products/dyneema_sk78_2.webp", is_main=False, index=2, is_active=True),
        )

        # ---------------------------------------------------------
        # Товар 3: OceanFlex 3-Strand Polyester (Швартовный трехпрядный)
        # ---------------------------------------------------------
        p3 = await create_product_factory(
            session,
            CreateProductFixtureDTO(
                category_id=created_cats["mooring-anchor"].id,
                slug="oceanflex-3strand-polyester",
                price_unit="meter",
                has_configurator=True,
                construction_type="polyester_core",
                index=3,
                locale=Language.ENG,
                name="OceanFlex 3-Strand Polyester Mooring Line",
                subtitle="Classic shock-absorbing mooring and anchor rope",
                description="Traditional 3-strand laid polyester rope. Supple, easy to handle, highly shock absorbent, and remains soft even after years in saltwater.",
            ),
        )
        await create_product_translation_factory(
            session,
            CreateProductTranslationFixtureDTO(
                product_id=p3.id,
                locale=Language.RUS,
                name="OceanFlex 3-прядный полиэстер",
                subtitle="Классический амортизирующий швартовный и якорный канат",
                description="Традиционный крученый трехпрядный канат из термофиксированного полиэстера. Отлично гасит рывки волны, не дубеет в соленой воде.",
            ),
        )
        await create_product_translation_factory(
            session,
            CreateProductTranslationFixtureDTO(
                product_id=p3.id,
                locale=Language.GER,
                name="OceanFlex 3-schäftiges Polyestertauwerk",
                subtitle="Klassischer ruckdämpfender Festmacher und Ankerleine",
                description="Klassisch geschlagenes 3-kardeliges Festmachertauwerk. Hohe Elastizität, bleibt dauerhaft weich und flexibel bei Seewasser.",
            ),
        )
        await create_rope_product_factory(
            session,
            CreateRopeProductFixtureDTO(
                product_id=p3.id,
                material_group_id=created_mg["polyester"].id,
                material_id=created_materials["pes_standard"].id,
                splice_material_id=created_sm["polyester_3strand"].id,
                construction="3-strand laid thermofixed construction",
                core_description="Solid 3-strand polyester twist",
                cover_description="Self-covered laid rope",
                can_be_spliced=True,
            ),
        )
        p3_variants = [
            ("10 мм", 10.0, 2.10, 2100.0, 450.0, 12.0, 80.0, "OF3S-10", 1),
            ("12 мм", 12.0, 2.95, 3000.0, 650.0, 12.0, 115.0, "OF3S-12", 2),
            ("14 мм", 14.0, 4.10, 4100.0, 900.0, 11.5, 155.0, "OF3S-14", 3),
            ("16 мм", 16.0, 5.40, 5300.0, 1150.0, 11.0, 205.0, "OF3S-16", 4),
            ("18 мм", 18.0, 6.90, 6700.0, 1450.0, 10.5, 260.0, "OF3S-18", 5),
            ("20 мм", 20.0, 8.60, 8200.0, 1800.0, 10.0, 320.0, "OF3S-20", 6),
        ]
        for v_name, s_val, pr, bl, wl, st, w_g, sku, idx in p3_variants:
            await create_rope_variant_factory(
                session,
                CreateRopeVariantFixtureDTO(
                    product_id=p3.id,
                    variant_name=v_name,
                    size_value=s_val,
                    price=pr,
                    breaking_load_dan=bl,
                    working_load_dan=wl,
                    working_stretch_percent=st,
                    weight_g=w_g,
                    sku=sku,
                    index=idx,
                    is_active=True,
                ),
            )
        for col_idx, col_code in enumerate(["navy_blue", "black", "white", "classic_hemp"], start=1):
            await create_rope_product_color_factory(
                session,
                CreateRopeProductColorFixtureDTO(product_id=p3.id, color_id=created_colors[col_code].id, index=col_idx),
            )
        for st_code in ["aug_splice", "kausche_splice", "takling"]:
            await create_rope_allowed_splice_factory(
                session,
                CreateRopeAllowedSpliceFixtureDTO(product_id=p3.id, splice_type_id=created_st[st_code].id),
            )
        for app_code in ["mooring", "anchor"]:
            await create_product_assigned_application_factory(
                session,
                CreateProductAssignedApplicationFixtureDTO(product_id=p3.id, application_id=created_apps[app_code].id),
            )
        await add_product_specs(
            p3.id,
            [
                ("Material", "100% High-Tenacity Thermofixed Polyester", "Материал", "100% высокопрочный термофиксированный полиэстер", "Material", "100% hochfestes Polyester"),
                ("Elongation at Break", "Approx. 18-20% for excellent shock absorption", "Удлинение при разрыве", "Около 18-20% для мягкого гашения рывков", "Bruchdehnung", "Ca. 18-20% für sanfte Ruckdämpfung"),
                ("UV Stability", "Superior UV protection (500kLy rating)", "УФ-стабильность", "Наивысшая стойкость к солнечному свету", "UV-Beständigkeit", "Hervorragende UV-Stabilität"),
            ],
        )
        await create_product_image_factory(
            session,
            CreateProductImageFixtureDTO(product_id=p3.id, image_url="/assets/products/oceanflex_3s_1.webp", is_main=True, index=1, is_active=True),
        )

        # ---------------------------------------------------------
        # Товар 4: Squareline 8-Plait Polyamide (Премиальный 8-прядный швартов)
        # ---------------------------------------------------------
        p4 = await create_product_factory(
            session,
            CreateProductFixtureDTO(
                category_id=created_cats["mooring-anchor"].id,
                slug="squareline-8plait-polyamide",
                price_unit="meter",
                has_configurator=True,
                construction_type="none",
                index=4,
                locale=Language.ENG,
                name="Squareline 8-Plait Polyamide Dockline",
                subtitle="Non-kinking premium 8-strand dockline with high elasticity",
                description="Square braided 8-strand high-elastic nylon dockline. Kink-free, extremely flexible, easy to coil, and stores compactly in deck lockers.",
            ),
        )
        await create_product_translation_factory(
            session,
            CreateProductTranslationFixtureDTO(
                product_id=p4.id,
                locale=Language.RUS,
                name="Squareline 8-прядный полиамид",
                subtitle="Премиальный нескручивающийся 8-прядный швартов с высокой эластичностью",
                description="8-прядный квадратного плетения швартовный конец из полиамида. Никогда не образует колышек, исключительно мягкий и эластичный.",
            ),
        )
        await create_product_translation_factory(
            session,
            CreateProductTranslationFixtureDTO(
                product_id=p4.id,
                locale=Language.GER,
                name="Squareline 8-fach quadratgeflochtenes Polyamid",
                subtitle="Knickfreier Premium-Festmacher mit maximaler Dehnung",
                description="8-schäftig quadratgeflochtene Festmacherleine aus Polyamid. Kinkt nicht, extrem flexibel und dämpft auch starke Windböen sicher ab.",
            ),
        )
        await create_rope_product_factory(
            session,
            CreateRopeProductFixtureDTO(
                product_id=p4.id,
                material_group_id=created_mg["polyamide"].id,
                material_id=created_materials["pa_nylon66"].id,
                splice_material_id=created_sm["octoplait_polyamide"].id,
                construction="8-plait balanced square braid",
                core_description="8-strand torque balanced polyamide",
                cover_description="Self-covered square braid",
                can_be_spliced=True,
            ),
        )
        p4_variants = [
            ("12 мм", 12.0, 3.40, 3400.0, 750.0, 16.0, 95.0, "SQL8-12", 1),
            ("14 мм", 14.0, 4.60, 4700.0, 1050.0, 16.0, 130.0, "SQL8-14", 2),
            ("16 мм", 16.0, 6.10, 6100.0, 1350.0, 15.0, 175.0, "SQL8-16", 3),
            ("18 мм", 18.0, 7.80, 7700.0, 1700.0, 15.0, 225.0, "SQL8-18", 4),
            ("20 мм", 20.0, 9.70, 9500.0, 2100.0, 14.0, 275.0, "SQL8-20", 5),
        ]
        for v_name, s_val, pr, bl, wl, st, w_g, sku, idx in p4_variants:
            await create_rope_variant_factory(
                session,
                CreateRopeVariantFixtureDTO(
                    product_id=p4.id,
                    variant_name=v_name,
                    size_value=s_val,
                    price=pr,
                    breaking_load_dan=bl,
                    working_load_dan=wl,
                    working_stretch_percent=st,
                    weight_g=w_g,
                    sku=sku,
                    index=idx,
                    is_active=True,
                ),
            )
        for col_idx, col_code in enumerate(["navy_blue", "black", "silver_grey"], start=1):
            await create_rope_product_color_factory(
                session,
                CreateRopeProductColorFixtureDTO(product_id=p4.id, color_id=created_colors[col_code].id, index=col_idx),
            )
        for st_code in ["aug_splice", "kausche_splice", "takling"]:
            await create_rope_allowed_splice_factory(
                session,
                CreateRopeAllowedSpliceFixtureDTO(product_id=p4.id, splice_type_id=created_st[st_code].id),
            )
        for app_code in ["mooring", "anchor"]:
            await create_product_assigned_application_factory(
                session,
                CreateProductAssignedApplicationFixtureDTO(product_id=p4.id, application_id=created_apps[app_code].id),
            )
        await add_product_specs(
            p4.id,
            [
                ("Material", "100% Polyamide 6.6 High Tenacity", "Материал", "100% полиамид 6.6 высокой прочности", "Material", "100% Polyamid 6.6 hochfest"),
                ("Shock Absorption", "Maximum energy damping (> 20% stretch)", "Амортизация", "Максимальное поглощение рывков (> 20% удлинение)", "Ruckdämpfung", "Hervorragend (> 20% Dehnung)"),
                ("Handling", "Zero torsion, no kink formation", "Удобство", "Полное отсутствие скручивания и заломов", "Handling", "Vollkommen drallfrei, kein Kinken"),
            ],
        )
        await create_product_image_factory(
            session,
            CreateProductImageFixtureDTO(product_id=p4.id, image_url="/assets/products/squareline_1.webp", is_main=True, index=1, is_active=True),
        )

        # ---------------------------------------------------------
        # Товар 5: Dyneema SK99 Grand Prix Pro (Топовый гоночный)
        # ---------------------------------------------------------
        p5 = await create_product_factory(
            session,
            CreateProductFixtureDTO(
                category_id=created_cats["racing-ropes"].id,
                slug="dyneema-sk99-grand-prix",
                price_unit="meter",
                has_configurator=True,
                construction_type="hm_core",
                index=5,
                locale=Language.ENG,
                name="Dyneema SK99 Grand Prix Pro",
                subtitle="The ultimate high-modulus racing line for TP52, Class40 and Maxi yachts",
                description="Uncompromised racing performance. Featuring pure Dyneema SK99 core delivering up to 20% higher breaking strength than SK78 at identical diameter.",
            ),
        )
        await create_product_translation_factory(
            session,
            CreateProductTranslationFixtureDTO(
                product_id=p5.id,
                locale=Language.RUS,
                name="Dyneema SK99 Grand Prix Pro",
                subtitle="Флагманский высокомодульный гоночный канат для TP52, Class40 и Maxi",
                description="Бескомпромиссный гоночный канат. Сердечник из Dyneema SK99 обеспечивает на 20% большую прочность, чем SK78, при минимальном весе.",
            ),
        )
        await create_product_translation_factory(
            session,
            CreateProductTranslationFixtureDTO(
                product_id=p5.id,
                locale=Language.GER,
                name="Dyneema SK99 Grand Prix Pro",
                subtitle="Ultimatives High-Modulus Regattatauwerk für maximale Ansprüche",
                description="Kompromisslose Performance für Grand-Prix-Yachten. Dyneema SK99 Kern bietet 20% mehr Festigkeit als SK78 bei geringstem Gewicht.",
            ),
        )
        await create_rope_product_factory(
            session,
            CreateRopeProductFixtureDTO(
                product_id=p5.id,
                material_group_id=created_mg["dyneema"].id,
                material_id=created_materials["sk99"].id,
                splice_material_id=created_sm["high_tech_dyneema"].id,
                construction="12-strand heat-stretched Dyneema SK99 core with Technora/Cordura cover",
                core_description="Pure Dyneema SK99 HPS pre-stretched",
                cover_description="Technora / Cordura / Dyneema 32-plait racing jacket",
                can_be_spliced=True,
            ),
        )
        p5_variants = [
            ("7 мм", 7.0, 7.20, 4800.0, 1600.0, 0.7, 36.0, "SK99-07", 1),
            ("9 мм", 9.0, 11.50, 7900.0, 2600.0, 0.6, 58.0, "SK99-09", 2),
            ("11 мм", 11.0, 16.80, 11800.0, 3900.0, 0.5, 87.0, "SK99-11", 3),
            ("13 мм", 13.0, 22.40, 16200.0, 5400.0, 0.5, 120.0, "SK99-13", 4),
        ]
        for v_name, s_val, pr, bl, wl, st, w_g, sku, idx in p5_variants:
            await create_rope_variant_factory(
                session,
                CreateRopeVariantFixtureDTO(
                    product_id=p5.id,
                    variant_name=v_name,
                    size_value=s_val,
                    price=pr,
                    breaking_load_dan=bl,
                    working_load_dan=wl,
                    working_stretch_percent=st,
                    weight_g=w_g,
                    sku=sku,
                    index=idx,
                    is_active=True,
                ),
            )
        for col_idx, col_code in enumerate(["anthracite", "signal_orange", "navy_blue"], start=1):
            await create_rope_product_color_factory(
                session,
                CreateRopeProductColorFixtureDTO(product_id=p5.id, color_id=created_colors[col_code].id, index=col_idx),
            )
        for st_code in ["aug_splice", "soft_shackle", "takling", "friction_ring_splice", "pilotauge"]:
            await create_rope_allowed_splice_factory(
                session,
                CreateRopeAllowedSpliceFixtureDTO(product_id=p5.id, splice_type_id=created_st[st_code].id),
            )
        for app_code in ["halyard", "sheet", "runner"]:
            await create_product_assigned_application_factory(
                session,
                CreateProductAssignedApplicationFixtureDTO(product_id=p5.id, application_id=created_apps[app_code].id),
            )
        await add_product_specs(
            p5.id,
            [
                ("Core", "Dyneema SK99 Ultra-High Modulus Polyethylene", "Сердечник", "Сверхвысокомодульный полиэтилен Dyneema SK99", "Kern", "Dyneema SK99 Ultra-High-Modul PE"),
                ("Creep Factor", "Near-zero creep under continuous high load", "Ползучесть", "Практически нулевая ползучесть под нагрузкой", "Kriechverhalten", "Nahezu kriechfrei unter Dauerlast"),
                ("Working Stretch", "< 0.6% at working load", "Рабочее удлинение", "< 0.6% при рабочей нагрузке", "Arbeitsdehnung", "< 0.6% bei Arbeitslast"),
            ],
        )
        await create_product_image_factory(
            session,
            CreateProductImageFixtureDTO(product_id=p5.id, image_url="/assets/products/sk99_gp_1.webp", is_main=True, index=1, is_active=True),
        )

        # ---------------------------------------------------------
        # Товар 6: Dinghy Soft Grip Sheet (Шкот для швертботов)
        # ---------------------------------------------------------
        p6 = await create_product_factory(
            session,
            CreateProductFixtureDTO(
                category_id=created_cats["dinghy-sport"].id,
                slug="dinghy-soft-grip-sheet",
                price_unit="meter",
                has_configurator=True,
                construction_type="hm_core",
                index=6,
                locale=Language.ENG,
                name="Dinghy Soft Grip Sheet",
                subtitle="Ultra-soft non-slip mainsheet and spinnaker sheet for dinghies",
                description="Designed specifically for hand-held sheets in dinghy and sportboat classes (Laser, 49er, J/70). Dyneema core with fuzzy spun polyester/Cordura cover.",
            ),
        )
        await create_product_translation_factory(
            session,
            CreateProductTranslationFixtureDTO(
                product_id=p6.id,
                locale=Language.RUS,
                name="Dinghy Soft Grip Шкот",
                subtitle="Мягкий нескользящий гика-шкот и спинакер-шкот для швертботов",
                description="Идеален для работы голыми руками в классах Laser, 49er, J/70. Ворсистая оплетка с добавлением Cordura не обжигает ладони.",
            ),
        )
        await create_product_translation_factory(
            session,
            CreateProductTranslationFixtureDTO(
                product_id=p6.id,
                locale=Language.GER,
                name="Dinghy Soft-Grip Großschot",
                subtitle="Handschmeichelnde rutschfeste Schot für Jollen und Sportboote",
                description="Speziell für das Fahren aus der Hand entwickelt. Dyneema-Kern mit flauschigem Cordura/Polyester-Mantel verhindert Brandblasen.",
            ),
        )
        await create_rope_product_factory(
            session,
            CreateRopeProductFixtureDTO(
                product_id=p6.id,
                material_group_id=created_mg["dyneema"].id,
                material_id=created_materials["sk78"].id,
                splice_material_id=created_sm["high_tech_dyneema"].id,
                construction="12-strand Dyneema core with fuzzy spun Cordura/PES cover",
                core_description="Dyneema SK78 coated",
                cover_description="Spun Cordura / Polyester fuzzy grip",
                can_be_spliced=True,
            ),
        )
        p6_variants = [
            ("7 мм", 7.0, 3.80, 1600.0, 480.0, 1.8, 38.0, "DSOF-07", 1),
            ("8 мм", 8.0, 4.70, 2200.0, 650.0, 1.6, 48.0, "DSOF-08", 2),
            ("9 мм", 9.0, 5.80, 2900.0, 850.0, 1.5, 62.0, "DSOF-09", 3),
            ("10 мм", 10.0, 7.10, 3700.0, 1100.0, 1.4, 76.0, "DSOF-10", 4),
        ]
        for v_name, s_val, pr, bl, wl, st, w_g, sku, idx in p6_variants:
            await create_rope_variant_factory(
                session,
                CreateRopeVariantFixtureDTO(
                    product_id=p6.id,
                    variant_name=v_name,
                    size_value=s_val,
                    price=pr,
                    breaking_load_dan=bl,
                    working_load_dan=wl,
                    working_stretch_percent=st,
                    weight_g=w_g,
                    sku=sku,
                    index=idx,
                    is_active=True,
                ),
            )
        for col_idx, col_code in enumerate(["solid_red", "ocean_blue", "navy_yellow_flecks"], start=1):
            await create_rope_product_color_factory(
                session,
                CreateRopeProductColorFixtureDTO(product_id=p6.id, color_id=created_colors[col_code].id, index=col_idx),
            )
        for st_code in ["aug_splice", "soft_shackle", "takling", "endless_splice"]:
            await create_rope_allowed_splice_factory(
                session,
                CreateRopeAllowedSpliceFixtureDTO(product_id=p6.id, splice_type_id=created_st[st_code].id),
            )
        for app_code in ["sheet", "control_line"]:
            await create_product_assigned_application_factory(
                session,
                CreateProductAssignedApplicationFixtureDTO(product_id=p6.id, application_id=created_apps[app_code].id),
            )
        await add_product_specs(
            p6.id,
            [
                ("Grip Surface", "Fuzzy spun Cordura for wet hand grip", "Поверхность", "Ворсистая Cordura для надежного хвата мокрыми руками", "Griffigkeit", "Flauschiges Spun-Gewebe für besten Nass-Grip"),
                ("Core", "Dyneema SK78 low-stretch", "Сердечник", "Малорастяжимая Dyneema SK78", "Kern", "Dyneema SK78 dehnungsarm"),
            ],
        )
        await create_product_image_factory(
            session,
            CreateProductImageFixtureDTO(product_id=p6.id, image_url="/assets/products/dinghy_grip_1.webp", is_main=True, index=1, is_active=True),
        )

        # ==========================================
        # 14. Примеры заявок (Quote Requests)
        # ==========================================
        print("  -> Creating Example Quote Requests...")
        # Заявка 1: Канат с сплайсом (Новая)
        await create_quote_request_factory(
            session,
            CreateQuoteRequestFixtureDTO(
                request_number="RPL-2026-0001",
                configurator_type=ConfiguratorType.ROPE_WITH_SPLICE,
                name="Hans Schmidt",
                email="schmidt@baltic-yachting.de",
                phone="+49 170 1234567",
                comment="Foresheet for 40ft cruiser/racer with leather protected eye",
                currency=Currency.EUR,
                subtotal=108.50,
                urgent_surcharge=0.0,
                total_price=129.12,
                vat_rate=19.0,
                is_urgent=False,
                status=QuoteRequestStatus.NEW,
                rope_items=[
                    CreateQuoteRopeItemFixtureDTO(
                        product_id=p1.id,
                        color_id=created_colors["navy_blue"].id,
                        product_name_snapshot="Cruising 16-plait Polyester",
                        color_name_snapshot="Marineblau",
                        diameter_mm=10.0,
                        length_m=30.0,
                        quantity=1,
                        price_per_meter_snapshot=2.60,
                        total_rope_cost=78.00,
                        end_a_type_id=created_st["aug_splice"].id,
                        end_a_name_snapshot="Augspleiß",
                        end_a_eye_size_cm=15.0,
                        end_a_cost=15.00,
                        end_b_type_id=created_st["takling"].id,
                        end_b_name_snapshot="Takling genäht",
                        end_b_cost=6.00,
                    )
                ],
                extra_items=[
                    CreateQuoteExtraItemFixtureDTO(
                        extra_id=created_extras["leather_protection"].id,
                        name_snapshot="Leder-Kauschschutz",
                        billing_type_snapshot="fixed",
                        quantity=1,
                        unit_price_snapshot=18.50,
                        total_cost=18.50,
                    )
                ],
            ),
        )

        # Заявка 2: Только петли (В работе)
        await create_quote_request_factory(
            session,
            CreateQuoteRequestFixtureDTO(
                request_number="RPL-2026-0002",
                configurator_type=ConfiguratorType.LOOP_ONLY,
                name="Markus Weber",
                email="m.weber@north-sea-rigging.com",
                phone="+49 151 9876543",
                comment="Rigging refit: 4 soft shackles for halyard blocks, urgent delivery",
                currency=Currency.EUR,
                subtotal=88.00,
                urgent_surcharge=12.50,
                total_price=119.60,
                vat_rate=19.0,
                is_urgent=True,
                status=QuoteRequestStatus.IN_PROGRESS,
                service_items=[
                    CreateQuoteServiceItemFixtureDTO(
                        splice_type_id=created_st["soft_shackle"].id,
                        splice_material_id=created_sm["high_tech_dyneema"].id,
                        service_name_snapshot="Softschäkel",
                        material_name_snapshot="High-Tech Dyneema Hohlgeflecht",
                        diameter_mm=8.0,
                        eye_size_cm=12.0,
                        quantity=4,
                        unit_price_snapshot=22.00,
                        total_cost=88.00,
                    )
                ],
            ),
        )

        # Заявка 3: Комплект швартовых (Подтверждена)
        await create_quote_request_factory(
            session,
            CreateQuoteRequestFixtureDTO(
                request_number="RPL-2026-0003",
                configurator_type=ConfiguratorType.ROPE_WITH_SPLICE,
                name="Elena Rostova",
                email="e.rostova@baltic-yachts.ru",
                phone="+7 911 555-4321",
                comment="Four mooring docklines 14mm x 15m with 40cm spliced eyes",
                currency=Currency.EUR,
                subtotal=334.00,
                urgent_surcharge=0.0,
                total_price=397.46,
                vat_rate=19.0,
                is_urgent=False,
                status=QuoteRequestStatus.CONFIRMED,
                rope_items=[
                    CreateQuoteRopeItemFixtureDTO(
                        product_id=p3.id,
                        color_id=created_colors["black"].id,
                        product_name_snapshot="OceanFlex 3-Strand Polyester Mooring Line",
                        color_name_snapshot="Black",
                        diameter_mm=14.0,
                        length_m=15.0,
                        quantity=4,
                        price_per_meter_snapshot=4.10,
                        total_rope_cost=246.00,
                        end_a_type_id=created_st["aug_splice"].id,
                        end_a_name_snapshot="Augspleiß 40cm",
                        end_a_eye_size_cm=40.0,
                        end_a_cost=14.00,
                        end_b_type_id=created_st["takling"].id,
                        end_b_name_snapshot="Takling genäht",
                        end_b_cost=5.00,
                    )
                ],
                extra_items=[
                    CreateQuoteExtraItemFixtureDTO(
                        extra_id=created_extras["chafe_sleeve"].id,
                        name_snapshot="Scheuerschutz-Schlauch",
                        billing_type_snapshot="per_meter",
                        quantity=4,
                        unit_price_snapshot=6.50,
                        total_cost=26.00,
                    )
                ],
            ),
        )

        # Заявка 4: Гоночный спинакер-фал Dyneema SK99 (Выполнена)
        await create_quote_request_factory(
            session,
            CreateQuoteRequestFixtureDTO(
                request_number="RPL-2026-0004",
                configurator_type=ConfiguratorType.ROPE_WITH_SPLICE,
                name="Dirk van der Meer",
                email="dirk@amsterdam-sailing.nl",
                phone="+31 6 12345678",
                comment="Spinnaker halyard for Swan 50, Tylaska snap shackle splice + break certificate",
                currency=Currency.EUR,
                subtotal=541.00,
                urgent_surcharge=0.0,
                total_price=643.79,
                vat_rate=19.0,
                is_urgent=False,
                status=QuoteRequestStatus.COMPLETED,
                rope_items=[
                    CreateQuoteRopeItemFixtureDTO(
                        product_id=p5.id,
                        color_id=created_colors["signal_orange"].id,
                        product_name_snapshot="Dyneema SK99 Grand Prix Pro",
                        color_name_snapshot="Signalorange",
                        diameter_mm=9.0,
                        length_m=42.0,
                        quantity=1,
                        price_per_meter_snapshot=11.50,
                        total_rope_cost=483.00,
                        end_a_type_id=created_st["aug_splice"].id,
                        end_a_name_snapshot="Augspleiß für Schnappschäkel",
                        end_a_eye_size_cm=6.0,
                        end_a_cost=25.00,
                        end_b_type_id=created_st["pilotauge"].id,
                        end_b_name_snapshot="Pilotauge / Einziehspleiß",
                        end_b_cost=14.00,
                    )
                ],
                extra_items=[
                    CreateQuoteExtraItemFixtureDTO(
                        extra_id=created_extras["break_load_cert"].id,
                        name_snapshot="Prüfzeugnis / Zugtest-Zertifikat",
                        billing_type_snapshot="fixed",
                        quantity=1,
                        unit_price_snapshot=35.00,
                        total_cost=35.00,
                    )
                ],
            ),
        )

        # Заявка 5: Бесконечная петля Endless Splice (Новая)
        await create_quote_request_factory(
            session,
            CreateQuoteRequestFixtureDTO(
                request_number="RPL-2026-0005",
                configurator_type=ConfiguratorType.SPLICE_ONLY,
                name="Sven Larsson",
                email="sven.larsson@stockholm-marine.se",
                phone="+46 8 555 123",
                comment="Endless loop for Facnor continuous furler line",
                currency=Currency.EUR,
                subtotal=60.00,
                urgent_surcharge=0.0,
                total_price=71.40,
                vat_rate=19.0,
                is_urgent=False,
                status=QuoteRequestStatus.NEW,
                service_items=[
                    CreateQuoteServiceItemFixtureDTO(
                        splice_type_id=created_st["endless_splice"].id,
                        splice_material_id=created_sm["high_tech_dyneema"].id,
                        service_name_snapshot="Endlosspleiß",
                        material_name_snapshot="High-Tech Dyneema Hohlgeflecht",
                        diameter_mm=10.0,
                        eye_size_cm=0.0,
                        quantity=1,
                        unit_price_snapshot=60.00,
                        total_cost=60.00,
                    )
                ],
            ),
        )

        # Заявка 6: Шкоты для Laser / J70 (Отменена)
        await create_quote_request_factory(
            session,
            CreateQuoteRequestFixtureDTO(
                request_number="RPL-2026-0006",
                configurator_type=ConfiguratorType.ROPE_WITH_SPLICE,
                name="Christian Meyer",
                email="meyer.sail@gmx.de",
                phone="+49 176 99887766",
                comment="Mainsheet test order - cancelled by customer due to regatta postpone",
                currency=Currency.EUR,
                subtotal=65.20,
                urgent_surcharge=0.0,
                total_price=77.59,
                vat_rate=19.0,
                is_urgent=False,
                status=QuoteRequestStatus.CANCELLED,
                rope_items=[
                    CreateQuoteRopeItemFixtureDTO(
                        product_id=p6.id,
                        color_id=created_colors["solid_red"].id,
                        product_name_snapshot="Dinghy Soft Grip Sheet",
                        color_name_snapshot="Solid Red",
                        diameter_mm=8.0,
                        length_m=12.0,
                        quantity=1,
                        price_per_meter_snapshot=4.70,
                        total_rope_cost=56.40,
                        end_a_type_id=created_st["takling"].id,
                        end_a_name_snapshot="Takling",
                        end_a_cost=6.00,
                        end_b_type_id=created_st["takling"].id,
                        end_b_name_snapshot="Takling",
                        end_b_cost=6.00,
                    )
                ],
            ),
        )

        # ==========================================
        # 15. Отзывы клиентов (Reviews)
        # ==========================================
        print("  -> Creating Reviews...")
        reviews_meta = [
            (
                "Michael Kramer (Yacht Club Kiel)",
                5,
                1,
                "Outstanding eye splice quality on our Dyneema halyards. Running smoothly through the masthead sheaves and clutches.",
                "Великолепное качество сплайсов на фалах из Dyneema. Идеально проходят через шкивы на топе мачты и стопора.",
                "Hervorragende Qualität der Augspleiße an unseren Dyneema-Fallen. Laufen butterweich durch die Masttopp-Rollen.",
            ),
            (
                "Dr. Stefan Lindemann",
                5,
                2,
                "Custom 16mm Squareline mooring docklines with leather protected eyes look fantastic and protect our Hallberg-Rassy in heavy surge.",
                "Индивидуальные швартовы Squareline 16мм с кожаной защитой огонов выглядят безупречно и надежно защищают лодку в марине.",
                "Maßgefertigte Squareline-Festmacher mit Leder-Kauschschutz. Sieht edel aus und dämpft Schwell in der Marina perfekt ab.",
            ),
            (
                "Capitaine Laurent Dubois",
                5,
                3,
                "The fast 24h express turnaround saved our regatta schedule. Accurate breaking load certificates provided with the rigging.",
                "Срочное изготовление за 24 часа спасло наш календарь регат. Приложили официальный сертификат разрывных испытаний.",
                "Der 24h-Express-Service hat unseren Regattastart gerettet. Zertifizierte Prüfzeugnisse lagen direkt bei.",
            ),
            (
                "Alexander Smirnov (Neva Regatta Team)",
                4,
                4,
                "Excellent rope grip and splice durability. The Soft Shackles are very light and strong. Delivery took 4 days to Baltic port.",
                "Отличное сцепление оплетки и прочность сплайсов. Мягкие мочки легкие и очень надежные.",
                "Sehr gute Griffigkeit und Haltbarkeit der Spleiße. Die Softschäkel sind extrem leicht und stabil.",
            ),
            (
                "Hanna Lindqvist (Stockholm)",
                5,
                5,
                "Configurator is so easy to use! We ordered complete running rigging for our 34ft sailboat with custom lengths.",
                "Конфигуратор невероятно удобен! Заказали весь бегучий такелаж для 34-футовой яхты с индивидуальными размерами.",
                "Der Konfigurator ist genial einfach zu bedienen! Haben das komplette laufende Gut für unsere 34-Fuß-Yacht bestellt.",
            ),
        ]
        for author, rating, idx, t_en, t_ru, t_de in reviews_meta:
            rev_dto = await create_review_factory(
                session,
                CreateReviewFixtureDTO(
                    author_name=author,
                    rating=rating,
                    is_published=True,
                    status=ReviewsStatus.CONFIRMED,
                    index=idx,
                    locale=Language.ENG,
                    text=t_en,
                ),
            )
            await create_review_translation_factory(
                session,
                CreateReviewTranslationFixtureDTO(
                    review_id=rev_dto.id,
                    locale=Language.RUS,
                    text=t_ru,
                ),
            )
            await create_review_translation_factory(
                session,
                CreateReviewTranslationFixtureDTO(
                    review_id=rev_dto.id,
                    locale=Language.GER,
                    text=t_de,
                ),
            )

        # ==========================================
        # 16. Фото выполненных работ (Work Photos)
        # ==========================================
        print("  -> Creating Work Photos...")
        work_photos_meta = [
            (
                "/assets/work_photos/work_eye_leather.webp",
                1,
                "Leather Covered Eye Splice on 14mm Halyard",
                "Eye splice on Dyneema halyard with hand-stitched marine leather protector.",
                "Огон с кожаной оплеткой на фале 14мм",
                "Огон на фале из Dyneema с защитой из прошитой натуральной морской кожи.",
                "Augspleiß mit handgenähtem Leder-Kauschschutz",
                "Präziser Augspleiß an 14mm Dyneema-Fall mit echtem Segelleder genäht.",
            ),
            (
                "/assets/work_photos/work_soft_shackles.webp",
                2,
                "Set of Heavy-Duty Dyneema Soft Shackles",
                "Custom manufactured soft shackles with diamond stopper knot for halyard blocks.",
                "Комплект усиленных мягких мочек из Dyneema",
                "Мягкие мочки с алмазным стопорным узлом для крепления фаловых блоков.",
                "Satz hochfester Dyneema-Softschäkel",
                "Maßgefertigte Softschäkel mit Diamantknoten für Fallenumlenkblöcke.",
            ),
            (
                "/assets/work_photos/work_endless_loop.webp",
                3,
                "Continuous Loop Splicing for Gennaker Furler",
                "Endless continuous line splice with identical diameter for smooth drum rotation.",
                "Бесконечная петля для закрутки генакера",
                "Сращивание бесконечной петли с сохранением диаметра для плавной работы барабана.",
                "Endlosspleiß für Gennaker-Rollreffanlage",
                "Geschlossener Endlosspleiß mit gleichmäßigem Durchmesser für ruckfreies Einrollen.",
            ),
            (
                "/assets/work_photos/work_stripping_core.webp",
                4,
                "Stripped Halyard Core with Chafe Cover",
                "Grand Prix halyard with cover stripped for weight reduction aloft.",
                "Облегченный фал со снятой оплеткой (Stripped Core)",
                "Гоночный фал со снятой оплеткой для снижения веса бегучего такелажа на топе мачты.",
                "Abgemanteltes Fall mit Dyneema-Hohlgeflecht",
                "Gewichtsoptimiertes Regattafall mit abgemanteltem Topp-Bereich.",
            ),
            (
                "/assets/work_photos/work_thimble_mooring.webp",
                5,
                "Stainless Steel Thimble Eye Splice on Docklines",
                "Heavy duty eye splice holding AISI 316 stainless steel thimble for storm mooring.",
                "Огон с нержавеющим коушем для штормового швартова",
                "Усиленный огон с запрессованным полированным коушем для надежной стоянки в шторм.",
                "Kauschspleiß mit V4A Edelstahlkausche für Festmacher",
                "Solider Kauschspleiß für extreme Belastungen an Bojen und Moorings.",
            ),
        ]
        for img, idx, t_en, d_en, t_ru, d_ru, t_de, d_de in work_photos_meta:
            wp_dto = await create_work_photo_factory(
                session,
                conf,
                CreateWorkPhotoFixtureDTO(
                    image_url=img,
                    index=idx,
                    is_active=True,
                    title=t_en,
                    description=d_en,
                ),
            )
            # Дополнительные переводы на русский и немецкий
            session.add(
                WorkPhotoTranslation(
                    work_photo_id=wp_dto.id,
                    locale=Language.RUS,
                    title=t_ru,
                    description=d_ru,
                )
            )
            session.add(
                WorkPhotoTranslation(
                    work_photo_id=wp_dto.id,
                    locale=Language.GER,
                    title=t_de,
                    description=d_de,
                )
            )
            await session.commit()

        # ==========================================
        # 17. Благотворительность и экология (Charity Photos)
        # ==========================================
        print("  -> Creating Charity Photos...")
        charity_meta = [
            (
                "/assets/charity/ghost_nets_cleanup.webp",
                1,
                "Ocean Cleanup: Upcycling Discarded Fishing Gear",
                "We collect discarded commercial fishing nets and ropes to recycle into fenders and dock accessories.",
                "Очистка моря: переработка старых рыболовных сетей",
                "Собираем старые тросы и сети, превращая их во вторичные кранцы и аксессуары.",
                "Upcycling alter Fischernetze und Taue",
                "Wir sammeln ausgediente Fischernetze und Taue, um sie zu neuen Bootsfendern zu verarbeiten.",
            ),
            (
                "/assets/charity/youth_sailing_support.webp",
                2,
                "Youth Sailing Academy Rigging Support",
                "Donating running rigging and splicing workshops to young aspiring dinghy sailors.",
                "Поддержка юношеской парусной школы",
                "Бесплатная поставка бегучего такелажа и мастер-классы по заделкам для детских парусных школ.",
                "Förderung des Jugend-Segelsports",
                "Spende von laufendem Gut und Spleiß-Workshops für Nachwuchs-Jollensegler.",
            ),
            (
                "/assets/charity/safe_harbors_initiative.webp",
                3,
                "Baltic Sea Habitat Preservation",
                "Portion of every custom rope order is contributed to Baltic marine flora restoration projects.",
                "Сохранение экосистемы Балтийского моря",
                "Часть средств от каждого заказа направляется на восстановление водорослей и морской флоры Балтики.",
                "Meeresschutz-Initiative Ostsee",
                "Ein Teil jedes Auftrags fließt in Seegraswiesen-Renaturierungsprojekte der Ostsee.",
            ),
        ]
        for img, idx, t_en, d_en, t_ru, d_ru, t_de, d_de in charity_meta:
            cp_dto = await create_charity_photo_factory(
                session,
                conf,
                CreateCharityPhotoFixtureDTO(
                    image_url=img,
                    index=idx,
                    is_active=True,
                    title=t_en,
                    description=d_en,
                ),
            )
            session.add(
                CharityPhotoTranslation(
                    charity_photo_id=cp_dto.id,
                    locale=Language.RUS,
                    title=t_ru,
                    description=d_ru,
                )
            )
            session.add(
                CharityPhotoTranslation(
                    charity_photo_id=cp_dto.id,
                    locale=Language.GER,
                    title=t_de,
                    description=d_de,
                )
            )
            await session.commit()

        # ==========================================
        # 18. Информационные блоки (Content Blocks)
        # ==========================================
        print("  -> Creating Content Blocks...")
        content_blocks_meta = [
            (
                "home",
                "hero_banner",
                1,
                "Master Rigging & Custom Rope Splicing",
                "Precision nautical cordage and certified splicing crafted individually for your yacht. Configure and order online.",
                "Такелажная мастерская высшего класса: канаты и профессиональные сращивания",
                "Высокотехнологичные канаты и сертифицированные сплайсы по вашим размерам. Рассчитайте в онлайн-конфигураторе.",
                "Meisterliche Rigg-Arbeiten & Individueller Spleiß-Service",
                "Präzises Tauwerk und zertifizierte Spleiße, exakt nach Maß für Ihre Yacht gefertigt. Jetzt online konfigurieren.",
            ),
            (
                "home",
                "custom_splicing_feature",
                2,
                "Online Rigging Configurator",
                "Select exact rope diameters, colors, eye dimensions, and specialized finishes in real time.",
                "Онлайн-конфигуратор бегучего такелажа",
                "Выбирайте точные длины, диаметры, цвета, размеры огонов и защитных оплеток с мгновенным расчетом стоимости.",
                "Online Tauwerk-Konfigurator",
                "Wählen Sie exakte Längen, Durchmesser, Farben, Augengrößen und Sonderausstattungen in Echtzeit.",
            ),
            (
                "about",
                "our_workshop",
                1,
                "Decades of Passion on the Water",
                "Our master riggers bring over 25 years of experience in ocean racing and superyacht rigging.",
                "Десятилетия страсти к морю и парусу",
                "Наши такелажные мастера обладают более чем 25-летним опытом в кругосветных гонках и оснащении яхт.",
                "Jahrzehnte Erfahrung im Segelsport",
                "Unsere Rigg-Meister blicken auf über 25 Jahre Erfahrung im Hochseesegeln und Megayacht-Rigg zurück.",
            ),
            (
                "standards",
                "quality_test_bench",
                1,
                "Calibrated 30-Ton Tensile Test Bench",
                "Every splice design undergoes strict testing according to international naval standards ISO 2307.",
                "Сертифицированный разрывной стенд 30 тонн",
                "Каждый тип заделки проходит регулярные разрушающие и статические испытания по стандарту ISO 2307.",
                "Kalibrierte 30-Tonnen-Prüfbank",
                "Jede Spleiß-Konstruktion wird auf unserer hauseigenen Zugprüfbank nach DIN EN ISO 2307 geprüft.",
            ),
            (
                "delivery",
                "fast_turnaround",
                1,
                "Fast Worldwide Delivery & 24h Express",
                "Standard turnaround is 72 hours. Urgent regatta orders completed and dispatched within 24 hours.",
                "Быстрая доставка по всему миру и экспресс за 24 часа",
                "Стандартный срок изготовления — 72 часа. Срочные заказы для регат собираются и отправляются за 24 часа.",
                "Weltweiter Versand & 24h Express-Fertigung",
                "Reguläre Fertigungszeit 72 Stunden. Eilige Regatta-Aufträge werden innerhalb von 24 Stunden versendet.",
            ),
        ]
        for p_code, b_code, idx, t_en, c_en, t_ru, c_ru, t_de, c_de in content_blocks_meta:
            cb_dto = await create_content_block_factory(
                session,
                CreateContentBlockFixtureDTO(
                    page_code=p_code,
                    block_code=b_code,
                    index=idx,
                    is_active=True,
                    locale=Language.ENG,
                    title=t_en,
                    content=c_en,
                ),
            )
            await create_content_block_translation_factory(
                session,
                CreateContentBlockTranslationFixtureDTO(
                    content_block_id=cb_dto.id,
                    locale=Language.RUS,
                    title=t_ru,
                    content=c_ru,
                ),
            )
            await create_content_block_translation_factory(
                session,
                CreateContentBlockTranslationFixtureDTO(
                    content_block_id=cb_dto.id,
                    locale=Language.GER,
                    title=t_de,
                    content=c_de,
                ),
            )

        # ==========================================
        # 19. Запросы обратной связи (Contact Requests)
        # ==========================================
        print("  -> Creating Contact Requests...")
        contact_requests_meta = [
            (
                "Jörg Petersen",
                "j.petersen@baltic-marina.de",
                "+49 431 876543",
                "We need an offer for refitting complete running rigging for two Bavaria Cruiser 46 charter yachts.",
            ),
            (
                "Capt. Robert MacLeod",
                "robert.macleod@scot-rigging.co.uk",
                "+44 141 555 9876",
                "Can you produce custom Dyneema lifelines with pelican hooks certified for offshore category 1?",
            ),
            (
                "Mikhail Voronov",
                "m.voronov@spb-yachtclub.ru",
                "+7 812 345-6789",
                "Interested in wholesale supply of 3-strand polyester ropes and soft shackles for our club fleet.",
            ),
            (
                "Laura van Dijk",
                "laura@zeilmakerij-ijssel.nl",
                "+31 20 654 3210",
                "Question about your endless continuous loop splices: can you splice 8mm rope with 14m circumference?",
            ),
        ]
        for name, email, phone, msg in contact_requests_meta:
            await create_contact_request_factory(
                session,
                CreateContactRequestFixtureDTO(
                    name=name,
                    email=email,
                    phone=phone,
                    message=msg,
                ),
            )

    print("\n[OK] Test data population successfully completed!")


async def main():
    conf = Config()
    await clear_database(conf)
    await fill_data(conf)


if __name__ == "__main__":
    asyncio.run(main())

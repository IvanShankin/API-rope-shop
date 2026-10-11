import argparse
import asyncio
import inspect
import logging
import sys
from pathlib import Path
from typing import Any, Callable, Dict, Optional

# Добавляем корень проекта и директорию tests в sys.path для корректных импортов
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

TESTS_DIR = PROJECT_ROOT / "tests"
if str(TESTS_DIR) not in sys.path:
    sys.path.insert(0, str(TESTS_DIR))

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from src.core.config import Config
from src.core.database.database import Base
from src.modules.base.database_model import Language
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
from src.modules.rope_product_color.models import RopeProductColor
from src.modules.rope_products.models import RopeProduct, RopeVariant
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
    create_quote_request_fixture,
    create_rope_allowed_splice_fixture,
    create_rope_product_color_fixture,
    create_rope_product_fixture,
    create_rope_variant_fixture,
    create_splice_material_fixture,
    create_splice_price_rule_fixture,
    create_splice_type_fixture,
    create_splice_type_translation_fixture,
    create_user_fixture,
)

# Импортируем DTO для фикстур
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

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("create_test_data")


async def clear_test_data(conf: Config) -> None:
    """
    Очищает базу данных в строгом порядке соблюдения внешних ключей (FK)
    аналогично фикстуре clearing_db в conftest.py.
    """
    logger.info("Clearing existing data from database...")
    async with conf.db_connection.session_local() as session:
        await session.execute(delete(QuoteRopeItem))
        await session.execute(delete(QuoteServiceItem))
        await session.execute(delete(QuoteExtraItem))
        await session.execute(delete(QuoteRequest))
        await session.execute(delete(ConfiguratorSetting))
        await session.execute(delete(ConfiguratorExtraTranslation))
        await session.execute(delete(ConfiguratorExtra))
        await session.execute(delete(RopeAllowedSplice))
        await session.execute(delete(RopeProductColor))
        await session.execute(delete(RopeVariant))
        await session.execute(delete(RopeProduct))
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
    logger.info("Database cleared successfully.")


async def _resolve_fixture_callable(
    fixture_obj: Any,
    conf: Config,
    session: AsyncSession,
) -> Callable[..., Any]:
    """
    Универсально вызывает pytest-фикстуру из tests/fixturs, передавая
    необходимые зависимости (session_db, not_open_session_db, config_fix)
    и возвращая результирующую фабричную функцию.
    """
    fn = getattr(fixture_obj, "__wrapped__", fixture_obj)
    sig = inspect.signature(fn)
    kwargs: Dict[str, Any] = {}

    for param_name in sig.parameters:
        if param_name == "config_fix":
            kwargs["config_fix"] = conf
        elif param_name == "not_open_session_db":
            kwargs["not_open_session_db"] = conf.db_connection.session_local
        elif param_name == "session_db":
            kwargs["session_db"] = session

    return await fn(**kwargs)


async def _init_fixture_callables(
    conf: Config,
    session: AsyncSession,
) -> Dict[str, Callable[..., Any]]:
    """
    Инициализирует фабричные вызовы всех фикстур из tests/fixturs/__init__.py.
    """
    user_fix = await _resolve_fixture_callable(create_user_fixture, conf, session)
    splice_mat_fix = await _resolve_fixture_callable(create_splice_material_fixture, conf, session)
    splice_type_fix = await _resolve_fixture_callable(create_splice_type_fixture, conf, session)
    splice_type_tr_fix = await _resolve_fixture_callable(create_splice_type_translation_fixture, conf, session)
    splice_price_fix = await _resolve_fixture_callable(create_splice_price_rule_fixture, conf, session)
    color_fix = await _resolve_fixture_callable(create_color_fixture, conf, session)
    color_tr_fix = await _resolve_fixture_callable(create_color_translation_fixture, conf, session)
    mat_group_fix = await _resolve_fixture_callable(create_material_group_fixture, conf, session)
    mat_group_tr_fix = await _resolve_fixture_callable(create_material_group_translation_fixture, conf, session)
    mat_fix = await _resolve_fixture_callable(create_material_fixture, conf, session)
    mat_tr_fix = await _resolve_fixture_callable(create_material_translation_fixture, conf, session)
    rope_prod_fix = await _resolve_fixture_callable(create_rope_product_fixture, conf, session)
    rope_var_fix = await _resolve_fixture_callable(create_rope_variant_fixture, conf, session)
    rope_color_fix = await _resolve_fixture_callable(create_rope_product_color_fixture, conf, session)
    rope_splice_fix = await _resolve_fixture_callable(create_rope_allowed_splice_fixture, conf, session)
    extra_fix = await _resolve_fixture_callable(create_configurator_extra_fixture, conf, session)
    extra_tr_fix = await _resolve_fixture_callable(create_configurator_extra_translation_fixture, conf, session)
    setting_fix = await _resolve_fixture_callable(create_configurator_setting_fixture, conf, session)
    quote_req_fix = await _resolve_fixture_callable(create_quote_request_fixture, conf, session)

    return {
        "user": user_fix,
        "splice_material": splice_mat_fix,
        "splice_type": splice_type_fix,
        "splice_type_translation": splice_type_tr_fix,
        "splice_price_rule": splice_price_fix,
        "color": color_fix,
        "color_translation": color_tr_fix,
        "material_group": mat_group_fix,
        "material_group_translation": mat_group_tr_fix,
        "material": mat_fix,
        "material_translation": mat_tr_fix,
        "rope_product": rope_prod_fix,
        "rope_variant": rope_var_fix,
        "rope_color": rope_color_fix,
        "rope_allowed_splice": rope_splice_fix,
        "configurator_extra": extra_fix,
        "configurator_extra_translation": extra_tr_fix,
        "configurator_setting": setting_fix,
        "quote_request": quote_req_fix,
    }


async def create_test_data(
    clean: bool = True,
    config: Optional[Config] = None,
) -> Dict[str, Any]:
    """
    Создаёт базовые записи в БД для тестов с использованием фикстур проекта
    из tests/fixturs/__init__.py.

    :param clean: Если True (по умолчанию), предварительно очищает таблицы БД.
    :param config: Опциональный объект конфигурации Config.
    :return: Словарь со всеми созданными сущностями.
    """
    conf = config or Config()

    # Убеждаемся, что схема и таблицы в целевой БД созданы
    engine = create_async_engine(conf.db_connection.sql_db_url)
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    finally:
        await engine.dispose()

    if clean:
        await clear_test_data(conf)

    async with conf.db_connection.session_local() as session:
        logger.info("Initializing fixtures from tests/fixturs/__init__.py...")
        f = await _init_fixture_callables(conf, session)

        # 1. Глобальные настройки конфигуратора
        logger.info("Creating configurator setting via create_configurator_setting_fixture...")
        setting = await f["configurator_setting"](
            CreateConfiguratorSettingFixtureDTO(
                min_length_m=1.0,
                max_length_m=200.0,
                splice_allowance_until_mm=12.0,
                splice_allowance_until_m=0.6,
                splice_allowance_over_m=1.0,
                urgent_surcharge_per_splice=10.0,
                urgent_max_splices=10,
                standard_turnaround_hours=72,
                urgent_turnaround_hours=24,
                currency=Currency.EUR,
                vat_rate=0.0,
                vat_note="inkl. MwSt.",
            )
        )

        # 2. Пользователи (Admin и Customer)
        logger.info("Creating test users via create_user_fixture...")
        admin_user, admin_token = await f["user"](
            CreateUserFixtureDTO(
                email="admin@example.com",
                username="admin",
                password="admin12345",
                role=UserRole.ADMIN,
            )
        )
        customer_user, customer_token = await f["user"](
            CreateUserFixtureDTO(
                email="user@example.com",
                username="customer",
                password="user12345",
                role=UserRole.USER,
            )
        )

        # 3. Тарифные группы сложности материалов для сращивания
        logger.info("Creating splice materials via create_splice_material_fixture...")
        sm_standard = await f["splice_material"](
            CreateSpliceMaterialFixtureDTO(
                code="standard",
                name="Standard (Kern-Mantel)",
            )
        )
        sm_hightech = await f["splice_material"](
            CreateSpliceMaterialFixtureDTO(
                code="high_tech",
                name="High-Tech (Dyneema / Vectran / Zylon)",
            )
        )

        # 4. Виды услуг/сращиваний и их переводы
        logger.info("Creating splice types and translations via fixtures...")
        st_aug = await f["splice_type"](
            CreateSpliceTypeFixtureDTO(
                code="aug_splice",
                category=SpliceCategory.LOOP,
                visual_type=SpliceVisualType.AUG_SPLICE,
                index=1,
                is_active=True,
                image_url="/media/splice_types/aug_splice.webp",
                locale=Language.GER,
                name="Augspleiß",
                description="Standard Augspleiß für Kern-Mantel und Tauwerk",
            )
        )
        await f["splice_type_translation"](
            CreateSpliceTypeTranslationFixtureDTO(
                splice_type_id=st_aug.id,
                locale=Language.ENG,
                name="Eye Splice",
                description="Standard eye splice for double braid and ropes",
            )
        )

        st_endless = await f["splice_type"](
            CreateSpliceTypeFixtureDTO(
                code="endless",
                category=SpliceCategory.SPLICE,
                visual_type=SpliceVisualType.ENDLESS_SPLICE,
                index=2,
                is_active=True,
                image_url="/media/splice_types/endless.webp",
                locale=Language.GER,
                name="Endlosspleiß",
                description="Endlosspleiß für geschlossene Endlosverbindung",
            )
        )
        await f["splice_type_translation"](
            CreateSpliceTypeTranslationFixtureDTO(
                splice_type_id=st_endless.id,
                locale=Language.ENG,
                name="Endless Splice",
                description="Endless splice for continuous loop connection",
            )
        )

        st_takling = await f["splice_type"](
            CreateSpliceTypeFixtureDTO(
                code="takling",
                category=SpliceCategory.SPLICE,
                visual_type=SpliceVisualType.TAKLING,
                index=3,
                is_active=True,
                image_url="/media/splice_types/takling.webp",
                locale=Language.GER,
                name="Takling",
                description="Genähter Takling am Seilende gegen Aufdrehen",
            )
        )
        await f["splice_type_translation"](
            CreateSpliceTypeTranslationFixtureDTO(
                splice_type_id=st_takling.id,
                locale=Language.ENG,
                name="Whipped End",
                description="Stitched whipping at the rope end against fraying",
            )
        )

        # 5. Матрица цен на работы (сращивания и петли)
        logger.info("Creating splice price rules via create_splice_price_rule_fixture...")
        rules = [
            # Augspleiss + Standard (0-14mm: 15.00, 14.01-22mm: 20.00)
            await f["splice_price_rule"](
                CreateSplicePriceRuleFixtureDTO(
                    splice_type_id=st_aug.id,
                    splice_material_id=sm_standard.id,
                    diameter_from_mm=0.0,
                    diameter_to_mm=14.0,
                    price=15.00,
                )
            ),
            await f["splice_price_rule"](
                CreateSplicePriceRuleFixtureDTO(
                    splice_type_id=st_aug.id,
                    splice_material_id=sm_standard.id,
                    diameter_from_mm=14.01,
                    diameter_to_mm=22.0,
                    price=20.00,
                )
            ),
            # Augspleiss + High-Tech (0-14mm: 30.00, 14.01-99mm: 40.00)
            await f["splice_price_rule"](
                CreateSplicePriceRuleFixtureDTO(
                    splice_type_id=st_aug.id,
                    splice_material_id=sm_hightech.id,
                    diameter_from_mm=0.0,
                    diameter_to_mm=14.0,
                    price=30.00,
                )
            ),
            await f["splice_price_rule"](
                CreateSplicePriceRuleFixtureDTO(
                    splice_type_id=st_aug.id,
                    splice_material_id=sm_hightech.id,
                    diameter_from_mm=14.01,
                    diameter_to_mm=99.0,
                    price=40.00,
                )
            ),
            # Endless + Standard (0-99mm: 33.00)
            await f["splice_price_rule"](
                CreateSplicePriceRuleFixtureDTO(
                    splice_type_id=st_endless.id,
                    splice_material_id=sm_standard.id,
                    diameter_from_mm=0.0,
                    diameter_to_mm=99.0,
                    price=33.00,
                )
            ),
            # Takling + Standard (0-12mm: 1.50, 12.01-99mm: 2.50)
            await f["splice_price_rule"](
                CreateSplicePriceRuleFixtureDTO(
                    splice_type_id=st_takling.id,
                    splice_material_id=sm_standard.id,
                    diameter_from_mm=0.0,
                    diameter_to_mm=12.0,
                    price=1.50,
                )
            ),
            await f["splice_price_rule"](
                CreateSplicePriceRuleFixtureDTO(
                    splice_type_id=st_takling.id,
                    splice_material_id=sm_standard.id,
                    diameter_from_mm=12.01,
                    diameter_to_mm=99.0,
                    price=2.50,
                )
            ),
        ]

        # 6. Цвета и их переводы
        logger.info("Creating colors and translations via create_color_fixture...")
        c_red = await f["color"](
            CreateColorFixtureDTO(
                code="red",
                hex="#E63946",
                index=1,
                is_active=True,
                locale=Language.GER,
                name="Rot",
            )
        )
        await f["color_translation"](
            CreateColorTranslationFixtureDTO(color_id=c_red.id, locale=Language.ENG, name="Red")
        )

        c_blue = await f["color"](
            CreateColorFixtureDTO(
                code="blue",
                hex="#1D3557",
                index=2,
                is_active=True,
                locale=Language.GER,
                name="Blau",
            )
        )
        await f["color_translation"](
            CreateColorTranslationFixtureDTO(color_id=c_blue.id, locale=Language.ENG, name="Blue")
        )

        c_black = await f["color"](
            CreateColorFixtureDTO(
                code="black",
                hex="#111111",
                index=3,
                is_active=True,
                locale=Language.GER,
                name="Schwarz",
            )
        )
        await f["color_translation"](
            CreateColorTranslationFixtureDTO(color_id=c_black.id, locale=Language.ENG, name="Black")
        )

        c_white = await f["color"](
            CreateColorFixtureDTO(
                code="white",
                hex="#F8F9FA",
                index=4,
                is_active=True,
                locale=Language.GER,
                name="Weiß",
            )
        )
        await f["color_translation"](
            CreateColorTranslationFixtureDTO(color_id=c_white.id, locale=Language.ENG, name="White")
        )

        c_navy = await f["color"](
            CreateColorFixtureDTO(
                code="navy",
                hex="#001F3F",
                index=5,
                is_active=True,
                locale=Language.GER,
                name="Navyblau",
            )
        )
        await f["color_translation"](
            CreateColorTranslationFixtureDTO(color_id=c_navy.id, locale=Language.ENG, name="Navy Blue")
        )

        # 7. Группы материалов и материалы
        logger.info("Creating material groups and materials via fixtures...")
        mg_poly = await f["material_group"](
            CreateMaterialGroupFixtureDTO(
                code="polyester",
                index=1,
                is_active=True,
                locale=Language.GER,
                name="Polyester",
            )
        )
        await f["material_group_translation"](
            CreateMaterialGroupTranslationFixtureDTO(
                material_group_id=mg_poly.id,
                locale=Language.ENG,
                name="Polyester",
            )
        )

        mg_dyneema = await f["material_group"](
            CreateMaterialGroupFixtureDTO(
                code="dyneema",
                index=2,
                is_active=True,
                locale=Language.GER,
                name="Dyneema",
            )
        )
        await f["material_group_translation"](
            CreateMaterialGroupTranslationFixtureDTO(
                material_group_id=mg_dyneema.id,
                locale=Language.ENG,
                name="Dyneema",
            )
        )

        mg_polyamid = await f["material_group"](
            CreateMaterialGroupFixtureDTO(
                code="polyamid",
                index=3,
                is_active=True,
                locale=Language.GER,
                name="Polyamid",
            )
        )
        await f["material_group_translation"](
            CreateMaterialGroupTranslationFixtureDTO(
                material_group_id=mg_polyamid.id,
                locale=Language.ENG,
                name="Polyamide",
            )
        )

        # Материалы внутри групп
        m_pes = await f["material"](
            CreateMaterialFixtureDTO(
                material_group_id=mg_poly.id,
                code="pes_standard",
                index=1,
                is_active=True,
                locale=Language.GER,
                name="Standard Polyester",
            )
        )
        await f["material_translation"](
            CreateMaterialTranslationFixtureDTO(
                material_id=m_pes.id,
                locale=Language.ENG,
                name="Standard Polyester",
            )
        )

        m_sk78 = await f["material"](
            CreateMaterialFixtureDTO(
                material_group_id=mg_dyneema.id,
                code="sk78",
                index=1,
                is_active=True,
                locale=Language.GER,
                name="Dyneema SK78",
            )
        )
        await f["material_translation"](
            CreateMaterialTranslationFixtureDTO(
                material_id=m_sk78.id,
                locale=Language.ENG,
                name="Dyneema SK78",
            )
        )

        m_sk99 = await f["material"](
            CreateMaterialFixtureDTO(
                material_group_id=mg_dyneema.id,
                code="sk99",
                index=2,
                is_active=True,
                locale=Language.GER,
                name="Dyneema SK99",
            )
        )
        await f["material_translation"](
            CreateMaterialTranslationFixtureDTO(
                material_id=m_sk99.id,
                locale=Language.ENG,
                name="Dyneema SK99",
            )
        )

        # 8. Товары-канаты, диаметры-варианты, цвета и разрешённые работы
        logger.info("Creating rope products, variants, colors, and allowed splices via fixtures...")
        # Канат 1: Polyester Rope (Standard)
        rope_1 = await f["rope_product"](
            CreateRopeProductFixtureDTO(
                material_group_id=mg_poly.id,
                splice_material_id=sm_standard.id,
                construction="16-plait braided core with cover",
                core_description="High tenacity polyester core",
                cover_description="Abrasion resistant polyester cover",
                working_stretch_percent=4.5,
                can_be_spliced=True,
            )
        )
        await f["rope_variant"](
            CreateRopeVariantFixtureDTO(
                rope_product_id=rope_1.product_id,
                diameter_mm=10.0,
                price_per_meter=2.50,
                breaking_load_dan=2300.0,
                weight_g_per_m=65.0,
                index=1,
                is_active=True,
            )
        )
        await f["rope_variant"](
            CreateRopeVariantFixtureDTO(
                rope_product_id=rope_1.product_id,
                diameter_mm=12.0,
                price_per_meter=3.80,
                breaking_load_dan=3200.0,
                weight_g_per_m=90.0,
                index=2,
                is_active=True,
            )
        )
        await f["rope_variant"](
            CreateRopeVariantFixtureDTO(
                rope_product_id=rope_1.product_id,
                diameter_mm=14.0,
                price_per_meter=5.20,
                breaking_load_dan=4400.0,
                weight_g_per_m=125.0,
                index=3,
                is_active=True,
            )
        )
        await f["rope_color"](
            CreateRopeProductColorFixtureDTO(
                rope_product_id=rope_1.product_id,
                color_id=c_navy.id,
                index=1,
            )
        )
        await f["rope_color"](
            CreateRopeProductColorFixtureDTO(
                rope_product_id=rope_1.product_id,
                color_id=c_white.id,
                index=2,
            )
        )
        await f["rope_color"](
            CreateRopeProductColorFixtureDTO(
                rope_product_id=rope_1.product_id,
                color_id=c_black.id,
                index=3,
            )
        )
        await f["rope_allowed_splice"](
            CreateRopeAllowedSpliceFixtureDTO(
                rope_product_id=rope_1.product_id,
                splice_type_id=st_aug.id,
            )
        )
        await f["rope_allowed_splice"](
            CreateRopeAllowedSpliceFixtureDTO(
                rope_product_id=rope_1.product_id,
                splice_type_id=st_endless.id,
            )
        )
        await f["rope_allowed_splice"](
            CreateRopeAllowedSpliceFixtureDTO(
                rope_product_id=rope_1.product_id,
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
                working_stretch_percent=1.2,
                can_be_spliced=True,
            )
        )
        await f["rope_variant"](
            CreateRopeVariantFixtureDTO(
                rope_product_id=rope_2.product_id,
                diameter_mm=8.0,
                price_per_meter=4.50,
                breaking_load_dan=3500.0,
                weight_g_per_m=45.0,
                index=1,
                is_active=True,
            )
        )
        await f["rope_variant"](
            CreateRopeVariantFixtureDTO(
                rope_product_id=rope_2.product_id,
                diameter_mm=10.0,
                price_per_meter=6.80,
                breaking_load_dan=5000.0,
                weight_g_per_m=60.0,
                index=2,
                is_active=True,
            )
        )
        await f["rope_variant"](
            CreateRopeVariantFixtureDTO(
                rope_product_id=rope_2.product_id,
                diameter_mm=12.0,
                price_per_meter=9.50,
                breaking_load_dan=7200.0,
                weight_g_per_m=85.0,
                index=3,
                is_active=True,
            )
        )
        await f["rope_color"](
            CreateRopeProductColorFixtureDTO(
                rope_product_id=rope_2.product_id,
                color_id=c_red.id,
                index=1,
            )
        )
        await f["rope_color"](
            CreateRopeProductColorFixtureDTO(
                rope_product_id=rope_2.product_id,
                color_id=c_blue.id,
                index=2,
            )
        )
        await f["rope_color"](
            CreateRopeProductColorFixtureDTO(
                rope_product_id=rope_2.product_id,
                color_id=c_black.id,
                index=3,
            )
        )
        await f["rope_allowed_splice"](
            CreateRopeAllowedSpliceFixtureDTO(
                rope_product_id=rope_2.product_id,
                splice_type_id=st_aug.id,
            )
        )

        # 9. Дополнительные опции конфигуратора
        logger.info("Creating configurator extras via fixtures...")
        extra_1 = await f["configurator_extra"](
            CreateConfiguratorExtraFixtureDTO(
                code="leather_protection",
                price=15.00,
                billing_type=BillingType.PER_ITEM,
                currency=Currency.EUR,
                index=1,
                is_active=True,
                locale=Language.GER,
                name="Leder Scheuerschutz",
                description="Hochwertiger Lederschutz gegen Abrieb im Auge",
            )
        )
        await f["configurator_extra_translation"](
            CreateConfiguratorExtraTranslationFixtureDTO(
                extra_id=extra_1.id,
                locale=Language.ENG,
                name="Leather Chafe Protection",
                description="Premium leather protection against abrasion in the eye",
            )
        )

        extra_2 = await f["configurator_extra"](
            CreateConfiguratorExtraFixtureDTO(
                code="dyneema_chafe_sleeve",
                price=8.50,
                billing_type=BillingType.PER_METER,
                currency=Currency.EUR,
                index=2,
                is_active=True,
                locale=Language.GER,
                name="Dyneema Scheuerschutzschlauch",
                description="Geflochtener Dyneema-Schutzschlauch pro Meter",
            )
        )
        await f["configurator_extra_translation"](
            CreateConfiguratorExtraTranslationFixtureDTO(
                extra_id=extra_2.id,
                locale=Language.ENG,
                name="Dyneema Chafe Sleeve",
                description="Braided Dyneema protective sleeve per meter",
            )
        )

        extra_3 = await f["configurator_extra"](
            CreateConfiguratorExtraFixtureDTO(
                code="messenger_line_loop",
                price=5.00,
                billing_type=BillingType.PER_ITEM,
                currency=Currency.EUR,
                index=3,
                is_active=True,
                locale=Language.GER,
                name="Pilotaug / Einziehhilfe",
                description="Kleine Hilfsschlaufe zum Einziehen des Falls",
            )
        )
        await f["configurator_extra_translation"](
            CreateConfiguratorExtraTranslationFixtureDTO(
                extra_id=extra_3.id,
                locale=Language.ENG,
                name="Messenger Line Loop",
                description="Small auxiliary loop for reeving halyards",
            )
        )

        # 10. Примеры заявок для всех трёх конфигураторов
        logger.info("Creating sample quote requests via create_quote_request_fixture...")
        # Конфигуратор 1: Канат + петли
        req_1 = await f["quote_request"](
            CreateQuoteRequestFixtureDTO(
                request_number="RPL-TEST-0001",
                configurator_type=ConfiguratorType.ROPE_WITH_SPLICE,
                name="Max Mustermann",
                email="max@example.com",
                phone="+49 170 1234567",
                comment="Test request: 20m polyester rope with eye splice and whipped end",
                currency=Currency.EUR,
                total_price=81.50,
                vat_rate=0.0,
                is_urgent=False,
                status=QuoteRequestStatus.NEW,
                rope_items=[
                    CreateQuoteRopeItemFixtureDTO(
                        rope_product_id=rope_1.product_id,
                        color_id=c_navy.id,
                        product_name_snapshot="Standard Polyester Rope",
                        color_name_snapshot="Navyblau",
                        diameter_mm=10.0,
                        length_m=20.0,
                        quantity=1,
                        price_per_meter_snapshot=2.50,
                        total_rope_cost=50.00,
                        end_a_type_id=st_aug.id,
                        end_a_name_snapshot="Augspleiß",
                        end_a_eye_size_cm=15.0,
                        end_a_cost=15.00,
                        end_b_type_id=st_takling.id,
                        end_b_name_snapshot="Takling",
                        end_b_eye_size_cm=None,
                        end_b_cost=1.50,
                    )
                ],
                extra_items=[
                    CreateQuoteExtraItemFixtureDTO(
                        extra_id=extra_1.id,
                        name_snapshot="Leder Scheuerschutz",
                        billing_type_snapshot="per_item",
                        quantity=1,
                        unit_price_snapshot=15.00,
                        total_cost=15.00,
                    )
                ],
            )
        )

        # Конфигуратор 2: Только петли
        req_2 = await f["quote_request"](
            CreateQuoteRequestFixtureDTO(
                request_number="RPL-TEST-0002",
                configurator_type=ConfiguratorType.LOOP_ONLY,
                name="Anna Schmidt",
                email="anna@example.com",
                phone="+49 171 9876543",
                comment="Test request: Two high-tech eye splices on customer rope",
                currency=Currency.EUR,
                total_price=60.00,
                vat_rate=0.0,
                is_urgent=False,
                status=QuoteRequestStatus.IN_PROGRESS,
                service_items=[
                    CreateQuoteServiceItemFixtureDTO(
                        splice_type_id=st_aug.id,
                        splice_material_id=sm_hightech.id,
                        service_name_snapshot="Augspleiß",
                        material_name_snapshot="High-Tech (Dyneema / Vectran / Zylon)",
                        diameter_mm=10.0,
                        eye_size_cm=20.0,
                        quantity=2,
                        unit_price_snapshot=30.00,
                        total_cost=60.00,
                    )
                ],
            )
        )

        # Конфигуратор 3: Только сращивание
        req_3 = await f["quote_request"](
            CreateQuoteRequestFixtureDTO(
                request_number="RPL-TEST-0003",
                configurator_type=ConfiguratorType.SPLICE_ONLY,
                name="Lukas Weber",
                email="lukas@example.com",
                phone="+49 172 5554433",
                comment="Test request: Endless splice with urgent processing",
                currency=Currency.EUR,
                total_price=43.00,
                vat_rate=0.0,
                is_urgent=True,
                status=QuoteRequestStatus.CONFIRMED,
                service_items=[
                    CreateQuoteServiceItemFixtureDTO(
                        splice_type_id=st_endless.id,
                        splice_material_id=sm_standard.id,
                        service_name_snapshot="Endlosspleiß",
                        material_name_snapshot="Standard (Kern-Mantel)",
                        diameter_mm=12.0,
                        eye_size_cm=None,
                        quantity=1,
                        unit_price_snapshot=33.00,
                        total_cost=33.00,
                    )
                ],
            )
        )

        logger.info("Test records created successfully using fixtures from tests/fixturs/__init__.py!")
        logger.info(
            f"Summary: 2 users, 1 setting, 2 splice materials, 3 splice types, {len(rules)} price rules, "
            "5 colors, 3 material groups, 3 materials, 2 rope products, 3 extras, 3 quote requests."
        )

        return {
            "setting": setting,
            "users": {"admin": admin_user, "customer": customer_user},
            "splice_materials": {"standard": sm_standard, "high_tech": sm_hightech},
            "splice_types": {"aug_splice": st_aug, "endless": st_endless, "takling": st_takling},
            "price_rules": rules,
            "colors": {"red": c_red, "blue": c_blue, "black": c_black, "white": c_white, "navy": c_navy},
            "material_groups": {"polyester": mg_poly, "dyneema": mg_dyneema, "polyamid": mg_polyamid},
            "materials": {"pes_standard": m_pes, "sk78": m_sk78, "sk99": m_sk99},
            "rope_products": [rope_1, rope_2],
            "configurator_extras": {"leather": extra_1, "sleeve": extra_2, "loop": extra_3},
            "quote_requests": [req_1, req_2, req_3],
        }


create_test_records = create_test_data


def main() -> None:
    """Точка входа CLI."""
    parser = argparse.ArgumentParser(description="Create basic test records in DB using test fixtures")
    parser.add_argument(
        "--no-clean",
        action="store_true",
        help="Do not clear existing database records before creating",
    )
    args = parser.parse_args()

    asyncio.run(create_test_data(clean=not args.no_clean))


if __name__ == "__main__":
    main()

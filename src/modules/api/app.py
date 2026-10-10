from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from passlib.context import CryptContext

from src.core.config import create_config
from src.modules.api.exception_handler import register_exception_handlers
from src.modules.auth.views import router as auth_router
from src.modules.users.views import router as user_router
from src.modules.splice_types.views import router as splice_types_router
from src.modules.splice_materials.views import router as splice_materials_router
from src.modules.splice_prices.views import router as splice_prices_router
from src.modules.colors.views import router as colors_router
from src.modules.rope_product_color.views import router as rope_product_colors_router
from src.modules.rope_allowed_splice.views import router as rope_allowed_splices_router
from src.modules.rope_products.views import router as rope_products_router, variants_router as rope_variants_router
from src.modules.material_groups.views import router as material_groups_router


def _include_routers(app: FastAPI) -> FastAPI:
    app.include_router(auth_router)
    app.include_router(user_router)
    app.include_router(splice_types_router)
    app.include_router(splice_materials_router)
    app.include_router(splice_prices_router)
    app.include_router(colors_router)
    app.include_router(rope_product_colors_router)
    app.include_router(rope_allowed_splices_router)
    app.include_router(rope_products_router)
    app.include_router(rope_variants_router)
    app.include_router(material_groups_router)
    return app


def init_fastapi_app() -> FastAPI:
    app = FastAPI(
        title="Auth Service",
        lifespan=lifespan
    )

    config = create_config()
    app.state.config = config
    register_exception_handlers(app)

    # Раздача медиа файлов (статических изображений)
    app.mount("/media", StaticFiles(directory=config.paths.media), name="media")

    _include_routers(app)

    return app


@asynccontextmanager
async def lifespan(app: FastAPI):
    config = create_config()
    app.state.config = config
    app.state.cr_context = CryptContext(
        schemes=["bcrypt"],
        deprecated="auto"
    )

    try:
        yield
    finally:
        pass

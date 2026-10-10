from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from passlib.context import CryptContext

from src.core.config import create_config, Config
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
from src.modules.materials.views import router as materials_router
from src.modules.quote_requests.views import router as quote_requests_router


def _include_middlewares(app: FastAPI, config: Config) -> FastAPI:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.cors.allow_origins,
        allow_origin_regex=config.cors.allow_origin_regex,
        allow_credentials=config.cors.allow_credentials,
        allow_methods=config.cors.allow_methods,
        allow_headers=config.cors.allow_headers,
        expose_headers=config.cors.expose_headers,
    )
    return app


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
    app.include_router(materials_router)
    app.include_router(quote_requests_router)
    return app


def init_fastapi_app() -> FastAPI:
    app = FastAPI(
        title="Auth Service",
        lifespan=lifespan
    )

    config = create_config()
    app.state.config = config

    _include_middlewares(app, config)
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

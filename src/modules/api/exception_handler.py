from fastapi import FastAPI
from starlette.responses import JSONResponse

from src.modules.base.exception import ServiceException, NoDataForUpdate, NotFoundData
from src.modules.check_permission.exception import PermissionErrorService
from src.modules.colors.exception import (
    ColorAlreadyExists,
    ColorTranslationAlreadyExists,
    ColorTranslationDeleteError,
    ColorHasDependencies,
)
from src.modules.splice_materials.exception import SpliceMaterialHasDependencies
from src.modules.splice_types.exception import (
    SpliceTypeAlreadyExists,
    SpliceTypeTranslationAlreadyExists,
    SpliceTypeTranslationDeleteError,
    SpliceTypeHasDependencies,
)
from src.modules.rope_product_color.exception import RopeProductColorAlreadyExists
from src.modules.rope_allowed_splice.exception import RopeAllowedSpliceAlreadyExists
from src.modules.rope_products.exception import (
    RopeProductAlreadyExists,
    RopeVariantAlreadyExists,
    RopeProductHasDependencies,
)
from src.modules.material_groups.exception import (
    MaterialGroupAlreadyExists,
    MaterialGroupTranslationAlreadyExists,
    MaterialGroupTranslationDeleteError,
    MaterialGroupHasDependencies,
)
from src.modules.materials.exception import (
    MaterialAlreadyExists,
    MaterialTranslationAlreadyExists,
    MaterialTranslationDeleteError,
    MaterialHasDependencies,
)
from src.modules.quote_requests.exception import (
    QuoteRequestValidationError,
    ColorNotAllowedForProduct,
    RopeCannotBeSplicedError,
    SpliceNotAllowedForProductError,
    SplicePriceRuleNotFound,
)

def register_exception_handlers(app: FastAPI):

    @app.exception_handler(PermissionErrorService)
    async def permission_error_handler(request, exc):
        return JSONResponse(status_code=403, content={"detail": "Forbidden"})

    @app.exception_handler(ServiceException)
    async def service_handler(request, exc):
        return JSONResponse(status_code=500, content={"detail": "Server Error"})

    @app.exception_handler(NoDataForUpdate)
    async def nodata_handler(request, exc):
        return JSONResponse(status_code=400, content={"detail": "Did not transmit data"})

    @app.exception_handler(NotFoundData)
    async def notfound_handler(request, exc):
        return JSONResponse(status_code=404, content={"detail": "Not found data"})

    @app.exception_handler(SpliceTypeAlreadyExists)
    async def splice_type_already_exists_handler(request, exc):
        return JSONResponse(status_code=409, content={"detail": str(exc)})

    @app.exception_handler(SpliceTypeTranslationAlreadyExists)
    async def splice_type_translation_already_exists_handler(request, exc):
        return JSONResponse(status_code=409, content={"detail": str(exc)})

    @app.exception_handler(SpliceTypeTranslationDeleteError)
    async def splice_type_translation_delete_error_handler(request, exc):
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    @app.exception_handler(SpliceTypeHasDependencies)
    async def splice_type_has_dependencies_handler(request, exc):
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    @app.exception_handler(SpliceMaterialHasDependencies)
    async def splice_material_has_dependencies_handler(request, exc):
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    @app.exception_handler(ColorAlreadyExists)
    async def color_already_exists_handler(request, exc):
        return JSONResponse(status_code=409, content={"detail": str(exc)})

    @app.exception_handler(ColorTranslationAlreadyExists)
    async def color_translation_already_exists_handler(request, exc):
        return JSONResponse(status_code=409, content={"detail": str(exc)})

    @app.exception_handler(ColorTranslationDeleteError)
    async def color_translation_delete_error_handler(request, exc):
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    @app.exception_handler(ColorHasDependencies)
    async def color_has_dependencies_handler(request, exc):
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    @app.exception_handler(RopeProductColorAlreadyExists)
    async def rope_product_color_already_exists_handler(request, exc):
        return JSONResponse(status_code=409, content={"detail": str(exc)})

    @app.exception_handler(RopeAllowedSpliceAlreadyExists)
    async def rope_allowed_splice_already_exists_handler(request, exc):
        return JSONResponse(status_code=409, content={"detail": str(exc)})

    @app.exception_handler(RopeProductAlreadyExists)
    async def rope_product_already_exists_handler(request, exc):
        return JSONResponse(status_code=409, content={"detail": str(exc)})

    @app.exception_handler(RopeVariantAlreadyExists)
    async def rope_variant_already_exists_handler(request, exc):
        return JSONResponse(status_code=409, content={"detail": str(exc)})

    @app.exception_handler(RopeProductHasDependencies)
    async def rope_product_has_dependencies_handler(request, exc):
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    @app.exception_handler(MaterialGroupAlreadyExists)
    async def material_group_already_exists_handler(request, exc):
        return JSONResponse(status_code=409, content={"detail": str(exc)})

    @app.exception_handler(MaterialGroupTranslationAlreadyExists)
    async def material_group_translation_already_exists_handler(request, exc):
        return JSONResponse(status_code=409, content={"detail": str(exc)})

    @app.exception_handler(MaterialGroupTranslationDeleteError)
    async def material_group_translation_delete_error_handler(request, exc):
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    @app.exception_handler(MaterialGroupHasDependencies)
    async def material_group_has_dependencies_handler(request, exc):
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    @app.exception_handler(MaterialAlreadyExists)
    async def material_already_exists_handler(request, exc):
        return JSONResponse(status_code=409, content={"detail": str(exc)})

    @app.exception_handler(MaterialTranslationAlreadyExists)
    async def material_translation_already_exists_handler(request, exc):
        return JSONResponse(status_code=409, content={"detail": str(exc)})

    @app.exception_handler(MaterialTranslationDeleteError)
    async def material_translation_delete_error_handler(request, exc):
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    @app.exception_handler(MaterialHasDependencies)
    async def material_has_dependencies_handler(request, exc):
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    @app.exception_handler(QuoteRequestValidationError)
    async def quote_validation_handler(request, exc):
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    @app.exception_handler(ColorNotAllowedForProduct)
    async def color_not_allowed_handler(request, exc):
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    @app.exception_handler(RopeCannotBeSplicedError)
    async def rope_cannot_be_spliced_handler(request, exc):
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    @app.exception_handler(SpliceNotAllowedForProductError)
    async def splice_not_allowed_handler(request, exc):
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    @app.exception_handler(SplicePriceRuleNotFound)
    async def splice_price_not_found_handler(request, exc):
        return JSONResponse(status_code=400, content={"detail": str(exc)})

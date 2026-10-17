from fastapi import FastAPI
from sqlalchemy.exc import IntegrityError
from starlette.responses import JSONResponse

from src.modules.base.exception import ServiceException, NoDataForUpdate, NotFoundData, DataAlreadyExists, \
    HasDependencies, DeleteError
from src.modules.check_permission.exception import PermissionErrorService
from src.modules.configurator_setting.exception import ConfiguratorSettingValidationError
from src.modules.product_specification.exception import (
    ProductSpecificationInvalidBatch,
)
from src.modules.quote_requests.exception import (
    QuoteRequestValidationError,
    ColorNotAllowedForProduct,
    RopeCannotBeSplicedError,
    SpliceNotAllowedForProductError,
    SplicePriceRuleNotFound,
)


def register_exception_handlers(app: FastAPI):

    # ==================== 400 Bad Request ====================
    @app.exception_handler(NoDataForUpdate)
    async def nodata_handler(request, exc):
        return JSONResponse(status_code=400, content={"detail": "Did not transmit data"})

    @app.exception_handler(DeleteError)
    async def delete_error_handler(request, exc):
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    @app.exception_handler(HasDependencies)
    async def has_dependencies_handler(request, exc):
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

    @app.exception_handler(ConfiguratorSettingValidationError)
    async def configurator_setting_validation_handler(request, exc):
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    @app.exception_handler(ProductSpecificationInvalidBatch)
    async def product_specification_invalid_batch_handler(request, exc):
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    # ==================== 403 Forbidden ====================
    @app.exception_handler(PermissionErrorService)
    async def permission_error_handler(request, exc):
        return JSONResponse(status_code=403, content={"detail": "Forbidden"})

    # ==================== 404 Not Found ====================
    @app.exception_handler(NotFoundData)
    async def notfound_handler(request, exc):
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    # ==================== 409 Conflict ====================
    @app.exception_handler(IntegrityError)
    async def integrity_error_handler(request, exc):
        return JSONResponse(status_code=409, content={"detail": "conflict with the current state of the resource"})

    @app.exception_handler(DataAlreadyExists)
    async def data_already_exists_handler(request, exc):
        return JSONResponse(status_code=409, content={"detail": str(exc)})

    # ==================== 500 Internal Server Error ====================
    @app.exception_handler(ServiceException)
    async def service_handler(request, exc):
        return JSONResponse(status_code=500, content={"detail": "Server Error"})



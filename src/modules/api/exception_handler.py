import logging
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from slowapi.errors import RateLimitExceeded
from sqlalchemy.exc import IntegrityError
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)

from src.modules.base.exception import (
    DataAlreadyExists,
    DeleteError,
    HasDependencies,
    NoDataForUpdate,
    NotFoundData,
    ServiceException,
    ValidationError,
)
from src.modules.categories.exception import CategoryValidationError
from src.modules.colors.exception import ColorValidationError
from src.modules.configurator_extra.exception import ConfiguratorExtraValidationError
from src.modules.materials.exception import MaterialValidationError
from src.modules.material_groups.exception import MaterialGroupValidationError
from src.modules.products.exception import ProductValidationError
from src.modules.splice_types.exception import SpliceTypeValidationError
from src.modules.check_permission.exception import PermissionErrorService
from src.modules.configurator_setting.exception import ConfiguratorSettingValidationError
from src.modules.product_specification.exception import (
    ProductSpecificationInvalidBatch,
)
from src.modules.auth.exception import (
    InvalidCredentials,
    InvalidJWTToken,
    UserInactive,
)
from src.modules.handlers_files.exception import FileTooLarge, InvalidImageFormat
from src.modules.users.exception import IncorrectPassword
from src.modules.quote_requests.exception import (
    QuoteRequestValidationError,
    ColorNotAllowedForProduct,
    RopeCannotBeSplicedError,
    SpliceNotAllowedForProductError,
    SplicePriceRuleNotFound,
)


def register_exception_handlers(app: FastAPI):

    # ==================== 400 Bad Request ====================
    @app.exception_handler(IncorrectPassword)
    async def incorrect_password_handler(request, exc):
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    @app.exception_handler(InvalidImageFormat)
    async def invalid_image_format_handler(request, exc):
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    @app.exception_handler(ValidationError)
    async def validation_error_handler(request, exc):
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    @app.exception_handler(CategoryValidationError)
    async def category_validation_handler(request, exc):
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    @app.exception_handler(ColorValidationError)
    async def color_validation_handler(request, exc):
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    @app.exception_handler(ConfiguratorExtraValidationError)
    async def configurator_extra_validation_handler(request, exc):
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    @app.exception_handler(MaterialValidationError)
    async def material_validation_handler(request, exc):
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    @app.exception_handler(MaterialGroupValidationError)
    async def material_group_validation_handler(request, exc):
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    @app.exception_handler(ProductValidationError)
    async def product_validation_handler(request, exc):
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    @app.exception_handler(SpliceTypeValidationError)
    async def splice_type_validation_handler(request, exc):
        return JSONResponse(status_code=400, content={"detail": str(exc)})

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

    # ==================== 401 Unauthorized ====================
    @app.exception_handler(InvalidCredentials)
    async def invalid_credentials_handler(request, exc):
        return JSONResponse(status_code=401, content={"detail": "Invalid credentials"})

    @app.exception_handler(InvalidJWTToken)
    async def invalid_jwt_token_handler(request, exc):
        return JSONResponse(status_code=401, content={"detail": "Invalid or expired token"})

    # ==================== 403 Forbidden ====================
    @app.exception_handler(PermissionErrorService)
    async def permission_error_handler(request, exc):
        return JSONResponse(status_code=403, content={"detail": "Forbidden"})

    @app.exception_handler(UserInactive)
    async def user_inactive_handler(request, exc):
        return JSONResponse(status_code=403, content={"detail": "User account is inactive"})

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

    # ==================== 409 RateLimit ====================
    @app.exception_handler(RateLimitExceeded)
    async def rate_limit_handler(request, exc: RateLimitExceeded):
        return JSONResponse(
            status_code=429,
            content={
                "detail": f"Rate limit exceeded: {exc.detail}. Please try again later."
            },
            headers={"Retry-After": str(exc.detail)}
        )

    # ==================== 422 Unprocessable Entity ====================
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request, exc: RequestValidationError):
        errors = exc.errors()
        if errors:
            first_err = errors[0]
            field = first_err.get("loc", ["field"])[-1]
            readable_msg = f"{field}: {first_err.get('msg', 'Validation error')}"
        else:
            readable_msg = "Validation error"

        return JSONResponse(
            status_code=422,
            content={
                "detail": readable_msg,
                "message": readable_msg,
                "errors": errors,
            },
        )

    # ==================== 413 Payload Too Large ====================
    @app.exception_handler(FileTooLarge)
    async def file_too_large_handler(request, exc):
        return JSONResponse(status_code=413, content={"detail": str(exc)})

    # ==================== 500 Internal Server Error ====================
    @app.exception_handler(ServiceException)
    async def service_handler(request, exc):
        return JSONResponse(status_code=500, content={"detail": "Server Error"})

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request, exc):
        logger.error("Unhandled server exception: %s", exc, exc_info=True)
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})




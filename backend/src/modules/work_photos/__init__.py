from src.modules.work_photos.models import WorkPhoto, WorkPhotoTranslation
from src.modules.work_photos.models_dto import (
    CreateWorkPhotoRequestDTO,
    UpdateWorkPhotoIndexRequestDTO,
    UpdateWorkPhotoRequestDTO,
    WorkPhotoBaseDTO,
    WorkPhotoResponseDTO,
    WorkPhotoTranslationCreate,
    WorkPhotoTranslationInsert,
    WorkPhotoTranslationResponseDTO,
    WorkPhotoTranslationUpdate,
)
from src.modules.work_photos.repository import (
    WorkPhotoRepository,
    WorkPhotoTranslationRepository,
)
from src.modules.work_photos.service import WorkPhotoService
from src.modules.work_photos.views import router as work_photos_router

__all__ = [
    "WorkPhoto",
    "WorkPhotoTranslation",
    "WorkPhotoBaseDTO",
    "CreateWorkPhotoRequestDTO",
    "UpdateWorkPhotoRequestDTO",
    "UpdateWorkPhotoIndexRequestDTO",
    "WorkPhotoResponseDTO",
    "WorkPhotoTranslationCreate",
    "WorkPhotoTranslationUpdate",
    "WorkPhotoTranslationResponseDTO",
    "WorkPhotoTranslationInsert",
    "WorkPhotoRepository",
    "WorkPhotoTranslationRepository",
    "WorkPhotoService",
    "work_photos_router",
]

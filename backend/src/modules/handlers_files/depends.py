from fastapi import Request

from src.modules.handlers_files.service import ImageManager


def get_image_manager(
    request: Request,
) -> ImageManager:
    return ImageManager(
        config=request.app.state.config,
    )

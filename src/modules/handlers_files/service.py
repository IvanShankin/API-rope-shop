from pathlib import Path
from typing import Tuple, Optional

from fastapi import UploadFile

from src.core.config import Config
from src.modules.handlers_files.converter_images import HandlerImages
from src.modules.handlers_files.compression_images import CompressionImages


class ImageManager:
    """
    Универсальный менеджер для обработки, конвертации и сохранения изображений.
    Объединяет HandlerImages (конвертация в .webp) и CompressionImages (сжатие/ресайз).
    """

    def __init__(
        self,
        config: Config,
        converter: Optional[HandlerImages] = None,
        compressor: Optional[CompressionImages] = None,
    ):
        self.config = config
        self.converter = converter or HandlerImages(config=config)
        self.compressor = compressor or CompressionImages(config=config)

    async def save_image(
        self,
        file: UploadFile,
        destination: Path,
        compress: bool = True,
        max_size: Tuple[int, int] = (512, 512),
        quality: int = 80,
    ) -> Path:
        """
        Конвертирует входящее изображение в .webp, при необходимости сжимает
        и сохраняет по указанному пути destination.
        
        :param file: Входящий файл UploadFile.
        :param destination: Полный путь к целевому файлу или целевая директория.
        :param compress: Сжимать/ресайзить ли изображение.
        :param max_size: Максимальные размеры (ширина, высота) при сжатии.
        :param quality: Качество WebP (1-100).
        :return: Итоговый путь к сохраненному файлу .webp.
        """
        # Сначала конвертируем файл в .webp по указанному пути назначения
        saved_webp_path = await self.converter.convert_to_webp(
            photo=file,
            dest=destination,
            quality=quality,
        )

        # Если требуется сжатие/ресайз — сжимаем прямо на месте
        if compress:
            saved_webp_path = await self.compressor.compress_webp(
                file=saved_webp_path,
                dest=saved_webp_path,
                max_size=max_size,
                quality=quality,
            )

        return saved_webp_path

    def to_media_url(self, file_path: Path | str) -> str:
        """
        Преобразует абсолютный путь к файлу в относительный URL для медиа-раздачи.
        Например: /media/splice_types/1/image.webp
        """
        path = Path(file_path).resolve()
        media_root = self.config.paths.media.resolve()
        try:
            rel_path = path.relative_to(media_root)
            return f"/media/{rel_path.as_posix()}"
        except ValueError:
            return path.as_posix()

    def delete_image(self, file_path: Path | str | None) -> None:
        """
        Безопасно удаляет файл изображения с диска.
        """
        if not file_path:
            return

        # Если передан URL вида /media/..., переводим в путь на диске
        path_str = str(file_path)
        if path_str.startswith("/media/"):
            rel_part = path_str.removeprefix("/media/")
            target_path = (self.config.paths.media / rel_part).resolve()
        else:
            target_path = Path(file_path).resolve()

        if target_path.exists() and target_path.is_file():
            target_path.unlink(missing_ok=True)

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
        max_size: Tuple[int, int] = (1920, 1920),
        quality: int = 100,
        original_destination: Optional[Path] = None,
    ) -> Path:
        """
        Конвертирует входящее изображение в .webp, при необходимости сжимает
        и сохраняет по указанному пути destination.
        При передаче original_destination сохраняет точную копию оригинального файла.
        
        :param file: Входящий файл UploadFile.
        :param destination: Полный путь к целевому файлу или целевая директория.
        :param compress: Сжимать/ресайзить ли изображение.
        :param max_size: Максимальные размеры (ширина, высота) при сжатии (по умолчанию 1920x1920 Full HD).
        :param quality: Качество WebP (1-100).
        :param original_destination: Путь для сохранения исходного файла без модификаций.
        :return: Итоговый путь к сохраненному файлу .webp.
        """
        # Сначала конвертируем файл в .webp по указанному пути назначения
        saved_webp_path = await self.converter.convert_to_webp(
            photo=file,
            dest=destination,
            quality=quality,
            original_dest=original_destination,
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
            return f"/{self.config.paths.media.name}/{rel_path.as_posix()}"
        except ValueError:
            return path.as_posix()

    def delete_image(self, file_path: Path | str | None) -> None:
        """
        Безопасно удаляет файл изображения с диска и сопутствующий оригинал (если есть).
        """
        if not file_path:
            return

        # Если передан URL вида /media/..., переводим в путь на диске
        path_str = str(file_path)
        if path_str.startswith(f"/{self.config.paths.media.name}/"):
            rel_part = path_str.removeprefix(f"/{self.config.paths.media.name}/")
            target_path = (self.config.paths.media / rel_part).resolve()
        else:
            target_path = Path(file_path).resolve()

        if target_path.exists() and target_path.is_file():
            target_path.unlink(missing_ok=True)

        # Проверяем и удаляем сопутствующий исходный файл в подпапке original/
        orig_dir = target_path.parent / "original"
        if orig_dir.exists() and orig_dir.is_dir():
            for orig_file in orig_dir.glob(f"{target_path.stem}.*"):
                orig_file.unlink(missing_ok=True)
            if orig_dir.exists() and not any(orig_dir.iterdir()):
                try:
                    orig_dir.rmdir()
                except OSError:
                    pass

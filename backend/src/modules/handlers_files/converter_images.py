import asyncio
import shutil
import uuid
from pathlib import Path
from typing import Optional, Set

from fastapi import UploadFile
from PIL import Image, ImageOps, ImageSequence, UnidentifiedImageError
import pillow_heif

from src.core.config import Config
from src.modules.handlers_files.exception import (
    InvalidImageFormat,
    FileTooLarge,
    ImageConversionError,
)

# Регистрируем поддержку HEIF/HEIC для Pillow
pillow_heif.register_heif_opener()


def _convert_image_sync(
    source_path: Path,
    target_path: Path,
    quality: int,
    lossless: bool,
) -> None:
    """
    Синхронная CPU-bound конвертация изображения в WebP.
    Выполняется в отдельном потоке пула worker-ов (asyncio.to_thread),
    чтобы не блокировать основной Event Loop FastAPI.
    """
    try:
        with Image.open(source_path) as image:
            is_animated = (
                getattr(image, "is_animated", False)
                and getattr(image, "n_frames", 1) > 1
            )

            if is_animated:
                frames = []
                durations = []
                for frame in ImageSequence.Iterator(image):
                    f = ImageOps.exif_transpose(frame) or frame
                    if f.mode in ("RGBA", "LA"):
                        f_conv = f.copy()
                    elif f.mode == "P":
                        if "transparency" in f.info:
                            f_conv = f.convert("RGBA")
                        else:
                            f_conv = f.convert("RGB")
                    elif f.mode in ("RGB", "L"):
                        f_conv = f.copy()
                    else:
                        f_conv = f.convert("RGB")

                    frames.append(f_conv)
                    durations.append(
                        frame.info.get("duration", image.info.get("duration", 100))
                    )

                duration = (
                    durations
                    if any(d != durations[0] for d in durations)
                    else durations[0]
                )

                frames[0].save(
                    target_path,
                    format="WEBP",
                    save_all=True,
                    append_images=frames[1:],
                    quality=quality,
                    lossless=lossless,
                    loop=image.info.get("loop", 0),
                    duration=duration,
                )
            else:
                # Корректируем ориентацию по EXIF (актуально для фото со смартфонов/камер)
                image = ImageOps.exif_transpose(image) or image

                # Обработка цветовых режимов для статического изображения
                if image.mode in ("RGBA", "LA"):
                    converted_img = image
                elif image.mode == "P":
                    if "transparency" in image.info:
                        converted_img = image.convert("RGBA")
                    else:
                        converted_img = image.convert("RGB")
                elif image.mode in ("RGB", "L"):
                    converted_img = image
                else:
                    converted_img = image.convert("RGB")

                converted_img.save(
                    target_path,
                    format="WEBP",
                    quality=quality,
                    lossless=lossless,
                )
    except (UnidentifiedImageError, OSError) as e:
        raise InvalidImageFormat(
            f"Не удалось распознать изображение или файл поврежден: {e}"
        ) from e
    except Exception as e:
        raise ImageConversionError(
            f"Ошибка при конвертации изображения в .webp: {e}"
        ) from e


class HandlerImages:
    CHUNK_SIZE: int = 64 * 1024  # 64 KB чанки для потокового чтения без переполнения RAM

    def __init__(
        self,
        config: Config,
    ):
        self.config = config
        max_mb = getattr(
            getattr(config, "allowed_extensions", None), "max_image_size_mb", 15
        )
        self.max_file_size_bytes = max_mb * 1024 * 1024

    def _get_allowed_extensions(self) -> Set[str]:
        """Возвращает нормализованное множество разрешенных расширений без точек в нижнем регистре."""
        return {
            ext.lstrip(".").lower()
            for ext in self.config.allowed_extensions.for_image
        }

    def _validate_extension(self, filename: str | None) -> str:
        """
        Проверяет расширение файла на допустимость.
        :raises InvalidImageFormat: если расширение недопустимо или отсутствует.
        :return: расширение файла в нижнем регистре без точки.
        """
        if not filename:
            raise InvalidImageFormat("Имя файла не передано.")

        suffix = Path(filename).suffix
        if not suffix:
            raise InvalidImageFormat(f"Файл '{filename}' не имеет расширения.")

        ext = suffix.lstrip(".").lower()
        allowed = self._get_allowed_extensions()
        if ext not in allowed:
            raise InvalidImageFormat(
                f"Недопустимый формат файла '{suffix}'. Разрешенные форматы: {', '.join(sorted(allowed))}."
            )
        return ext

    async def convert_to_webp(
        self,
        photo: UploadFile,
        dest: Path,
        quality: int = 100,
        lossless: bool = True,
        original_dest: Optional[Path] = None,
    ) -> Path:
        """
        Конвертирует переданное изображение в формат .webp и сохраняет по указанному пути dest.
        Читает файл чанками для защиты от OOM DoS, проверяет ограничение размера,
        опционально сохраняет точную копию оригинального файла в original_dest
        и выполняет вычисления Pillow в worker-треде через asyncio.to_thread.

        :param photo: Загружаемый файл UploadFile.
        :param dest: Директория или полный путь к файлу назначения.
        :param quality: Качество сжатия WebP (1-100).
        :param lossless: Использовать ли сжатие без потерь.
        :param original_dest: Путь для сохранения исходного файла без конвертации.
        :return: Итоговый путь Path к сохраненному .webp файлу.
        :raises InvalidImageFormat: Если расширение или формат файла недопустимы / повреждены.
        :raises FileTooLarge: Если размер файла превышает лимит.
        :raises ImageConversionError: При ошибке в процессе конвертации / сохранения.
        """
        self._validate_extension(photo.filename)

        # Определяем итоговый путь сохранения файла
        if dest.is_dir() or not dest.suffix:
            filename_stem = (
                Path(photo.filename).stem if photo.filename else uuid.uuid4().hex
            )
            target_path = (dest / f"{filename_stem}.webp").resolve()
        else:
            target_path = dest.with_suffix(".webp").resolve()

        target_path.parent.mkdir(parents=True, exist_ok=True)

        # Временный файл в директории temp из конфига
        temp_filename = f"temp_{uuid.uuid4().hex}_{photo.filename or 'upload'}"
        temp_file_path = (self.config.paths.temp / temp_filename).resolve()

        try:
            # Читаем содержимое загруженного файла чанками для защиты от OOM
            total_size = 0
            with open(temp_file_path, "wb") as temp_file:
                while chunk := await photo.read(self.CHUNK_SIZE):
                    total_size += len(chunk)
                    if total_size > self.max_file_size_bytes:
                        limit_mb = self.max_file_size_bytes // (1024 * 1024)
                        raise FileTooLarge(
                            f"Размер файла превышает максимально допустимый ({limit_mb} МБ)."
                        )
                    temp_file.write(chunk)

            if total_size == 0:
                raise InvalidImageFormat("Файл пуст.")

            # Сохранение оригинала до конвертации (если запрошено)
            if original_dest is not None:
                original_dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(temp_file_path, original_dest)

            # Выполняем тяжелую конвертацию Pillow в фоновом потоке
            await asyncio.to_thread(
                _convert_image_sync,
                temp_file_path,
                target_path,
                quality,
                lossless,
            )

        finally:
            # Удаляем временный файл
            if temp_file_path.exists():
                temp_file_path.unlink(missing_ok=True)
            # Возвращаем указатель файла в начало
            await photo.seek(0)

        return target_path

from pathlib import Path
from typing import Callable
from PIL import Image
import pytest
from fastapi import UploadFile

from src.core.config.config import Config
from src.modules.handlers_files.converter_images import HandlerImages
from src.modules.handlers_files.compression_images import CompressionImages
from src.modules.handlers_files.exception import InvalidImageFormat
from src.modules.handlers_files.service import ImageManager


def test_image_manager_init(config_fix: Config):
    """Проверка инициализации менеджера с дефолтными и кастомными компонентами."""
    # Дефолтная инициализация
    manager_default = ImageManager(config=config_fix)
    assert isinstance(manager_default.converter, HandlerImages)
    assert isinstance(manager_default.compressor, CompressionImages)
    assert manager_default.config is config_fix

    # Инициализация с переданными converter и compressor
    custom_converter = HandlerImages(config=config_fix)
    custom_compressor = CompressionImages(config=config_fix)
    manager_custom = ImageManager(
        config=config_fix,
        converter=custom_converter,
        compressor=custom_compressor,
    )
    assert manager_custom.converter is custom_converter
    assert manager_custom.compressor is custom_compressor


@pytest.mark.asyncio
async def test_save_image_with_compression(
    image_manager_fixture: ImageManager,
    create_upload_file_fixture: Callable[[bytes, str], UploadFile],
    create_image_bytes_fixture: Callable[..., bytes],
    tmp_path: Path,
):
    """Проверка сохранения изображения со сжатием и ресайзом."""
    img_bytes = create_image_bytes_fixture(format_="PNG", size=(1200, 800), color="blue")
    upload_file = create_upload_file_fixture(img_bytes, "source.png")

    dest_file = tmp_path / "result.webp"
    saved_path = await image_manager_fixture.save_image(
        file=upload_file,
        destination=dest_file,
        compress=True,
        max_size=(400, 400),
        quality=80,
    )

    assert saved_path.exists()
    assert saved_path == dest_file.resolve()

    with Image.open(saved_path) as img:
        assert img.format == "WEBP"
        # Пропорция 1200x800 с ограничением 400x400 -> 400x266 (или 400x267)
        assert img.size[0] <= 400
        assert img.size[1] <= 400
        assert img.size[0] == 400


@pytest.mark.asyncio
async def test_save_image_without_compression(
    image_manager_fixture: ImageManager,
    create_upload_file_fixture: Callable[[bytes, str], UploadFile],
    create_image_bytes_fixture: Callable[..., bytes],
    tmp_path: Path,
):
    """Проверка сохранения изображения без сжатия (compress=False)."""
    img_bytes = create_image_bytes_fixture(format_="JPEG", size=(800, 600), color="green")
    upload_file = create_upload_file_fixture(img_bytes, "photo.jpg")

    dest_file = tmp_path / "uncompressed.webp"
    saved_path = await image_manager_fixture.save_image(
        file=upload_file,
        destination=dest_file,
        compress=False,
    )

    assert saved_path.exists()
    with Image.open(saved_path) as img:
        assert img.format == "WEBP"
        # Размеры должны сохраниться оригинальными
        assert img.size == (800, 600)


@pytest.mark.asyncio
async def test_save_image_destination_directory(
    image_manager_fixture: ImageManager,
    create_upload_file_fixture: Callable[[bytes, str], UploadFile],
    create_image_bytes_fixture: Callable[..., bytes],
    tmp_path: Path,
):
    """Проверка сохранения, когда destination является директорией."""
    img_bytes = create_image_bytes_fixture(format_="PNG", size=(200, 200), color="yellow")
    upload_file = create_upload_file_fixture(img_bytes, "avatar.png")

    dest_dir = tmp_path / "images_folder"
    dest_dir.mkdir(parents=True, exist_ok=True)

    saved_path = await image_manager_fixture.save_image(
        file=upload_file,
        destination=dest_dir,
        compress=True,
    )

    assert saved_path.exists()
    assert saved_path.parent == dest_dir.resolve()
    assert saved_path.suffix == ".webp"
    with Image.open(saved_path) as img:
        assert img.format == "WEBP"


@pytest.mark.asyncio
async def test_save_image_invalid_format(
    image_manager_fixture: ImageManager,
    create_upload_file_fixture: Callable[[bytes, str], UploadFile],
    tmp_path: Path,
):
    """Проверка выброса исключения InvalidImageFormat при попытке сохранить невалидный файл."""
    upload_file = create_upload_file_fixture(b"invalid image content", "test.txt")

    dest_file = tmp_path / "out.webp"
    with pytest.raises(InvalidImageFormat):
        await image_manager_fixture.save_image(
            file=upload_file,
            destination=dest_file,
        )


def test_to_media_url_inside_media(
    image_manager_fixture: ImageManager,
    config_fix: Config,
):
    """Проверка генерации media url для пути внутри папки media."""
    media_root = config_fix.paths.media.resolve()
    test_file_path = media_root / f"{config_fix.paths.splice_types.name}" / "1" / "preview.webp"

    url_from_path = image_manager_fixture.to_media_url(test_file_path)
    assert url_from_path == f"/{config_fix.paths.media.name}/{config_fix.paths.splice_types.name}/1/preview.webp"

    url_from_str = image_manager_fixture.to_media_url(str(test_file_path))
    assert url_from_str == f"/{config_fix.paths.media.name}/{config_fix.paths.splice_types.name}/1/preview.webp"


def test_to_media_url_outside_media(
    image_manager_fixture: ImageManager,
    tmp_path: Path,
):
    """Проверка генерации URL для пути вне папки media."""
    outside_file = tmp_path / "some_folder" / "photo.webp"

    url = image_manager_fixture.to_media_url(outside_file)
    assert url == outside_file.resolve().as_posix()


def test_delete_image_with_media_url(
    image_manager_fixture: ImageManager,
    config_fix: Config,
):
    """Проверка удаления файла по URL вида /media/..."""
    rel_subpath = Path("test_delete_manager") / "test_img.webp"
    full_path = config_fix.paths.media / rel_subpath
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_bytes(b"dummy webp content")

    assert full_path.exists()

    media_url = f"/{config_fix.paths.media.name}/{rel_subpath.as_posix()}"
    image_manager_fixture.delete_image(media_url)

    assert not full_path.exists()

    # Очистка созданной тестовой поддиректории
    if full_path.parent.exists():
        full_path.parent.rmdir()


def test_delete_image_with_path_and_str(
    image_manager_fixture: ImageManager,
    tmp_path: Path,
):
    """Проверка удаления файла по Path и строковому пути."""
    file_path = tmp_path / "to_delete.webp"
    file_path.write_bytes(b"test content")
    assert file_path.exists()

    # Удаление через Path
    image_manager_fixture.delete_image(file_path)
    assert not file_path.exists()

    # Удаление через строку
    file_str_path = tmp_path / "to_delete_str.webp"
    file_str_path.write_bytes(b"test content")
    assert file_str_path.exists()

    image_manager_fixture.delete_image(str(file_str_path))
    assert not file_str_path.exists()


def test_delete_image_safe_handling(
    image_manager_fixture: ImageManager,
    tmp_path: Path,
    config_fix: Config,
):
    """Проверка безопасного вызова delete_image при None, пустой строке, несуществующем файле или папке."""
    # None и пустая строка не должны вызывать исключений
    image_manager_fixture.delete_image(None)
    image_manager_fixture.delete_image("")

    # Несуществующий URL и файл не должны вызывать исключений
    image_manager_fixture.delete_image(f"/{config_fix.paths.media.name}/non_existent_folder/missing.webp")
    image_manager_fixture.delete_image(tmp_path / "non_existent_file.webp")

    # Папка не должна удаляться
    sub_dir = tmp_path / "sub_dir"
    sub_dir.mkdir(parents=True, exist_ok=True)
    image_manager_fixture.delete_image(sub_dir)
    assert sub_dir.exists()

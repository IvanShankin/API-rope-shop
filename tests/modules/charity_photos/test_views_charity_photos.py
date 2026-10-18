import pytest
from sqlalchemy import select

from src.core.config import Config
from src.modules.base.database_model import Language
from src.modules.charity_photos.models import CharityPhoto
from src.modules.charity_photos.models_dto import (
    CharityPhotoResponseDTO,
    CreateCharityPhotoRequestDTO,
    UpdateCharityPhotoIndexRequestDTO,
    UpdateCharityPhotoRequestDTO,
)
from src.modules.users.models import UserRole
from tests.helpers.functions import comparison_models
from tests.modules.charity_photos.fixtures.models_dto import (
    CreateCharityPhotoFixtureDTO,
)
from tests.modules.users.fixtures.models_dto import CreateUserFixtureDTO


class TestsForSuccess:

    @pytest.mark.asyncio
    async def test_get_all_charity_photos(
        self,
        client_for_tests,
        create_charity_photo_fixture,
    ):
        """Получение списка благотворительных фото (публичный доступ)."""
        photo_1 = await create_charity_photo_fixture(
            CreateCharityPhotoFixtureDTO(index=0, is_active=True, title="Charity 1")
        )
        photo_2 = await create_charity_photo_fixture(
            CreateCharityPhotoFixtureDTO(index=1, is_active=True, title="Charity 2")
        )

        response = await client_for_tests.get("/charity_photos")
        assert response.status_code == 200

        data = [CharityPhotoResponseDTO.model_validate(item) for item in response.json()]
        assert len(data) == 2
        assert data[0].id == photo_1.id
        assert data[1].id == photo_2.id

    @pytest.mark.asyncio
    async def test_get_all_charity_photos_filter_active(
        self,
        client_for_tests,
        create_charity_photo_fixture,
    ):
        """Получение списка благотворительных фото с фильтрацией по is_active."""
        active_photo = await create_charity_photo_fixture(
            CreateCharityPhotoFixtureDTO(index=0, is_active=True)
        )
        await create_charity_photo_fixture(
            CreateCharityPhotoFixtureDTO(index=1, is_active=False)
        )

        response = await client_for_tests.get("/charity_photos?is_active=true")
        assert response.status_code == 200

        data = [CharityPhotoResponseDTO.model_validate(item) for item in response.json()]
        assert len(data) == 1
        assert data[0].id == active_photo.id

    @pytest.mark.asyncio
    async def test_get_charity_photo_by_id(
        self,
        client_for_tests,
        create_charity_photo_fixture,
    ):
        """Получение одного благотворительного фото по ID (публичный доступ)."""
        photo = await create_charity_photo_fixture()

        response = await client_for_tests.get(f"/charity_photos/{photo.id}")
        assert response.status_code == 200

        data = CharityPhotoResponseDTO.model_validate(response.json())
        assert data.id == photo.id
        assert data.image_url == photo.image_url

    @pytest.mark.asyncio
    async def test_create_charity_photo_file(
        self,
        client_for_tests,
        create_user_fixture,
        create_image_bytes_fixture,
        session_db,
        config_fix: Config,
    ):
        """Создание благотворительного фото через multipart upload (админ)."""
        _, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        img_bytes = create_image_bytes_fixture(format_="PNG", size=(200, 200), color="blue")

        response = await client_for_tests.post(
            "/charity_photos",
            headers={"Authorization": f"Bearer {access_token}"},
            files={"file": ("charity_event.png", img_bytes, "image/png")},
            data={
                "title": "Charity Event",
                "description": "Helping shelter",
                "index": "0",
                "is_active": "true",
            },
        )
        assert response.status_code == 201

        resp_dto = CharityPhotoResponseDTO.model_validate(response.json())
        assert resp_dto.title == "Charity Event"
        assert resp_dto.description == "Helping shelter"
        assert resp_dto.index == 0
        assert resp_dto.is_active is True
        assert resp_dto.image_url.startswith(
            f"/{config_fix.paths.media.name}/{config_fix.paths.charity_photos.name}"
        )
        assert resp_dto.image_url.endswith(".webp")

        db_obj = await session_db.scalar(
            select(CharityPhoto).where(CharityPhoto.id == resp_dto.id)
        )
        assert db_obj is not None
        assert db_obj.image_url == resp_dto.image_url
        assert db_obj.title == resp_dto.title

    @pytest.mark.asyncio
    async def test_upload_charity_photo_file(
        self,
        config_fix,
        client_for_tests,
        create_user_fixture,
        create_image_bytes_fixture,
        session_db,
    ):
        """Загрузка файла благотворительного фото (админ)."""
        _, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        img_bytes = create_image_bytes_fixture(format_="PNG", size=(200, 200), color="yellow")

        response = await client_for_tests.post(
            "/charity_photos/upload",
            headers={"Authorization": f"Bearer {access_token}"},
            files={"file": ("charity.png", img_bytes, "image/png")},
            data={"title": "Uploaded Charity", "description": "Good deed", "is_active": "true"},
        )
        assert response.status_code == 201

        resp_dto = CharityPhotoResponseDTO.model_validate(response.json())
        assert resp_dto.title == "Uploaded Charity"
        assert resp_dto.description == "Good deed"
        assert resp_dto.image_url.startswith(f"/{config_fix.paths.media.name}/{config_fix.paths.charity_photos.name}")
        assert resp_dto.image_url.endswith(".webp")

        db_obj = await session_db.scalar(
            select(CharityPhoto).where(CharityPhoto.id == resp_dto.id)
        )
        assert db_obj is not None
        assert db_obj.image_url == resp_dto.image_url

    @pytest.mark.asyncio
    async def test_upload_image_for_existing_charity_photo(
        self,
        config_fix,
        client_for_tests,
        create_user_fixture,
        create_charity_photo_fixture,
        create_image_bytes_fixture,
        session_db,
    ):
        """Замена файла для существующего благотворительного фото (админ)."""
        _, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        photo = await create_charity_photo_fixture()
        img_bytes = create_image_bytes_fixture(format_="PNG", size=(200, 200), color="purple")

        response = await client_for_tests.post(
            f"/charity_photos/{photo.id}/upload-image",
            headers={"Authorization": f"Bearer {access_token}"},
            files={"file": ("new_charity.png", img_bytes, "image/png")},
        )
        assert response.status_code == 200

        resp_dto = CharityPhotoResponseDTO.model_validate(response.json())
        assert resp_dto.id == photo.id
        assert resp_dto.image_url.startswith(f"/{config_fix.paths.media.name}/{config_fix.paths.charity_photos.name}")
        assert resp_dto.image_url.endswith(".webp")

    @pytest.mark.asyncio
    async def test_update_charity_photo(
        self,
        client_for_tests,
        create_user_fixture,
        create_charity_photo_fixture,
        create_image_bytes_fixture,
        session_db,
        config_fix: Config,
    ):
        """Обновление атрибутов благотворительного фото и замена файла изображения (админ)."""
        _, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        photo = await create_charity_photo_fixture()

        update_dto = UpdateCharityPhotoRequestDTO(
            title="Updated Charity Title",
            description="Updated Charity Description",
            is_active=False,
        )

        response = await client_for_tests.patch(
            f"/charity_photos/{photo.id}",
            headers={"Authorization": f"Bearer {access_token}"},
            json=update_dto.model_dump(exclude_unset=True),
        )
        assert response.status_code == 200

        resp_dto = CharityPhotoResponseDTO.model_validate(response.json())
        assert resp_dto.title == "Updated Charity Title"
        assert resp_dto.description == "Updated Charity Description"
        assert resp_dto.is_active is False
        assert resp_dto.image_url == photo.image_url

        # Замена файла изображения через PATCH
        new_img_bytes = create_image_bytes_fixture(format_="PNG", size=(150, 150), color="orange")
        replace_res = await client_for_tests.patch(
            f"/charity_photos/{photo.id}",
            headers={"Authorization": f"Bearer {access_token}"},
            files={"file": ("replaced_charity.png", new_img_bytes, "image/png")},
            data={"title": "Replaced Title"},
        )
        assert replace_res.status_code == 200
        replace_dto = CharityPhotoResponseDTO.model_validate(replace_res.json())
        assert replace_dto.title == "Replaced Title"
        assert replace_dto.image_url != photo.image_url
        assert replace_dto.image_url.startswith(
            f"/{config_fix.paths.media.name}/{config_fix.paths.charity_photos.name}"
        )

    @pytest.mark.asyncio
    async def test_reorder_charity_photo(
        self,
        client_for_tests,
        create_user_fixture,
        create_charity_photo_fixture,
        session_db,
    ):
        """Перемещение позиции благотворительного фото со сдвигом соседей (админ)."""
        _, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        p0 = await create_charity_photo_fixture(CreateCharityPhotoFixtureDTO(index=0))
        p1 = await create_charity_photo_fixture(CreateCharityPhotoFixtureDTO(index=1))
        p2 = await create_charity_photo_fixture(CreateCharityPhotoFixtureDTO(index=2))

        # Перемещаем p2 на позицию 0 (сдвигает p0->1, p1->2)
        reorder_dto = UpdateCharityPhotoIndexRequestDTO(new_index=0)
        response = await client_for_tests.patch(
            f"/charity_photos/{p2.id}/index",
            headers={"Authorization": f"Bearer {access_token}"},
            json=reorder_dto.model_dump(),
        )
        assert response.status_code == 200
        resp_dto = CharityPhotoResponseDTO.model_validate(response.json())
        assert resp_dto.index == 0

        # Проверяем в базе
        db_p0 = await session_db.scalar(select(CharityPhoto).where(CharityPhoto.id == p0.id))
        db_p1 = await session_db.scalar(select(CharityPhoto).where(CharityPhoto.id == p1.id))
        db_p2 = await session_db.scalar(select(CharityPhoto).where(CharityPhoto.id == p2.id))

        assert db_p2.index == 0
        assert db_p0.index == 1
        assert db_p1.index == 2

    @pytest.mark.asyncio
    async def test_delete_charity_photo(
        self,
        client_for_tests,
        create_user_fixture,
        create_charity_photo_fixture,
        session_db,
    ):
        """Удаление благотворительного фото со сдвигом последующих индексов (админ)."""
        _, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        p0 = await create_charity_photo_fixture(CreateCharityPhotoFixtureDTO(index=0))
        p1 = await create_charity_photo_fixture(CreateCharityPhotoFixtureDTO(index=1))

        response = await client_for_tests.delete(
            f"/charity_photos/{p0.id}",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 204

        # p0 удален
        deleted = await session_db.scalar(select(CharityPhoto).where(CharityPhoto.id == p0.id))
        assert deleted is None

        # p1 сдвинулся на index 0
        remaining = await session_db.scalar(select(CharityPhoto).where(CharityPhoto.id == p1.id))
        assert remaining.index == 0

    @pytest.mark.asyncio
    async def test_get_charity_photos_with_locale(
        self,
        client_for_tests,
        create_user_fixture,
        create_charity_photo_fixture,
    ):
        """Получение благотворительных фото с запросом определенной локали."""
        _, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        photo = await create_charity_photo_fixture(
            CreateCharityPhotoFixtureDTO(title="English Title", description="English Desc")
        )
        # Добавляем перевод на русский через API
        add_res = await client_for_tests.post(
            f"/charity_photos/{photo.id}/translations",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "locale": "rus",
                "title": "Русское название",
                "description": "Русское описание",
            },
        )
        assert add_res.status_code == 201

        # Запрос с locale=ru
        resp_ru = await client_for_tests.get(f"/charity_photos/{photo.id}?locale=ru")
        assert resp_ru.status_code == 200
        dto_ru = CharityPhotoResponseDTO.model_validate(resp_ru.json())
        assert dto_ru.title == "Русское название"
        assert dto_ru.description == "Русское описание"
        assert len(dto_ru.translations) == 2

        # Запрос с locale=en
        resp_en = await client_for_tests.get(f"/charity_photos/{photo.id}?locale=en")
        assert resp_en.status_code == 200
        dto_en = CharityPhotoResponseDTO.model_validate(resp_en.json())
        assert dto_en.title == "English Title"

    @pytest.mark.asyncio
    async def test_charity_photo_translations_crud(
        self,
        client_for_tests,
        create_user_fixture,
        create_charity_photo_fixture,
    ):
        """CRUD операции с переводами благотворительного фото (админ)."""
        _, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        photo = await create_charity_photo_fixture(
            CreateCharityPhotoFixtureDTO(title="Charity EN", description="Desc EN")
        )

        # 1. Добавление перевода (ger)
        add_res = await client_for_tests.post(
            f"/charity_photos/{photo.id}/translations",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "locale": "ger",
                "title": "Spende DE",
                "description": "Beschreibung DE",
            },
        )
        assert add_res.status_code == 201
        tr_data = add_res.json()
        assert tr_data["locale"] == "ger"
        assert tr_data["title"] == "Spende DE"
        tr_id = tr_data["id"]

        # 2. Обновление перевода
        patch_res = await client_for_tests.patch(
            f"/charity_photos/{photo.id}/translations/{tr_id}",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"title": "Aktualisierte Spende DE"},
        )
        assert patch_res.status_code == 200
        assert patch_res.json()["title"] == "Aktualisierte Spende DE"

        # 3. Удаление перевода
        del_res = await client_for_tests.delete(
            f"/charity_photos/{photo.id}/translations/{tr_id}",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert del_res.status_code == 204


class TestsForFailed:

    @pytest.mark.asyncio
    async def test_get_nonexistent_charity_photo_returns_404(
        self,
        client_for_tests,
    ):
        """Запрос несуществующего благотворительного фото возвращает 404."""
        response = await client_for_tests.get("/charity_photos/999999")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_create_charity_photo_unauthorized_returns_401(
        self,
        client_for_tests,
    ):
        """Создание благотворительного фото без токена возвращает 401."""
        response = await client_for_tests.post(
            "/charity_photos",
            files={"file": ("photo.png", b"test", "image/png")},
            data={"title": "Test"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_create_charity_photo_regular_user_returns_403(
        self,
        client_for_tests,
        create_user_fixture,
    ):
        """Создание благотворительного фото обычным пользователем возвращает 403."""
        _, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.USER)
        )
        response = await client_for_tests.post(
            "/charity_photos",
            headers={"Authorization": f"Bearer {access_token}"},
            files={"file": ("photo.png", b"test", "image/png")},
            data={"title": "Test"},
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_upload_charity_photo_regular_user_returns_403(
        self,
        client_for_tests,
        create_user_fixture,
        create_image_bytes_fixture,
    ):
        """Загрузка файла обычным пользователем возвращает 403."""
        _, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.USER)
        )
        img_bytes = create_image_bytes_fixture()

        response = await client_for_tests.post(
            "/charity_photos/upload",
            headers={"Authorization": f"Bearer {access_token}"},
            files={"file": ("photo.png", img_bytes, "image/png")},
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_update_charity_photo_no_data_returns_400(
        self,
        client_for_tests,
        create_user_fixture,
        create_charity_photo_fixture,
    ):
        """Обновление фото без данных возвращает 400."""
        _, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        photo = await create_charity_photo_fixture()

        response = await client_for_tests.patch(
            f"/charity_photos/{photo.id}",
            headers={"Authorization": f"Bearer {access_token}"},
            json={},
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_update_nonexistent_charity_photo_returns_404(
        self,
        client_for_tests,
        create_user_fixture,
    ):
        """Обновление несуществующего фото возвращает 404."""
        _, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        response = await client_for_tests.patch(
            "/charity_photos/999999",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"title": "New Title"},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_nonexistent_charity_photo_returns_404(
        self,
        client_for_tests,
        create_user_fixture,
    ):
        """Удаление несуществующего фото возвращает 404."""
        _, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        response = await client_for_tests.delete(
            "/charity_photos/999999",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 404

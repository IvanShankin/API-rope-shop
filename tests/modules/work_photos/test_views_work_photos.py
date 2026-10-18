import pytest
from sqlalchemy import select

from src.modules.users.models import UserRole
from src.modules.work_photos.models import WorkPhoto
from src.modules.work_photos.models_dto import (
    CreateWorkPhotoRequestDTO,
    UpdateWorkPhotoIndexRequestDTO,
    UpdateWorkPhotoRequestDTO,
    WorkPhotoResponseDTO,
)
from tests.helpers.functions import comparison_models
from tests.modules.users.fixtures.models_dto import CreateUserFixtureDTO
from tests.modules.work_photos.fixtures.models_dto import (
    CreateWorkPhotoFixtureDTO,
)


class TestsForSuccess:

    @pytest.mark.asyncio
    async def test_get_all_work_photos(
        self,
        client_for_tests,
        create_work_photo_fixture,
    ):
        """Получение списка фотографий работ (публичный доступ)."""
        photo_1 = await create_work_photo_fixture(
            CreateWorkPhotoFixtureDTO(index=0, is_active=True, title="Photo 1")
        )
        photo_2 = await create_work_photo_fixture(
            CreateWorkPhotoFixtureDTO(index=1, is_active=True, title="Photo 2")
        )

        response = await client_for_tests.get("/work_photos")
        assert response.status_code == 200

        data = [WorkPhotoResponseDTO.model_validate(item) for item in response.json()]
        assert len(data) == 2
        assert data[0].id == photo_1.id
        assert data[1].id == photo_2.id

    @pytest.mark.asyncio
    async def test_get_all_work_photos_filter_active(
        self,
        client_for_tests,
        create_work_photo_fixture,
    ):
        """Получение списка фотографий работ с фильтрацией по is_active."""
        active_photo = await create_work_photo_fixture(
            CreateWorkPhotoFixtureDTO(index=0, is_active=True)
        )
        await create_work_photo_fixture(
            CreateWorkPhotoFixtureDTO(index=1, is_active=False)
        )

        response = await client_for_tests.get("/work_photos?is_active=true")
        assert response.status_code == 200

        data = [WorkPhotoResponseDTO.model_validate(item) for item in response.json()]
        assert len(data) == 1
        assert data[0].id == active_photo.id

    @pytest.mark.asyncio
    async def test_get_work_photo_by_id(
        self,
        client_for_tests,
        create_work_photo_fixture,
    ):
        """Получение одной фотографии работы по ID (публичный доступ)."""
        photo = await create_work_photo_fixture()

        response = await client_for_tests.get(f"/work_photos/{photo.id}")
        assert response.status_code == 200

        data = WorkPhotoResponseDTO.model_validate(response.json())
        assert data.id == photo.id
        assert data.image_url == photo.image_url

    @pytest.mark.asyncio
    async def test_create_work_photo_via_json(
        self,
        client_for_tests,
        create_user_fixture,
        session_db,
    ):
        """Создание фотографии работы через JSON (админ)."""
        _, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )

        create_dto = CreateWorkPhotoRequestDTO(
            image_url="/media/work_photos/test.webp",
            title="Custom Title",
            description="Custom Description",
            index=0,
            is_active=True,
        )

        response = await client_for_tests.post(
            "/work_photos",
            headers={"Authorization": f"Bearer {access_token}"},
            json=create_dto.model_dump(),
        )
        assert response.status_code == 201

        resp_dto = WorkPhotoResponseDTO.model_validate(response.json())
        comparison_models(
            Expected=create_dto,
            Actual=resp_dto,
            keys_not_checked=["created_at", "updated_at"],
        )

        db_obj = await session_db.scalar(
            select(WorkPhoto).where(WorkPhoto.id == resp_dto.id)
        )
        assert db_obj is not None
        comparison_models(
            Expected=create_dto,
            Actual=db_obj,
            keys_not_checked=["created_at", "updated_at"],
        )

    @pytest.mark.asyncio
    async def test_upload_work_photo_file(
        self,
        config_fix,
        client_for_tests,
        create_user_fixture,
        create_image_bytes_fixture,
        session_db,
    ):
        """Загрузка файла фотографии работы (админ)."""
        _, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        img_bytes = create_image_bytes_fixture(format_="PNG", size=(200, 200), color="blue")

        response = await client_for_tests.post(
            "/work_photos/upload",
            headers={"Authorization": f"Bearer {access_token}"},
            files={"file": ("photo.png", img_bytes, "image/png")},
            data={"title": "Uploaded Work", "description": "Desc", "is_active": "true"},
        )
        assert response.status_code == 201

        resp_dto = WorkPhotoResponseDTO.model_validate(response.json())
        assert resp_dto.title == "Uploaded Work"
        assert resp_dto.description == "Desc"
        assert resp_dto.image_url.startswith(f"/{config_fix.paths.media.name}/{config_fix.paths.work_photos.name}")
        assert resp_dto.image_url.endswith(".webp")

        db_obj = await session_db.scalar(
            select(WorkPhoto).where(WorkPhoto.id == resp_dto.id)
        )
        assert db_obj is not None
        assert db_obj.image_url == resp_dto.image_url

    @pytest.mark.asyncio
    async def test_upload_image_for_existing_work_photo(
        self,
        config_fix,
        client_for_tests,
        create_user_fixture,
        create_work_photo_fixture,
        create_image_bytes_fixture,
        session_db,
    ):
        """Замена файла для существующей фотографии работы (админ)."""
        _, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        photo = await create_work_photo_fixture()
        img_bytes = create_image_bytes_fixture(format_="PNG", size=(200, 200), color="green")

        response = await client_for_tests.post(
            f"/work_photos/{photo.id}/upload-image",
            headers={"Authorization": f"Bearer {access_token}"},
            files={"file": ("new_photo.png", img_bytes, "image/png")},
        )
        assert response.status_code == 200

        resp_dto = WorkPhotoResponseDTO.model_validate(response.json())
        assert resp_dto.id == photo.id
        assert resp_dto.image_url.startswith(f"/{config_fix.paths.media.name}/{config_fix.paths.work_photos.name}")
        assert resp_dto.image_url.endswith(".webp")

    @pytest.mark.asyncio
    async def test_update_work_photo(
        self,
        client_for_tests,
        create_user_fixture,
        create_work_photo_fixture,
        session_db,
    ):
        """Обновление атрибутов фотографии работы (админ)."""
        _, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        photo = await create_work_photo_fixture()

        update_dto = UpdateWorkPhotoRequestDTO(
            title="Updated Title",
            description="Updated Description",
            is_active=False,
        )

        response = await client_for_tests.patch(
            f"/work_photos/{photo.id}",
            headers={"Authorization": f"Bearer {access_token}"},
            json=update_dto.model_dump(exclude_unset=True),
        )
        assert response.status_code == 200

        resp_dto = WorkPhotoResponseDTO.model_validate(response.json())
        assert resp_dto.title == "Updated Title"
        assert resp_dto.description == "Updated Description"
        assert resp_dto.is_active is False

    @pytest.mark.asyncio
    async def test_reorder_work_photo(
        self,
        client_for_tests,
        create_user_fixture,
        create_work_photo_fixture,
        session_db,
    ):
        """Перемещение позиции фотографии работы со сдвигом соседей (админ)."""
        _, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        p0 = await create_work_photo_fixture(CreateWorkPhotoFixtureDTO(index=0))
        p1 = await create_work_photo_fixture(CreateWorkPhotoFixtureDTO(index=1))
        p2 = await create_work_photo_fixture(CreateWorkPhotoFixtureDTO(index=2))

        # Перемещаем p2 на позицию 0 (сдвигает p0->1, p1->2)
        reorder_dto = UpdateWorkPhotoIndexRequestDTO(new_index=0)
        response = await client_for_tests.patch(
            f"/work_photos/{p2.id}/index",
            headers={"Authorization": f"Bearer {access_token}"},
            json=reorder_dto.model_dump(),
        )
        assert response.status_code == 200
        resp_dto = WorkPhotoResponseDTO.model_validate(response.json())
        assert resp_dto.index == 0

        # Проверяем в базе
        db_p0 = await session_db.scalar(select(WorkPhoto).where(WorkPhoto.id == p0.id))
        db_p1 = await session_db.scalar(select(WorkPhoto).where(WorkPhoto.id == p1.id))
        db_p2 = await session_db.scalar(select(WorkPhoto).where(WorkPhoto.id == p2.id))

        assert db_p2.index == 0
        assert db_p0.index == 1
        assert db_p1.index == 2

    @pytest.mark.asyncio
    async def test_delete_work_photo(
        self,
        client_for_tests,
        create_user_fixture,
        create_work_photo_fixture,
        session_db,
    ):
        """Удаление фотографии работы со сдвигом последующих индексов (админ)."""
        _, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        p0 = await create_work_photo_fixture(CreateWorkPhotoFixtureDTO(index=0))
        p1 = await create_work_photo_fixture(CreateWorkPhotoFixtureDTO(index=1))

        response = await client_for_tests.delete(
            f"/work_photos/{p0.id}",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 204

        # p0 удален
        deleted = await session_db.scalar(select(WorkPhoto).where(WorkPhoto.id == p0.id))
        assert deleted is None

        # p1 сдвинулся на index 0
        remaining = await session_db.scalar(select(WorkPhoto).where(WorkPhoto.id == p1.id))
        assert remaining.index == 0


class TestsForFailed:

    @pytest.mark.asyncio
    async def test_get_nonexistent_work_photo_returns_404(
        self,
        client_for_tests,
    ):
        """Запрос несуществующей фотографии работы возвращает 404."""
        response = await client_for_tests.get("/work_photos/999999")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_create_work_photo_unauthorized_returns_401(
        self,
        client_for_tests,
    ):
        """Создание фотографии работы без токена возвращает 401."""
        response = await client_for_tests.post(
            "/work_photos",
            json={"image_url": "/media/test.webp"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_create_work_photo_regular_user_returns_403(
        self,
        client_for_tests,
        create_user_fixture,
    ):
        """Создание фотографии работы обычным пользователем возвращает 403."""
        _, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.USER)
        )
        response = await client_for_tests.post(
            "/work_photos",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"image_url": "/media/test.webp"},
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_upload_work_photo_regular_user_returns_403(
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
            "/work_photos/upload",
            headers={"Authorization": f"Bearer {access_token}"},
            files={"file": ("photo.png", img_bytes, "image/png")},
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_update_work_photo_no_data_returns_400(
        self,
        client_for_tests,
        create_user_fixture,
        create_work_photo_fixture,
    ):
        """Обновление фотографии без данных возвращает 400."""
        _, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        photo = await create_work_photo_fixture()

        response = await client_for_tests.patch(
            f"/work_photos/{photo.id}",
            headers={"Authorization": f"Bearer {access_token}"},
            json={},
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_update_nonexistent_work_photo_returns_404(
        self,
        client_for_tests,
        create_user_fixture,
    ):
        """Обновление несуществующей фотографии возвращает 404."""
        _, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        response = await client_for_tests.patch(
            "/work_photos/999999",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"title": "New Title"},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_nonexistent_work_photo_returns_404(
        self,
        client_for_tests,
        create_user_fixture,
    ):
        """Удаление несуществующей фотографии возвращает 404."""
        _, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        response = await client_for_tests.delete(
            "/work_photos/999999",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 404

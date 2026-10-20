import pytest
from sqlalchemy import select

from src.core.config import Config
from src.modules.product_images.models import ProductImage
from src.modules.product_images.models_dto import (
    ProductImageCreate,
    ProductImageResponseDTO,
    ProductImageUpdate,
    ProductImageUpdateIndexDTO,
)
from src.modules.users.models import UserRole
from tests.helpers.functions import comparison_models
from tests.modules.product_images.fixtures.models_dto import (
    CreateProductImageFixtureDTO,
)
from tests.modules.users.fixtures.models_dto import CreateUserFixtureDTO
from tests.modules.products.fixtures.models_dto import CreateProductFixtureDTO


class TestsForSuccess:

    @pytest.mark.asyncio
    async def test_get_images_by_product_id(
        self,
        client_for_tests,
        create_product_fixture,
        create_product_image_fixture,
        config_fix: Config,
    ):
        """Получение списка изображений товара с фильтрацией по умолчанию."""
        product = await create_product_fixture()
        img_1 = await create_product_image_fixture(
            CreateProductImageFixtureDTO(
                product_id=product.id,
                image_url=f"/{config_fix.paths.media.name}/{config_fix.paths.products.name}/1/img1.webp",
                is_main=True,
                index=0,
                is_active=True,
            )
        )
        img_2 = await create_product_image_fixture(
            CreateProductImageFixtureDTO(
                product_id=product.id,
                image_url=f"/{config_fix.paths.media.name}/{config_fix.paths.products.name}/1/img2.webp",
                is_main=False,
                index=1,
                is_active=True,
            )
        )

        response = await client_for_tests.get(f"/product_images/by-product/{product.id}")
        assert response.status_code == 200

        data = [ProductImageResponseDTO.model_validate(item) for item in response.json()]
        assert len(data) == 2
        assert data[0].id == img_1.id
        assert data[0].is_main is True
        assert data[0].index == 0
        assert data[1].id == img_2.id
        assert data[1].is_main is False
        assert data[1].index == 1

    @pytest.mark.asyncio
    async def test_get_images_by_product_filter_active(
        self,
        client_for_tests,
        create_product_fixture,
        create_product_image_fixture,
    ):
        """Получение только активных изображений товара."""
        product = await create_product_fixture()
        img_active = await create_product_image_fixture(
            CreateProductImageFixtureDTO(
                product_id=product.id,
                index=0,
                is_active=True,
            )
        )
        await create_product_image_fixture(
            CreateProductImageFixtureDTO(
                product_id=product.id,
                index=1,
                is_active=False,
            )
        )

        response = await client_for_tests.get(
            f"/product_images/by-product/{product.id}?is_active=true"
        )
        assert response.status_code == 200

        data = [ProductImageResponseDTO.model_validate(item) for item in response.json()]
        assert len(data) == 1
        assert data[0].id == img_active.id

    @pytest.mark.asyncio
    async def test_get_images_by_product_filter_inactive_admin(
        self,
        client_for_tests,
        create_user_fixture,
        create_product_fixture,
        create_product_image_fixture,
    ):
        """Администратор может запросить неактивные изображения."""
        _, admin_token = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.ADMIN))
        product = await create_product_fixture()
        img_active = await create_product_image_fixture(
            CreateProductImageFixtureDTO(product_id=product.id, index=0, is_active=True)
        )
        img_inactive = await create_product_image_fixture(
            CreateProductImageFixtureDTO(product_id=product.id, index=1, is_active=False)
        )

        response = await client_for_tests.get(
            f"/product_images/by-product/{product.id}?is_active=false",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        ids = [item["id"] for item in response.json()]
        assert img_inactive.id in ids
        assert img_active.id not in ids

        # Аноним при ?is_active=false получает только активные
        anon_resp = await client_for_tests.get(f"/product_images/by-product/{product.id}?is_active=false")
        assert anon_resp.status_code == 200
        anon_ids = [item["id"] for item in anon_resp.json()]
        assert img_inactive.id not in anon_ids
        assert img_active.id in anon_ids

    @pytest.mark.asyncio
    async def test_get_image_by_id(
        self,
        client_for_tests,
        create_product_image_fixture,
    ):
        """Получение изображения по ID."""
        image = await create_product_image_fixture()

        response = await client_for_tests.get(f"/product_images/{image.id}")
        assert response.status_code == 200

        data = ProductImageResponseDTO.model_validate(response.json())
        assert data.id == image.id
        assert data.image_url == image.image_url

    @pytest.mark.asyncio
    async def test_create_product_image_file(
        self,
        session_db,
        client_for_tests,
        create_user_fixture,
        create_product_fixture,
        create_image_bytes_fixture,
        config_fix: Config,
    ):
        """Создание первого изображения товара через multipart (автоматически становится is_main=True)."""
        admin_user, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        product = await create_product_fixture()
        img_bytes = create_image_bytes_fixture(format_="PNG", size=(200, 200), color="blue")

        response = await client_for_tests.post(
            "/product_images",
            headers={"Authorization": f"Bearer {access_token}"},
            data={"product_id": str(product.id), "is_main": "false", "is_active": "true"},
            files={"file": ("img1.png", img_bytes, "image/png")},
        )
        assert response.status_code == 201

        resp_dto = ProductImageResponseDTO.model_validate(response.json())
        assert resp_dto.product_id == product.id
        assert resp_dto.image_url.startswith(
            f"/{config_fix.paths.media.name}/{config_fix.paths.products.name}/{product.id}/"
        )
        assert resp_dto.is_main is True
        assert resp_dto.index == 1
        assert resp_dto.is_active is True

        res = await session_db.execute(select(ProductImage).where(ProductImage.id == resp_dto.id))
        db_img = res.scalar_one_or_none()
        assert db_img is not None
        assert comparison_models(resp_dto, db_img)

    @pytest.mark.asyncio
    async def test_create_second_image_auto_index(
        self,
        session_db,
        client_for_tests,
        create_user_fixture,
        create_product_fixture,
        create_product_image_fixture,
        create_image_bytes_fixture,
        config_fix: Config,
    ):
        """Создание второго изображения товара получает index = max_index + 1 и is_main=False."""
        admin_user, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        product = await create_product_fixture()
        await create_product_image_fixture(
            CreateProductImageFixtureDTO(
                product_id=product.id,
                index=1,
                is_main=True,
            )
        )
        img_bytes = create_image_bytes_fixture(format_="PNG", size=(200, 200), color="green")

        response = await client_for_tests.post(
            "/product_images",
            headers={"Authorization": f"Bearer {access_token}"},
            data={"product_id": str(product.id), "is_main": "false", "is_active": "true"},
            files={"file": ("second_img.png", img_bytes, "image/png")},
        )
        assert response.status_code == 201

        resp_dto = ProductImageResponseDTO.model_validate(response.json())
        assert resp_dto.index == 2
        assert resp_dto.is_main is False

    @pytest.mark.asyncio
    async def test_upload_product_image_file(
        self,
        session_db,
        config_fix,
        client_for_tests,
        create_user_fixture,
        create_product_fixture,
        create_image_bytes_fixture,
    ):
        """Загрузка изображения через multipart form data."""
        admin_user, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        product = await create_product_fixture()
        img_bytes = create_image_bytes_fixture(format_="PNG", size=(300, 300), color="red")

        response = await client_for_tests.post(
            "/product_images/upload",
            headers={"Authorization": f"Bearer {access_token}"},
            data={"product_id": str(product.id), "is_main": "true", "is_active": "true"},
            files={"file": ("photo.png", img_bytes, "image/png")},
        )
        assert response.status_code == 201

        resp_dto = ProductImageResponseDTO.model_validate(response.json())
        assert resp_dto.product_id == product.id
        assert resp_dto.is_main is True
        assert resp_dto.image_url.startswith(f"/{config_fix.paths.media.name}/")

        rel_path = resp_dto.image_url.removeprefix(f"/{config_fix.paths.media.name}/")
        saved_file = config_fix.paths.media / rel_path
        assert saved_file.exists()

        if saved_file.exists():
            saved_file.unlink()
        if saved_file.parent.exists() and not any(saved_file.parent.iterdir()):
            saved_file.parent.rmdir()

    @pytest.mark.asyncio
    async def test_update_product_image(
        self,
        session_db,
        client_for_tests,
        create_user_fixture,
        create_product_image_fixture,
        create_image_bytes_fixture,
        config_fix: Config,
    ):
        """Обновление атрибутов изображения и замена файла изображения."""
        admin_user, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        image = await create_product_image_fixture(
            CreateProductImageFixtureDTO(is_active=True)
        )

        update_data = ProductImageUpdate(
            is_active=False,
        )

        response = await client_for_tests.patch(
            f"/product_images/{image.id}",
            headers={"Authorization": f"Bearer {access_token}"},
            json=update_data.model_dump(exclude_unset=True),
        )
        assert response.status_code == 200

        resp_dto = ProductImageResponseDTO.model_validate(response.json())
        assert resp_dto.is_active is False
        assert resp_dto.image_url == image.image_url

        session_db.expire_all()
        res = await session_db.execute(select(ProductImage).where(ProductImage.id == image.id))
        db_img = res.scalar_one_or_none()
        assert db_img.is_active is False

        # Замена файла изображения
        new_img_bytes = create_image_bytes_fixture(format_="PNG", size=(150, 150), color="yellow")
        replace_res = await client_for_tests.patch(
            f"/product_images/{image.id}",
            headers={"Authorization": f"Bearer {access_token}"},
            files={"file": ("replaced.png", new_img_bytes, "image/png")},
            data={"is_active": "true"},
        )
        assert replace_res.status_code == 200
        replace_dto = ProductImageResponseDTO.model_validate(replace_res.json())
        assert replace_dto.is_active is True
        assert replace_dto.image_url != image.image_url
        assert replace_dto.image_url.startswith(
            f"/{config_fix.paths.media.name}/{config_fix.paths.products.name}/{image.product_id}/"
        )

    @pytest.mark.asyncio
    async def test_set_main_product_image(
        self,
        session_db,
        client_for_tests,
        create_user_fixture,
        create_product_fixture,
        create_product_image_fixture,
    ):
        """Переключение главного изображения сбрасывает is_main у остальных."""
        admin_user, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        product = await create_product_fixture()
        img_1 = await create_product_image_fixture(
            CreateProductImageFixtureDTO(
                product_id=product.id,
                index=0,
                is_main=True,
            )
        )
        img_2 = await create_product_image_fixture(
            CreateProductImageFixtureDTO(
                product_id=product.id,
                index=1,
                is_main=False,
            )
        )

        response = await client_for_tests.patch(
            f"/product_images/{img_2.id}/main",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 200

        resp_dto = ProductImageResponseDTO.model_validate(response.json())
        assert resp_dto.id == img_2.id
        assert resp_dto.is_main is True

        session_db.expire_all()
        res1 = await session_db.execute(select(ProductImage).where(ProductImage.id == img_1.id))
        db_img1 = res1.scalar_one()
        assert db_img1.is_main is False

    @pytest.mark.asyncio
    async def test_reorder_product_image(
        self,
        session_db,
        client_for_tests,
        create_user_fixture,
        create_product_fixture,
        create_product_image_fixture,
    ):
        """Изменение позиции изображения со сдвигом соседей."""
        admin_user, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        product = await create_product_fixture()
        img_0 = await create_product_image_fixture(
            CreateProductImageFixtureDTO(product_id=product.id, index=0)
        )
        img_1 = await create_product_image_fixture(
            CreateProductImageFixtureDTO(product_id=product.id, index=1)
        )
        img_2 = await create_product_image_fixture(
            CreateProductImageFixtureDTO(product_id=product.id, index=2)
        )

        # Перемещаем img_2 на позицию 0
        response = await client_for_tests.patch(
            f"/product_images/{img_2.id}/index",
            headers={"Authorization": f"Bearer {access_token}"},
            json=ProductImageUpdateIndexDTO(new_index=0).model_dump(),
        )
        assert response.status_code == 200

        session_db.expire_all()
        res_0 = await session_db.execute(select(ProductImage).where(ProductImage.id == img_0.id))
        res_1 = await session_db.execute(select(ProductImage).where(ProductImage.id == img_1.id))
        res_2 = await session_db.execute(select(ProductImage).where(ProductImage.id == img_2.id))

        assert res_2.scalar_one().index == 0
        assert res_0.scalar_one().index == 1
        assert res_1.scalar_one().index == 2

    @pytest.mark.asyncio
    async def test_delete_product_image_promotes_next_main(
        self,
        session_db,
        client_for_tests,
        create_user_fixture,
        create_product_fixture,
        create_product_image_fixture,
    ):
        """Удаление главного изображения автоматически делает следующее главное."""
        admin_user, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        product = await create_product_fixture()
        img_1 = await create_product_image_fixture(
            CreateProductImageFixtureDTO(product_id=product.id, index=0, is_main=True)
        )
        img_2 = await create_product_image_fixture(
            CreateProductImageFixtureDTO(product_id=product.id, index=1, is_main=False)
        )

        response = await client_for_tests.delete(
            f"/product_images/{img_1.id}",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 204

        session_db.expire_all()
        res_deleted = await session_db.execute(select(ProductImage).where(ProductImage.id == img_1.id))
        assert res_deleted.scalar_one_or_none() is None

        res_remaining = await session_db.execute(select(ProductImage).where(ProductImage.id == img_2.id))
        remaining = res_remaining.scalar_one()
        assert remaining.is_main is True
        assert remaining.index == 0

    @pytest.mark.asyncio
    async def test_delete_product_image_removes_physical_file(
        self,
        config_fix,
        client_for_tests,
        create_user_fixture,
        create_product_fixture,
        create_image_bytes_fixture,
    ):
        """Удаление записи изображения удаляет соответствующий файл с диска."""
        admin_user, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        product = await create_product_fixture()
        img_bytes = create_image_bytes_fixture()

        upload_res = await client_for_tests.post(
            "/product_images/upload",
            headers={"Authorization": f"Bearer {access_token}"},
            data={"product_id": str(product.id)},
            files={"file": ("test.png", img_bytes, "image/png")},
        )
        assert upload_res.status_code == 201
        dto = ProductImageResponseDTO.model_validate(upload_res.json())

        rel_path = dto.image_url.removeprefix(f"/{config_fix.paths.media.name}/")
        saved_file = config_fix.paths.media / rel_path
        assert saved_file.exists()

        delete_res = await client_for_tests.delete(
            f"/product_images/{dto.id}",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert delete_res.status_code == 204
        assert not saved_file.exists()


class TestsForFail:

    @pytest.mark.asyncio
    async def test_get_images_by_nonexistent_product_returns_404(
        self,
        client_for_tests,
    ):
        response = await client_for_tests.get("/product_images/by-product/99999")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_nonexistent_image_by_id_returns_404(
        self,
        client_for_tests,
    ):
        response = await client_for_tests.get("/product_images/99999")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_create_product_image_unauthorized_returns_401(
        self,
        client_for_tests,
    ):
        response = await client_for_tests.post(
            "/product_images",
            data={"product_id": "1"},
            files={"file": ("photo.png", b"test", "image/png")},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_create_product_image_regular_user_returns_403(
        self,
        client_for_tests,
        create_user_fixture,
    ):
        user, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.USER)
        )
        response = await client_for_tests.post(
            "/product_images",
            headers={"Authorization": f"Bearer {access_token}"},
            data={"product_id": "1"},
            files={"file": ("photo.png", b"test", "image/png")},
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_create_product_image_nonexistent_product_returns_404(
        self,
        client_for_tests,
        create_user_fixture,
    ):
        admin_user, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        response = await client_for_tests.post(
            "/product_images",
            headers={"Authorization": f"Bearer {access_token}"},
            data={"product_id": "99999"},
            files={"file": ("photo.png", b"test", "image/png")},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_upload_image_nonexistent_product_returns_404(
        self,
        client_for_tests,
        create_user_fixture,
        create_image_bytes_fixture,
    ):
        admin_user, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        img_bytes = create_image_bytes_fixture()
        response = await client_for_tests.post(
            "/product_images/upload",
            headers={"Authorization": f"Bearer {access_token}"},
            data={"product_id": "99999"},
            files={"file": ("test.png", img_bytes, "image/png")},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_nonexistent_image_returns_404(
        self,
        client_for_tests,
        create_user_fixture,
    ):
        admin_user, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        response = await client_for_tests.patch(
            "/product_images/99999",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"is_active": False},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_image_empty_body_returns_400(
        self,
        client_for_tests,
        create_user_fixture,
        create_product_image_fixture,
    ):
        admin_user, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        img = await create_product_image_fixture()
        response = await client_for_tests.patch(
            f"/product_images/{img.id}",
            headers={"Authorization": f"Bearer {access_token}"},
            json={},
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_set_main_nonexistent_image_returns_404(
        self,
        client_for_tests,
        create_user_fixture,
    ):
        admin_user, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        response = await client_for_tests.patch(
            "/product_images/99999/main",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_reorder_nonexistent_image_returns_404(
        self,
        client_for_tests,
        create_user_fixture,
    ):
        admin_user, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        response = await client_for_tests.patch(
            "/product_images/99999/index",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"new_index": 0},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_inactive_image_by_id_anonymous_returns_404(
        self,
        client_for_tests,
        create_product_fixture,
        create_product_image_fixture,
    ):
        """Анонимный запрос неактивного изображения по ID -> 404."""
        product = await create_product_fixture()
        img = await create_product_image_fixture(
            CreateProductImageFixtureDTO(product_id=product.id, is_active=False)
        )
        response = await client_for_tests.get(f"/product_images/{img.id}")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_images_for_inactive_product_anonymous_returns_404(
        self,
        client_for_tests,
        create_product_fixture,
        create_product_image_fixture,
    ):
        """Анонимный запрос изображений неактивного товара -> 404."""
        product = await create_product_fixture(CreateProductFixtureDTO(is_active=False))
        await create_product_image_fixture(
            CreateProductImageFixtureDTO(product_id=product.id, is_active=True)
        )
        response = await client_for_tests.get(f"/product_images/by-product/{product.id}")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_nonexistent_image_returns_404(
        self,
        client_for_tests,
        create_user_fixture,
    ):
        admin_user, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        response = await client_for_tests.delete(
            "/product_images/99999",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 404

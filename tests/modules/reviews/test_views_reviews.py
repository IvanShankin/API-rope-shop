import pytest
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.modules.base.database_model import Language
from src.modules.reviews.models import Review, ReviewsStatus, ReviewTranslation
from src.modules.reviews.models_dto import (
    ReviewCreate,
    ReviewListResponseDTO,
    ReviewResponseDTO,
    ReviewStatusUpdate,
    ReviewTranslationCreate,
    ReviewTranslationResponseDTO,
    ReviewTranslationUpdate,
    ReviewUpdate,
    ReviewUpdateIndexDTO,
)
from src.modules.users.models import UserRole
from tests.helpers.functions import comparison_models
from tests.modules.reviews.fixtures.models_dto import (
    CreateReviewFixtureDTO,
    CreateReviewTranslationFixtureDTO,
)
from tests.modules.users.fixtures.models_dto import CreateUserFixtureDTO


class TestsForSuccess:

    @pytest.mark.asyncio
    async def test_create_review_public(
        self,
        client_for_tests,
        session_db,
    ):
        """Публичное создание отзыва любым пользователем без авторизации."""
        create_data = ReviewCreate(
            author_name="Alice Wonder",
            rating=5,
            locale=Language.ENG,
            text="Amazing high quality ropes!",
        )

        response = await client_for_tests.post(
            "/reviews",
            json=create_data.model_dump(mode="json"),
        )
        assert response.status_code == 201

        resp_dto = ReviewResponseDTO.model_validate(response.json())
        assert resp_dto.author_name == "Alice Wonder"
        assert resp_dto.rating == 5
        assert resp_dto.status == ReviewsStatus.NEW
        assert resp_dto.is_published is False
        assert len(resp_dto.translations) == 1
        assert resp_dto.translations[0].locale == Language.ENG
        assert resp_dto.translations[0].text == "Amazing high quality ropes!"

        # Проверка сохранения в БД
        res = await session_db.execute(
            select(Review)
            .where(Review.id == resp_dto.id)
            .options(selectinload(Review.translations))
        )
        review_in_db = res.scalar_one_or_none()
        assert review_in_db is not None
        assert review_in_db.author_name == "Alice Wonder"
        assert review_in_db.status == ReviewsStatus.NEW
        assert review_in_db.is_published is False
        assert len(review_in_db.translations) == 1

    @pytest.mark.asyncio
    async def test_get_reviews_guest_only_confirmed_and_published(
        self,
        client_for_tests,
        create_review_fixture,
    ):
        """
        Гость (без токена) видит ТОЛЬКО отзывы со статусом confirmed и is_published=True.
        """
        # 1. Confirmed + Published (должен быть виден)
        rev_valid = await create_review_fixture(
            CreateReviewFixtureDTO(
                author_name="Confirmed User",
                status=ReviewsStatus.CONFIRMED,
                is_published=True,
            )
        )
        # 2. New + Published (не должен быть виден гостю)
        await create_review_fixture(
            CreateReviewFixtureDTO(
                author_name="New User",
                status=ReviewsStatus.NEW,
                is_published=True,
            )
        )
        # 3. Confirmed + Unpublished (не должен быть виден гостю)
        await create_review_fixture(
            CreateReviewFixtureDTO(
                author_name="Unpublished User",
                status=ReviewsStatus.CONFIRMED,
                is_published=False,
            )
        )
        # 4. Rejected + Published (не должен быть виден гостю)
        await create_review_fixture(
            CreateReviewFixtureDTO(
                author_name="Rejected User",
                status=ReviewsStatus.REJECTED,
                is_published=True,
            )
        )

        response = await client_for_tests.get("/reviews")
        assert response.status_code == 200

        data = ReviewListResponseDTO.model_validate(response.json())
        assert data.total == 1
        assert len(data.items) == 1
        assert data.items[0].id == rev_valid.id
        assert data.items[0].author_name == "Confirmed User"

    @pytest.mark.asyncio
    async def test_get_reviews_admin_can_filter_any_status(
        self,
        client_for_tests,
        create_user_fixture,
        create_review_fixture,
    ):
        """Администратор может видеть отзывы в любых статусах и фильтровать по ним."""
        _, admin_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        headers = {"Authorization": f"Bearer {admin_token}"}

        rev_new = await create_review_fixture(
            CreateReviewFixtureDTO(
                author_name="New Rev",
                status=ReviewsStatus.NEW,
                is_published=False,
            )
        )
        rev_conf = await create_review_fixture(
            CreateReviewFixtureDTO(
                author_name="Conf Rev",
                status=ReviewsStatus.CONFIRMED,
                is_published=True,
            )
        )
        rev_rej = await create_review_fixture(
            CreateReviewFixtureDTO(
                author_name="Rej Rev",
                status=ReviewsStatus.REJECTED,
                is_published=False,
            )
        )

        # Админ без фильтра видит все 3
        resp_all = await client_for_tests.get("/reviews", headers=headers)
        assert resp_all.status_code == 200
        data_all = ReviewListResponseDTO.model_validate(resp_all.json())
        assert data_all.total == 3

        # Админ фильтрует status=new
        resp_new = await client_for_tests.get("/reviews?status=new", headers=headers)
        assert resp_new.status_code == 200
        data_new = ReviewListResponseDTO.model_validate(resp_new.json())
        assert data_new.total == 1
        assert data_new.items[0].id == rev_new.id

        # Админ фильтрует status=rejected
        resp_rej = await client_for_tests.get("/reviews?status=rejected", headers=headers)
        assert resp_rej.status_code == 200
        data_rej = ReviewListResponseDTO.model_validate(resp_rej.json())
        assert data_rej.total == 1
        assert data_rej.items[0].id == rev_rej.id

        # Админ фильтрует status=confirmed
        resp_conf = await client_for_tests.get("/reviews?status=confirmed", headers=headers)
        assert resp_conf.status_code == 200
        data_conf = ReviewListResponseDTO.model_validate(resp_conf.json())
        assert data_conf.total == 1
        assert data_conf.items[0].id == rev_conf.id

    @pytest.mark.asyncio
    async def test_get_reviews_filter_rating_and_search(
        self,
        client_for_tests,
        create_review_fixture,
    ):
        """Фильтрация по рейтингу и текстовый поиск."""
        rev_1 = await create_review_fixture(
            CreateReviewFixtureDTO(
                author_name="Gregory House",
                rating=5,
                status=ReviewsStatus.CONFIRMED,
                is_published=True,
                text="The best medical climbing ropes!",
            )
        )
        rev_2 = await create_review_fixture(
            CreateReviewFixtureDTO(
                author_name="James Wilson",
                rating=3,
                status=ReviewsStatus.CONFIRMED,
                is_published=True,
                text="Average quality yacht line.",
            )
        )

        # Фильтр по рейтингу
        resp_rating = await client_for_tests.get("/reviews?rating=5")
        assert resp_rating.status_code == 200
        data_rating = ReviewListResponseDTO.model_validate(resp_rating.json())
        assert data_rating.total == 1
        assert data_rating.items[0].id == rev_1.id

        # Поиск по имени автора
        resp_search_author = await client_for_tests.get("/reviews?search=Gregory")
        assert resp_search_author.status_code == 200
        data_search_author = ReviewListResponseDTO.model_validate(resp_search_author.json())
        assert data_search_author.total == 1
        assert data_search_author.items[0].id == rev_1.id

        # Поиск по тексту отзыва
        resp_search_text = await client_for_tests.get("/reviews?search=yacht")
        assert resp_search_text.status_code == 200
        data_search_text = ReviewListResponseDTO.model_validate(resp_search_text.json())
        assert data_search_text.total == 1
        assert data_search_text.items[0].id == rev_2.id

    @pytest.mark.asyncio
    async def test_get_reviews_pagination(
        self,
        client_for_tests,
        create_review_fixture,
    ):
        """Пагинация списка отзывов (skip & limit)."""
        for i in range(5):
            await create_review_fixture(
                CreateReviewFixtureDTO(
                    author_name=f"User {i}",
                    index=i,
                    status=ReviewsStatus.CONFIRMED,
                    is_published=True,
                )
            )

        resp = await client_for_tests.get("/reviews?skip=2&limit=2")
        assert resp.status_code == 200
        data = ReviewListResponseDTO.model_validate(resp.json())
        assert data.total == 5
        assert len(data.items) == 2
        assert data.skip == 2
        assert data.limit == 2

    @pytest.mark.asyncio
    async def test_get_review_by_id_guest_confirmed(
        self,
        client_for_tests,
        create_review_fixture,
    ):
        """Гость может получить подтвержденный и опубликованный отзыв по ID."""
        rev = await create_review_fixture(
            CreateReviewFixtureDTO(
                author_name="Public Tester",
                status=ReviewsStatus.CONFIRMED,
                is_published=True,
            )
        )

        resp = await client_for_tests.get(f"/reviews/{rev.id}")
        assert resp.status_code == 200
        data = ReviewResponseDTO.model_validate(resp.json())
        assert data.id == rev.id
        assert data.author_name == "Public Tester"

    @pytest.mark.asyncio
    async def test_get_review_by_id_admin_any_status(
        self,
        client_for_tests,
        create_user_fixture,
        create_review_fixture,
    ):
        """Администратор может получить по ID отзыв со статусом new или rejected."""
        _, admin_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        rev = await create_review_fixture(
            CreateReviewFixtureDTO(
                status=ReviewsStatus.NEW,
                is_published=False,
            )
        )

        resp = await client_for_tests.get(
            f"/reviews/{rev.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        data = ReviewResponseDTO.model_validate(resp.json())
        assert data.id == rev.id
        assert data.status == ReviewsStatus.NEW

    @pytest.mark.asyncio
    async def test_update_review_admin(
        self,
        client_for_tests,
        create_user_fixture,
        create_review_fixture,
        session_db,
    ):
        """Администратор обновляет поля отзыва."""
        _, admin_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        rev = await create_review_fixture(
            CreateReviewFixtureDTO(
                author_name="Old Author",
                rating=3,
                is_published=False,
            )
        )

        update_data = ReviewUpdate(
            author_name="Renamed Author",
            rating=5,
            is_published=True,
        )

        resp = await client_for_tests.patch(
            f"/reviews/{rev.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json=update_data.model_dump(exclude_unset=True, mode="json"),
        )
        assert resp.status_code == 200
        data = ReviewResponseDTO.model_validate(resp.json())
        assert data.author_name == "Renamed Author"
        assert data.rating == 5
        assert data.is_published is True

    @pytest.mark.asyncio
    async def test_update_review_status_admin(
        self,
        client_for_tests,
        create_user_fixture,
        create_review_fixture,
    ):
        """Администратор меняет статус модерации отзыва и публикацию."""
        _, admin_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        rev = await create_review_fixture(
            CreateReviewFixtureDTO(
                status=ReviewsStatus.NEW,
                is_published=False,
            )
        )

        status_update = ReviewStatusUpdate(
            status=ReviewsStatus.CONFIRMED,
            is_published=True,
        )

        resp = await client_for_tests.patch(
            f"/reviews/{rev.id}/status",
            headers={"Authorization": f"Bearer {admin_token}"},
            json=status_update.model_dump(exclude_unset=True, mode="json"),
        )
        assert resp.status_code == 200
        data = ReviewResponseDTO.model_validate(resp.json())
        assert data.status == ReviewsStatus.CONFIRMED
        assert data.is_published is True

    @pytest.mark.asyncio
    async def test_reorder_review_admin(
        self,
        client_for_tests,
        create_user_fixture,
        create_review_fixture,
    ):
        """Администратор меняет порядковый номер отзыва со сдвигом соседей."""
        _, admin_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        rev_0 = await create_review_fixture(CreateReviewFixtureDTO(index=0))
        rev_1 = await create_review_fixture(CreateReviewFixtureDTO(index=1))

        resp = await client_for_tests.patch(
            f"/reviews/{rev_0.id}/index",
            headers={"Authorization": f"Bearer {admin_token}"},
            json=ReviewUpdateIndexDTO(new_index=1).model_dump(mode="json"),
        )
        assert resp.status_code == 200
        data = ReviewResponseDTO.model_validate(resp.json())
        assert data.index == 1

    @pytest.mark.asyncio
    async def test_delete_review_admin(
        self,
        client_for_tests,
        create_user_fixture,
        create_review_fixture,
    ):
        """Администратор удаляет отзыв со всеми переводами."""
        _, admin_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        rev = await create_review_fixture()

        resp_del = await client_for_tests.delete(
            f"/reviews/{rev.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp_del.status_code == 204

        # Проверяем 404
        resp_get = await client_for_tests.get(
            f"/reviews/{rev.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp_get.status_code == 404

    @pytest.mark.asyncio
    async def test_add_translation_admin(
        self,
        client_for_tests,
        create_user_fixture,
        create_review_fixture,
        session_db,
    ):
        """Администратор добавляет перевод отзыва на новый язык."""
        _, admin_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        rev = await create_review_fixture(CreateReviewFixtureDTO(locale=Language.ENG))

        trans_data = ReviewTranslationCreate(
            locale=Language.GER,
            text="Ausgezeichnete Seile für den Segelsport!",
        )

        resp = await client_for_tests.post(
            f"/reviews/{rev.id}/translations",
            headers={"Authorization": f"Bearer {admin_token}"},
            json=trans_data.model_dump(mode="json"),
        )
        assert resp.status_code == 201

        resp_dto = ReviewTranslationResponseDTO.model_validate(resp.json())
        assert resp_dto.locale == Language.GER
        assert resp_dto.text == trans_data.text
        assert resp_dto.review_id == rev.id

    @pytest.mark.asyncio
    async def test_update_translation_admin(
        self,
        client_for_tests,
        create_user_fixture,
        create_review_fixture,
    ):
        """Администратор обновляет текст существующего перевода отзыва."""
        _, admin_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        rev = await create_review_fixture()
        trans_id = rev.translations[0].id

        update_dto = ReviewTranslationUpdate(text="Corrected review translation text")

        resp = await client_for_tests.patch(
            f"/reviews/{rev.id}/translations/{trans_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json=update_dto.model_dump(mode="json"),
        )
        assert resp.status_code == 200
        resp_dto = ReviewTranslationResponseDTO.model_validate(resp.json())
        assert resp_dto.id == trans_id
        assert resp_dto.text == "Corrected review translation text"

    @pytest.mark.asyncio
    async def test_delete_translation_admin(
        self,
        client_for_tests,
        create_user_fixture,
        create_review_fixture,
        create_review_translation_fixture,
    ):
        """Администратор удаляет перевод отзыва, если он не последний."""
        _, admin_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        rev = await create_review_fixture(CreateReviewFixtureDTO(locale=Language.ENG))
        # Добавляем 2-й перевод
        trans_2 = await create_review_translation_fixture(
            CreateReviewTranslationFixtureDTO(
                review_id=rev.id,
                locale=Language.GER,
                text="German translation",
            )
        )

        # Удаляем второй перевод
        resp_del = await client_for_tests.delete(
            f"/reviews/{rev.id}/translations/{trans_2.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp_del.status_code == 204

        # Проверяем, что в отзыве остался 1 перевод
        resp_rev = await client_for_tests.get(
            f"/reviews/{rev.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp_rev.status_code == 200
        rev_data = ReviewResponseDTO.model_validate(resp_rev.json())
        assert len(rev_data.translations) == 1
        assert rev_data.translations[0].locale == Language.ENG

    @pytest.mark.asyncio
    async def test_get_reviews_localized_fallback(
        self,
        client_for_tests,
        create_review_fixture,
        create_review_translation_fixture,
    ):
        """Проверка возврата локализованного текста с fallback."""
        rev = await create_review_fixture(
            CreateReviewFixtureDTO(
                locale=Language.ENG,
                text="English text",
                status=ReviewsStatus.CONFIRMED,
                is_published=True,
            )
        )
        await create_review_translation_fixture(
            CreateReviewTranslationFixtureDTO(
                review_id=rev.id,
                locale=Language.GER,
                text="Deutscher Text",
            )
        )

        # Запрос с locale=ger
        resp_ger = await client_for_tests.get("/reviews?locale=ger")
        assert resp_ger.status_code == 200
        data_ger = ReviewListResponseDTO.model_validate(resp_ger.json())
        assert data_ger.items[0].text == "Deutscher Text"
        assert data_ger.items[0].locale == Language.GER

        # Запрос с отсутствующей русской локалью -> fallback на eng
        resp_ru = await client_for_tests.get("/reviews?locale=ru")
        assert resp_ru.status_code == 200
        data_ru = ReviewListResponseDTO.model_validate(resp_ru.json())
        assert data_ru.items[0].text == "English text"


class TestsForFailed:

    @pytest.mark.asyncio
    async def test_get_review_by_id_guest_new_returns_404(
        self,
        client_for_tests,
        create_review_fixture,
    ):
        """Гость получает 404 при попытке открыть новый или неопубликованный отзыв."""
        rev = await create_review_fixture(
            CreateReviewFixtureDTO(
                status=ReviewsStatus.NEW,
                is_published=False,
            )
        )

        resp = await client_for_tests.get(f"/reviews/{rev.id}")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_last_translation_returns_400(
        self,
        client_for_tests,
        create_user_fixture,
        create_review_fixture,
    ):
        """Попытка удаления единственного перевода отзыва возвращает 400 Bad Request."""
        _, admin_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        rev = await create_review_fixture()
        only_trans_id = rev.translations[0].id

        resp = await client_for_tests.delete(
            f"/reviews/{rev.id}/translations/{only_trans_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 400
        assert "remaining translation" in resp.json()["detail"]

    @pytest.mark.asyncio
    async def test_add_duplicate_translation_returns_409(
        self,
        client_for_tests,
        create_user_fixture,
        create_review_fixture,
    ):
        """Попытка добавить перевод для уже существующего языка возвращает 409 Conflict."""
        _, admin_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        rev = await create_review_fixture(CreateReviewFixtureDTO(locale=Language.ENG))

        resp = await client_for_tests.post(
            f"/reviews/{rev.id}/translations",
            headers={"Authorization": f"Bearer {admin_token}"},
            json=ReviewTranslationCreate(
                locale=Language.ENG,
                text="Duplicate english text",
            ).model_dump(mode="json"),
        )
        assert resp.status_code == 409

    @pytest.mark.asyncio
    async def test_create_review_rating_invalid(
        self,
        client_for_tests,
    ):
        """Валидация рейтинга (rating должен быть от 1 до 5 включительно)."""
        # Рейтинг > 5
        resp_too_high = await client_for_tests.post(
            "/reviews",
            json={
                "author_name": "Test",
                "rating": 6,
                "locale": "en",
                "text": "Rope",
            },
        )
        assert resp_too_high.status_code == 422

        # Рейтинг < 1
        resp_too_low = await client_for_tests.post(
            "/reviews",
            json={
                "author_name": "Test",
                "rating": 0,
                "locale": "en",
                "text": "Rope",
            },
        )
        assert resp_too_low.status_code == 422

    @pytest.mark.asyncio
    async def test_admin_endpoints_unauthorized_returns_401(
        self,
        client_for_tests,
        create_review_fixture,
    ):
        """Запросы к защищенным эндпоинтам без токена возвращают 401."""
        rev = await create_review_fixture()

        # PATCH /reviews/{id}
        resp_patch = await client_for_tests.patch(
            f"/reviews/{rev.id}",
            json={"author_name": "Hacker"},
        )
        assert resp_patch.status_code == 401

        # DELETE /reviews/{id}
        resp_delete = await client_for_tests.delete(f"/reviews/{rev.id}")
        assert resp_delete.status_code == 401

        # POST /reviews/{id}/translations
        resp_trans = await client_for_tests.post(
            f"/reviews/{rev.id}/translations",
            json={"locale": "de", "text": "Hacked"},
        )
        assert resp_trans.status_code == 401

    @pytest.mark.asyncio
    async def test_admin_endpoints_regular_user_returns_403(
        self,
        client_for_tests,
        create_user_fixture,
        create_review_fixture,
    ):
        """Обычный пользователь с ролью USER получает 403 Forbidden."""
        _, user_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.USER)
        )
        headers = {"Authorization": f"Bearer {user_token}"}
        rev = await create_review_fixture()

        resp_patch = await client_for_tests.patch(
            f"/reviews/{rev.id}",
            headers=headers,
            json={"author_name": "User Attempt"},
        )
        assert resp_patch.status_code == 403

        resp_del = await client_for_tests.delete(
            f"/reviews/{rev.id}",
            headers=headers,
        )
        assert resp_del.status_code == 403

    @pytest.mark.asyncio
    async def test_get_nonexistent_review_returns_404(
        self,
        client_for_tests,
        create_user_fixture,
    ):
        """Запрос несуществующего отзыва возвращает 404."""
        _, admin_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        resp = await client_for_tests.get(
            "/reviews/99999",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_update_nonexistent_review_returns_404(
        self,
        client_for_tests,
        create_user_fixture,
    ):
        """Обновление несуществующего отзыва возвращает 404."""
        _, admin_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        resp = await client_for_tests.patch(
            "/reviews/99999",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"author_name": "No Name"},
        )
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_nonexistent_review_returns_404(
        self,
        client_for_tests,
        create_user_fixture,
    ):
        """Удаление несуществующего отзыва возвращает 404."""
        _, admin_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        resp = await client_for_tests.delete(
            "/reviews/99999",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_update_nonexistent_translation_returns_404(
        self,
        client_for_tests,
        create_user_fixture,
        create_review_fixture,
    ):
        """Обновление несуществующего перевода отзыва возвращает 404."""
        _, admin_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        rev = await create_review_fixture()

        resp = await client_for_tests.patch(
            f"/reviews/{rev.id}/translations/99999",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"text": "Nonexistent"},
        )
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_nonexistent_translation_returns_404(
        self,
        client_for_tests,
        create_user_fixture,
        create_review_fixture,
    ):
        """Удаление несуществующего перевода отзыва возвращает 404."""
        _, admin_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        rev = await create_review_fixture()

        resp = await client_for_tests.delete(
            f"/reviews/{rev.id}/translations/99999",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 404

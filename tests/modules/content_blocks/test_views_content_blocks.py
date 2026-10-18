import pytest
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.modules.base.database_model import Language
from src.modules.content_blocks.models import ContentBlock, ContentBlockTranslation
from src.modules.content_blocks.models_dto import (
    ContentBlockResponseDTO,
    ContentBlockTranslationUpsertDTO,
    ContentBlockUpdateDTO,
)
from src.modules.users.models import UserRole
from tests.modules.content_blocks.fixtures.models_dto import (
    CreateContentBlockFixtureDTO,
    CreateContentBlockTranslationFixtureDTO,
)
from tests.modules.users.fixtures.models_dto import CreateUserFixtureDTO


class TestsForSuccess:

    @pytest.mark.asyncio
    async def test_get_blocks_by_page_code_path_public(
        self,
        client_for_tests,
        create_content_block_fixture,
    ):
        """Получение списка блоков контента по page_code в пути (публичный доступ)."""
        block_1 = await create_content_block_fixture(
            CreateContentBlockFixtureDTO(
                page_code="home",
                block_code="home_hero",
                is_active=True,
                title="Hero Title",
                content="Hero Content",
            )
        )
        block_2 = await create_content_block_fixture(
            CreateContentBlockFixtureDTO(
                page_code="home",
                block_code="home_features",
                is_active=True,
                title="Features Title",
                content="Features Content",
            )
        )
        # Блок для другой страницы
        await create_content_block_fixture(
            CreateContentBlockFixtureDTO(
                page_code="about",
                block_code="about_story",
                is_active=True,
            )
        )

        response = await client_for_tests.get("/content_blocks/page/home")
        assert response.status_code == 200

        data = [
            ContentBlockResponseDTO.model_validate(item)
            for item in response.json()
        ]
        assert len(data) == 2
        block_codes = [b.block_code for b in data]
        assert "home_hero" in block_codes
        assert "home_features" in block_codes

        # Проверяем, что переводы всегда подгружены
        for b in data:
            assert len(b.translations) > 0
            assert b.translations[0].locale is not None

    @pytest.mark.asyncio
    async def test_get_blocks_by_page_code_query_public(
        self,
        client_for_tests,
        create_content_block_fixture,
    ):
        """Получение списка блоков контента через query-параметр ?page_code=..."""
        block = await create_content_block_fixture(
            CreateContentBlockFixtureDTO(
                page_code="catalog_page",
                block_code="catalog_banner",
                is_active=True,
            )
        )

        response = await client_for_tests.get(
            "/content_blocks", params={"page_code": "catalog_page"}
        )
        assert response.status_code == 200

        data = [
            ContentBlockResponseDTO.model_validate(item)
            for item in response.json()
        ]
        assert len(data) == 1
        assert data[0].block_code == "catalog_banner"
        assert len(data[0].translations) > 0

    @pytest.mark.asyncio
    async def test_get_blocks_by_page_filter_is_active(
        self,
        client_for_tests,
        create_user_fixture,
        create_content_block_fixture,
    ):
        """
        Публичный пользователь видит только активные блоки.
        Администратор может просматривать все блоки или фильтровать по is_active.
        """
        active_block = await create_content_block_fixture(
            CreateContentBlockFixtureDTO(
                page_code="contact",
                block_code="contact_info",
                is_active=True,
            )
        )
        inactive_block = await create_content_block_fixture(
            CreateContentBlockFixtureDTO(
                page_code="contact",
                block_code="contact_promo",
                is_active=False,
            )
        )

        # Публичный запрос: только активные
        resp_pub = await client_for_tests.get("/content_blocks/page/contact")
        assert resp_pub.status_code == 200
        pub_data = [
            ContentBlockResponseDTO.model_validate(item)
            for item in resp_pub.json()
        ]
        assert len(pub_data) == 1
        assert pub_data[0].block_code == "contact_info"

        # Админский запрос без фильтра: видит оба
        _, admin_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        headers = {"Authorization": f"Bearer {admin_token}"}
        resp_admin = await client_for_tests.get(
            "/content_blocks/page/contact", headers=headers
        )
        assert resp_admin.status_code == 200
        admin_data = [
            ContentBlockResponseDTO.model_validate(item)
            for item in resp_admin.json()
        ]
        assert len(admin_data) == 2

        # Админский запрос с фильтром is_active=false
        resp_inactive = await client_for_tests.get(
            "/content_blocks/page/contact",
            headers=headers,
            params={"is_active": "false"},
        )
        assert resp_inactive.status_code == 200
        inactive_data = [
            ContentBlockResponseDTO.model_validate(item)
            for item in resp_inactive.json()
        ]
        assert len(inactive_data) == 1
        assert inactive_data[0].block_code == "contact_promo"

    @pytest.mark.asyncio
    async def test_get_block_by_code_public(
        self,
        client_for_tests,
        create_content_block_fixture,
    ):
        """Получение одного экземпляра блока по block_code (публичный доступ)."""
        block = await create_content_block_fixture(
            CreateContentBlockFixtureDTO(
                block_code="unique_cta",
                is_active=True,
                title="Call to Action",
                content="Subscribe now",
            )
        )

        response = await client_for_tests.get(f"/content_blocks/{block.block_code}")
        assert response.status_code == 200

        data = ContentBlockResponseDTO.model_validate(response.json())
        assert data.id == block.id
        assert data.block_code == "unique_cta"
        assert len(data.translations) > 0

    @pytest.mark.asyncio
    async def test_get_block_with_locale_and_fallback(
        self,
        client_for_tests,
        create_content_block_fixture,
        create_content_block_translation_fixture,
    ):
        """Проверка локализации и fallback при получении блока контента."""
        block = await create_content_block_fixture(
            CreateContentBlockFixtureDTO(
                block_code="locale_block",
                locale=Language.ENG,
                title="English Title",
                content="English Content",
                is_active=True,
            )
        )
        await create_content_block_translation_fixture(
            CreateContentBlockTranslationFixtureDTO(
                content_block_id=block.id,
                locale=Language.GER,
                title="Deutscher Titel",
                content="Deutscher Inhalt",
            )
        )

        # Запрос с locale=ger -> немецкий перевод
        resp_ger = await client_for_tests.get(
            f"/content_blocks/{block.block_code}", params={"locale": "ger"}
        )
        assert resp_ger.status_code == 200
        data_ger = ContentBlockResponseDTO.model_validate(resp_ger.json())
        assert data_ger.title == "Deutscher Titel"
        assert data_ger.content == "Deutscher Inhalt"
        assert data_ger.locale == Language.GER
        assert len(data_ger.translations) == 2

        # Запрос с отсутствующей русской локалью -> fallback на eng
        resp_ru = await client_for_tests.get(
            f"/content_blocks/{block.block_code}", params={"locale": "rus"}
        )
        assert resp_ru.status_code == 200
        data_ru = ContentBlockResponseDTO.model_validate(resp_ru.json())
        assert data_ru.title == "English Title"
        assert data_ru.content == "English Content"

    @pytest.mark.asyncio
    async def test_update_block_by_code_admin(
        self,
        client_for_tests,
        create_user_fixture,
        create_content_block_fixture,
        session_db,
    ):
        """
        Изменение блока по block_code администратором.
        В рамках одной транзакции обновляются атрибуты блока и пачка переводов по всем языкам.
        """
        _, admin_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        headers = {"Authorization": f"Bearer {admin_token}"}

        block = await create_content_block_fixture(
            CreateContentBlockFixtureDTO(
                block_code="footer_block",
                locale=Language.ENG,
                title="Old English Title",
                content="Old Content",
                is_active=True,
            )
        )

        update_dto = ContentBlockUpdateDTO(
            is_active=False,
            translations=[
                ContentBlockTranslationUpsertDTO(
                    locale=Language.ENG,
                    title="Updated EN Title",
                    content="Updated EN Content",
                ),
                ContentBlockTranslationUpsertDTO(
                    locale=Language.RUS,
                    title="Заголовок на русском",
                    content="Контент на русском",
                ),
                ContentBlockTranslationUpsertDTO(
                    locale=Language.GER,
                    title="Deutscher Titel",
                    content="Deutscher Inhalt",
                ),
            ],
        )

        response = await client_for_tests.patch(
            f"/content_blocks/{block.block_code}",
            headers=headers,
            json=update_dto.model_dump(mode="json"),
        )
        assert response.status_code == 200

        resp_dto = ContentBlockResponseDTO.model_validate(response.json())
        assert resp_dto.block_code == "footer_block"
        assert resp_dto.is_active is False
        assert len(resp_dto.translations) == 3

        # Проверка в БД
        res = await session_db.execute(
            select(ContentBlock)
            .where(ContentBlock.id == block.id)
            .options(selectinload(ContentBlock.translations))
        )
        db_block = res.scalar_one()
        assert db_block.is_active is False
        assert len(db_block.translations) == 3
        locales = [t.locale for t in db_block.translations]
        assert Language.ENG in locales
        assert Language.RUS in locales
        assert Language.GER in locales

    @pytest.mark.asyncio
    async def test_update_block_create_if_not_exists_upsert(
        self,
        client_for_tests,
        create_user_fixture,
        session_db,
    ):
        """
        Если блок с block_code еще не существует, но передан page_code,
        он создается с переводами (upsert для админки).
        """
        _, admin_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        headers = {"Authorization": f"Bearer {admin_token}"}

        create_dto = ContentBlockUpdateDTO(
            page_code="new_page",
            is_active=True,
            translations=[
                ContentBlockTranslationUpsertDTO(
                    locale=Language.ENG,
                    title="Created via Upsert",
                    content="Brand new content",
                ),
                ContentBlockTranslationUpsertDTO(
                    locale=Language.RUS,
                    title="Создан через upsert",
                    content="Совершенно новый контент",
                ),
            ],
        )

        response = await client_for_tests.put(
            "/content_blocks/newly_created_block",
            headers=headers,
            json=create_dto.model_dump(mode="json"),
        )
        assert response.status_code == 200

        resp_dto = ContentBlockResponseDTO.model_validate(response.json())
        assert resp_dto.block_code == "newly_created_block"
        assert resp_dto.page_code == "new_page"
        assert resp_dto.is_active is True
        assert len(resp_dto.translations) == 2

        # Проверяем в БД
        res = await session_db.execute(
            select(ContentBlock)
            .where(ContentBlock.block_code == "newly_created_block")
            .options(selectinload(ContentBlock.translations))
        )
        db_block = res.scalar_one_or_none()
        assert db_block is not None
        assert db_block.page_code == "new_page"
        assert len(db_block.translations) == 2

    @pytest.mark.asyncio
    async def test_admin_can_view_inactive_block(
        self,
        client_for_tests,
        create_user_fixture,
        create_content_block_fixture,
    ):
        """Администратор может получить неактивный блок по block_code."""
        _, admin_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        headers = {"Authorization": f"Bearer {admin_token}"}

        block = await create_content_block_fixture(
            CreateContentBlockFixtureDTO(
                block_code="admin_draft",
                is_active=False,
            )
        )

        response = await client_for_tests.get(
            f"/content_blocks/{block.block_code}", headers=headers
        )
        assert response.status_code == 200
        data = ContentBlockResponseDTO.model_validate(response.json())
        assert data.block_code == "admin_draft"
        assert data.is_active is False


class TestsForFailed:

    @pytest.mark.asyncio
    async def test_get_nonexistent_block_by_code_returns_404(
        self,
        client_for_tests,
    ):
        """Запрос несуществующего block_code возвращает 404."""
        response = await client_for_tests.get("/content_blocks/nonexistent_code")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_public_user_cannot_view_inactive_block_returns_404(
        self,
        client_for_tests,
        create_content_block_fixture,
    ):
        """Обычный пользователь получает 404 при запросе неактивного блока."""
        block = await create_content_block_fixture(
            CreateContentBlockFixtureDTO(
                block_code="inactive_block",
                is_active=False,
            )
        )

        response = await client_for_tests.get(f"/content_blocks/{block.block_code}")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_block_unauthorized_returns_401(
        self,
        client_for_tests,
        create_content_block_fixture,
    ):
        """Попытка изменения блока без авторизации возвращает 401."""
        block = await create_content_block_fixture()

        response = await client_for_tests.patch(
            f"/content_blocks/{block.block_code}",
            json={"is_active": False},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_update_block_regular_user_returns_403(
        self,
        client_for_tests,
        create_user_fixture,
        create_content_block_fixture,
    ):
        """Попытка изменения блока пользователем с ролью USER возвращает 403."""
        _, user_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.USER)
        )
        headers = {"Authorization": f"Bearer {user_token}"}
        block = await create_content_block_fixture()

        response = await client_for_tests.patch(
            f"/content_blocks/{block.block_code}",
            headers=headers,
            json={"is_active": False},
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_update_nonexistent_block_without_page_code_returns_404(
        self,
        client_for_tests,
        create_user_fixture,
    ):
        """
        Попытка обновления несуществующего блока без указания page_code
        возвращает 404.
        """
        _, admin_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        headers = {"Authorization": f"Bearer {admin_token}"}

        response = await client_for_tests.patch(
            "/content_blocks/unknown_block",
            headers=headers,
            json={"is_active": False},
        )
        assert response.status_code == 404

import pytest
from sqlalchemy import select

from src.modules.base.database_model import Language
from src.modules.users.models import UserRole
from tests.modules.users.fixtures.models_dto import CreateUserFixtureDTO
from tests.modules.configurator_extra.fixtures.models_dto import (
    CreateConfiguratorExtraFixtureDTO,
    CreateConfiguratorExtraTranslationFixtureDTO,
)
from src.modules.configurator_extra.models import (
    ConfiguratorExtra,
    ConfiguratorExtraTranslation,
    BillingType,
)
from src.modules.configurator_extra.models_dto import (
    ConfiguratorExtraCreate,
    ConfiguratorExtraUpdate,
    ConfiguratorExtraUpdateIndexDTO,
    ConfiguratorExtraResponseDTO,
    ConfiguratorExtraLocalizedResponseDTO,
    ConfiguratorExtraTranslationCreate,
    ConfiguratorExtraTranslationUpdate,
    ConfiguratorExtraTranslationResponseDTO,
)


class TestsForSuccess:

    @pytest.mark.asyncio
    async def test_get_all_configurator_extras_public(
        self,
        client_for_tests,
        create_configurator_extra_fixture,
    ):
        """Любой пользователь может получить список опций без авторизации (public)."""
        e1 = await create_configurator_extra_fixture(
            CreateConfiguratorExtraFixtureDTO(
                code="whipping",
                price=5.00,
                billing_type=BillingType.PER_ITEM,
                name="Tackling / Whipping",
                description="Whipped ends",
            )
        )
        e2 = await create_configurator_extra_fixture(
            CreateConfiguratorExtraFixtureDTO(
                code="certificate",
                price=15.00,
                billing_type=BillingType.FIXED,
                name="Safety Certificate",
            )
        )

        response = await client_for_tests.get("/configurator_extras")
        assert response.status_code == 200

        items = [ConfiguratorExtraLocalizedResponseDTO.model_validate(i) for i in response.json()]
        ids = [i.id for i in items]
        assert e1.id in ids
        assert e2.id in ids

        item1 = next(i for i in items if i.id == e1.id)
        assert item1.code == "whipping"
        assert item1.price == 5.00
        assert item1.billing_type == BillingType.PER_ITEM
        assert item1.name == "Tackling / Whipping"
        assert item1.description == "Whipped ends"

    @pytest.mark.asyncio
    async def test_get_all_configurator_extras_filters(
        self,
        client_for_tests,
        create_configurator_extra_fixture,
        create_configurator_extra_translation_fixture,
    ):
        """Фильтрация по billing_type, is_active и локализации."""
        e1 = await create_configurator_extra_fixture(
            CreateConfiguratorExtraFixtureDTO(
                code="extra_active_fixed",
                billing_type=BillingType.FIXED,
                is_active=True,
                locale=Language.ENG,
                name="Fixed Extra EN",
            )
        )
        await create_configurator_extra_translation_fixture(
            CreateConfiguratorExtraTranslationFixtureDTO(
                extra_id=e1.id,
                locale=Language.GER,
                name="Fixed Extra DE",
            )
        )

        e2 = await create_configurator_extra_fixture(
            CreateConfiguratorExtraFixtureDTO(
                code="extra_inactive",
                billing_type=BillingType.FIXED,
                is_active=False,
            )
        )
        e3 = await create_configurator_extra_fixture(
            CreateConfiguratorExtraFixtureDTO(
                code="extra_per_meter",
                billing_type=BillingType.PER_METER,
                is_active=True,
            )
        )

        # 1. Filter by billing_type
        resp_billing = await client_for_tests.get(
            "/configurator_extras",
            params={"billing_type": "fixed", "is_active": "true"},
        )
        assert resp_billing.status_code == 200
        data_billing = [ConfiguratorExtraLocalizedResponseDTO.model_validate(i) for i in resp_billing.json()]
        billing_ids = [i.id for i in data_billing]
        assert e1.id in billing_ids
        assert e2.id not in billing_ids
        assert e3.id not in billing_ids

        # 2. Localized GER
        resp_ger = await client_for_tests.get(
            "/configurator_extras",
            params={"locale": "ger"},
        )
        assert resp_ger.status_code == 200
        data_ger = [ConfiguratorExtraLocalizedResponseDTO.model_validate(i) for i in resp_ger.json()]
        ger_item = next(i for i in data_ger if i.id == e1.id)
        assert ger_item.name == "Fixed Extra DE"

    @pytest.mark.asyncio
    async def test_get_configurator_extra_by_id_public(
        self,
        client_for_tests,
        create_configurator_extra_fixture,
    ):
        """Любой пользователь может получить отдельную опцию по ID со всеми переводами (public)."""
        extra = await create_configurator_extra_fixture(
            CreateConfiguratorExtraFixtureDTO(
                code="label_tag",
                price=3.50,
                billing_type=BillingType.PER_ITEM,
                name="Custom Tag",
                description="Engraved metal tag",
            )
        )

        response = await client_for_tests.get(f"/configurator_extras/{extra.id}")
        assert response.status_code == 200

        dto = ConfiguratorExtraResponseDTO.model_validate(response.json())
        assert dto.id == extra.id
        assert dto.code == "label_tag"
        assert dto.price == 3.50
        assert len(dto.translations) == 1
        assert dto.translations[0].name == "Custom Tag"
        assert dto.translations[0].description == "Engraved metal tag"

    @pytest.mark.asyncio
    async def test_create_configurator_extra_admin(
        self,
        client_for_tests,
        create_user_fixture,
    ):
        """Администратор успешно создает новую дополнительную опцию с переводами."""
        admin, token = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.ADMIN))

        payload = ConfiguratorExtraCreate(
            code="special_packaging",
            price=12.50,
            billing_type=BillingType.FIXED,
            is_active=True,
            translations=[
                ConfiguratorExtraTranslationCreate(
                    locale=Language.ENG,
                    name="Special Wooden Box Packaging",
                    description="Packed in safe wooden crate",
                ),
                ConfiguratorExtraTranslationCreate(
                    locale=Language.GER,
                    name="Holzkiste Verpackung",
                    description="Sicher in Holzkiste verpackt",
                ),
            ],
        )

        response = await client_for_tests.post(
            "/configurator_extras",
            headers={"Authorization": f"Bearer {token}"},
            json=payload.model_dump(),
        )
        assert response.status_code == 201

        dto = ConfiguratorExtraResponseDTO.model_validate(response.json())
        assert dto.code == "special_packaging"
        assert dto.price == 12.50
        assert dto.billing_type == BillingType.FIXED
        assert dto.index == 1
        assert len(dto.translations) == 2

    @pytest.mark.asyncio
    async def test_create_configurator_extra_with_explicit_index_admin(
        self,
        client_for_tests,
        create_user_fixture,
        create_configurator_extra_fixture,
    ):
        """Создание с явным index вызывает автоматический сдвиг индексов (shift_indexes_for_insert)."""
        admin, token = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.ADMIN))

        e1 = await create_configurator_extra_fixture(CreateConfiguratorExtraFixtureDTO(index=1))
        e2 = await create_configurator_extra_fixture(CreateConfiguratorExtraFixtureDTO(index=2))

        payload = ConfiguratorExtraCreate(
            code="inserted_at_index_1",
            price=20.00,
            billing_type=BillingType.FIXED,
            index=1,
            translations=[
                ConfiguratorExtraTranslationCreate(
                    locale=Language.ENG,
                    name="First In Order",
                )
            ],
        )

        response = await client_for_tests.post(
            "/configurator_extras",
            headers={"Authorization": f"Bearer {token}"},
            json=payload.model_dump(),
        )
        assert response.status_code == 201
        created_dto = ConfiguratorExtraResponseDTO.model_validate(response.json())
        assert created_dto.index == 1

        # Check e1 and e2 shifted
        r1 = await client_for_tests.get(f"/configurator_extras/{e1.id}")
        r2 = await client_for_tests.get(f"/configurator_extras/{e2.id}")
        assert ConfiguratorExtraResponseDTO.model_validate(r1.json()).index == 2
        assert ConfiguratorExtraResponseDTO.model_validate(r2.json()).index == 3

    @pytest.mark.asyncio
    async def test_update_configurator_extra_admin(
        self,
        client_for_tests,
        create_user_fixture,
        create_configurator_extra_fixture,
    ):
        """Администратор обновляет поля опции."""
        admin, token = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.ADMIN))
        extra = await create_configurator_extra_fixture(
            CreateConfiguratorExtraFixtureDTO(code="old_code", price=10.00, billing_type=BillingType.FIXED)
        )

        payload = ConfiguratorExtraUpdate(code="new_code", price=25.00, billing_type=BillingType.PER_ITEM)
        response = await client_for_tests.patch(
            f"/configurator_extras/{extra.id}",
            headers={"Authorization": f"Bearer {token}"},
            json=payload.model_dump(exclude_unset=True),
        )
        assert response.status_code == 200

        dto = ConfiguratorExtraResponseDTO.model_validate(response.json())
        assert dto.code == "new_code"
        assert dto.price == 25.00
        assert dto.billing_type == BillingType.PER_ITEM

    @pytest.mark.asyncio
    async def test_reorder_configurator_extra_admin(
        self,
        client_for_tests,
        create_user_fixture,
        create_configurator_extra_fixture,
    ):
        """Администратор изменяет индекс опции с автоматическим сдвигом соседних."""
        admin, token = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.ADMIN))
        e1 = await create_configurator_extra_fixture(CreateConfiguratorExtraFixtureDTO(index=1))
        e2 = await create_configurator_extra_fixture(CreateConfiguratorExtraFixtureDTO(index=2))
        e3 = await create_configurator_extra_fixture(CreateConfiguratorExtraFixtureDTO(index=3))

        # Move e3 to index 1
        response = await client_for_tests.patch(
            f"/configurator_extras/{e3.id}/index",
            headers={"Authorization": f"Bearer {token}"},
            json=ConfiguratorExtraUpdateIndexDTO(new_index=1).model_dump(),
        )
        assert response.status_code == 200
        assert ConfiguratorExtraResponseDTO.model_validate(response.json()).index == 1

        r1 = await client_for_tests.get(f"/configurator_extras/{e1.id}")
        r2 = await client_for_tests.get(f"/configurator_extras/{e2.id}")
        assert ConfiguratorExtraResponseDTO.model_validate(r1.json()).index == 2
        assert ConfiguratorExtraResponseDTO.model_validate(r2.json()).index == 3

    @pytest.mark.asyncio
    async def test_delete_configurator_extra_admin(
        self,
        session_db,
        client_for_tests,
        create_user_fixture,
        create_configurator_extra_fixture,
    ):
        """Администратор удаляет опцию и происходит сдвиг индексов оставшихся элементов."""
        admin, token = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.ADMIN))
        e1 = await create_configurator_extra_fixture(CreateConfiguratorExtraFixtureDTO(index=1))
        e2 = await create_configurator_extra_fixture(CreateConfiguratorExtraFixtureDTO(index=2))
        e3 = await create_configurator_extra_fixture(CreateConfiguratorExtraFixtureDTO(index=3))

        response = await client_for_tests.delete(
            f"/configurator_extras/{e2.id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 204

        # e2 deleted from DB
        res = await session_db.execute(select(ConfiguratorExtra).where(ConfiguratorExtra.id == e2.id))
        assert res.scalar_one_or_none() is None

        # Translations deleted cascade
        res_t = await session_db.execute(
            select(ConfiguratorExtraTranslation).where(ConfiguratorExtraTranslation.extra_id == e2.id)
        )
        assert res_t.scalars().all() == []

        # e3 shifted down to index 2
        r3 = await client_for_tests.get(f"/configurator_extras/{e3.id}")
        assert ConfiguratorExtraResponseDTO.model_validate(r3.json()).index == 2

    @pytest.mark.asyncio
    async def test_translations_crud_admin(
        self,
        client_for_tests,
        create_user_fixture,
        create_configurator_extra_fixture,
    ):
        """CRUD операции над переводами опции администратором."""
        admin, token = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.ADMIN))
        extra = await create_configurator_extra_fixture(
            CreateConfiguratorExtraFixtureDTO(locale=Language.ENG, name="Original Name")
        )

        # 1. Add GER translation
        add_resp = await client_for_tests.post(
            f"/configurator_extras/{extra.id}/translations",
            headers={"Authorization": f"Bearer {token}"},
            json=ConfiguratorExtraTranslationCreate(
                locale=Language.GER,
                name="Deutscher Name",
                description="Deutsche Beschreibung",
            ).model_dump(),
        )
        assert add_resp.status_code == 201
        trans_dto = ConfiguratorExtraTranslationResponseDTO.model_validate(add_resp.json())
        assert trans_dto.locale == Language.GER
        assert trans_dto.name == "Deutscher Name"

        # 2. Update GER translation
        patch_resp = await client_for_tests.patch(
            f"/configurator_extras/translations/{trans_dto.id}",
            headers={"Authorization": f"Bearer {token}"},
            json=ConfiguratorExtraTranslationUpdate(name="Aktualisierter Name").model_dump(exclude_unset=True),
        )
        assert patch_resp.status_code == 200
        updated_trans = ConfiguratorExtraTranslationResponseDTO.model_validate(patch_resp.json())
        assert updated_trans.name == "Aktualisierter Name"

        # 3. Delete GER translation (ENG still remains)
        del_resp = await client_for_tests.delete(
            f"/configurator_extras/translations/{trans_dto.id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert del_resp.status_code == 204


class TestsForFailures:

    @pytest.mark.asyncio
    async def test_create_configurator_extra_unauthorized(
        self,
        client_for_tests,
    ):
        """Попытка создания опции без авторизации -> 401."""
        response = await client_for_tests.post(
            "/configurator_extras",
            json={"code": "test", "price": 10.0, "billing_type": "fixed", "translations": []},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_create_configurator_extra_forbidden(
        self,
        client_for_tests,
        create_user_fixture,
    ):
        """Попытка создания опции обычным пользователем -> 403."""
        user, token = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.USER))
        response = await client_for_tests.post(
            "/configurator_extras",
            headers={"Authorization": f"Bearer {token}"},
            json={"code": "test", "price": 10.0, "billing_type": "fixed", "translations": []},
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_create_configurator_extra_empty_translations(
        self,
        client_for_tests,
        create_user_fixture,
    ):
        """Создание без переводов -> 400 Bad Request."""
        admin, token = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.ADMIN))
        response = await client_for_tests.post(
            "/configurator_extras",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "code": "test_empty_trans",
                "price": 10.0,
                "billing_type": "fixed",
                "translations": [],
            },
        )
        assert response.status_code == 422  # Pydantic min_length=1

    @pytest.mark.asyncio
    async def test_create_configurator_extra_duplicate_locales(
        self,
        client_for_tests,
        create_user_fixture,
    ):
        """Создание с дублирующимися локалями в переводах -> 400 Bad Request."""
        admin, token = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.ADMIN))
        response = await client_for_tests.post(
            "/configurator_extras",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "code": "dup_locale",
                "price": 10.0,
                "billing_type": "fixed",
                "translations": [
                    {"locale": "eng", "name": "Name 1"},
                    {"locale": "eng", "name": "Name 2"},
                ],
            },
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_create_configurator_extra_duplicate_code(
        self,
        client_for_tests,
        create_user_fixture,
        create_configurator_extra_fixture,
    ):
        """Создание с уже существующим code -> 409 Conflict."""
        admin, token = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.ADMIN))
        await create_configurator_extra_fixture(CreateConfiguratorExtraFixtureDTO(code="existing_code"))

        response = await client_for_tests.post(
            "/configurator_extras",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "code": "existing_code",
                "price": 10.0,
                "billing_type": "fixed",
                "translations": [{"locale": "eng", "name": "Name"}],
            },
        )
        assert response.status_code == 409

    @pytest.mark.asyncio
    async def test_get_configurator_extra_not_found(
        self,
        client_for_tests,
    ):
        """Запрос несуществующей опции -> 404."""
        response = await client_for_tests.get("/configurator_extras/999999")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_configurator_extra_duplicate_code(
        self,
        client_for_tests,
        create_user_fixture,
        create_configurator_extra_fixture,
    ):
        """Обновление code на уже занятый -> 409 Conflict."""
        admin, token = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.ADMIN))
        await create_configurator_extra_fixture(CreateConfiguratorExtraFixtureDTO(code="code_one"))
        extra_two = await create_configurator_extra_fixture(CreateConfiguratorExtraFixtureDTO(code="code_two"))

        response = await client_for_tests.patch(
            f"/configurator_extras/{extra_two.id}",
            headers={"Authorization": f"Bearer {token}"},
            json={"code": "code_one"},
        )
        assert response.status_code == 409

    @pytest.mark.asyncio
    async def test_update_configurator_extra_no_data(
        self,
        client_for_tests,
        create_user_fixture,
        create_configurator_extra_fixture,
    ):
        """Пустой запрос на обновление -> 400 Bad Request."""
        admin, token = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.ADMIN))
        extra = await create_configurator_extra_fixture()

        response = await client_for_tests.patch(
            f"/configurator_extras/{extra.id}",
            headers={"Authorization": f"Bearer {token}"},
            json={},
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_add_translation_already_exists(
        self,
        client_for_tests,
        create_user_fixture,
        create_configurator_extra_fixture,
    ):
        """Попытка добавления перевода с уже существующей локалью -> 409 Conflict."""
        admin, token = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.ADMIN))
        extra = await create_configurator_extra_fixture(CreateConfiguratorExtraFixtureDTO(locale=Language.ENG))

        response = await client_for_tests.post(
            f"/configurator_extras/{extra.id}/translations",
            headers={"Authorization": f"Bearer {token}"},
            json={"locale": "eng", "name": "Duplicate ENG"},
        )
        assert response.status_code == 409

    @pytest.mark.asyncio
    async def test_delete_last_translation_error(
        self,
        client_for_tests,
        create_user_fixture,
        create_configurator_extra_fixture,
    ):
        """Попытка удаления единственного оставшегося перевода -> 400 Bad Request (Правило 5.1)."""
        admin, token = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.ADMIN))
        extra = await create_configurator_extra_fixture()
        trans_id = extra.translations[0].id

        response = await client_for_tests.delete(
            f"/configurator_extras/translations/{trans_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 400

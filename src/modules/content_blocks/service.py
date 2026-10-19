from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.base.database_model import Language
from src.modules.content_blocks.exception import ContentBlockNotFound
from src.modules.content_blocks.models import ContentBlock, ContentBlockTranslation
from src.modules.content_blocks.models_dto import (
    ContentBlockResponseDTO,
    ContentBlockTranslationResponseDTO,
    ContentBlockUpdateDTO,
)
from src.modules.content_blocks.repository import (
    ContentBlockRepository,
    ContentBlockTranslationRepository,
)


class ContentBlockService:
    def __init__(
        self,
        block_repo: ContentBlockRepository,
        trans_repo: ContentBlockTranslationRepository,
        session: AsyncSession,
    ):
        self.block_repo = block_repo
        self.trans_repo = trans_repo
        self.session = session

    async def get_blocks_by_page(
        self,
        page_code: str,
        locale: Optional[Language] = None,
        is_active: Optional[bool] = None,
        is_admin: bool = False,
    ) -> List[ContentBlockResponseDTO]:
        """
        Получение списка всех блоков контента для указанного page_code.
        Для обычных пользователей возвращаются только активные блоки (is_active=True).
        Администратор может передавать фильтр is_active или получать все блоки.
        Все блоки возвращаются с подгруженными переводами.
        """
        effective_active = is_active if is_admin else True

        blocks = await self.block_repo.get_by_page_code(
            page_code=page_code,
            is_active=effective_active,
        )
        return [self._to_response_dto(b, locale=locale) for b in blocks]

    async def get_block_by_code(
        self,
        block_code: str,
        locale: Optional[Language] = None,
        is_admin: bool = False,
    ) -> ContentBlockResponseDTO:
        """
        Получение одного экземпляра блока контента по block_code.
        Обычные пользователи могут получить только активный блок (is_active=True).
        Данные всегда возвращаются с подгруженными переводами.
        """
        block = await self.block_repo.get_by_block_code(block_code)
        if not block:
            raise ContentBlockNotFound(
                f"ContentBlock with block_code '{block_code}' not found."
            )

        if not is_admin and not block.is_active:
            raise ContentBlockNotFound(
                f"ContentBlock with block_code '{block_code}' not found."
            )

        return self._to_response_dto(block, locale=locale)

    async def update_block_by_code(
        self,
        block_code: str,
        data: ContentBlockUpdateDTO,
    ) -> ContentBlockResponseDTO:
        """
        Изменение блока контента по block_code (только админ).
        Позволяет в рамках одной транзакции изменить атрибуты блока и сразу пачку
        переводов по каждому языку (upsert).
        Если блок с block_code еще не существует и передан page_code, он создается.
        """
        block = await self.block_repo.get_by_block_code(block_code)

        if not block:
            if not data.page_code:
                raise ContentBlockNotFound(
                    f"ContentBlock with block_code '{block_code}' not found."
                )

            # Создание нового блока (upsert по block_code)
            block = ContentBlock(
                page_code=data.page_code,
                block_code=block_code,
                is_active=data.is_active if data.is_active is not None else True,
            )
            self.block_repo.add_block(block)
            await self.session.flush()
        else:
            # Обновление существующего блока
            update_dict = {}
            if data.page_code is not None:
                update_dict["page_code"] = data.page_code
            if data.is_active is not None:
                update_dict["is_active"] = data.is_active

            if update_dict:
                await self.block_repo.update_block(block.id, update_dict)

        # Пакетное обновление / вставка переводов (по каждому языку)
        if data.translations is not None:
            for trans_dto in data.translations:
                existing_trans = await self.trans_repo.get_by_block_and_locale(
                    block_id=block.id,
                    locale=trans_dto.locale,
                )
                if existing_trans:
                    trans_update = {}
                    if trans_dto.title is not None:
                        trans_update["title"] = trans_dto.title
                    if trans_dto.content is not None:
                        trans_update["content"] = trans_dto.content
                    if trans_update:
                        await self.trans_repo.update_translation(
                            trans_id=existing_trans.id,
                            values=trans_update,
                        )
                else:
                    new_trans = ContentBlockTranslation(
                        content_block_id=block.id,
                        locale=trans_dto.locale,
                        title=trans_dto.title,
                        content=trans_dto.content,
                    )
                    self.trans_repo.add_translation(new_trans)

        await self.session.commit()
        self.session.expire_all()

        reloaded = await self.block_repo.get_by_block_code(block_code)
        if not reloaded:
            raise ContentBlockNotFound(
                f"ContentBlock with block_code '{block_code}' not found after update."
            )

        return self._to_response_dto(reloaded)

    def _to_response_dto(
        self,
        block: ContentBlock,
        locale: Optional[Language] = None,
    ) -> ContentBlockResponseDTO:
        """
        Преобразование ORM ContentBlock в DTO с подгруженными переводами
        и локализованными полями title/content (с fallback-логикой).
        """
        target_locale = locale or Language.ENG
        title = block._get_field_with_translation(
            lambda t: t.title,
            target_locale,
            fallback=Language.ENG,
        )
        content = block._get_field_with_translation(
            lambda t: t.content,
            target_locale,
            fallback=Language.ENG,
        )

        matched_locale: Optional[Language] = None
        if block.translations:
            target_norm = ContentBlock._normalize_locale(target_locale)
            for t in block.translations:
                if ContentBlock._normalize_locale(t.locale) == target_norm:
                    matched_locale = t.locale
                    break
            if not matched_locale:
                fallback_norm = ContentBlock._normalize_locale(Language.ENG)
                for t in block.translations:
                    if ContentBlock._normalize_locale(t.locale) == fallback_norm:
                        matched_locale = t.locale
                        break
            if not matched_locale and block.translations:
                matched_locale = block.translations[0].locale

        return ContentBlockResponseDTO(
            id=block.id,
            page_code=block.page_code,
            block_code=block.block_code,
            is_active=block.is_active,
            title=title,
            content=content,
            locale=matched_locale,
            translations=[
                ContentBlockTranslationResponseDTO.model_validate(t)
                for t in block.translations
            ],
            created_at=block.created_at,
            updated_at=block.updated_at,
        )

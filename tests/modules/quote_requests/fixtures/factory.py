from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from tests.helpers.functions import random_string
from tests.modules.quote_requests.fixtures.models_dto import (
    CreateQuoteRequestFixtureDTO,
    CreateQuoteRopeItemFixtureDTO,
    CreateQuoteServiceItemFixtureDTO,
)
from src.modules.configurator_setting.models import Currency
from src.modules.quote_requests.models import (
    QuoteRequest,
    QuoteRopeItem,
    QuoteServiceItem,
    ConfiguratorType,
    QuoteRequestStatus,
)
from src.modules.quote_requests.models_dto import QuoteRequestResponseDTO
from tests.modules.rope_products.fixtures.factory import create_rope_product_factory
from tests.modules.colors.fixtures.factory import create_color_factory
from tests.modules.splice_types.fixtures.factory import create_splice_type_factory
from tests.modules.splice_materials.fixtures.factory import create_splice_material_factory


async def create_quote_request_factory(
    session_db: AsyncSession,
    new_request: CreateQuoteRequestFixtureDTO = CreateQuoteRequestFixtureDTO(),
) -> QuoteRequestResponseDTO:
    request_number = (
        new_request.request_number
        if new_request.request_number is not None
        else f"RPL-TEST-{random_string(8)}"
    )

    configurator_type = (
        new_request.configurator_type
        if new_request.configurator_type is not None
        else ConfiguratorType.ROPE_WITH_SPLICE
    )

    # 1. Determine items lists based on configuration if none explicitly supplied
    if new_request.rope_items is None and new_request.service_items is None:
        if configurator_type == ConfiguratorType.ROPE_WITH_SPLICE:
            rope_items_dtos = [CreateQuoteRopeItemFixtureDTO()]
            service_items_dtos = []
        elif configurator_type in (ConfiguratorType.LOOP_ONLY, ConfiguratorType.SPLICE_ONLY):
            rope_items_dtos = []
            service_items_dtos = [CreateQuoteServiceItemFixtureDTO()]
        else:
            rope_items_dtos = [CreateQuoteRopeItemFixtureDTO()]
            service_items_dtos = []
    else:
        rope_items_dtos = new_request.rope_items if new_request.rope_items is not None else []
        service_items_dtos = new_request.service_items if new_request.service_items is not None else []

    # 2. Resolve dependencies for rope items
    resolved_rope_items: List[QuoteRopeItem] = []
    for r_dto in rope_items_dtos:
        if r_dto.rope_product_id is None:
            rp = await create_rope_product_factory(session_db=session_db)
            rope_product_id = rp.product_id
            default_prod_name = rp.construction or "Standard Yacht Rope"
        else:
            rope_product_id = r_dto.rope_product_id
            default_prod_name = "Standard Yacht Rope"

        if r_dto.color_id is None:
            col = await create_color_factory(session_db=session_db)
            color_id = col.id
            default_color_name = col.translations[0].name if getattr(col, "translations", None) else "Red"
        else:
            color_id = r_dto.color_id
            default_color_name = "Red"

        end_a_type_id = r_dto.end_a_type_id
        end_a_name = r_dto.end_a_name_snapshot
        if end_a_type_id is None and (r_dto.end_a_name_snapshot is not None or (r_dto.end_a_cost is not None and r_dto.end_a_cost > 0)):
            st_a = await create_splice_type_factory(session_db=session_db)
            end_a_type_id = st_a.id
            if end_a_name is None:
                end_a_name = st_a.translations[0].name if getattr(st_a, "translations", None) else "Augspleiss"

        end_b_type_id = r_dto.end_b_type_id
        end_b_name = r_dto.end_b_name_snapshot
        if end_b_type_id is None and (r_dto.end_b_name_snapshot is not None or (r_dto.end_b_cost is not None and r_dto.end_b_cost > 0)):
            st_b = await create_splice_type_factory(session_db=session_db)
            end_b_type_id = st_b.id
            if end_b_name is None:
                end_b_name = st_b.translations[0].name if getattr(st_b, "translations", None) else "Augspleiss"

        resolved_rope_items.append(
            QuoteRopeItem(
                rope_product_id=rope_product_id,
                color_id=color_id,
                product_name_snapshot=r_dto.product_name_snapshot or default_prod_name,
                color_name_snapshot=r_dto.color_name_snapshot or default_color_name,
                diameter_mm=r_dto.diameter_mm if r_dto.diameter_mm is not None else 10.0,
                length_m=r_dto.length_m if r_dto.length_m is not None else 20.0,
                quantity=r_dto.quantity if r_dto.quantity is not None else 1,
                price_per_meter_snapshot=r_dto.price_per_meter_snapshot if r_dto.price_per_meter_snapshot is not None else 5.0,
                total_rope_cost=r_dto.total_rope_cost if r_dto.total_rope_cost is not None else 100.0,
                end_a_type_id=end_a_type_id,
                end_a_name_snapshot=end_a_name,
                end_a_eye_size_cm=r_dto.end_a_eye_size_cm,
                end_a_cost=r_dto.end_a_cost if r_dto.end_a_cost is not None else 0.0,
                end_b_type_id=end_b_type_id,
                end_b_name_snapshot=end_b_name,
                end_b_eye_size_cm=r_dto.end_b_eye_size_cm,
                end_b_cost=r_dto.end_b_cost if r_dto.end_b_cost is not None else 0.0,
            )
        )

    # 3. Resolve dependencies for service items
    resolved_service_items: List[QuoteServiceItem] = []
    for s_dto in service_items_dtos:
        if s_dto.splice_type_id is None:
            st = await create_splice_type_factory(session_db=session_db)
            splice_type_id = st.id
            default_svc_name = st.translations[0].name if getattr(st, "translations", None) else "Augspleiss"
        else:
            splice_type_id = s_dto.splice_type_id
            default_svc_name = "Augspleiss"

        if s_dto.splice_material_id is None:
            sm = await create_splice_material_factory(session_db=session_db)
            splice_material_id = sm.id
            default_mat_name = getattr(sm, "name", "Kern-Mantel")
        else:
            splice_material_id = s_dto.splice_material_id
            default_mat_name = "Kern-Mantel"

        resolved_service_items.append(
            QuoteServiceItem(
                splice_type_id=splice_type_id,
                splice_material_id=splice_material_id,
                service_name_snapshot=s_dto.service_name_snapshot or default_svc_name,
                material_name_snapshot=s_dto.material_name_snapshot or default_mat_name,
                diameter_mm=s_dto.diameter_mm if s_dto.diameter_mm is not None else 10.0,
                eye_size_cm=s_dto.eye_size_cm if s_dto.eye_size_cm is not None else 15.0,
                quantity=s_dto.quantity if s_dto.quantity is not None else 1,
                unit_price_snapshot=s_dto.unit_price_snapshot if s_dto.unit_price_snapshot is not None else 15.0,
                total_cost=s_dto.total_cost if s_dto.total_cost is not None else 15.0,
            )
        )

    # 4. Create QuoteRequest
    quote_request = QuoteRequest(
        request_number=request_number,
        configurator_type=configurator_type,
        name=new_request.name if new_request.name is not None else "Test Customer",
        email=new_request.email if new_request.email is not None else f"{random_string(6)}@example.com",
        phone=new_request.phone if new_request.phone is not None else "+49 123 456789",
        comment=new_request.comment if new_request.comment is not None else "Test comment",
        currency=new_request.currency if new_request.currency is not None else Currency.EUR,
        total_price=new_request.total_price if new_request.total_price is not None else 100.0,
        vat_rate=new_request.vat_rate if new_request.vat_rate is not None else 0.0,
        is_urgent=new_request.is_urgent if new_request.is_urgent is not None else False,
        status=new_request.status if new_request.status is not None else QuoteRequestStatus.NEW,
        rope_items=resolved_rope_items,
        service_items=resolved_service_items,
    )
    session_db.add(quote_request)
    await session_db.commit()

    stmt = (
        select(QuoteRequest)
        .options(
            selectinload(QuoteRequest.rope_items),
            selectinload(QuoteRequest.service_items),
        )
        .where(QuoteRequest.id == quote_request.id)
    )
    result = await session_db.execute(stmt)
    loaded = result.scalar_one()

    return QuoteRequestResponseDTO.model_validate(loaded)


async def create_quote_rope_item_factory(
    session_db: AsyncSession,
    quote_request_id: Optional[int] = None,
    new_item: CreateQuoteRopeItemFixtureDTO = CreateQuoteRopeItemFixtureDTO(),
) -> QuoteRopeItem:
    if quote_request_id is None:
        qr = await create_quote_request_factory(
            session_db=session_db,
            new_request=CreateQuoteRequestFixtureDTO(rope_items=[]),
        )
        quote_request_id = qr.id

    if new_item.rope_product_id is None:
        rp = await create_rope_product_factory(session_db=session_db)
        rope_product_id = rp.product_id
        default_prod_name = rp.construction or "Standard Yacht Rope"
    else:
        rope_product_id = new_item.rope_product_id
        default_prod_name = "Standard Yacht Rope"

    if new_item.color_id is None:
        col = await create_color_factory(session_db=session_db)
        color_id = col.id
        default_color_name = col.translations[0].name if getattr(col, "translations", None) else "Red"
    else:
        color_id = new_item.color_id
        default_color_name = "Red"

    end_a_type_id = new_item.end_a_type_id
    end_a_name = new_item.end_a_name_snapshot
    if end_a_type_id is None and (new_item.end_a_name_snapshot is not None or (new_item.end_a_cost is not None and new_item.end_a_cost > 0)):
        st_a = await create_splice_type_factory(session_db=session_db)
        end_a_type_id = st_a.id
        if end_a_name is None:
            end_a_name = st_a.translations[0].name if getattr(st_a, "translations", None) else "Augspleiss"

    end_b_type_id = new_item.end_b_type_id
    end_b_name = new_item.end_b_name_snapshot
    if end_b_type_id is None and (new_item.end_b_name_snapshot is not None or (new_item.end_b_cost is not None and new_item.end_b_cost > 0)):
        st_b = await create_splice_type_factory(session_db=session_db)
        end_b_type_id = st_b.id
        if end_b_name is None:
            end_b_name = st_b.translations[0].name if getattr(st_b, "translations", None) else "Augspleiss"

    item = QuoteRopeItem(
        quote_request_id=quote_request_id,
        rope_product_id=rope_product_id,
        color_id=color_id,
        product_name_snapshot=new_item.product_name_snapshot or default_prod_name,
        color_name_snapshot=new_item.color_name_snapshot or default_color_name,
        diameter_mm=new_item.diameter_mm if new_item.diameter_mm is not None else 10.0,
        length_m=new_item.length_m if new_item.length_m is not None else 20.0,
        quantity=new_item.quantity if new_item.quantity is not None else 1,
        price_per_meter_snapshot=new_item.price_per_meter_snapshot if new_item.price_per_meter_snapshot is not None else 5.0,
        total_rope_cost=new_item.total_rope_cost if new_item.total_rope_cost is not None else 100.0,
        end_a_type_id=end_a_type_id,
        end_a_name_snapshot=end_a_name,
        end_a_eye_size_cm=new_item.end_a_eye_size_cm,
        end_a_cost=new_item.end_a_cost if new_item.end_a_cost is not None else 0.0,
        end_b_type_id=end_b_type_id,
        end_b_name_snapshot=end_b_name,
        end_b_eye_size_cm=new_item.end_b_eye_size_cm,
        end_b_cost=new_item.end_b_cost if new_item.end_b_cost is not None else 0.0,
    )
    session_db.add(item)
    await session_db.commit()
    await session_db.refresh(item)
    return item


async def create_quote_service_item_factory(
    session_db: AsyncSession,
    quote_request_id: Optional[int] = None,
    new_item: CreateQuoteServiceItemFixtureDTO = CreateQuoteServiceItemFixtureDTO(),
) -> QuoteServiceItem:
    if quote_request_id is None:
        qr = await create_quote_request_factory(
            session_db=session_db,
            new_request=CreateQuoteRequestFixtureDTO(
                configurator_type=ConfiguratorType.LOOP_ONLY,
                service_items=[],
            ),
        )
        quote_request_id = qr.id

    if new_item.splice_type_id is None:
        st = await create_splice_type_factory(session_db=session_db)
        splice_type_id = st.id
        default_svc_name = st.translations[0].name if getattr(st, "translations", None) else "Augspleiss"
    else:
        splice_type_id = new_item.splice_type_id
        default_svc_name = "Augspleiss"

    if new_item.splice_material_id is None:
        sm = await create_splice_material_factory(session_db=session_db)
        splice_material_id = sm.id
        default_mat_name = getattr(sm, "name", "Kern-Mantel")
    else:
        splice_material_id = new_item.splice_material_id
        default_mat_name = "Kern-Mantel"

    item = QuoteServiceItem(
        quote_request_id=quote_request_id,
        splice_type_id=splice_type_id,
        splice_material_id=splice_material_id,
        service_name_snapshot=new_item.service_name_snapshot or default_svc_name,
        material_name_snapshot=new_item.material_name_snapshot or default_mat_name,
        diameter_mm=new_item.diameter_mm if new_item.diameter_mm is not None else 10.0,
        eye_size_cm=new_item.eye_size_cm if new_item.eye_size_cm is not None else 15.0,
        quantity=new_item.quantity if new_item.quantity is not None else 1,
        unit_price_snapshot=new_item.unit_price_snapshot if new_item.unit_price_snapshot is not None else 15.0,
        total_cost=new_item.total_cost if new_item.total_cost is not None else 15.0,
    )
    session_db.add(item)
    await session_db.commit()
    await session_db.refresh(item)
    return item

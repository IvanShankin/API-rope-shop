from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from tests.helpers.functions import random_string
from tests.modules.quote_requests.fixtures.models_dto import (
    CreateQuoteRequestFixtureDTO,
)
from src.modules.configurator.models import Currency
from src.modules.quote_requests.models import (
    QuoteRequest,
    QuoteRopeItem,
    QuoteServiceItem,
    ConfiguratorType,
    QuoteRequestStatus,
)
from src.modules.quote_requests.models_dto import QuoteRequestResponseDTO


async def create_quote_request_factory(
    session_db: AsyncSession,
    new_request: CreateQuoteRequestFixtureDTO = CreateQuoteRequestFixtureDTO(),
) -> QuoteRequestResponseDTO:
    request_number = (
        new_request.request_number
        if new_request.request_number is not None
        else f"RPL-TEST-{random_string(8)}"
    )

    quote_request = QuoteRequest(
        request_number=request_number,
        configurator_type=(
            new_request.configurator_type
            if new_request.configurator_type is not None
            else ConfiguratorType.ROPE_WITH_SPLICE
        ),
        name=new_request.name if new_request.name is not None else random_string(10),
        email=new_request.email if new_request.email is not None else f"{random_string(6)}@example.com",
        phone=new_request.phone if new_request.phone is not None else "+49 123 456789",
        comment=new_request.comment if new_request.comment is not None else "Test comment",
        currency=new_request.currency if new_request.currency is not None else Currency.EUR,
        total_price=new_request.total_price if new_request.total_price is not None else 100.0,
        vat_rate=new_request.vat_rate if new_request.vat_rate is not None else 0.0,
        is_urgent=new_request.is_urgent if new_request.is_urgent is not None else False,
        status=new_request.status if new_request.status is not None else QuoteRequestStatus.NEW,
    )
    session_db.add(quote_request)
    await session_db.flush()

    for r_dto in new_request.rope_items:
        r_item = QuoteRopeItem(
            quote_request_id=quote_request.id,
            rope_product_id=r_dto.rope_product_id,
            color_id=r_dto.color_id,
            product_name_snapshot=r_dto.product_name_snapshot or "Test Rope",
            color_name_snapshot=r_dto.color_name_snapshot or "Red",
            diameter_mm=r_dto.diameter_mm if r_dto.diameter_mm is not None else 10.0,
            length_m=r_dto.length_m if r_dto.length_m is not None else 20.0,
            quantity=r_dto.quantity if r_dto.quantity is not None else 1,
            price_per_meter_snapshot=r_dto.price_per_meter_snapshot if r_dto.price_per_meter_snapshot is not None else 5.0,
            total_rope_cost=r_dto.total_rope_cost if r_dto.total_rope_cost is not None else 100.0,
            end_a_type_id=r_dto.end_a_type_id,
            end_a_name_snapshot=r_dto.end_a_name_snapshot,
            end_a_eye_size_cm=r_dto.end_a_eye_size_cm,
            end_a_cost=r_dto.end_a_cost if r_dto.end_a_cost is not None else 0.0,
            end_b_type_id=r_dto.end_b_type_id,
            end_b_name_snapshot=r_dto.end_b_name_snapshot,
            end_b_eye_size_cm=r_dto.end_b_eye_size_cm,
            end_b_cost=r_dto.end_b_cost if r_dto.end_b_cost is not None else 0.0,
        )
        session_db.add(r_item)

    for s_dto in new_request.service_items:
        s_item = QuoteServiceItem(
            quote_request_id=quote_request.id,
            splice_type_id=s_dto.splice_type_id,
            splice_material_id=s_dto.splice_material_id,
            service_name_snapshot=s_dto.service_name_snapshot or "Augspleiss",
            material_name_snapshot=s_dto.material_name_snapshot or "Kern-Mantel",
            diameter_mm=s_dto.diameter_mm if s_dto.diameter_mm is not None else 10.0,
            eye_size_cm=s_dto.eye_size_cm,
            quantity=s_dto.quantity if s_dto.quantity is not None else 1,
            unit_price_snapshot=s_dto.unit_price_snapshot if s_dto.unit_price_snapshot is not None else 15.0,
            total_cost=s_dto.total_cost if s_dto.total_cost is not None else 15.0,
        )
        session_db.add(s_item)

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

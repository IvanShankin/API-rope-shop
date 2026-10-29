from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database.database import get_db
from src.modules.rope_products.repository import RopeProductRepository, ProductVariantRepository
from src.modules.rope_products.service import RopeProductsService
from src.modules.material_groups.repository import MaterialGroupRepository
from src.modules.materials.repository import MaterialRepository
from src.modules.splice_materials.repository import SpliceMaterialRepository


def get_rope_product_repository(
    session: AsyncSession = Depends(get_db)
) -> RopeProductRepository:
    return RopeProductRepository(session=session)


def get_product_variant_repository(
    session: AsyncSession = Depends(get_db)
) -> ProductVariantRepository:
    return ProductVariantRepository(session=session)


def get_material_group_repository(
    session: AsyncSession = Depends(get_db)
) -> MaterialGroupRepository:
    return MaterialGroupRepository(session=session)


def get_material_repository(
    session: AsyncSession = Depends(get_db)
) -> MaterialRepository:
    return MaterialRepository(session=session)


def get_splice_material_repository(
    session: AsyncSession = Depends(get_db)
) -> SpliceMaterialRepository:
    return SpliceMaterialRepository(session=session)


def get_rope_products_service(
    session: AsyncSession = Depends(get_db),
    product_repo: RopeProductRepository = Depends(get_rope_product_repository),
    variant_repo: ProductVariantRepository = Depends(get_product_variant_repository),
    material_group_repo: MaterialGroupRepository = Depends(get_material_group_repository),
    material_repo: MaterialRepository = Depends(get_material_repository),
    splice_material_repo: SpliceMaterialRepository = Depends(get_splice_material_repository),
) -> RopeProductsService:
    return RopeProductsService(
        product_repo=product_repo,
        variant_repo=variant_repo,
        material_group_repo=material_group_repo,
        material_repo=material_repo,
        splice_material_repo=splice_material_repo,
        session=session,
    )

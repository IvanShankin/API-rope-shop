from typing import List
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.splice_materials.repository import SpliceMaterialRepository
from src.modules.splice_materials.models_dto import (
    SpliceMaterialDependenciesDTO,
    SpliceMaterialPriceRuleDependencyDTO,
    SpliceMaterialRopeDependencyDTO,
    SpliceMaterialCreate,
    SpliceMaterialUpdate,
    SpliceMaterialResponseDTO,
    SpliceMaterialWithRulesResponseDTO
)
from src.modules.splice_materials.exception import (
    SpliceMaterialNotFound,
    SpliceMaterialAlreadyExists,
    SpliceMaterialHasDependencies
)


class SpliceMaterialService:
    def __init__(
        self,
        material_repo: SpliceMaterialRepository,
        session: AsyncSession
    ):
        self.material_repo = material_repo
        self.session = session

    async def create_material(self, data: SpliceMaterialCreate) -> SpliceMaterialResponseDTO:
        existing = await self.material_repo.get_by_code(data.code)
        if existing:
            raise SpliceMaterialAlreadyExists(f"SpliceMaterial with code '{data.code}' already exists.")
            
        new_material = await self.material_repo.add_material(data.model_dump())
        await self.session.commit()
        await self.session.refresh(new_material)
        return SpliceMaterialResponseDTO.model_validate(new_material)

    async def get_all_materials(self, include_rules: bool = False, is_admin: bool = False) -> List[SpliceMaterialResponseDTO]:
        materials = await self.material_repo.get_all(include_rules=include_rules)
        if include_rules:
            if not is_admin:
                for m in materials:
                    if hasattr(m, "rules") and m.rules:
                        m.rules = [r for r in m.rules if r.is_active]
            return [SpliceMaterialWithRulesResponseDTO.model_validate(m) for m in materials]
        return [SpliceMaterialResponseDTO.model_validate(m) for m in materials]

    async def get_material_by_id(self, material_id: int, include_rules: bool = False, is_admin: bool = False) -> SpliceMaterialResponseDTO:
        material = await self.material_repo.get_by_id(material_id, include_rules=include_rules)
        if not material:
            raise SpliceMaterialNotFound(f"SpliceMaterial with id {material_id} not found.")
        
        if include_rules:
            if not is_admin and hasattr(material, "rules") and material.rules:
                material.rules = [r for r in material.rules if r.is_active]
            return SpliceMaterialWithRulesResponseDTO.model_validate(material)
        return SpliceMaterialResponseDTO.model_validate(material)

    async def update_material(self, material_id: int, data: SpliceMaterialUpdate) -> SpliceMaterialResponseDTO:
        material = await self.material_repo.get_by_id(material_id)
        if not material:
            raise SpliceMaterialNotFound(f"SpliceMaterial with id {material_id} not found.")

        if data.code is not None and data.code != material.code:
            existing = await self.material_repo.get_by_code(data.code)
            if existing:
                raise SpliceMaterialAlreadyExists(f"SpliceMaterial with code '{data.code}' already exists.")

        update_data = data.model_dump(exclude_unset=True)
        if update_data:
            await self.material_repo.update_material(material_id, update_data)
            await self.session.commit()
            
        updated_material = await self.material_repo.get_by_id(material_id)
        return SpliceMaterialResponseDTO.model_validate(updated_material)

    async def get_dependencies(self, material_id: int) -> SpliceMaterialDependenciesDTO:
        """Получение зависимостей тарифного материала перед удалением."""
        item = await self.material_repo.get_by_id(material_id)
        if not item:
            raise SpliceMaterialNotFound(f"Splice material with id {material_id} not found.")

        deps = await self.material_repo.get_dependencies(material_id)
        rules = deps["rules"]
        ropes = deps["ropes"]

        rules_dto = [
            SpliceMaterialPriceRuleDependencyDTO(
                id=r.id,
                splice_type_id=r.splice_type_id,
                splice_type_code=r.splice_type.code if r.splice_type else None,
                diameter_from_mm=float(r.diameter_from_mm),
                diameter_to_mm=float(r.diameter_to_mm),
                price=float(r.price),
            )
            for r in rules
        ]
        ropes_dto = [
            SpliceMaterialRopeDependencyDTO(
                product_id=p.id,
                name=p.translations[0].name if p.translations else f"Product #{p.id}",
            )
            for p in ropes
        ]

        rules_count = len(rules_dto)
        ropes_count = len(ropes_dto)
        has_dependencies = (rules_count > 0 or ropes_count > 0)

        return SpliceMaterialDependenciesDTO(
            has_dependencies=has_dependencies,
            can_delete=not has_dependencies,
            rules_count=rules_count,
            ropes_count=ropes_count,
            rules=rules_dto,
            ropes=ropes_dto,
        )

    async def delete_material(self, material_id: int) -> None:
        material = await self.material_repo.get_by_id(material_id)
        if not material:
            raise SpliceMaterialNotFound(f"SpliceMaterial with id {material_id} not found.")
            
        has_deps = await self.material_repo.has_dependencies(material_id)
        if has_deps:
            raise SpliceMaterialHasDependencies(
                f"Cannot delete SpliceMaterial with id {material_id} because it is referenced by SplicePriceRules or RopeProducts."
            )
            
        await self.material_repo.delete_material(material_id)
        await self.session.commit()

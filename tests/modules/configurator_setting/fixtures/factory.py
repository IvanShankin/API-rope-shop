from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from tests.modules.configurator_setting.fixtures.models_dto import CreateConfiguratorSettingFixtureDTO
from src.modules.configurator_setting.models import ConfiguratorSetting, Currency
from src.modules.configurator_setting.models_dto import ConfiguratorSettingResponseDTO


async def create_configurator_setting_factory(
    session_db: AsyncSession,
    new_setting: CreateConfiguratorSettingFixtureDTO = CreateConfiguratorSettingFixtureDTO(),
) -> ConfiguratorSettingResponseDTO:
    stmt = select(ConfiguratorSetting).limit(1)
    res = await session_db.execute(stmt)
    setting = res.scalar_one_or_none()

    if setting is None:
        setting = ConfiguratorSetting(
            min_length_m=new_setting.min_length_m if new_setting.min_length_m is not None else 1.0,
            max_length_m=new_setting.max_length_m if new_setting.max_length_m is not None else 200.0,
            splice_allowance_until_mm=new_setting.splice_allowance_until_mm if new_setting.splice_allowance_until_mm is not None else 12.0,
            splice_allowance_until_m=new_setting.splice_allowance_until_m if new_setting.splice_allowance_until_m is not None else 0.6,
            splice_allowance_over_m=new_setting.splice_allowance_over_m if new_setting.splice_allowance_over_m is not None else 1.0,
            urgent_surcharge_per_splice=new_setting.urgent_surcharge_per_splice if new_setting.urgent_surcharge_per_splice is not None else 10.0,
            urgent_max_splices=new_setting.urgent_max_splices if new_setting.urgent_max_splices is not None else 10,
            standard_turnaround_hours=new_setting.standard_turnaround_hours if new_setting.standard_turnaround_hours is not None else 72,
            urgent_turnaround_hours=new_setting.urgent_turnaround_hours if new_setting.urgent_turnaround_hours is not None else 24,
            currency=new_setting.currency if new_setting.currency is not None else Currency.EUR,
            vat_rate=new_setting.vat_rate if new_setting.vat_rate is not None else 0.0,
            vat_note=new_setting.vat_note if new_setting.vat_note is not None else "inkl. MwSt.",
        )
        session_db.add(setting)
    else:
        if new_setting.min_length_m is not None:
            setting.min_length_m = new_setting.min_length_m
        if new_setting.max_length_m is not None:
            setting.max_length_m = new_setting.max_length_m
        if new_setting.splice_allowance_until_mm is not None:
            setting.splice_allowance_until_mm = new_setting.splice_allowance_until_mm
        if new_setting.splice_allowance_until_m is not None:
            setting.splice_allowance_until_m = new_setting.splice_allowance_until_m
        if new_setting.splice_allowance_over_m is not None:
            setting.splice_allowance_over_m = new_setting.splice_allowance_over_m
        if new_setting.urgent_surcharge_per_splice is not None:
            setting.urgent_surcharge_per_splice = new_setting.urgent_surcharge_per_splice
        if new_setting.urgent_max_splices is not None:
            setting.urgent_max_splices = new_setting.urgent_max_splices
        if new_setting.standard_turnaround_hours is not None:
            setting.standard_turnaround_hours = new_setting.standard_turnaround_hours
        if new_setting.urgent_turnaround_hours is not None:
            setting.urgent_turnaround_hours = new_setting.urgent_turnaround_hours
        if new_setting.currency is not None:
            setting.currency = new_setting.currency
        if new_setting.vat_rate is not None:
            setting.vat_rate = new_setting.vat_rate
        if new_setting.vat_note is not None:
            setting.vat_note = new_setting.vat_note

    await session_db.commit()
    await session_db.refresh(setting)
    return ConfiguratorSettingResponseDTO.model_validate(setting)

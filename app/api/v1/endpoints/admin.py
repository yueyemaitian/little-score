from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.api.deps import get_current_admin
from app.db.session import get_db
from app.models.system import SystemSettings
from app.models.user import User

router = APIRouter()


class SystemSettingsRead(BaseModel):
    allow_registration: bool

    class Config:
        from_attributes = True


class SystemSettingsUpdate(BaseModel):
    allow_registration: bool


@router.get("/settings", response_model=SystemSettingsRead)
async def get_system_settings(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """获取系统设置（仅管理员）"""
    result = await db.execute(select(SystemSettings).limit(1))
    settings = result.scalar_one_or_none()

    if not settings:
        # 如果不存在，创建默认设置
        settings = SystemSettings(allow_registration=True)
        db.add(settings)
        await db.commit()
        await db.refresh(settings)

    return SystemSettingsRead.model_validate(settings)


@router.put("/settings", response_model=SystemSettingsRead)
async def update_system_settings(
    settings_update: SystemSettingsUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """更新系统设置（仅管理员）"""
    result = await db.execute(select(SystemSettings).limit(1))
    settings = result.scalar_one_or_none()

    if not settings:
        # 如果不存在，创建
        settings = SystemSettings(**settings_update.model_dump())
        db.add(settings)
    else:
        settings.allow_registration = settings_update.allow_registration

    await db.commit()
    await db.refresh(settings)
    return SystemSettingsRead.model_validate(settings)


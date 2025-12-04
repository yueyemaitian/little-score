from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_admin
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import UserRead

router = APIRouter()


@router.get("/", response_model=List[UserRead])
async def list_users(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
) -> list[UserRead]:
    stmt: Select[tuple[User]] = select(User).order_by(User.created_at.desc())
    result = await db.execute(stmt)
    users = list(result.scalars().all())
    return [UserRead.model_validate(u) for u in users]



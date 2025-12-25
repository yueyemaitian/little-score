from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash
from app.models.user import User
from app.schemas.user import UserCreate


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
    return await db.get(User, user_id)


async def create_user(db: AsyncSession, obj_in: UserCreate, is_admin: bool = False) -> User:
    db_obj = User(
        email=obj_in.email,
        hashed_password=get_password_hash(obj_in.password),
        is_admin=is_admin,
    )
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj


async def create_user_without_password(db: AsyncSession, is_admin: bool = False) -> User:
    """创建没有密码的用户（用于第三方登录）"""
    db_obj = User(
        email=None,
        hashed_password=None,
        is_admin=is_admin,
    )
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj



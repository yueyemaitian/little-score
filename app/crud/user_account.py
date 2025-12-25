from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.user_account import UserAccount
from app.schemas.user_account import UserAccountCreate, UserAccountUpdate


async def get_user_account_by_type_and_id(
    db: AsyncSession,
    account_type: str,
    account_id: str
) -> Optional[UserAccount]:
    """根据账号类型和账号ID查找用户账号"""
    result = await db.execute(
        select(UserAccount).where(
            UserAccount.account_type == account_type,
            UserAccount.account_id == account_id
        )
    )
    return result.scalar_one_or_none()


async def get_user_accounts_by_user_id(
    db: AsyncSession,
    user_id: int
) -> list[UserAccount]:
    """获取用户的所有账号"""
    result = await db.execute(
        select(UserAccount).where(UserAccount.user_id == user_id)
    )
    return list(result.scalars().all())


async def create_user_account(
    db: AsyncSession,
    obj_in: UserAccountCreate
) -> UserAccount:
    """创建用户账号"""
    db_obj = UserAccount(
        user_id=obj_in.user_id,
        account_type=obj_in.account_type,
        account_id=obj_in.account_id,
        account_name=obj_in.account_name,
        avatar_url=obj_in.avatar_url,
        extra_data=obj_in.extra_data,
    )
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj


async def update_user_account(
    db: AsyncSession,
    account_id: int,
    obj_in: UserAccountUpdate
) -> Optional[UserAccount]:
    """更新用户账号"""
    account = await db.get(UserAccount, account_id)
    if not account:
        return None
    
    if obj_in.account_name is not None:
        account.account_name = obj_in.account_name
    if obj_in.avatar_url is not None:
        account.avatar_url = obj_in.avatar_url
    if obj_in.extra_data is not None:
        account.extra_data = obj_in.extra_data
    
    await db.commit()
    await db.refresh(account)
    return account


async def delete_user_account(
    db: AsyncSession,
    account_id: int
) -> bool:
    """删除用户账号"""
    account = await db.get(UserAccount, account_id)
    if not account:
        return False
    
    await db.delete(account)
    await db.commit()
    return True


async def get_user_by_account(
    db: AsyncSession,
    account_type: str,
    account_id: str
) -> Optional[User]:
    """根据账号类型和账号ID查找用户"""
    account = await get_user_account_by_type_and_id(db, account_type, account_id)
    if not account:
        return None
    
    return await db.get(User, account.user_id)



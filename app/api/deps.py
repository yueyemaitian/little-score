from typing import AsyncGenerator

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.security import verify_password
from app.crud.user import get_user_by_email, get_user_by_id
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import TokenData

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    db: AsyncSession = Depends(get_db),
    token: str = Depends(oauth2_scheme),
) -> User:
    settings = get_settings()
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        sub: str | None = payload.get("sub")
        if sub is None:
            raise credentials_exception
        token_data = TokenData(sub=sub)
    except JWTError:
        raise credentials_exception

    # token的sub可能是email或user_id（格式：user_id:123）
    sub_str = token_data.sub  # type: ignore[arg-type]
    if sub_str.startswith("user_id:"):
        # 使用user_id查找
        user_id = int(sub_str.split(":")[1])
        user = await get_user_by_id(db, user_id)
    else:
        # 使用email查找（向后兼容）
        user = await get_user_by_email(db, sub_str)
    
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="用户已被禁用")
    return current_user


async def get_current_admin(
    current_user: User = Depends(get_current_active_user),
) -> User:
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="权限不足")
    return current_user



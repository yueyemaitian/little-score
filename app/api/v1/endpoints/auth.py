from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user
from app.core.config import get_settings
from app.core.security import create_access_token, verify_password, get_password_hash
from app.crud.user import create_user, create_user_without_password, get_user_by_email, get_user_by_id
from app.crud.user_account import (
    create_user_account,
    get_user_account_by_type_and_id,
    get_user_accounts_by_user_id,
    get_user_by_account,
)
from app.db.session import get_db
from app.models.system import SystemSettings
from app.models.user import User
from app.schemas.auth import BindAccountRequest, DingtalkLoginRequest, WechatLoginRequest
from app.schemas.user import Token, UserCreate, UserRead
from app.schemas.user_account import UserAccountRead
from app.utils.oauth import get_dingtalk_user_info, get_wechat_user_info

router = APIRouter()


@router.post("/register", response_model=UserRead)
async def register(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db),
) -> UserRead:
    # 检查系统是否允许注册
    settings_row = await db.get(SystemSettings, 1)
    if settings_row and not settings_row.allow_registration:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="系统禁止新用户注册，请稍后重试",
        )

    # 检查邮箱是否已存在
    user = await get_user_by_email(db, user_in.email)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该邮箱已被注册",
        )
    
    # 创建用户
    try:
        user = await create_user(db, user_in)
        return UserRead.model_validate(user)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"注册失败: {str(e)}",
        )


@router.post("/login", response_model=Token)
async def login_for_access_token(
    db: AsyncSession = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> Token:
    user = await get_user_by_email(db, form_data.username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名或密码错误",
        )
    
    # 检查用户是否有密码（可能只有第三方登录账号）
    if not user.hashed_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该账号未设置密码，请使用其他方式登录",
        )
    
    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名或密码错误",
        )

    settings = get_settings()
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    # 使用user_id作为subject，格式：user_id:123
    access_token = create_access_token(
        subject=f"user_id:{user.id}",
        expires_delta=access_token_expires,
    )
    return Token(access_token=access_token)


@router.get("/me", response_model=UserRead)
async def read_users_me(current_user: User = Depends(get_current_active_user)) -> UserRead:
    return UserRead.model_validate(current_user)


@router.post("/login/wechat", response_model=Token)
async def login_with_wechat(
    request: WechatLoginRequest,
    db: AsyncSession = Depends(get_db),
) -> Token:
    """微信登录"""
    try:
        # 获取微信用户信息
        wechat_info = await get_wechat_user_info(request.code)
        openid = wechat_info["openid"]
        
        # 查找是否已有账号
        account = await get_user_account_by_type_and_id(db, "wechat", openid)
        
        if account:
            # 已有账号，直接登录
            user = await get_user_by_id(db, account.user_id)
        else:
            # 新用户，创建账号
            user = await create_user_without_password(db)
            from app.schemas.user_account import UserAccountCreate
            await create_user_account(
                db,
                UserAccountCreate(
                    user_id=user.id,
                    account_type="wechat",
                    account_id=openid,
                    account_name=wechat_info.get("nickname"),
                    avatar_url=wechat_info.get("headimgurl"),
                    extra_data=wechat_info.get("extra_data"),
                )
            )
        
        settings = get_settings()
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            subject=f"user_id:{user.id}",
            expires_delta=access_token_expires,
        )
        return Token(access_token=access_token)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"微信登录失败: {str(e)}",
        )


@router.post("/login/dingtalk", response_model=Token)
async def login_with_dingtalk(
    request: DingtalkLoginRequest,
    db: AsyncSession = Depends(get_db),
) -> Token:
    """钉钉登录"""
    try:
        # 获取钉钉用户信息
        dingtalk_info = await get_dingtalk_user_info(request.code)
        openid = dingtalk_info["openid"]
        
        # 查找是否已有账号
        account = await get_user_account_by_type_and_id(db, "dingtalk", openid)
        
        if account:
            # 已有账号，直接登录
            user = await get_user_by_id(db, account.user_id)
        else:
            # 新用户，创建账号
            user = await create_user_without_password(db)
            from app.schemas.user_account import UserAccountCreate
            await create_user_account(
                db,
                UserAccountCreate(
                    user_id=user.id,
                    account_type="dingtalk",
                    account_id=openid,
                    account_name=dingtalk_info.get("nickname"),
                    avatar_url=dingtalk_info.get("avatar_url"),
                    extra_data=dingtalk_info.get("extra_data"),
                )
            )
        
        settings = get_settings()
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            subject=f"user_id:{user.id}",
            expires_delta=access_token_expires,
        )
        return Token(access_token=access_token)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"钉钉登录失败: {str(e)}",
        )


@router.get("/accounts", response_model=list[UserAccountRead])
async def get_my_accounts(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> list[UserAccountRead]:
    """获取当前用户的所有关联账号"""
    accounts = await get_user_accounts_by_user_id(db, current_user.id)
    return [UserAccountRead.model_validate(account) for account in accounts]


@router.post("/accounts/bind", response_model=UserAccountRead)
async def bind_account(
    request: BindAccountRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> UserAccountRead:
    """绑定账号"""
    # 检查账号是否已被其他用户绑定
    existing_account = await get_user_account_by_type_and_id(
        db, request.account_type, request.account_id
    )
    if existing_account and existing_account.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该账号已被其他用户绑定",
        )
    
    # 检查当前用户是否已绑定该类型的账号
    user_accounts = await get_user_accounts_by_user_id(db, current_user.id)
    for account in user_accounts:
        if account.account_type == request.account_type:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"您已绑定{request.account_type}账号",
            )
    
    # 如果是邮箱绑定，需要设置密码
    if request.account_type == "email":
        if not request.password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱绑定需要提供密码",
            )
        # 更新用户的email和password
        current_user.email = request.account_id
        current_user.hashed_password = get_password_hash(request.password)
        await db.commit()
    
    # 创建账号关联
    from app.schemas.user_account import UserAccountCreate
    account = await create_user_account(
        db,
        UserAccountCreate(
            user_id=current_user.id,
            account_type=request.account_type,
            account_id=request.account_id,
            account_name=request.account_name,
            avatar_url=request.avatar_url,
            extra_data=request.extra_data,
        )
    )
    return UserAccountRead.model_validate(account)



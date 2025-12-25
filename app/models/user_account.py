from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.utils.time import utcnow


class AccountType(str, Enum):
    """账号类型"""
    EMAIL = "email"  # 邮箱登录
    WECHAT = "wechat"  # 微信登录
    DINGTALK = "dingtalk"  # 钉钉登录


class UserAccount(Base):
    """用户账号关联表，支持多种登录方式"""
    __tablename__ = "user_accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    account_type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)  # email, wechat, dingtalk
    account_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)  # 第三方平台的唯一ID
    account_name: Mapped[str | None] = mapped_column(String(255), nullable=True)  # 账号显示名称（如微信昵称、钉钉名称）
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)  # 头像URL
    extra_data: Mapped[str | None] = mapped_column(String(1000), nullable=True)  # JSON格式的额外数据

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        onupdate=utcnow,
        nullable=False,
    )

    # 关系
    user: Mapped["User"] = relationship("User", back_populates="accounts")

    # 唯一约束：同一类型的账号ID在同一用户下唯一
    __table_args__ = (
        UniqueConstraint("user_id", "account_type", "account_id", name="uq_user_account_type_id"),
    )




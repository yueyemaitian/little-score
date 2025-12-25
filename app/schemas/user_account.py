from datetime import datetime

from pydantic import BaseModel, field_validator


class UserAccountBase(BaseModel):
    account_type: str  # email, wechat, dingtalk
    account_id: str
    account_name: str | None = None
    avatar_url: str | None = None
    extra_data: str | None = None

    @field_validator("account_type")
    @classmethod
    def validate_account_type(cls, v: str) -> str:
        valid_types = ["email", "wechat", "dingtalk"]
        if v not in valid_types:
            raise ValueError(f"账号类型必须是以下之一: {', '.join(valid_types)}")
        return v


class UserAccountCreate(UserAccountBase):
    user_id: int


class UserAccountRead(UserAccountBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserAccountUpdate(BaseModel):
    account_name: str | None = None
    avatar_url: str | None = None
    extra_data: str | None = None




from datetime import datetime

from pydantic import BaseModel, EmailStr, field_validator


class UserBase(BaseModel):
    email: EmailStr | None = None


class UserCreate(UserBase):
    password: str

    @field_validator("password")
    @classmethod
    def validate_password_length(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError("密码长度至少为6位")
        if len(v) > 20:
            raise ValueError("密码长度不能超过20位")
        return v


class UserRead(UserBase):
    id: int
    is_active: bool
    is_admin: bool
    created_at: datetime
    last_login_at: datetime | None

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    sub: str | None = None



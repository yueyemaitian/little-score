from datetime import date, datetime

from pydantic import BaseModel, Field, field_validator

from app.core.enums import EducationStage, Gender, format_enum_error, get_enum_values


class StudentBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=64, description="姓名")
    gender: str | None = Field(None, description="性别")
    birthday: date | None = Field(None, description="出生年月")
    stage: str | None = Field(None, description="教育阶段")
    school: str | None = Field(None, max_length=128, description="学校")
    enroll_date: date | None = Field(None, description="入学时间")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("姓名不能为空")
        if len(v.strip()) > 64:
            raise ValueError("姓名长度不能超过64个字符")
        return v.strip()

    @field_validator("gender")
    @classmethod
    def validate_gender(cls, v: str | None) -> str | None:
        if v is not None:
            valid_values = get_enum_values("gender")
            if v not in valid_values:
                raise ValueError(f"性别{format_enum_error('gender', valid_values)}")
        return v

    @field_validator("stage")
    @classmethod
    def validate_stage(cls, v: str | None) -> str | None:
        if v is not None:
            valid_values = get_enum_values("education_stage")
            if v not in valid_values:
                raise ValueError(f"教育阶段{format_enum_error('education_stage', valid_values)}")
        return v

    @field_validator("school")
    @classmethod
    def validate_school(cls, v: str | None) -> str | None:
        if v is not None:
            v = v.strip() if v else None
            if v and len(v) > 128:
                raise ValueError("学校名称长度不能超过128个字符")
        return v


class StudentCreate(StudentBase):
    pass


class StudentUpdate(StudentBase):
    pass


class StudentRead(StudentBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True



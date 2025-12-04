from datetime import datetime

from pydantic import BaseModel, Field, field_validator, model_validator

from app.core.enums import ProjectLevel, format_enum_error, get_enum_values


class ProjectBase(BaseModel):
    level: int = Field(..., description="项目层级")
    name: str = Field(..., min_length=1, max_length=128, description="项目名称")
    description: str | None = Field(None, max_length=255, description="项目描述")
    parent_id: int | None = Field(None, description="父项目ID（二级项目需要）")

    @field_validator("level")
    @classmethod
    def validate_level(cls, v: int) -> int:
        valid_values = get_enum_values("project_level")
        if v not in valid_values:
            raise ValueError(f"项目层级{format_enum_error('project_level', valid_values)}")
        return v

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("项目名称不能为空")
        if len(v.strip()) > 128:
            raise ValueError("项目名称长度不能超过128个字符")
        return v.strip()

    @field_validator("description")
    @classmethod
    def validate_description(cls, v: str | None) -> str | None:
        if v is not None:
            v = v.strip() if v else None
            if v and len(v) > 255:
                raise ValueError("项目描述长度不能超过255个字符")
        return v

    @model_validator(mode="after")
    def validate_parent_id(self):
        from app.core.enums import get_enum_label
        
        if self.level == ProjectLevel.LEVEL_2.value and not self.parent_id:
            level2_label = get_enum_label("project_level", ProjectLevel.LEVEL_2.value)
            raise ValueError(f"{level2_label}必须指定父项目")
        if self.level == ProjectLevel.LEVEL_1.value and self.parent_id:
            level1_label = get_enum_label("project_level", ProjectLevel.LEVEL_1.value)
            raise ValueError(f"{level1_label}不能有父项目")
        return self


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=128)
    description: str | None = Field(None, max_length=255)
    parent_id: int | None = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str | None) -> str | None:
        if v is not None:
            if not v or not v.strip():
                raise ValueError("项目名称不能为空")
            if len(v.strip()) > 128:
                raise ValueError("项目名称长度不能超过128个字符")
            return v.strip()
        return v

    @field_validator("description")
    @classmethod
    def validate_description(cls, v: str | None) -> str | None:
        if v is not None:
            v = v.strip() if v else None
            if v and len(v) > 255:
                raise ValueError("项目描述长度不能超过255个字符")
        return v


class ProjectRead(ProjectBase):
    id: int
    user_id: int
    parent_name: str | None = None  # 父项目名称（二级项目时返回）
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


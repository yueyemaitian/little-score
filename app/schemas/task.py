from datetime import datetime

from pydantic import BaseModel, Field, field_validator, model_validator

from app.core.enums import (
    RewardType,
    TaskRating,
    TaskStatus,
    format_enum_error,
    get_enum_label,
    get_enum_values,
)


class TaskBase(BaseModel):
    student_id: int = Field(..., description="学生ID")
    project_level1_id: int = Field(..., description="一级项目ID")
    project_level2_id: int | None = Field(None, description="二级项目ID")
    status: str = Field(..., description="任务状态")
    rating: str | None = Field(None, description="评分（仅已完成时）")
    reward_type: str = Field(..., description="惩奖类型")
    reward_points: int | None = Field(None, description="奖励积分（reward_type=reward时）")
    punishment_option_id: int | None = Field(None, description="惩罚选项ID（reward_type=punish时）")

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        valid_values = get_enum_values("task_status")
        if v not in valid_values:
            raise ValueError(f"状态{format_enum_error('task_status', valid_values)}")
        return v

    @field_validator("rating")
    @classmethod
    def validate_rating(cls, v: str | None) -> str | None:
        if v is not None:
            valid_values = get_enum_values("task_rating")
            if v not in valid_values:
                raise ValueError(f"评分{format_enum_error('task_rating', valid_values)}")
        return v

    @field_validator("reward_type")
    @classmethod
    def validate_reward_type(cls, v: str) -> str:
        valid_values = get_enum_values("reward_type")
        if v not in valid_values:
            raise ValueError(f"惩奖类型{format_enum_error('reward_type', valid_values)}")
        return v

    @field_validator("reward_points")
    @classmethod
    def validate_reward_points(cls, v: int | None) -> int | None:
        if v is not None and v <= 0:
            raise ValueError("奖励积分必须大于0")
        return v

    @model_validator(mode="after")
    def validate_task_logic(self):
        # 已完成的任务必须提供评分
        if self.status == TaskStatus.COMPLETED.value and not self.rating:
            raise ValueError("已完成的任务必须提供评分")
        
        # reward_type=reward 时必须提供 reward_points
        if self.reward_type == RewardType.REWARD.value and not self.reward_points:
            reward_label = get_enum_label("reward_type", RewardType.REWARD.value)
            raise ValueError(f"{reward_label}类型必须提供奖励积分")
        
        # reward_type=punish 时必须提供 punishment_option_id
        if self.reward_type == RewardType.PUNISH.value and not self.punishment_option_id:
            punish_label = get_enum_label("reward_type", RewardType.PUNISH.value)
            raise ValueError(f"{punish_label}类型必须提供惩罚选项")
        
        # reward_type=none 时不应有 reward_points 或 punishment_option_id
        if self.reward_type == RewardType.NONE.value:
            none_label = get_enum_label("reward_type", RewardType.NONE.value)
            if self.reward_points:
                raise ValueError(f"{none_label}类型不应有奖励积分")
            if self.punishment_option_id:
                raise ValueError(f"{none_label}类型不应有惩罚选项")
        
        return self


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    project_level1_id: int | None = None
    project_level2_id: int | None = None
    status: str | None = None
    rating: str | None = None
    reward_type: str | None = None
    reward_points: int | None = None
    punishment_option_id: int | None = None


class TaskRead(TaskBase):
    id: int
    created_at: datetime
    updated_at: datetime
    is_deleted: bool | None = None
    deleted_at: datetime | None = None
    project_level1_name: str | None = None
    project_level2_name: str | None = None

    class Config:
        from_attributes = True


class TaskFilter(BaseModel):
    student_id: int | None = None
    project_level1_id: int | None = None
    project_level2_id: int | None = None
    status: str | None = None


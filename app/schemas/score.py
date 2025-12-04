from datetime import datetime

from pydantic import BaseModel, Field


class ScoreSummary(BaseModel):
    """积分汇总"""
    available_points: int = Field(..., description="可用积分")
    exchanged_points: int = Field(..., description="已兑换积分")


class ScoreIncreaseRead(BaseModel):
    """积分增加记录"""
    id: int
    student_id: int
    task_id: int
    project_level1_id: int
    project_level2_id: int | None
    points: int
    created_at: datetime

    class Config:
        from_attributes = True


class RewardExchangeOptionBase(BaseModel):
    name: str = Field(..., max_length=128, description="奖励名称")
    description: str | None = Field(None, max_length=255, description="奖励描述")
    cost_points: int = Field(..., description="消耗积分")


class RewardExchangeOptionCreate(RewardExchangeOptionBase):
    pass


class RewardExchangeOptionUpdate(BaseModel):
    name: str | None = Field(None, max_length=128)
    description: str | None = Field(None, max_length=255)
    cost_points: int | None = None


class RewardExchangeOptionRead(RewardExchangeOptionBase):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class ScoreExchangeCreate(BaseModel):
    student_id: int = Field(..., description="学生ID")
    reward_option_id: int = Field(..., description="奖励选项ID")


class ScoreExchangeRead(BaseModel):
    id: int
    student_id: int
    reward_option_id: int
    cost_points: int
    created_at: datetime

    class Config:
        from_attributes = True


class PunishmentOptionBase(BaseModel):
    name: str = Field(..., max_length=128, description="惩罚选项名称")
    description: str | None = Field(None, max_length=255, description="惩罚选项描述")
    generate_related_task: bool = Field(False, description="是否生成关联任务")
    related_project_level1_id: int | None = Field(None, description="关联一级项目ID")
    related_project_level2_id: int | None = Field(None, description="关联二级项目ID")


class PunishmentOptionCreate(PunishmentOptionBase):
    pass


class PunishmentOptionUpdate(BaseModel):
    name: str | None = Field(None, max_length=128)
    description: str | None = Field(None, max_length=255)
    generate_related_task: bool | None = None
    related_project_level1_id: int | None = None
    related_project_level2_id: int | None = None


class PunishmentOptionRead(PunishmentOptionBase):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True


"""
枚举值 API - 返回所有固定的下拉选项，保持前后端一致
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List

from app.core.enums import (
    EducationStage,
    Gender,
    ProjectLevel,
    RewardType,
    TaskRating,
    TaskStatus,
    get_enum_label,
    get_enum_values,
)

router = APIRouter()


class EnumOption(BaseModel):
    """枚举选项"""
    label: str  # 显示文本
    value: str | int  # 值


class EnumsResponse(BaseModel):
    """枚举值响应"""
    task_status: List[EnumOption]  # 任务状态
    task_rating: List[EnumOption]  # 任务评分
    reward_type: List[EnumOption]  # 惩奖类型
    reward_points: List[EnumOption]  # 奖励积分选项
    gender: List[EnumOption]  # 性别
    education_stage: List[EnumOption]  # 教育阶段
    project_level: List[EnumOption]  # 项目层级


@router.get("/enums", response_model=EnumsResponse)
async def get_enums():
    """
    获取所有枚举值
    所有固定的下拉选项都从这里获取，保持前后端一致
    """
    return EnumsResponse(
        task_status=[
            EnumOption(
                label=get_enum_label("task_status", status.value),
                value=status.value
            )
            for status in TaskStatus
        ],
        task_rating=[
            EnumOption(
                label=get_enum_label("task_rating", rating.value),
                value=rating.value
            )
            for rating in TaskRating
        ],
        reward_type=[
            EnumOption(
                label=get_enum_label("reward_type", reward_type.value),
                value=reward_type.value
            )
            for reward_type in RewardType
        ],
        reward_points=[
            EnumOption(label="1积分", value=1),
            EnumOption(label="3积分", value=3),
            EnumOption(label="5积分", value=5),
            EnumOption(label="7积分", value=7),
            EnumOption(label="10积分", value=10),
        ],
        gender=[
            EnumOption(
                label=get_enum_label("gender", gender.value),
                value=gender.value
            )
            for gender in Gender
        ],
        education_stage=[
            EnumOption(
                label=get_enum_label("education_stage", stage.value),
                value=stage.value
            )
            for stage in EducationStage
        ],
        project_level=[
            EnumOption(
                label=get_enum_label("project_level", level.value),
                value=level.value
            )
            for level in ProjectLevel
        ],
    )


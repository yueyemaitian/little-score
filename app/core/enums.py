"""
统一的枚举定义
所有枚举值都在这里定义，确保前后端一致
"""
from enum import Enum
from typing import Dict, List, Tuple


class Gender(str, Enum):
    """性别枚举"""
    MALE = "male"
    FEMALE = "female"


class EducationStage(str, Enum):
    """教育阶段枚举"""
    PRIMARY = "primary"
    JUNIOR_HIGH = "junior_high"


class TaskStatus(str, Enum):
    """任务状态枚举"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELED = "canceled"


class TaskRating(str, Enum):
    """任务评分枚举"""
    A_STAR = "A*"
    A = "A"
    A_MINUS = "A-"
    B = "B"
    B_MINUS = "B-"
    C = "C"


class RewardType(str, Enum):
    """惩奖类型枚举"""
    NONE = "none"
    REWARD = "reward"
    PUNISH = "punish"


class ProjectLevel(int, Enum):
    """项目层级枚举"""
    LEVEL_1 = 1
    LEVEL_2 = 2


# 枚举值到标签的映射（用于错误提示）
# 使用字符串值作为键，因为 value 可能是 str 或 int
ENUM_LABELS: Dict[str, Dict[str | int, str]] = {
    "gender": {
        Gender.MALE.value: "男",
        Gender.FEMALE.value: "女",
    },
    "education_stage": {
        EducationStage.PRIMARY.value: "小学",
        EducationStage.JUNIOR_HIGH.value: "初中",
    },
    "task_status": {
        TaskStatus.NOT_STARTED.value: "未开始",
        TaskStatus.IN_PROGRESS.value: "进行中",
        TaskStatus.COMPLETED.value: "已完成",
        TaskStatus.CANCELED.value: "已取消",
    },
    "task_rating": {
        TaskRating.A_STAR.value: "A*",
        TaskRating.A.value: "A",
        TaskRating.A_MINUS.value: "A-",
        TaskRating.B.value: "B",
        TaskRating.B_MINUS.value: "B-",
        TaskRating.C.value: "C",
    },
    "reward_type": {
        RewardType.NONE.value: "无",
        RewardType.REWARD.value: "奖励",
        RewardType.PUNISH.value: "惩罚",
    },
    "project_level": {
        ProjectLevel.LEVEL_1.value: "一级项目",
        ProjectLevel.LEVEL_2.value: "二级项目",
    },
}


def get_enum_label(enum_type: str, value: str | int) -> str:
    """获取枚举值的标签"""
    labels = ENUM_LABELS.get(enum_type, {})
    return labels.get(value, str(value))


def get_enum_values(enum_type: str) -> List[str | int]:
    """获取枚举类型的所有值"""
    if enum_type == "gender":
        return [e.value for e in Gender]
    elif enum_type == "education_stage":
        return [e.value for e in EducationStage]
    elif enum_type == "task_status":
        return [e.value for e in TaskStatus]
    elif enum_type == "task_rating":
        return [e.value for e in TaskRating]
    elif enum_type == "reward_type":
        return [e.value for e in RewardType]
    elif enum_type == "project_level":
        return [e.value for e in ProjectLevel]
    return []


def get_enum_labels(enum_type: str) -> List[str]:
    """获取枚举类型的所有标签"""
    labels = ENUM_LABELS.get(enum_type, {})
    return [labels.get(value, str(value)) for value in get_enum_values(enum_type)]


def format_enum_error(enum_type: str, valid_values: List[str | int]) -> str:
    """格式化枚举错误提示，使用标签而不是值"""
    labels = ENUM_LABELS.get(enum_type, {})
    valid_labels = [labels.get(v, str(v)) for v in valid_values]
    return f"必须是以下之一: {', '.join(valid_labels)}"


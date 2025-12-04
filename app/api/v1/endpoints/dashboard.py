from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user
from app.db.session import get_db
from app.models.student import Student
from app.models.task_and_score import Task
from app.models.user import User
from app.schemas.student import StudentRead
from pydantic import BaseModel

router = APIRouter()


class TaskRatingSummary(BaseModel):
    """任务评分汇总"""
    project_level1_id: int
    project_level1_name: str
    ratings: dict[str, int]  # {"A*": 3, "A": 2, "B": 1}


class StudentDashboard(BaseModel):
    """学生首页数据"""
    student: StudentRead
    score_summary: dict[str, int]  # {"available_points": 100, "exchanged_points": 20}
    task_rating_summary: list[TaskRatingSummary]  # 最近1个月的任务评分汇总


class DashboardResponse(BaseModel):
    """首页响应"""
    students: list[StudentDashboard]


@router.get("/", response_model=DashboardResponse)
async def get_dashboard(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取首页数据：学生列表、积分汇总、最近1个月任务评分汇总"""
    # 1. 获取所有学生
    from app.crud import student as student_crud

    students = await student_crud.get_students_by_user(db, current_user.id)

    # 2. 获取每个学生的积分汇总和任务评分
    from app.crud import score as score_crud
    from app.crud import project as project_crud

    student_dashboards = []
    one_month_ago = datetime.now(timezone.utc) - timedelta(days=30)

    for student in students:
        # 积分汇总
        score_summary = await score_crud.get_score_summary(db, student.id)

        # 任务评分汇总（最近1个月，已完成的任务）
        # 按一级项目分组统计评分
        task_query = (
            select(
                Task.project_level1_id,
                Task.rating,
                func.count(Task.id).label("count"),
            )
            .where(
                Task.student_id == student.id,
                Task.status == "completed",
                Task.rating.isnot(None),
                Task.updated_at >= one_month_ago,
            )
            .group_by(Task.project_level1_id, Task.rating)
        )

        result = await db.execute(task_query)
        task_stats = result.all()

        # 按一级项目分组
        project_ratings: dict[int, dict[str, int]] = {}
        project_ids = set()

        for stat in task_stats:
            project_id = stat.project_level1_id
            rating = stat.rating
            count = stat.count

            if project_id not in project_ratings:
                project_ratings[project_id] = {}
            project_ratings[project_id][rating] = count
            project_ids.add(project_id)

        # 获取项目名称
        task_rating_summary = []
        for project_id in project_ids:
            project = await project_crud.get_project_by_id(db, project_id, current_user.id)
            if project:
                task_rating_summary.append(
                    TaskRatingSummary(
                        project_level1_id=project_id,
                        project_level1_name=project.name,
                        ratings=project_ratings.get(project_id, {}),
                    )
                )

        student_dashboards.append(
            StudentDashboard(
                student=StudentRead.model_validate(student),
                score_summary=score_summary,
                task_rating_summary=task_rating_summary,
            )
        )

    return DashboardResponse(students=student_dashboards)


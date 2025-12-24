from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.models.task_and_score import PunishmentOption, Task, TaskStatus
from app.schemas.task import TaskCreate, TaskUpdate


async def get_tasks(
    db: AsyncSession,
    student_id: int,
    project_level1_id: int | None = None,
    project_level2_id: int | None = None,
    status: list[str] | str | None = None,
    include_all_status: bool = False,
    completed_after: datetime | None = None,
) -> list[Task]:
    """获取任务列表（默认只返回未开始和进行中的，排除已删除的）"""
    query = select(Task).where(
        Task.student_id == student_id,
        Task.is_deleted == False
    )

    if project_level1_id is not None:
        query = query.where(Task.project_level1_id == project_level1_id)
    if project_level2_id is not None:
        query = query.where(Task.project_level2_id == project_level2_id)
    # 完成时间过滤：如果指定了 completed_after，只返回在该时间之后完成的任务
    # 注意：completed_after 过滤会覆盖默认的状态过滤
    if completed_after is not None:
        query = query.where(
            Task.status == TaskStatus.COMPLETED,
            Task.updated_at >= completed_after
        )
    elif status is not None:
        # 支持多个状态筛选
        if isinstance(status, list):
            if len(status) > 0:
                query = query.where(Task.status.in_(status))
        else:
            # 兼容单个状态（字符串）
            query = query.where(Task.status == status)
    elif not include_all_status:
        # 默认只显示未开始和进行中的
        query = query.where(Task.status.in_([TaskStatus.NOT_STARTED, TaskStatus.IN_PROGRESS]))

    result = await db.execute(query.order_by(Task.created_at.desc()))
    tasks = list(result.scalars().all())

    if not tasks:
        return tasks

    project_ids: set[int] = set()
    for task in tasks:
        project_ids.add(task.project_level1_id)
        if task.project_level2_id:
            project_ids.add(task.project_level2_id)

    if project_ids:
        project_result = await db.execute(
            select(Project.id, Project.name).where(Project.id.in_(project_ids))
        )
        project_map = {row.id: row.name for row in project_result.all()}
        for task in tasks:
            setattr(task, "project_level1_name", project_map.get(task.project_level1_id))
            setattr(task, "project_level2_name", project_map.get(task.project_level2_id))

    return tasks


async def get_task_by_id(db: AsyncSession, task_id: int, student_id: int) -> Task | None:
    """根据ID获取任务（确保属于指定学生且未删除）"""
    result = await db.execute(select(Task).where(
        Task.id == task_id,
        Task.student_id == student_id,
        Task.is_deleted == False
    ))
    return result.scalar_one_or_none()


async def create_task(db: AsyncSession, task: TaskCreate) -> Task:
    """创建任务"""
    db_task = Task(**task.model_dump())
    db.add(db_task)
    
    # 如果直接创建已完成的任务，处理奖励和惩罚逻辑
    if db_task.status == TaskStatus.COMPLETED:
        await db.flush() # 确保 task.id 已生成
        await _handle_task_completion(db, db_task)
    
    await db.commit()
    await db.refresh(db_task)
    return db_task


async def update_task(db: AsyncSession, task_id: int, task_update: TaskUpdate, student_id: int) -> Task | None:
    """更新任务（只有未开始和进行中的可以修改）"""
    db_task = await get_task_by_id(db, task_id, student_id)
    if not db_task:
        return None

    # 只有未开始和进行中的任务可以修改
    if db_task.status not in [TaskStatus.NOT_STARTED, TaskStatus.IN_PROGRESS]:
        return None

    update_data = task_update.model_dump(exclude_unset=True)
    old_status = db_task.status

    for field, value in update_data.items():
        setattr(db_task, field, value)

    # 如果状态变为已完成，处理奖励和惩罚逻辑
    if update_data.get("status") == TaskStatus.COMPLETED and old_status != TaskStatus.COMPLETED:
        await _handle_task_completion(db, db_task)

    await db.commit()
    await db.refresh(db_task)
    return db_task


async def _handle_task_completion(db: AsyncSession, task: Task) -> None:
    """处理任务完成时的逻辑：生成积分记录和惩罚任务"""
    from app.models.task_and_score import ScoreIncrease
    from app.models.task_and_score import Task as TaskModel

    # 1. 如果奖励积分 > 0，生成积分增加记录
    if task.reward_type == "reward" and task.reward_points and task.reward_points > 0:
        score_increase = ScoreIncrease(
            student_id=task.student_id,
            task_id=task.id,
            project_level1_id=task.project_level1_id,
            project_level2_id=task.project_level2_id,
            points=task.reward_points,
        )
        db.add(score_increase)

    # 2. 如果是惩罚且需要生成关联任务
    if task.reward_type == "punish" and task.punishment_option_id:
        punishment_option = await db.get(PunishmentOption, task.punishment_option_id)
        # 如果惩罚选项已被删除，跳过生成关联任务
        if punishment_option and punishment_option.generate_related_task:
            if punishment_option.related_project_level1_id:
                punishment_task = TaskModel(
                    student_id=task.student_id,
                    project_level1_id=punishment_option.related_project_level1_id,
                    project_level2_id=punishment_option.related_project_level2_id,
                    status=TaskStatus.NOT_STARTED,
                    reward_type="none",
                )
                db.add(punishment_task)

    await db.flush()  # 先 flush，让上面的操作生效，但不 commit（由调用者 commit）


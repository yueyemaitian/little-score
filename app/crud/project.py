from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.models.task_and_score import Task, ScoreIncrease
from app.schemas.project import ProjectCreate, ProjectUpdate


async def get_projects_by_user(
    db: AsyncSession, user_id: int, level: int | None = None, parent_id: int | None = None
) -> list[Project]:
    """获取用户的项目列表"""
    query = select(Project).where(Project.user_id == user_id)
    if level is not None:
        query = query.where(Project.level == level)
    if parent_id is not None:
        query = query.where(Project.parent_id == parent_id)
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_project_by_id(db: AsyncSession, project_id: int, user_id: int) -> Project | None:
    """根据ID获取项目（确保属于当前用户）"""
    result = await db.execute(select(Project).where(Project.id == project_id, Project.user_id == user_id))
    return result.scalar_one_or_none()


async def create_project(db: AsyncSession, project: ProjectCreate, user_id: int) -> Project:
    """创建项目"""
    db_project = Project(**project.model_dump(), user_id=user_id)
    db.add(db_project)
    await db.commit()
    await db.refresh(db_project)
    return db_project


async def update_project(db: AsyncSession, project_id: int, project_update: ProjectUpdate, user_id: int) -> Project | None:
    """更新项目"""
    db_project = await get_project_by_id(db, project_id, user_id)
    if not db_project:
        return None

    update_data = project_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_project, field, value)

    await db.commit()
    await db.refresh(db_project)
    return db_project


async def delete_project(db: AsyncSession, project_id: int, user_id: int) -> bool:
    """删除项目"""
    db_project = await get_project_by_id(db, project_id, user_id)
    if not db_project:
        return False

    # 检查是否有任务引用该项目
    task_query = select(Task).where(
        (Task.project_level1_id == project_id) | (Task.project_level2_id == project_id)
    )
    task_result = await db.execute(task_query)
    tasks = task_result.scalars().all()
    
    # 检查是否有积分记录引用该项目
    score_query = select(ScoreIncrease).where(
        (ScoreIncrease.project_level1_id == project_id) | (ScoreIncrease.project_level2_id == project_id)
    )
    score_result = await db.execute(score_query)
    scores = score_result.scalars().all()
    
    # 如果有引用，抛出异常
    if tasks or scores:
        from fastapi import HTTPException
        ref_count = len(tasks) + len(scores)
        raise HTTPException(
            status_code=400,
            detail=f"无法删除项目：该项目已被 {ref_count} 条记录引用（任务或积分记录），请先删除相关记录"
        )
    
    # 检查是否有子项目（二级项目）
    if db_project.level == 1:
        children_query = select(Project).where(Project.parent_id == project_id)
        children_result = await db.execute(children_query)
        children = children_result.scalars().all()
        if children:
            raise HTTPException(
                status_code=400,
                detail=f"无法删除项目：该项目下有 {len(children)} 个子项目，请先删除子项目"
            )

    await db.delete(db_project)
    await db.commit()
    return True


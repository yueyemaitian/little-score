from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
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

    await db.delete(db_project)
    await db.commit()
    return True


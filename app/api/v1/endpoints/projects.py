from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user
from app.crud import project as crud
from app.db.session import get_db
from app.models.user import User
from app.schemas.project import ProjectCreate, ProjectRead, ProjectUpdate

router = APIRouter()


@router.get("/", response_model=list[ProjectRead])
async def get_projects(
    level: Annotated[int | None, Query(description="层级：1=一级，2=二级")] = None,
    parent_id: Annotated[int | None, Query(description="父项目ID")] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取项目列表"""
    projects = await crud.get_projects_by_user(db, current_user.id, level=level, parent_id=parent_id)
    return projects


@router.post("/", response_model=ProjectRead, status_code=201)
async def create_project(
    project: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """创建项目"""
    # 验证层级和父项目
    if project.level == 2 and not project.parent_id:
        raise HTTPException(status_code=400, detail="二级项目必须指定父项目ID")
    if project.level == 1 and project.parent_id:
        raise HTTPException(status_code=400, detail="一级项目不能有父项目")

    # 如果指定了父项目，验证父项目存在且属于当前用户
    if project.parent_id:
        parent = await crud.get_project_by_id(db, project.parent_id, current_user.id)
        if not parent:
            raise HTTPException(status_code=404, detail="父项目不存在")
        if parent.level != 1:
            raise HTTPException(status_code=400, detail="父项目必须是一级项目")

    return await crud.create_project(db, project, current_user.id)


@router.put("/{project_id}", response_model=ProjectRead)
async def update_project(
    project_id: int,
    project_update: ProjectUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """更新项目"""
    project = await crud.update_project(db, project_id, project_update, current_user.id)
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    return project


@router.delete("/{project_id}", status_code=204)
async def delete_project(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """删除项目"""
    success = await crud.delete_project(db, project_id, current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="项目不存在")


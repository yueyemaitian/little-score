from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user
from app.crud import task as crud
from app.db.session import get_db
from app.models.user import User
from app.schemas.task import TaskCreate, TaskRead, TaskUpdate

router = APIRouter()


@router.get("/", response_model=list[TaskRead])
async def get_tasks(
    student_id: Annotated[int, Query(description="学生ID")],
    project_level1_id: Annotated[int | None, Query(description="一级项目ID")] = None,
    project_level2_id: Annotated[int | None, Query(description="二级项目ID")] = None,
    status: Annotated[str | None, Query(description="状态")] = None,
    include_all_status: Annotated[bool, Query(description="是否包含所有状态", example=False)] = False,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取任务列表（默认只返回未开始和进行中的）"""
    # 验证学生属于当前用户
    from app.crud import student as student_crud

    student = await student_crud.get_student_by_id(db, student_id, current_user.id)
    if not student:
        raise HTTPException(status_code=404, detail="学生不存在")

    tasks = await crud.get_tasks(
        db,
        student_id,
        project_level1_id=project_level1_id,
        project_level2_id=project_level2_id,
        status=status,
        include_all_status=include_all_status,
    )
    return tasks


@router.post("/", response_model=TaskRead, status_code=201)
async def create_task(
    task: TaskCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """创建任务"""
    # 验证学生属于当前用户
    from app.crud import student as student_crud

    student = await student_crud.get_student_by_id(db, task.student_id, current_user.id)
    if not student:
        raise HTTPException(status_code=404, detail="学生不存在")

    # 验证项目属于当前用户
    from app.crud import project as project_crud

    project1 = await project_crud.get_project_by_id(db, task.project_level1_id, current_user.id)
    if not project1:
        raise HTTPException(status_code=404, detail="一级项目不存在")

    if task.project_level2_id:
        project2 = await project_crud.get_project_by_id(db, task.project_level2_id, current_user.id)
        if not project2:
            raise HTTPException(status_code=404, detail="二级项目不存在")
        if project2.parent_id != task.project_level1_id:
            raise HTTPException(status_code=400, detail="二级项目不属于指定的一级项目")

    # 验证状态和评分
    if task.status == "completed" and not task.rating:
        raise HTTPException(status_code=400, detail="已完成的任务必须提供评分")

    # 验证惩奖逻辑
    if task.reward_type == "reward" and (not task.reward_points or task.reward_points <= 0):
        raise HTTPException(status_code=400, detail="奖励类型必须提供大于0的积分")
    if task.reward_type == "punish" and not task.punishment_option_id:
        raise HTTPException(status_code=400, detail="惩罚类型必须提供惩罚选项ID")

    return await crud.create_task(db, task)


@router.put("/{task_id}", response_model=TaskRead)
async def update_task(
    task_id: int,
    task_update: TaskUpdate,
    student_id: Annotated[int, Query(description="学生ID")],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """更新任务（只有未开始和进行中的可以修改）"""
    # 验证学生属于当前用户
    from app.crud import student as student_crud

    student = await student_crud.get_student_by_id(db, student_id, current_user.id)
    if not student:
        raise HTTPException(status_code=404, detail="学生不存在")

    # 验证项目（如果更新了项目）
    if task_update.project_level1_id:
        from app.crud import project as project_crud

        project1 = await project_crud.get_project_by_id(db, task_update.project_level1_id, current_user.id)
        if not project1:
            raise HTTPException(status_code=404, detail="一级项目不存在")

    # 验证状态和评分
    if task_update.status == "completed" and not task_update.rating:
        # 检查原任务是否有评分
        task = await crud.get_task_by_id(db, task_id, student_id)
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        if not task.rating and not task_update.rating:
            raise HTTPException(status_code=400, detail="已完成的任务必须提供评分")

    task = await crud.update_task(db, task_id, task_update, student_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在或不可修改")
    return task


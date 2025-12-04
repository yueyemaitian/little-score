from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user
from app.crud import score as crud
from app.db.session import get_db
from app.models.user import User
from app.schemas.score import (
    PunishmentOptionCreate,
    PunishmentOptionRead,
    PunishmentOptionUpdate,
    RewardExchangeOptionCreate,
    RewardExchangeOptionRead,
    RewardExchangeOptionUpdate,
    ScoreExchangeCreate,
    ScoreExchangeRead,
    ScoreIncreaseRead,
    ScoreSummary,
)

router = APIRouter()


@router.get("/summary", response_model=ScoreSummary)
async def get_score_summary(
    student_id: Annotated[int, Query(description="学生ID")],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取积分汇总"""
    # 验证学生属于当前用户
    from app.crud import student as student_crud

    student = await student_crud.get_student_by_id(db, student_id, current_user.id)
    if not student:
        raise HTTPException(status_code=404, detail="学生不存在")

    summary = await crud.get_score_summary(db, student_id)
    return ScoreSummary(**summary)


@router.get("/increases", response_model=list[ScoreIncreaseRead])
async def get_score_increases(
    student_id: Annotated[int, Query(description="学生ID")],
    limit: Annotated[int, Query(description="限制数量", ge=1, le=100)] = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取积分增加记录"""
    # 验证学生属于当前用户
    from app.crud import student as student_crud

    student = await student_crud.get_student_by_id(db, student_id, current_user.id)
    if not student:
        raise HTTPException(status_code=404, detail="学生不存在")

    increases = await crud.get_score_increases(db, student_id, limit=limit)
    return increases


@router.get("/exchanges", response_model=list[ScoreExchangeRead])
async def get_score_exchanges(
    student_id: Annotated[int, Query(description="学生ID")],
    limit: Annotated[int, Query(description="限制数量", ge=1, le=100)] = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取积分兑换记录"""
    # 验证学生属于当前用户
    from app.crud import student as student_crud

    student = await student_crud.get_student_by_id(db, student_id, current_user.id)
    if not student:
        raise HTTPException(status_code=404, detail="学生不存在")

    exchanges = await crud.get_score_exchanges(db, student_id, limit=limit)
    return exchanges


@router.post("/exchanges", response_model=ScoreExchangeRead, status_code=201)
async def create_score_exchange(
    exchange: ScoreExchangeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """创建积分兑换记录"""
    # 验证学生属于当前用户
    from app.crud import student as student_crud

    student = await student_crud.get_student_by_id(db, exchange.student_id, current_user.id)
    if not student:
        raise HTTPException(status_code=404, detail="学生不存在")

    # 验证奖励选项属于当前用户
    reward_option = await crud.get_reward_exchange_option_by_id(db, exchange.reward_option_id, current_user.id)
    if not reward_option:
        raise HTTPException(status_code=404, detail="奖励选项不存在")

    try:
        return await crud.create_score_exchange(db, exchange, exchange.student_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# 兑换奖励选项管理
@router.get("/reward-options", response_model=list[RewardExchangeOptionRead])
async def get_reward_exchange_options(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取兑换奖励选项列表"""
    options = await crud.get_reward_exchange_options(db, current_user.id)
    return options


@router.post("/reward-options", response_model=RewardExchangeOptionRead, status_code=201)
async def create_reward_exchange_option(
    option: RewardExchangeOptionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """创建兑换奖励选项"""
    return await crud.create_reward_exchange_option(db, option, current_user.id)


@router.put("/reward-options/{option_id}", response_model=RewardExchangeOptionRead)
async def update_reward_exchange_option(
    option_id: int,
    option_update: RewardExchangeOptionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """更新兑换奖励选项"""
    option = await crud.update_reward_exchange_option(db, option_id, option_update, current_user.id)
    if not option:
        raise HTTPException(status_code=404, detail="奖励选项不存在")
    return option


@router.delete("/reward-options/{option_id}", status_code=204)
async def delete_reward_exchange_option(
    option_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """删除兑换奖励选项"""
    success = await crud.delete_reward_exchange_option(db, option_id, current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="奖励选项不存在")


# 惩罚选项管理
@router.get("/punishment-options", response_model=list[PunishmentOptionRead])
async def get_punishment_options(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取惩罚选项列表"""
    options = await crud.get_punishment_options(db, current_user.id)
    return options


@router.post("/punishment-options", response_model=PunishmentOptionRead, status_code=201)
async def create_punishment_option(
    option: PunishmentOptionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """创建惩罚选项"""
    # 如果生成关联任务，验证项目
    if option.generate_related_task:
        if not option.related_project_level1_id:
            raise HTTPException(status_code=400, detail="生成关联任务时必须指定一级项目")
        from app.crud import project as project_crud

        project1 = await project_crud.get_project_by_id(db, option.related_project_level1_id, current_user.id)
        if not project1:
            raise HTTPException(status_code=404, detail="一级项目不存在")

    option_data = option.model_dump()
    return await crud.create_punishment_option(db, option_data, current_user.id)


@router.put("/punishment-options/{option_id}", response_model=PunishmentOptionRead)
async def update_punishment_option(
    option_id: int,
    option_update: PunishmentOptionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """更新惩罚选项"""
    option_data = option_update.model_dump(exclude_unset=True)
    option = await crud.update_punishment_option(db, option_id, option_data, current_user.id)
    if not option:
        raise HTTPException(status_code=404, detail="惩罚选项不存在")
    return option


@router.delete("/punishment-options/{option_id}", status_code=204)
async def delete_punishment_option(
    option_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """删除惩罚选项"""
    success = await crud.delete_punishment_option(db, option_id, current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="惩罚选项不存在")


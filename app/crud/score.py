from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task_and_score import (
    PunishmentOption,
    RewardExchangeOption,
    ScoreExchange,
    ScoreIncrease,
)
from app.schemas.score import RewardExchangeOptionCreate, RewardExchangeOptionUpdate, ScoreExchangeCreate


async def get_score_summary(db: AsyncSession, student_id: int) -> dict[str, int]:
    """获取积分汇总（排除已删除的记录）"""
    # 计算可用积分（总增加 - 总兑换）
    increase_result = await db.execute(
        select(func.sum(ScoreIncrease.points)).where(
            ScoreIncrease.student_id == student_id,
            ScoreIncrease.is_deleted == False
        )
    )
    total_increase = increase_result.scalar() or 0

    exchange_result = await db.execute(
        select(func.sum(ScoreExchange.cost_points)).where(
            ScoreExchange.student_id == student_id,
            ScoreExchange.is_deleted == False
        )
    )
    total_exchange = exchange_result.scalar() or 0

    return {
        "available_points": total_increase - total_exchange,
        "exchanged_points": total_exchange,
    }


async def get_score_increases(
    db: AsyncSession, student_id: int, limit: int = 100
) -> list[ScoreIncrease]:
    """获取积分增加记录（排除已删除的）"""
    result = await db.execute(
        select(ScoreIncrease)
        .where(
            ScoreIncrease.student_id == student_id,
            ScoreIncrease.is_deleted == False
        )
        .order_by(ScoreIncrease.created_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())


async def get_reward_exchange_options(db: AsyncSession, user_id: int) -> list[RewardExchangeOption]:
    """获取用户的奖励选项"""
    result = await db.execute(
        select(RewardExchangeOption)
        .where(RewardExchangeOption.user_id == user_id)
        .order_by(RewardExchangeOption.cost_points.asc())
    )
    return list(result.scalars().all())


async def get_reward_exchange_option_by_id(
    db: AsyncSession, option_id: int, user_id: int
) -> RewardExchangeOption | None:
    """根据ID获取奖励选项（确保属于当前用户）"""
    result = await db.execute(
        select(RewardExchangeOption).where(
            RewardExchangeOption.id == option_id, RewardExchangeOption.user_id == user_id
        )
    )
    return result.scalar_one_or_none()


async def create_reward_exchange_option(
    db: AsyncSession, option: RewardExchangeOptionCreate, user_id: int
) -> RewardExchangeOption:
    """创建奖励选项"""
    db_option = RewardExchangeOption(**option.model_dump(), user_id=user_id)
    db.add(db_option)
    await db.commit()
    await db.refresh(db_option)
    return db_option


async def update_reward_exchange_option(
    db: AsyncSession, option_id: int, option_update: RewardExchangeOptionUpdate, user_id: int
) -> RewardExchangeOption | None:
    """更新奖励选项"""
    db_option = await get_reward_exchange_option_by_id(db, option_id, user_id)
    if not db_option:
        return None

    update_data = option_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_option, field, value)

    await db.commit()
    await db.refresh(db_option)
    return db_option


async def delete_reward_exchange_option(db: AsyncSession, option_id: int, user_id: int) -> bool:
    """删除奖励选项"""
    db_option = await get_reward_exchange_option_by_id(db, option_id, user_id)
    if not db_option:
        return False

    # 检查是否有兑换记录引用该奖励选项
    from sqlalchemy import select
    from app.models.task_and_score import ScoreExchange
    
    exchange_query = select(ScoreExchange).where(ScoreExchange.reward_option_id == option_id)
    exchange_result = await db.execute(exchange_query)
    exchanges = exchange_result.scalars().all()
    
    # 如果有引用，抛出异常
    if exchanges:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=400,
            detail=f"无法删除奖励选项：该选项已被 {len(exchanges)} 条兑换记录引用，请先删除相关兑换记录"
        )

    await db.delete(db_option)
    await db.commit()
    return True


async def get_score_exchanges(db: AsyncSession, student_id: int, limit: int = 100) -> list[ScoreExchange]:
    """获取积分兑换记录（排除已删除的）"""
    result = await db.execute(
        select(ScoreExchange)
        .where(
            ScoreExchange.student_id == student_id,
            ScoreExchange.is_deleted == False
        )
        .order_by(ScoreExchange.created_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())


async def create_score_exchange(
    db: AsyncSession, exchange: ScoreExchangeCreate, student_id: int
) -> ScoreExchange:
    """创建积分兑换记录（需要校验可用积分）"""
    # 获取奖励选项
    reward_option = await db.get(RewardExchangeOption, exchange.reward_option_id)
    if not reward_option:
        raise ValueError("奖励选项不存在")

    # 检查可用积分
    summary = await get_score_summary(db, student_id)
    if summary["available_points"] < reward_option.cost_points:
        raise ValueError("可用积分不足")

    # 创建兑换记录
    db_exchange = ScoreExchange(
        student_id=student_id,
        reward_option_id=exchange.reward_option_id,
        cost_points=reward_option.cost_points,
    )
    db.add(db_exchange)
    await db.commit()
    await db.refresh(db_exchange)
    return db_exchange


async def get_punishment_options(db: AsyncSession, user_id: int) -> list[PunishmentOption]:
    """获取用户的惩罚选项"""
    result = await db.execute(
        select(PunishmentOption)
        .where(PunishmentOption.user_id == user_id)
        .order_by(PunishmentOption.created_at.desc())
    )
    return list(result.scalars().all())


async def get_punishment_option_by_id(
    db: AsyncSession, option_id: int, user_id: int
) -> PunishmentOption | None:
    """根据ID获取惩罚选项（确保属于当前用户）"""
    result = await db.execute(
        select(PunishmentOption).where(
            PunishmentOption.id == option_id, PunishmentOption.user_id == user_id
        )
    )
    return result.scalar_one_or_none()


async def create_punishment_option(
    db: AsyncSession, option_data: dict, user_id: int
) -> PunishmentOption:
    """创建惩罚选项"""
    db_option = PunishmentOption(**option_data, user_id=user_id)
    db.add(db_option)
    await db.commit()
    await db.refresh(db_option)
    return db_option


async def update_punishment_option(
    db: AsyncSession, option_id: int, option_update: dict, user_id: int
) -> PunishmentOption | None:
    """更新惩罚选项"""
    db_option = await get_punishment_option_by_id(db, option_id, user_id)
    if not db_option:
        return None

    for field, value in option_update.items():
        setattr(db_option, field, value)

    await db.commit()
    await db.refresh(db_option)
    return db_option


async def delete_punishment_option(db: AsyncSession, option_id: int, user_id: int) -> bool:
    """删除惩罚选项"""
    db_option = await get_punishment_option_by_id(db, option_id, user_id)
    if not db_option:
        return False

    # 检查是否有任务引用该惩罚选项
    from sqlalchemy import select
    from app.models.task_and_score import Task
    
    task_query = select(Task).where(Task.punishment_option_id == option_id)
    task_result = await db.execute(task_query)
    tasks = task_result.scalars().all()
    
    # 如果有引用，抛出异常
    if tasks:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=400,
            detail=f"无法删除惩罚选项：该选项已被 {len(tasks)} 条任务记录引用，请先删除相关任务"
        )

    await db.delete(db_option)
    await db.commit()
    return True


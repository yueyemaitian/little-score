from datetime import date, datetime, UTC
from typing import List

from sqlalchemy import Select, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.student import Student
from app.models.task_and_score import Task, ScoreIncrease, ScoreExchange
from app.schemas.student import StudentCreate, StudentUpdate


async def get_students_by_user(db: AsyncSession, user_id: int) -> List[Student]:
    """获取用户的所有学生（排除已删除的）"""
    stmt: Select[tuple[Student]] = select(Student).where(
        Student.user_id == user_id,
        Student.is_deleted == False
    ).order_by(Student.id)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_student_by_id(db: AsyncSession, student_id: int, user_id: int) -> Student | None:
    """根据ID获取学生（确保属于当前用户且未删除）"""
    result = await db.execute(select(Student).where(
        Student.id == student_id,
        Student.user_id == user_id,
        Student.is_deleted == False
    ))
    return result.scalar_one_or_none()


async def get_duplicate_student(
    db: AsyncSession,
    user_id: int,
    name: str,
    birthday: date | None,
    gender: str | None,
    exclude_id: int | None = None,
) -> Student | None:
    """检查是否存在重复的学生（姓名、出生年月、性别相同，排除已删除的）"""
    stmt = select(Student).where(
        Student.user_id == user_id,
        Student.name == name,
        Student.is_deleted == False,
    )
    if birthday:
        stmt = stmt.where(Student.birthday == birthday)
    if gender:
        stmt = stmt.where(Student.gender == gender)
    if exclude_id:
        stmt = stmt.where(Student.id != exclude_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def create_student(db: AsyncSession, user_id: int, obj_in: StudentCreate) -> Student:
    # 检查是否存在重复的学生
    duplicate = await get_duplicate_student(
        db,
        user_id,
        obj_in.name,
        obj_in.birthday,
        obj_in.gender,
    )
    if duplicate:
        raise ValueError("已存在相同姓名、出生年月和性别的学生")
    
    db_obj = Student(
        user_id=user_id,
        **obj_in.model_dump(),
    )
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj


async def update_student(db: AsyncSession, db_obj: Student, obj_in: StudentUpdate) -> Student:
    # 检查是否存在重复的学生（排除当前学生）
    update_data = obj_in.model_dump(exclude_unset=True)
    name = update_data.get("name", db_obj.name)
    birthday = update_data.get("birthday", db_obj.birthday)
    gender = update_data.get("gender", db_obj.gender)
    
    duplicate = await get_duplicate_student(
        db,
        db_obj.user_id,
        name,
        birthday,
        gender,
        exclude_id=db_obj.id,
    )
    if duplicate:
        raise ValueError("已存在相同姓名、出生年月和性别的学生")
    
    for field, value in update_data.items():
        setattr(db_obj, field, value)
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj


async def delete_student(db: AsyncSession, student_id: int, user_id: int) -> None:
    """
    逻辑删除学生及其所有相关记录
    包括：任务、积分增加记录、积分兑换记录
    """
    # 检查学生是否存在且属于当前用户
    student = await get_student_by_id(db, student_id, user_id)
    if not student:
        raise ValueError("学生不存在")
    
    now = datetime.now(UTC)
    
    # 逻辑删除学生
    student.is_deleted = True
    student.deleted_at = now
    
    # 逻辑删除所有相关任务
    await db.execute(
        update(Task)
        .where(Task.student_id == student_id)
        .values(is_deleted=True, deleted_at=now)
    )
    
    # 逻辑删除所有积分增加记录
    await db.execute(
        update(ScoreIncrease)
        .where(ScoreIncrease.student_id == student_id)
        .values(is_deleted=True, deleted_at=now)
    )
    
    # 逻辑删除所有积分兑换记录
    await db.execute(
        update(ScoreExchange)
        .where(ScoreExchange.student_id == student_id)
        .values(is_deleted=True, deleted_at=now)
    )
    
    await db.commit()



from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user
from app.crud.student import create_student, delete_student, get_students_by_user, update_student
from app.db.session import get_db
from app.models.student import Student
from app.models.user import User
from app.schemas.student import StudentCreate, StudentRead, StudentUpdate

router = APIRouter()


@router.get("/", response_model=List[StudentRead])
async def list_my_students(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[StudentRead]:
    students = await get_students_by_user(db, current_user.id)
    return [StudentRead.model_validate(s) for s in students]


@router.post("/", response_model=StudentRead, status_code=status.HTTP_201_CREATED)
async def create_my_student(
    student_in: StudentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> StudentRead:
    try:
        student = await create_student(db, current_user.id, student_in)
        return StudentRead.model_validate(student)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.put("/{student_id}", response_model=StudentRead)
async def update_my_student(
    student_id: int,
    student_in: StudentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> StudentRead:
    student = await db.get(Student, student_id)
    if not student or student.user_id != current_user.id or student.is_deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="学生不存在")
    try:
        student = await update_student(db, student, student_in)
        return StudentRead.model_validate(student)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.delete("/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_my_student(
    student_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> None:
    """删除学生（逻辑删除学生及其所有相关记录）"""
    try:
        await delete_student(db, student_id, current_user.id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )



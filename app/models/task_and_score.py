from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.utils.time import utcnow


class PunishmentOption(Base):
    __tablename__ = "punishment_options"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    generate_related_task: Mapped[bool] = mapped_column(default=False, nullable=False)
    related_project_level1_id: Mapped[int | None] = mapped_column(
        ForeignKey("projects.id", ondelete="SET NULL"),
        nullable=True,
    )
    related_project_level2_id: Mapped[int | None] = mapped_column(
        ForeignKey("projects.id", ondelete="SET NULL"),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        nullable=False,
    )


class TaskStatus(str):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELED = "canceled"


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)

    project_level1_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False)
    project_level2_id: Mapped[int | None] = mapped_column(ForeignKey("projects.id"), nullable=True)

    status: Mapped[str] = mapped_column(String(32), default=TaskStatus.NOT_STARTED, nullable=False)
    rating: Mapped[str | None] = mapped_column(String(8), nullable=True)  # A*, A, A-, B, B-, C

    reward_type: Mapped[str] = mapped_column(
        String(16),
        default="none",  # reward / punish / none
        nullable=False,
    )
    reward_points: Mapped[int | None] = mapped_column(Integer, nullable=True)
    punishment_option_id: Mapped[int | None] = mapped_column(
        ForeignKey("punishment_options.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    # 逻辑删除标记
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        onupdate=utcnow,
        nullable=False,
    )


class ScoreIncrease(Base):
    __tablename__ = "score_increases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)

    project_level1_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False)
    project_level2_id: Mapped[int | None] = mapped_column(ForeignKey("projects.id"), nullable=True)

    points: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # 逻辑删除标记
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        nullable=False,
    )


class RewardExchangeOption(Base):
    __tablename__ = "reward_exchange_options"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    cost_points: Mapped[int] = mapped_column(Integer, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        nullable=False,
    )


class ScoreExchange(Base):
    __tablename__ = "score_exchanges"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    reward_option_id: Mapped[int] = mapped_column(
        ForeignKey("reward_exchange_options.id", ondelete="RESTRICT"),
        nullable=False,
    )

    cost_points: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # 逻辑删除标记
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        nullable=False,
    )



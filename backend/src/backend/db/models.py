import uuid
import datetime
import enum
from typing import Optional, List
from sqlalchemy import text
from sqlalchemy import Index, UniqueConstraint
from sqlalchemy import ForeignKey
from sqlalchemy import String
from sqlalchemy import DateTime
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, ENUM

from backend.db.base import Base


class TrainingLevel(enum.Enum):
    beginner = "beginner"
    intermediate = "intermediate"
    advanced = "advanced"

class WorkoutStatus(enum.Enum):
    in_progress = "in_progress"
    completed = "completed"
    abandoned = "abandoned"
    synced = "synced"

class WorkoutStepStatus(enum.Enum):
    pending = "pending"
    completed = "completed"
    skipped = "skipped"

class SectionType(enum.Enum):
    warmup = "warmup"
    main = "main"
    cooldown = "cooldown"

class SwimmingStyle(enum.Enum):
    freestyle = "freestyle"
    backstroke = "backstroke"
    breaststroke = "breaststroke"
    butterfly = "butterfly"
    mixed = "mixed"

class UserRole(enum.Enum):
    user = "user"
    admin = "admin"


class User(Base):
    __tablename__ = "users"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True,
        server_default=text("gen_random_uuid()")
    )
    email: Mapped[str] = mapped_column(unique=True, index=True)
    password_hash: Mapped[str]
    full_name: Mapped[str]
    role: Mapped[UserRole] = mapped_column(
        ENUM(UserRole, name="user_role", create_type=False),
        nullable=False,
        server_default=UserRole.user.value
    )
    preferred_pool_size: Mapped[int] = mapped_column(server_default="25")
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("now()"),
        onupdate=text("now()")
    )

    refresh_tokens = relationship(
        "RefreshToken",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    workouts = relationship(
        "Workout",
        back_populates="user",
        cascade="all, delete-orphan"
    )


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True,
        server_default=text("gen_random_uuid()")
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=False
    )
    token_hash: Mapped[str]
    is_revoked: Mapped[bool] = mapped_column(server_default="false")
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))
    expires_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True))

    user = relationship("User", back_populates="refresh_tokens")

    __table_args__ = (
        Index('idx_token-user_id', 'user_id'),
        Index('idx_token_hash', 'token_hash'),
    )


class Exercise(Base):
    __tablename__ = "exercises"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True,
        server_default=text("gen_random_uuid()")
    )
    name: Mapped[str] = mapped_column(String(50))
    short_name: Mapped[str] = mapped_column(String(20))
    description: Mapped[Optional[str]]
    style: Mapped[SwimmingStyle] = mapped_column(
        ENUM(SwimmingStyle, name="swimming_style", create_type=False),
    )
    distance_meters: Mapped[int]
    content_markdown: Mapped[Optional[str]]
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("now()"),
        onupdate=text("now()")
    )

    __table_args__ = (
        Index('idx_style', 'style'),
        UniqueConstraint('name', 'distance_meters', name='uq_exercise_name-distance'),
    )

class TrainingTemplate(Base):
    __tablename__ = "training_templates"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True,
        server_default=text("gen_random_uuid()")
    )
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[Optional[str]]
    level: Mapped[TrainingLevel] = mapped_column(
        ENUM(TrainingLevel, name="training_level", create_type=False),
    )
    version: Mapped[int] = mapped_column(server_default="1")
    is_active: Mapped[bool] = mapped_column(server_default="true")
    total_distance: Mapped[int]
    estimated_duration_minutes: Mapped[Optional[int]]
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("now()"),
        onupdate=text("now()")
    )
    steps: Mapped[List["TrainingStep"]] = relationship(
        "TrainingStep",
        back_populates="training_template",
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    __table_args__ = (
        Index('idx_training_template-level', 'level'),
        Index('idx_training_template-is_active', 'is_active'),
        UniqueConstraint('name', 'version', name='unique_name-version'),
    )


class TrainingStep(Base):
    __tablename__ = "training_steps"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True,
        server_default=text("gen_random_uuid()")
    )
    training_template_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("training_templates.id", ondelete="CASCADE"),
        index=False
    )
    exercise_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("exercises.id", ondelete="RESTRICT"),
        index=False
    )
    step_number: Mapped[int]
    repetitions: Mapped[int] = mapped_column(server_default="1")
    section_type: Mapped[SectionType] = mapped_column(
        ENUM(SectionType, name="section_type", create_type=False),
    )
    rest_seconds: Mapped[Optional[int]]
    notes: Mapped[Optional[str]]
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))

    training_template: Mapped["TrainingTemplate"] = relationship(
        "TrainingTemplate",
        back_populates="steps"
    )
    exercise: Mapped["Exercise"] = relationship("Exercise")

    __table_args__ = (
        Index('idx_training_step-training_template', 'training_template_id'),
        UniqueConstraint('training_template_id', 'step_number', name='unique_training_step'),
    )


class Workout(Base):
    __tablename__ = "workouts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()")
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=False
    )
    training_template_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("training_templates.id", ondelete="RESTRICT"),
        index=False
    )
    pool_size_meters: Mapped[int]
    status: Mapped[WorkoutStatus] = mapped_column(
        ENUM(WorkoutStatus, name="workout_status", create_type=False),
        nullable=False,
        server_default=WorkoutStatus.in_progress.value,
    )
    actual_start_time: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True))
    actual_end_time: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True))
    total_distance_planned: Mapped[int]
    total_distance_completed: Mapped[int] = mapped_column(server_default="0")
    total_duration_seconds: Mapped[int] = mapped_column(server_default="0")
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("now()"),
        onupdate=text("now()")
    )
    synced_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True))

    user: Mapped["User"] = relationship(
        "User",
        back_populates="workouts"
    )
    steps: Mapped[List["WorkoutStep"]] = relationship(
        "WorkoutStep",
        back_populates="workout",
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    __table_args__ = (
        Index('idx_workout-user_id', 'user_id'),
        Index('idx_workout-status', 'status'),
        Index('idx_workout-actual_start_time', 'actual_start_time'),
    )


class WorkoutStep(Base):
    __tablename__ = "workout_steps"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()")
    )
    workout_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workouts.id", ondelete="CASCADE"),
        index=False
    )
    step_number: Mapped[int]
    exercise_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("exercises.id", ondelete="RESTRICT"),
        index=False
    )
    distance_meters: Mapped[int]
    status: Mapped[WorkoutStepStatus] = mapped_column(
        ENUM(WorkoutStepStatus, name="workout_step_status", create_type=False),
        server_default=WorkoutStepStatus.pending.value
    )
    started_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True))
    duration_seconds: Mapped[Optional[int]]
    avg_heart_rate: Mapped[Optional[int]]
    notes: Mapped[Optional[str]]
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))

    workout: Mapped["Workout"] = relationship(
        "Workout",
        back_populates="steps"
    )
    exercise: Mapped["Exercise"] = relationship("Exercise")

    __table_args__ = (
        Index('idx_workout_step-workout_id', 'workout_id'),
        UniqueConstraint('workout_id', 'step_number', name='unique_workout_step'),
    )

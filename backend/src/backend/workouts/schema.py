from typing import Optional
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime

from backend.db.models import WorkoutStatus, WorkoutStepStatus


# --- 4.1 POST /workouts ---

POOL_SIZE_MIN = 10
POOL_SIZE_MAX = 200  # TODO: remove upper limit when "open water" (unlimited distance) is supported


class WorkoutCreateRequest(BaseModel):
    training_id: UUID
    pool_size_meters: int = Field(ge=POOL_SIZE_MIN, le=POOL_SIZE_MAX)


class WorkoutCreateResponse(BaseModel):
    workout_id: UUID
    user_id: UUID
    training_id: UUID
    training_version: int
    pool_size_meters: int
    status: WorkoutStatus
    actual_start_time: Optional[datetime]
    actual_end_time: Optional[datetime]
    total_distance_planned: int
    total_distance_completed: int
    created_at: datetime


# --- 4.2 GET /workouts ---

class WorkoutListItem(BaseModel):
    workout_id: UUID
    training_name: str
    training_version: int
    status: WorkoutStatus
    actual_start_time: Optional[datetime]
    actual_end_time: Optional[datetime]
    total_distance_completed: int
    total_duration_seconds: int
    created_at: datetime


class WorkoutListResponse(BaseModel):
    workouts: list[WorkoutListItem]
    total: int


# --- 4.3 GET /workouts/{workout_id} ---

class WorkoutStepItem(BaseModel):
    step_number: int
    exercise_name: str
    exercise_short_name: str
    distance_meters: int
    status: WorkoutStepStatus
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    duration_seconds: Optional[int]
    avg_heart_rate: Optional[int]
    notes: Optional[str]


class WorkoutDetail(BaseModel):
    workout_id: UUID
    user_id: UUID
    training_id: UUID
    training_name: str
    training_version: int
    pool_size_meters: int
    status: WorkoutStatus
    actual_start_time: Optional[datetime]
    actual_end_time: Optional[datetime]
    total_distance_planned: int
    total_distance_completed: int
    total_duration_seconds: int
    steps: list[WorkoutStepItem]
    created_at: datetime
    updated_at: datetime


# --- 4.4 PATCH /workouts/{workout_id} ---

class WorkoutUpdateRequest(BaseModel):
    status: Optional[WorkoutStatus] = None
    pool_size_meters: Optional[int] = Field(default=None, ge=POOL_SIZE_MIN, le=POOL_SIZE_MAX)
    actual_start_time: Optional[datetime] = None
    actual_end_time: Optional[datetime] = None


# --- 4.5 POST /workouts/{workout_id}/sync ---

class SyncStepItem(BaseModel):
    step_number: int
    status: WorkoutStepStatus
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    avg_heart_rate: Optional[int] = None
    notes: Optional[str] = None


class WorkoutSyncRequest(BaseModel):
    status: WorkoutStatus
    actual_start_time: Optional[datetime] = None
    actual_end_time: Optional[datetime] = None
    steps: list[SyncStepItem]


class WorkoutSyncResponse(BaseModel):
    workout_id: UUID
    sync_status: str
    synced_at: datetime

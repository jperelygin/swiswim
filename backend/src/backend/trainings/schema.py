from uuid import UUID
from datetime import datetime
from typing import Optional
from pydantic import BaseModel

from backend.db.models import SectionType, TrainingLevel


class TrainingListItem(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    level: TrainingLevel
    total_distance: int
    estimated_duration_minutes: Optional[int]
    version: int
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class TrainingListResponse(BaseModel):
    trainings: list[TrainingListItem]
    total: int


class CreateTrainingStepRequest(BaseModel):
    exercise_id: UUID
    step_number: int
    repetitions: int = 1
    section_type: SectionType
    rest_seconds: Optional[int] = None
    notes: Optional[str] = None


class CreateTrainingRequest(BaseModel):
    name: str
    description: Optional[str] = None
    level: TrainingLevel
    estimated_duration_minutes: Optional[int] = None
    steps: list[CreateTrainingStepRequest]


class TrainingStepItem(BaseModel):
    step_number: int
    exercise_id: UUID
    exercise_name: str
    exercise_short_name: str
    repetitions: int
    section_type: SectionType
    rest_seconds: Optional[int]
    distance_meters: int  # computed: exercise.distance_meters * repetitions
    notes: Optional[str]


class TrainingDetail(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    level: TrainingLevel
    total_distance: int
    estimated_duration_minutes: Optional[int]
    version: int
    is_active: bool
    steps: list[TrainingStepItem]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

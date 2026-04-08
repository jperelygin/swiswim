from uuid import UUID
from datetime import datetime
from typing import Optional
from pydantic import BaseModel

from backend.db.models import SwimmingStyle


class ExerciseListItem(BaseModel):
    id: UUID
    name: str
    short_name: str
    description: Optional[str]
    style: SwimmingStyle
    distance_meters: int
    created_at: datetime

    model_config = {"from_attributes": True}


class ExerciseListResponse(BaseModel):
    exercises: list[ExerciseListItem]
    total: int


class CreateExerciseRequest(BaseModel):
    name: str
    short_name: str
    description: Optional[str] = None
    style: SwimmingStyle
    distance_meters: int
    content_markdown: Optional[str] = None


class ExerciseDetail(BaseModel):
    id: UUID
    name: str
    short_name: str
    description: Optional[str]
    style: SwimmingStyle
    distance_meters: int
    content_markdown: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

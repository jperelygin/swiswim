from typing import Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field

POOL_SIZE_MIN = 10
POOL_SIZE_MAX = 200  # TODO: remove upper limit when "open water" (unlimited distance) is supported


class UserProfileResponse(BaseModel):
    user_id: UUID
    email: str
    full_name: str
    is_admin: bool
    preferred_pool_size: int
    created_at: datetime

class UserUpdateRequest(BaseModel):
    full_name: Optional[str] = None
    preferred_pool_size: Optional[int] = Field(default=None, ge=POOL_SIZE_MIN, le=POOL_SIZE_MAX)

class UserUpdateResponse(BaseModel):
    user_id: UUID
    email: str
    full_name: str
    preferred_pool_size: int
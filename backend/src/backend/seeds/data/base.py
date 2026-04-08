from pydantic import BaseModel, ConfigDict


class Seed(BaseModel):
    model_config = ConfigDict(extra="forbid")

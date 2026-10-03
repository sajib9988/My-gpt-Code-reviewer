from datetime import datetime

from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str | None = None
    repository_url: str | None = Field(default=None, max_length=500)
    branch: str = Field(default="main", min_length=1, max_length=255)
    ai_provider: str = Field(default="ollama", min_length=1, max_length=50)
    ai_model: str = Field(default="llama3.1", min_length=1, max_length=150)
    instructions: str | None = None


class ProjectResponse(ProjectCreate):
    id: str
    owner_id: str
    created_at: datetime
    updated_at: datetime

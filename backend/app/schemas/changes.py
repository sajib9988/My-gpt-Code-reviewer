from datetime import datetime

from pydantic import BaseModel, Field


class CodeChangeCreate(BaseModel):
    path: str = Field(min_length=1, max_length=1000)
    new_content: str
    old_content: str | None = None
    run_id: str | None = None


class CodeChangeResponse(BaseModel):
    id: str
    project_id: str
    run_id: str | None
    path: str
    old_content: str | None
    new_content: str
    status: str
    branch: str | None
    commit_sha: str | None
    created_at: datetime
    approved_at: datetime | None


class CommitRequest(BaseModel):
    branch: str = Field(min_length=1, max_length=255)
    message: str = Field(min_length=1, max_length=200)


class PullRequestRequest(BaseModel):
    branch: str = Field(min_length=1, max_length=255)
    title: str = Field(min_length=1, max_length=200)
    body: str = ""
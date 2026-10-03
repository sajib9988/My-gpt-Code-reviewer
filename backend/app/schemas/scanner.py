from datetime import datetime

from pydantic import BaseModel


class ScanResponse(BaseModel):
    id: str
    project_id: str
    status: str
    branch: str
    commit_sha: str | None
    framework: str | None
    languages: dict
    files_count: int
    error: str | None
    created_at: datetime
    completed_at: datetime | None


class ProjectFileResponse(BaseModel):
    path: str
    file_type: str
    language: str | None
    size: int
    sha: str | None
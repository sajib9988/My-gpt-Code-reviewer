from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.auth import User


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(120))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    repository_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    branch: Mapped[str] = mapped_column(String(255), default="main")
    ai_provider: Mapped[str] = mapped_column(String(50), default="ollama")
    ai_model: Mapped[str] = mapped_column(String(150), default="llama3.1")
    instructions: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    owner: Mapped["User"] = relationship(back_populates="projects")


class RepositoryScan(Base):
    __tablename__ = "repository_scans"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), unique=True, index=True
    )
    status: Mapped[str] = mapped_column(String(30), default="pending")
    branch: Mapped[str] = mapped_column(String(255))
    commit_sha: Mapped[str | None] = mapped_column(String(100), nullable=True)
    framework: Mapped[str | None] = mapped_column(String(100), nullable=True)
    languages: Mapped[dict] = mapped_column(JSON, default=dict)
    files_count: Mapped[int] = mapped_column(default=0)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    project: Mapped["Project"] = relationship()


class ProjectFile(Base):
    __tablename__ = "project_files"

    # id is "{scan_id}:{path}" — must match the 1100 length in migration 0003
    id: Mapped[str] = mapped_column(String(1100), primary_key=True)
    scan_id: Mapped[str] = mapped_column(
        ForeignKey("repository_scans.id", ondelete="CASCADE"), index=True
    )
    path: Mapped[str] = mapped_column(String(1000))
    file_type: Mapped[str] = mapped_column(String(30), default="file")
    language: Mapped[str | None] = mapped_column(String(50), nullable=True)
    size: Mapped[int] = mapped_column(default=0)
    sha: Mapped[str | None] = mapped_column(String(100), nullable=True)
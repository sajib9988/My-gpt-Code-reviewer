from sqlalchemy import select
from sqlalchemy.orm import Session as DatabaseSession

from app.models.agent import Message
from app.models.project import Project, ProjectFile, RepositoryScan
from services.llm import LLMMessage

MAX_FILES_IN_CONTEXT = 300
MAX_HISTORY = 40


def system_prompt(database: DatabaseSession, project: Project) -> str:
    parts = [
        "You are a helpful senior software engineer working inside the user's project. "
        "Answer clearly, use markdown code blocks for code, and say when you are unsure."
    ]
    if project.instructions:
        parts.append(f"Project instructions:\n{project.instructions}")
    scan = database.scalar(select(RepositoryScan).where(RepositoryScan.project_id == project.id))
    if scan and scan.status == "completed":
        paths = database.scalars(
            select(ProjectFile.path)
            .where(ProjectFile.scan_id == scan.id)
            .order_by(ProjectFile.path)
            .limit(MAX_FILES_IN_CONTEXT)
        )
        parts.append(
            f"Repository: {project.repository_url} (branch {project.branch}, framework {scan.framework})\n"
            "Files:\n" + "\n".join(paths)
        )
    return "\n\n".join(parts)


def conversation_messages(database: DatabaseSession, project: Project, history: list[Message]) -> list[LLMMessage]:
    messages = [LLMMessage("system", system_prompt(database, project))]
    messages += [LLMMessage(item.role, item.content) for item in history[-MAX_HISTORY:]]
    return messages
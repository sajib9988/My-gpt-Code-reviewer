import json
import uuid
from collections.abc import Iterator
from datetime import UTC, datetime

import httpx

from app.core.config import get_settings
from app.schemas.agent import ChatReply
from services.chat import conversation_messages
from services.llm import provider_for
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session as DatabaseSession

from app.db.session import get_db
from app.models.agent import AgentEvent, AgentRun, Conversation, Message, Task
from app.models.auth import User
from app.models.project import Project
from app.schemas.agent import (
    AgentRunCreate,
    AgentRunResponse,
    ConversationCreate,
    ConversationResponse,
    MessageCreate,
    MessageResponse,
    TaskCreate,
    TaskResponse,
    TaskUpdate,
)
from dependencies import get_current_user, require_csrf

router = APIRouter(tags=["agent-workspace"])


def owned_project(project_id: str, user: User, database: DatabaseSession) -> Project:
    project = database.scalar(select(Project).where(Project.id == project_id, Project.owner_id == user.id))
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project


def owned_conversation(conversation_id: str, user: User, database: DatabaseSession) -> Conversation:
    conversation = database.scalar(
        select(Conversation)
        .join(Project, Project.id == Conversation.project_id)
        .where(Conversation.id == conversation_id, Project.owner_id == user.id)
    )
    if not conversation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    return conversation


def owned_task(task_id: str, user: User, database: DatabaseSession) -> Task:
    task = database.scalar(
        select(Task).join(Project, Project.id == Task.project_id).where(Task.id == task_id, Project.owner_id == user.id)
    )
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return task


@router.post(
    "/projects/{project_id}/conversations",
    response_model=ConversationResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_csrf)],
)
def create_conversation(
    project_id: str,
    payload: ConversationCreate,
    user: User = Depends(get_current_user),
    database: DatabaseSession = Depends(get_db),
) -> Conversation:
    owned_project(project_id, user, database)
    conversation = Conversation(id=str(uuid.uuid4()), project_id=project_id, title=payload.title)
    database.add(conversation)
    database.commit()
    database.refresh(conversation)
    return conversation


@router.get("/projects/{project_id}/conversations", response_model=list[ConversationResponse])
def list_conversations(
    project_id: str,
    user: User = Depends(get_current_user),
    database: DatabaseSession = Depends(get_db),
) -> list[Conversation]:
    owned_project(project_id, user, database)
    return list(
        database.scalars(
            select(Conversation)
            .where(Conversation.project_id == project_id)
            .order_by(Conversation.updated_at.desc())
        )
    )


@router.get("/conversations/{conversation_id}/messages", response_model=list[MessageResponse])
def list_messages(
    conversation_id: str,
    user: User = Depends(get_current_user),
    database: DatabaseSession = Depends(get_db),
) -> list[Message]:
    owned_conversation(conversation_id, user, database)
    return list(database.scalars(select(Message).where(Message.conversation_id == conversation_id).order_by(Message.created_at)))


@router.post(
    "/conversations/{conversation_id}/messages",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_csrf)],
)
def add_message(
    conversation_id: str,
    payload: MessageCreate,
    user: User = Depends(get_current_user),
    database: DatabaseSession = Depends(get_db),
) -> Message:
    owned_conversation(conversation_id, user, database)
    message = Message(id=str(uuid.uuid4()), conversation_id=conversation_id, role="user", content=payload.content)
    database.add(message)
    database.commit()
    database.refresh(message)
    return message
@router.post(
    "/conversations/{conversation_id}/chat",
    response_model=ChatReply,
    dependencies=[Depends(require_csrf)],
)
async def chat(
    conversation_id: str,
    payload: MessageCreate,
    user: User = Depends(get_current_user),
    database: DatabaseSession = Depends(get_db),
) -> dict:
    conversation = owned_conversation(conversation_id, user, database)
    project = database.get(Project, conversation.project_id)

    user_message = Message(
        id=str(uuid.uuid4()),
        conversation_id=conversation_id,
        role="user",
        content=payload.content,
        created_at=datetime.now(UTC),
    )
    database.add(user_message)
    if conversation.title == "New conversation":
        conversation.title = payload.content.strip()[:60] or conversation.title
    database.commit()
    database.refresh(user_message)

    history = list(
        database.scalars(
            select(Message).where(Message.conversation_id == conversation_id).order_by(Message.created_at)
        )
    )
    try:
        llm = provider_for(project.ai_provider)
        response = await llm.complete(conversation_messages(database, project, history), project.ai_model)
    except (httpx.HTTPError, KeyError, ValueError) as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail="AI provider request failed"
        ) from error

    assistant_message = Message(
        id=str(uuid.uuid4()),
        conversation_id=conversation_id,
        role="assistant",
        content=response.content,
        created_at=datetime.now(UTC),
    )
    database.add(assistant_message)
    database.commit()
    database.refresh(assistant_message)
    return {"user_message": user_message, "assistant_message": assistant_message}

@router.post(
    "/projects/{project_id}/tasks",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_csrf)],
)
def create_task(
    project_id: str,
    payload: TaskCreate,
    user: User = Depends(get_current_user),
    database: DatabaseSession = Depends(get_db),
) -> Task:
    owned_project(project_id, user, database)
    task = Task(id=str(uuid.uuid4()), project_id=project_id, **payload.model_dump())
    database.add(task)
    database.commit()
    database.refresh(task)
    return task


@router.get("/projects/{project_id}/tasks", response_model=list[TaskResponse])
def list_tasks(
    project_id: str,
    user: User = Depends(get_current_user),
    database: DatabaseSession = Depends(get_db),
) -> list[Task]:
    owned_project(project_id, user, database)
    return list(database.scalars(select(Task).where(Task.project_id == project_id).order_by(Task.created_at.desc())))


@router.patch("/tasks/{task_id}", response_model=TaskResponse, dependencies=[Depends(require_csrf)])
def update_task(
    task_id: str,
    payload: TaskUpdate,
    user: User = Depends(get_current_user),
    database: DatabaseSession = Depends(get_db),
) -> Task:
    task = owned_task(task_id, user, database)
    task.status = payload.status
    database.commit()
    database.refresh(task)
    return task


@router.post("/projects/{project_id}/runs", response_model=AgentRunResponse, dependencies=[Depends(require_csrf)])
def create_run(
    project_id: str,
    payload: AgentRunCreate,
    user: User = Depends(get_current_user),
    database: DatabaseSession = Depends(get_db),
) -> AgentRun:
    project = owned_project(project_id, user, database)
    if payload.task_id:
        task = database.scalar(select(Task).where(Task.id == payload.task_id, Task.project_id == project_id))
        if not task:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    run = AgentRun(
        id=str(uuid.uuid4()),
        project_id=project_id,
        task_id=payload.task_id,
        status="queued",
        current_agent="planner",
        provider=project.ai_provider,
        model=project.ai_model,
    )
    database.add(run)
    database.add(
        AgentEvent(
            id=str(uuid.uuid4()),
            run_id=run.id,
            sequence=1,
            agent="planner",
            event_type="status",
            message="Agent run queued",
        )
    )
    database.commit()
    database.refresh(run)
    return run


@router.get("/projects/{project_id}/runs", response_model=list[AgentRunResponse])
def list_runs(
    project_id: str,
    user: User = Depends(get_current_user),
    database: DatabaseSession = Depends(get_db),
) -> list[AgentRun]:
    owned_project(project_id, user, database)
    return list(database.scalars(select(AgentRun).where(AgentRun.project_id == project_id).order_by(AgentRun.created_at.desc())))


@router.get("/runs/{run_id}", response_model=AgentRunResponse)
def get_run(
    run_id: str,
    user: User = Depends(get_current_user),
    database: DatabaseSession = Depends(get_db),
) -> AgentRun:
    run = database.scalar(
        select(AgentRun).join(Project, Project.id == AgentRun.project_id).where(AgentRun.id == run_id, Project.owner_id == user.id)
    )
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent run not found")
    return run


@router.get("/runs/{run_id}/events")
def stream_run_events(
    run_id: str,
    after: int = Query(default=0, ge=0),
    user: User = Depends(get_current_user),
    database: DatabaseSession = Depends(get_db),
) -> StreamingResponse:
    get_run(run_id, user, database)
    events = list(
        database.scalars(
            select(AgentEvent).where(AgentEvent.run_id == run_id, AgentEvent.sequence > after).order_by(AgentEvent.sequence)
        )
    )

    def event_stream() -> Iterator[str]:
        for event in events:
            payload = {"agent": event.agent, "type": event.event_type, "message": event.message}
            yield f"id: {event.sequence}\nevent: agent\ndata: {json.dumps(payload)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream", headers={"Cache-Control": "no-cache"})


@router.get("/providers")
def list_providers() -> list[dict[str, object]]:
    return [
        {"id": "ollama", "name": "Ollama", "configured": True, "local": True},
        {"id": "openrouter", "name": "OpenRouter", "configured": bool(__import__("app.core.config", fromlist=["get_settings"]).get_settings().openrouter_api_key), "local": False},
    ]

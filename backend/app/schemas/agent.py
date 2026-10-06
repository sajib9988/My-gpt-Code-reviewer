from datetime import datetime

from pydantic import BaseModel, Field


class ConversationCreate(BaseModel):
    title: str = Field(default="New conversation", min_length=1, max_length=200)


class MessageCreate(BaseModel):
    content: str = Field(min_length=1, max_length=100_000)


class ConversationResponse(BaseModel):
    id: str
    project_id: str
    title: str
    created_at: datetime
    updated_at: datetime


class MessageResponse(BaseModel):
    id: str
    conversation_id: str
    role: str
    content: str
    created_at: datetime


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None
    priority: str = Field(default="normal", pattern="^(low|normal|high|urgent)$")


class TaskUpdate(BaseModel):
    status: str = Field(pattern="^(todo|in_progress|done|blocked)$")


class TaskResponse(BaseModel):
    id: str
    project_id: str
    title: str
    description: str | None
    status: str
    priority: str
    created_at: datetime
    updated_at: datetime


class AgentRunCreate(BaseModel):
    task_id: str | None = None


class AgentRunResponse(BaseModel):
    id: str
    project_id: str
    task_id: str | None
    status: str
    current_agent: str | None
    provider: str
    model: str
    result: str | None
    error: str | None
    created_at: datetime
    completed_at: datetime | None
class ChatReply(BaseModel):
    user_message: MessageResponse
    assistant_message: MessageResponse
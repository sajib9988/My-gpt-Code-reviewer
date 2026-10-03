from pydantic import BaseModel, Field


class GitHubConnectionResponse(BaseModel):
    connected: bool
    login: str | None = None
    scopes: list[str] = Field(default_factory=list)


class GitHubAuthUrlResponse(BaseModel):
    authorization_url: str


class GitHubRepositoryResponse(BaseModel):
    id: int
    full_name: str
    name: str
    private: bool
    default_branch: str
    html_url: str


class GitHubFileResponse(BaseModel):
    path: str
    content: str
    sha: str
    size: int


class GitHubSearchResponse(BaseModel):
    total_count: int
    items: list[dict]

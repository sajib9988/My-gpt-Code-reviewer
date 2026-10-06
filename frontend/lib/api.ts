const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

function csrfToken() {
    return document.cookie
        .split(";")
        .map((part) => part.trim())
        .find((part) => part.startsWith("csrf_token="))
        ?.split("=")[1];
}

export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
    const method = options.method?.toUpperCase() ?? "GET";
    const headers = new Headers(options.headers);
    headers.set("Content-Type", "application/json");
    if (method !== "GET" && method !== "HEAD") {
        const token = csrfToken();
        if (token) headers.set("X-CSRF-Token", decodeURIComponent(token));
    }
    const response = await fetch(`${API_URL}${path}`, {
        ...options,
        headers,
        credentials: "include",
    });
    if (!response.ok) {
        const body = await response.json().catch(() => null);
        throw new Error(body?.detail ?? "The API request failed");
    }
    if (response.status === 204) return undefined as T;
    return response.json() as Promise<T>;
}

export type User = { id: string; email: string; role: string };
export type Project = {
    id: string;
    owner_id: string;
    name: string;
    description: string | null;
    repository_url: string | null;
    branch: string;
    ai_provider: string;
    ai_model: string;
    instructions: string | null;
};
export type Scan = {
    id: string;
    status: string;
    branch: string;
    framework: string | null;
    languages: Record<string, number>;
    files_count: number;
    error: string | null;
};
export type ProjectFile = { path: string; language: string | null; size: number; sha: string | null };
export type Conversation = { id: string; project_id: string; title: string; created_at: string; updated_at: string };
export type Message = { id: string; conversation_id: string; role: string; content: string; created_at: string };
export type Task = { id: string; project_id: string; title: string; description: string | null; status: string; priority: string };
export type AgentRun = { id: string; project_id: string; task_id: string | null; status: string; current_agent: string | null; provider: string; model: string; result: string | null };
export type Repo = { id: number; full_name: string; default_branch: string; html_url: string; private: boolean };
export type ChatReply = { user_message: Message; assistant_message: Message };
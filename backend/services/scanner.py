from collections.abc import Iterable

from app.models.project import ProjectFile

LANGUAGES = {
    ".py": "Python",
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".go": "Go",
    ".rs": "Rust",
    ".java": "Java",
    ".cs": "C#",
    ".rb": "Ruby",
    ".php": "PHP",
    ".sql": "SQL",
}


def detect_framework(paths: Iterable[str]) -> str:
    path_set = set(paths)
    lower_paths = {path.lower() for path in path_set}
    if any(path.endswith("next.config.js") or path.endswith("next.config.ts") for path in lower_paths):
        return "Next.js"
    if "manage.py" in lower_paths or any("django" in path for path in lower_paths):
        return "Django"
    if "requirements.txt" in lower_paths or "pyproject.toml" in lower_paths:
        if any(path.endswith("main.py") or path.endswith("app.py") for path in lower_paths):
            return "Python"
    if "package.json" in lower_paths:
        return "Node.js"
    if "cargo.toml" in lower_paths:
        return "Rust"
    if "go.mod" in lower_paths:
        return "Go"
    return "Unknown"


def language_for_path(path: str) -> str | None:
    lowered = path.lower()
    for extension, language in LANGUAGES.items():
        if lowered.endswith(extension):
            return language
    return None


def project_file_from_tree(scan_id: str, item: dict) -> ProjectFile:
    path = item["path"]
    return ProjectFile(
        id=f"{scan_id}:{path}",
        scan_id=scan_id,
        path=path,
        file_type=item.get("type", "file"),
        language=language_for_path(path),
        size=item.get("size", 0),
        sha=item.get("sha"),
    )
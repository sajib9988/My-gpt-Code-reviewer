from urllib.parse import quote

import httpx


class GitHubAPIError(Exception):
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        super().__init__(message)


class GitHubClient:
    base_url = "https://api.github.com"

    def __init__(self, access_token: str):
        self.client = httpx.Client(
            base_url=self.base_url,
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {access_token}",
                "X-GitHub-Api-Version": "2022-11-28",
            },
            timeout=20.0,
        )

    def close(self) -> None:
        self.client.close()

    def _request(self, method: str, path: str, **kwargs) -> dict | list:
        response = self.client.request(method, path, **kwargs)
        if response.is_error:
            detail = response.json().get("message", "GitHub request failed")
            raise GitHubAPIError(response.status_code, detail)
        return response.json()

    def current_user(self) -> dict:
        return self._request("GET", "/user")

    def repositories(self) -> list[dict]:
        return self._request("GET", "/user/repos", params={"per_page": 100, "sort": "updated"})

    def repository(self, owner: str, repository: str) -> dict:
        return self._request("GET", f"/repos/{owner}/{repository}")

    def tree(self, owner: str, repository: str, branch: str) -> dict:
        return self._request(
            "GET", f"/repos/{owner}/{repository}/git/trees/{quote(branch, safe='')}", params={"recursive": "1"}
        )

    def languages(self, owner: str, repository: str) -> dict:
        return self._request("GET", f"/repos/{owner}/{repository}/languages")

    def file(self, owner: str, repository: str, path: str, branch: str) -> dict:
        encoded_path = quote(path.lstrip("/"), safe="/")
        return self._request(
            "GET", f"/repos/{owner}/{repository}/contents/{encoded_path}", params={"ref": branch}
        )

    def search_code(self, query: str, owner: str, repository: str) -> dict:
        return self._request(
            "GET", "/search/code", params={"q": f"{query} repo:{owner}/{repository}", "per_page": 50}
        )

    def create_branch(self, owner: str, repository: str, branch: str, from_sha: str) -> dict:
        return self._request("POST", f"/repos/{owner}/{repository}/git/refs", json={"ref": f"refs/heads/{branch}", "sha": from_sha})

    def branch(self, owner: str, repository: str, branch: str) -> dict:
        return self._request("GET", f"/repos/{owner}/{repository}/branches/{quote(branch, safe='')}")

    def commit_file(
        self,
        owner: str,
        repository: str,
        path: str,
        branch: str,
        content: str,
        message: str,
        sha: str | None = None,
    ) -> dict:
        import base64

        payload = {"message": message, "content": base64.b64encode(content.encode()).decode(), "branch": branch}
        if sha:
            payload["sha"] = sha
        return self._request("PUT", f"/repos/{owner}/{repository}/contents/{quote(path.lstrip('/'), safe='/')}", json=payload)

    def create_pull_request(self, owner: str, repository: str, title: str, body: str, head: str, base: str) -> dict:
        return self._request(
            "POST",
            f"/repos/{owner}/{repository}/pulls",
            json={"title": title, "body": body, "head": head, "base": base},
        )

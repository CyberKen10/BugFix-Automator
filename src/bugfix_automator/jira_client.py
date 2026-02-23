"""Cliente Jira para autenticación y consulta de issues por estado."""

from __future__ import annotations

from typing import Any

import requests

from bugfix_automator.config import JiraConfig
from bugfix_automator.models import JiraIssue


class JiraClient:
    """Cliente simple para Jira Cloud REST API v3."""

    def __init__(self, config: JiraConfig, timeout_seconds: int = 30) -> None:
        self._config = config
        self._timeout = timeout_seconds

    def fetch_issues_by_status(self, status: str, max_results: int = 200) -> list[JiraIssue]:
        """Obtiene issues filtrados por estado usando JQL."""
        url = f"{self._config.base_url}/rest/api/3/search/jql"
        headers = {"Accept": "application/json"}
        auth = (self._config.email, self._config.api_token)

        start_at = 0
        issues: list[JiraIssue] = []

        while True:
            payload = {
                "jql": f'status = "{status}" ORDER BY updated DESC',
                "maxResults": min(max_results, 100),
                "startAt": start_at,
                "fields": [
                    "summary",
                    "status",
                    "assignee",
                    "description",
                    "timespent",
                    "timeoriginalestimate",
                ],
            }
            response = requests.post(
                url,
                json=payload,
                headers=headers,
                auth=auth,
                timeout=self._timeout,
            )
            response.raise_for_status()

            data = response.json()
            batch = [self._to_issue(raw_issue) for raw_issue in data.get("issues", [])]
            issues.extend(batch)

            total = int(data.get("total", 0))
            start_at += len(batch)
            if start_at >= total or not batch:
                break

        return issues

    def _to_issue(self, raw_issue: dict[str, Any]) -> JiraIssue:
        fields = raw_issue.get("fields", {})
        status = fields.get("status", {}).get("name", "Unknown")
        assignee = fields.get("assignee", {})
        assignee_name = (
            assignee.get("displayName")
            if isinstance(assignee, dict)
            else "Unassigned"
        )

        return JiraIssue(
            key=raw_issue.get("key", ""),
            summary=fields.get("summary", ""),
            status=status,
            assignee=assignee_name or "Unassigned",
            description=_flatten_jira_description(fields.get("description")),
            timespent_seconds=fields.get("timespent"),
            timeoriginalestimate_seconds=fields.get("timeoriginalestimate"),
        )


def _flatten_jira_description(description_node: dict[str, Any] | None) -> str:
    """Convierte la descripción ADF de Jira en texto plano básico."""
    if not description_node:
        return ""

    chunks: list[str] = []

    def visit(node: Any) -> None:
        if isinstance(node, dict):
            if node.get("type") == "text":
                chunks.append(node.get("text", ""))
            for child in node.get("content", []):
                visit(child)
        elif isinstance(node, list):
            for item in node:
                visit(item)

    visit(description_node)
    return " ".join(chunk.strip() for chunk in chunks if chunk.strip())

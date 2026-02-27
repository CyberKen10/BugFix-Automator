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

    def fetch_issues_by_status(
        self,
        status: str,
        project: str | None = None,
        parent_key: str | None = None,
        max_results: int = 200,
    ) -> list[JiraIssue]:
        """Obtiene issues filtrados por estado (y opcionalmente epic/parent) usando JQL."""
        url = f"{self._config.base_url}/rest/api/3/search/jql"
        headers = {"Accept": "application/json"}
        auth = (self._config.email, self._config.api_token)

        jql = f'status = "{status}"'
        if parent_key:
            jql = f'parent = "{parent_key}" AND {jql}'
        elif project:
            jql = f'project = "{project}" AND {jql}'
        jql += " ORDER BY updated DESC"

        start_at = 0
        issues: list[JiraIssue] = []

        while True:
            params = {
                "jql": jql,
                "maxResults": min(max_results, 100),
                "startAt": start_at,
                "fields": "summary,status,assignee,description,timespent,timeoriginalestimate",
            }
            response = requests.get(
                url,
                params=params,
                headers=headers,
                auth=auth,
                timeout=self._timeout,
            )
            if response.status_code != 200:
                detail = response.text[:500] if response.text else "sin detalle"
                raise RuntimeError(
                    f"Jira respondió {response.status_code}: {detail}"
                )


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

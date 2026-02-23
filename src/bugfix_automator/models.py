"""Modelos de dominio compartidos."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class JiraIssue:
    key: str
    summary: str
    status: str
    assignee: str
    description: str
    timespent_seconds: int | None
    timeoriginalestimate_seconds: int | None

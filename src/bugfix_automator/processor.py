"""Módulo de transformación y cálculo de métricas del reporte."""

from __future__ import annotations

from dataclasses import dataclass
import re

from bugfix_automator.models import JiraIssue


OO_PATTERN = re.compile(r"OO")


@dataclass(frozen=True)
class ProcessedIssue:
    issue_key: str
    summary: str
    status: str
    assignee: str
    tiempo_minutos: int
    cantidad_oo: int


@dataclass(frozen=True)
class ProcessedReport:
    issues: list[ProcessedIssue]
    total_tiempo_minutos: int
    total_oo: int


def select_time_in_minutes(issue: JiraIssue) -> int:
    """Selecciona el tiempo en segundos con prioridad y devuelve minutos redondeados."""
    seconds = issue.timespent_seconds
    if seconds is None:
        seconds = issue.timeoriginalestimate_seconds
    if not seconds:
        return 0
    return max(0, round(seconds / 60))


def count_oo_occurrences(text: str) -> int:
    """Cuenta cuántas veces aparece 'OO' de forma literal en el texto."""
    if not text:
        return 0
    return len(OO_PATTERN.findall(text))


def process_issues(issues: list[JiraIssue]) -> ProcessedReport:
    """Transforma issues de Jira a estructura de reporte con acumulados."""
    processed: list[ProcessedIssue] = []
    total_time = 0
    total_oo = 0

    for issue in issues:
        minutes = select_time_in_minutes(issue)
        oo_count = count_oo_occurrences(f"{issue.summary} {issue.description}")
        processed_issue = ProcessedIssue(
            issue_key=issue.key,
            summary=issue.summary,
            status=issue.status,
            assignee=issue.assignee,
            tiempo_minutos=minutes,
            cantidad_oo=oo_count,
        )
        processed.append(processed_issue)
        total_time += minutes
        total_oo += oo_count

    return ProcessedReport(
        issues=processed,
        total_tiempo_minutos=total_time,
        total_oo=total_oo,
    )

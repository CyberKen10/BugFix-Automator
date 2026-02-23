"""Generador de reporte de verificación de bugs."""

from __future__ import annotations

from bugfix_automator.drive_client import DriveClient
from bugfix_automator.processor import ProcessedReport


def build_sheet_rows(report: ProcessedReport) -> list[list[str | int]]:
    header = [
        "Issue Key",
        "Summary",
        "Status",
        "Assignee",
        "Tiempo (minutos)",
        "Cantidad de OO",
    ]
    rows: list[list[str | int]] = [header]

    for issue in report.issues:
        rows.append(
            [
                issue.issue_key,
                issue.summary,
                issue.status,
                issue.assignee,
                issue.tiempo_minutos,
                issue.cantidad_oo,
            ]
        )

    rows.append([])
    rows.append([
        "TOTAL",
        "",
        "",
        "",
        report.total_tiempo_minutos,
        report.total_oo,
    ])
    return rows


def generate_report(
    drive_client: DriveClient,
    report: ProcessedReport,
    title_prefix: str = "Bug-Fix Verification Report",
    folder_id: str | None = None,
) -> dict:
    spreadsheet = drive_client.create_spreadsheet(title_prefix=title_prefix, folder_id=folder_id)
    rows = build_sheet_rows(report)
    drive_client.write_rows(spreadsheet_id=spreadsheet["spreadsheetId"], rows=rows)
    return spreadsheet

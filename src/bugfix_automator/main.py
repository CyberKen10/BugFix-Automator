"""Punto de entrada del flujo Jira -> procesamiento -> Google Sheets."""

from __future__ import annotations

import argparse

from bugfix_automator.config import load_config_from_env, load_env_file
from bugfix_automator.webapp import run_server


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Genera reporte de bugs For Review en Google Sheets")
    parser.add_argument(
        "--status",
        default=None,
        help="Estado Jira a filtrar (default: JIRA_STATUS o For Review)",
    )
    parser.add_argument(
        "--web",
        action="store_true",
        help="Levanta dashboard web moderno para ejecutar la herramienta visualmente",
    )
    parser.add_argument("--port", type=int, default=8080, help="Puerto para modo --web")
    return parser.parse_args()


def run() -> None:
    load_env_file()
    args = parse_args()

    if args.web:
        run_server(port=args.port)
        return

    from bugfix_automator.drive_client import DriveClient
    from bugfix_automator.jira_client import JiraClient
    from bugfix_automator.processor import process_issues
    from bugfix_automator.report_generator import generate_report

    config = load_config_from_env()
    target_status = args.status or config.jira_status

    jira_client = JiraClient(config.jira)
    drive_client = DriveClient(config.google.service_account_file)

    issues = jira_client.fetch_issues_by_status(status=target_status)
    report = process_issues(issues)
    spreadsheet = generate_report(
        drive_client=drive_client,
        report=report,
        folder_id=config.google.drive_folder_id,
        title_prefix=f"Bug Verification - {target_status}",
    )

    print("Reporte generado con éxito")
    print(f"Status filtrado: {target_status}")
    print(f"Total issues: {len(report.issues)}")
    print(f"Total tiempo (min): {report.total_tiempo_minutos}")
    print(f"Total OO: {report.total_oo}")
    print(f"Spreadsheet URL: {spreadsheet.get('spreadsheetUrl', 'N/A')}")


if __name__ == "__main__":
    run()

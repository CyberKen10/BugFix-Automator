"""Cliente de Google Sheets para crear y cargar reportes BFV."""

from __future__ import annotations

from typing import Any

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

HEADER_BG = {"red": 0.788, "green": 0.855, "blue": 0.973}

ISSUES_HEADERS = [
    "#", "Tester", "URL Ticket", "Comentario de revision para ticket",
    "Cant. OO", "Estado Actual en JIRA", "QA Result", "Status",
    "Tiempo", "Comments Internal (Expert & Auditors)",
]

NUM_COLS = len(ISSUES_HEADERS)

QA_TEMPLATE = (
    "Template:\n"
    "QA Passed / Failed \n"
    "Hi @dev, the issue is fixed / failing. Note that the... "
    "(explicar el issue brevemente). See the evidence below. Thanks!\n"
    "Sample URL: URL de testing\n"
    "Evidence:\n"
    "Regards!\n"
    "cc: @lydia"
)

ESTADO_JIRA_COLORS: dict[str, dict[str, float]] = {
    "QA Passed":            {"red": 0.42, "green": 0.82, "blue": 0.35},
    "QA Failed":            {"red": 0.91, "green": 0.30, "blue": 0.30},
    "Under Review":         {"red": 1.00, "green": 0.85, "blue": 0.40},
    "Won't Fix":            {"red": 0.70, "green": 0.70, "blue": 0.70},
    "On Hold":              {"red": 0.76, "green": 0.65, "blue": 0.90},
    "Needs clarification":  {"red": 1.00, "green": 0.65, "blue": 0.30},
    "For review":           {"red": 0.55, "green": 0.78, "blue": 1.00},
}

QA_RESULT_COLORS: dict[str, dict[str, float]] = {
    "Passed":        {"red": 0.42, "green": 0.82, "blue": 0.35},
    "Failed":        {"red": 0.91, "green": 0.30, "blue": 0.30},
    "Partially fix": {"red": 1.00, "green": 0.85, "blue": 0.40},
}

STATUS_COLORS: dict[str, dict[str, float]] = {
    "Jira Ready":      {"red": 0.42, "green": 0.82, "blue": 0.35},
    "Jira Uploaded":   {"red": 0.55, "green": 0.78, "blue": 1.00},
    "Ready to upload": {"red": 0.72, "green": 0.90, "blue": 0.55},
    "Jira to Update":  {"red": 1.00, "green": 0.65, "blue": 0.30},
    "No in Jira yet":  {"red": 0.91, "green": 0.50, "blue": 0.50},
    "Discussion":      {"red": 1.00, "green": 0.85, "blue": 0.40},
}

EXTRA_STATUS_COLORS = [
    {"red": 0.60, "green": 0.85, "blue": 0.75},
    {"red": 0.85, "green": 0.75, "blue": 0.55},
    {"red": 0.75, "green": 0.80, "blue": 0.95},
    {"red": 0.90, "green": 0.70, "blue": 0.80},
    {"red": 0.80, "green": 0.90, "blue": 0.65},
]


class DriveClient:
    """Cliente para crear hojas de cálculo y escribir datos tabulares."""

    def __init__(self, service_account_file: str) -> None:
        credentials = Credentials.from_service_account_file(
            service_account_file,
            scopes=SCOPES,
        )
        self._sheets = build("sheets", "v4", credentials=credentials)

    # ------------------------------------------------------------------
    # Setup BFV structure on an existing spreadsheet
    # ------------------------------------------------------------------

    def setup_bfv_spreadsheet(
        self,
        spreadsheet_id: str,
        title: str,
        jira_base_url: str,
        issues: list[Any],
        round_numbers: list[int] | None = None,
        default_status: str = "For review",
        tester: str = "",
    ) -> dict[str, Any]:
        """Configura un spreadsheet existente con la estructura BFV."""

        existing = self._sheets.spreadsheets().get(
            spreadsheetId=spreadsheet_id,
            fields="spreadsheetId,spreadsheetUrl,sheets/properties",
        ).execute()

        old_sheet_ids = [
            s["properties"]["sheetId"] for s in existing["sheets"]
        ]

        tab_names = ["Issues"]
        for rn in sorted(round_numbers or []):
            tab_names.append(f"Round {rn}")
        tab_names.append("Summary")

        add_requests: list[dict[str, Any]] = [
            {"addSheet": {"properties": {"title": name, "index": i}}}
            for i, name in enumerate(tab_names)
        ]

        self._sheets.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={"requests": add_requests},
        ).execute()

        delete_requests = [
            {"deleteSheet": {"sheetId": sid}} for sid in old_sheet_ids
        ]
        if delete_requests:
            self._sheets.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id,
                body={"requests": delete_requests},
            ).execute()

        self._sheets.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={"requests": [
                {"updateSpreadsheetProperties": {
                    "properties": {"title": title},
                    "fields": "title",
                }}
            ]},
        ).execute()

        refreshed = self._sheets.spreadsheets().get(
            spreadsheetId=spreadsheet_id,
            fields="spreadsheetId,spreadsheetUrl,sheets/properties",
        ).execute()

        sheet_ids = {
            s["properties"]["title"]: s["properties"]["sheetId"]
            for s in refreshed["sheets"]
        }

        issue_like_tabs = ["Issues"] + [
            f"Round {rn}" for rn in sorted(round_numbers or [])
        ]

        extra_statuses = []
        for issue in issues:
            st = issue.status
            if st and st not in ESTADO_JIRA_COLORS and st not in extra_statuses:
                extra_statuses.append(st)

        estado_colors = dict(ESTADO_JIRA_COLORS)
        for i, st in enumerate(extra_statuses):
            estado_colors[st] = EXTRA_STATUS_COLORS[i % len(EXTRA_STATUS_COLORS)]

        self._apply_bfv_formatting(spreadsheet_id, sheet_ids, issue_like_tabs)
        self._apply_data_validation(
            spreadsheet_id, sheet_ids, issue_like_tabs, len(issues),
            estado_colors,
        )
        self._apply_conditional_colors(
            spreadsheet_id, sheet_ids, issue_like_tabs, len(issues),
            estado_colors,
        )
        self._write_bfv_data(
            spreadsheet_id, jira_base_url, issues, issue_like_tabs,
            default_status, tester,
        )

        return refreshed

    def _apply_bfv_formatting(
        self,
        spreadsheet_id: str,
        sheet_ids: dict[str, int],
        issue_like_tabs: list[str],
    ) -> None:
        summary_id = sheet_ids["Summary"]

        all_cell = {
            "userEnteredFormat": {
                "wrapStrategy": "WRAP",
                "verticalAlignment": "TOP",
                "textFormat": {"fontFamily": "Arial"},
            }
        }
        all_fields = "userEnteredFormat(wrapStrategy,verticalAlignment,textFormat)"

        header_cell = {
            "userEnteredFormat": {
                "backgroundColor": HEADER_BG,
                "textFormat": {"fontFamily": "Arial", "bold": True},
                "wrapStrategy": "WRAP",
                "verticalAlignment": "TOP",
            }
        }
        header_fields = "userEnteredFormat(backgroundColor,textFormat,wrapStrategy,verticalAlignment)"

        requests: list[dict[str, Any]] = []

        all_sids = list(sheet_ids.values())
        for sid in all_sids:
            requests.append({
                "repeatCell": {
                    "range": {"sheetId": sid},
                    "cell": all_cell,
                    "fields": all_fields,
                }
            })

        for tab_name in issue_like_tabs:
            sid = sheet_ids[tab_name]
            requests.extend([
                {
                    "repeatCell": {
                        "range": _range(sid, rows=(0, 1), cols=(0, NUM_COLS)),
                        "cell": header_cell,
                        "fields": header_fields,
                    }
                },
                _col_width(sid, 2, 3, 320),   # C: URL Ticket
                _col_width(sid, 3, 4, 280),   # D: Comentario
                _col_width(sid, 9, 10, 350),  # J: Comments Internal
                {
                    "mergeCells": {
                        "range": _range(sid, rows=(1, 2), cols=(0, NUM_COLS)),
                        "mergeType": "MERGE_ALL",
                    }
                },
            ])

        self._sheets.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={"requests": requests},
        ).execute()

    def _apply_data_validation(
        self,
        spreadsheet_id: str,
        sheet_ids: dict[str, int],
        issue_like_tabs: list[str],
        num_issues: int,
        estado_colors: dict[str, dict[str, float]],
    ) -> None:
        data_row_start = 3
        data_row_end = max(data_row_start + num_issues, data_row_start + 200)

        requests: list[dict[str, Any]] = []

        validations = [
            (5, list(estado_colors.keys())),
            (6, list(QA_RESULT_COLORS.keys())),
            (7, list(STATUS_COLORS.keys())),
        ]

        for tab_name in issue_like_tabs:
            sid = sheet_ids[tab_name]
            for col_idx, options in validations:
                requests.append({
                    "setDataValidation": {
                        "range": _range(
                            sid,
                            rows=(data_row_start, data_row_end),
                            cols=(col_idx, col_idx + 1),
                        ),
                        "rule": {
                            "condition": {
                                "type": "ONE_OF_LIST",
                                "values": [
                                    {"userEnteredValue": v} for v in options
                                ],
                            },
                            "showCustomUi": True,
                            "strict": False,
                        },
                    }
                })

        if requests:
            self._sheets.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id,
                body={"requests": requests},
            ).execute()

    def _apply_conditional_colors(
        self,
        spreadsheet_id: str,
        sheet_ids: dict[str, int],
        issue_like_tabs: list[str],
        num_issues: int,
        estado_colors: dict[str, dict[str, float]],
    ) -> None:
        data_row_start = 3
        data_row_end = max(data_row_start + num_issues, data_row_start + 200)

        color_maps: list[tuple[int, dict[str, dict[str, float]]]] = [
            (5, estado_colors),
            (6, QA_RESULT_COLORS),
            (7, STATUS_COLORS),
        ]

        requests: list[dict[str, Any]] = []
        rule_idx = 0

        for tab_name in issue_like_tabs:
            sid = sheet_ids[tab_name]
            for col_idx, cmap in color_maps:
                for value, bg in cmap.items():
                    requests.append({
                        "addConditionalFormatRule": {
                            "rule": {
                                "ranges": [_range(
                                    sid,
                                    rows=(data_row_start, data_row_end),
                                    cols=(col_idx, col_idx + 1),
                                )],
                                "booleanRule": {
                                    "condition": {
                                        "type": "TEXT_EQ",
                                        "values": [{"userEnteredValue": value}],
                                    },
                                    "format": {
                                        "backgroundColor": bg,
                                        "textFormat": {
                                            "foregroundColor": {"red": 0, "green": 0, "blue": 0},
                                            "bold": True,
                                        },
                                    },
                                },
                            },
                            "index": rule_idx,
                        }
                    })
                    rule_idx += 1

        if requests:
            self._sheets.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id,
                body={"requests": requests},
            ).execute()

    def _write_bfv_data(
        self,
        spreadsheet_id: str,
        jira_base_url: str,
        issues: list[Any],
        issue_like_tabs: list[str],
        default_status: str,
        tester: str = "",
    ) -> None:
        data: list[dict[str, Any]] = []

        issues_rows: list[list[str]] = [
            ISSUES_HEADERS,
            ["Date", "", "", "", "", "", "", "", "", ""],
            ["", "", QA_TEMPLATE, "", "", "", "", "", "", ""],
        ]
        for idx, issue in enumerate(issues, start=1):
            url = f"{jira_base_url}/browse/{issue.key}"
            issues_rows.append([
                str(idx),
                tester,
                url,
                "",
                "",
                issue.status,
                "",
                "",
                "",
                "",
            ])
        data.append({"range": "Issues!A1", "values": issues_rows})

        for tab_name in issue_like_tabs:
            if tab_name == "Issues":
                continue
            data.append({
                "range": f"'{tab_name}'!A1",
                "values": [
                    ISSUES_HEADERS,
                    ["Date", "", "", "", "", "", "", "", "", ""],
                    ["", "", QA_TEMPLATE, "", "", "", "", "", "", ""],
                ],
            })

        data.append({
            "range": "Summary!A2",
            "values": [
                ["We have completed our review of the tickets listed "
                 "under the specified status."],
                ["QA Passed: 0"],
                ["QA Failed: 0"],
                ["Can't / Won't Fix: 0"],
            ],
        })

        self._sheets.spreadsheets().values().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={"valueInputOption": "RAW", "data": data},
        ).execute()

    # ------------------------------------------------------------------
    # Generic read helpers
    # ------------------------------------------------------------------

    def read_rows(self, spreadsheet_id: str, range_: str = "A:Z") -> list[list[str]]:
        result = self._sheets.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range=range_,
        ).execute()
        return result.get("values", [])


# ------------------------------------------------------------------
# Helpers for building Sheets API request dicts
# ------------------------------------------------------------------

def _range(
    sheet_id: int,
    rows: tuple[int, int],
    cols: tuple[int, int],
) -> dict[str, int]:
    return {
        "sheetId": sheet_id,
        "startRowIndex": rows[0],
        "endRowIndex": rows[1],
        "startColumnIndex": cols[0],
        "endColumnIndex": cols[1],
    }


def _col_width(sheet_id: int, start: int, end: int, px: int) -> dict[str, Any]:
    return {
        "updateDimensionProperties": {
            "range": {
                "sheetId": sheet_id,
                "dimension": "COLUMNS",
                "startIndex": start,
                "endIndex": end,
            },
            "properties": {"pixelSize": px},
            "fields": "pixelSize",
        }
    }

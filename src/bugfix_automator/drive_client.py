"""Cliente de Google Drive/Sheets para crear y cargar reportes."""

from __future__ import annotations

from datetime import datetime
from typing import Iterable

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


class DriveClient:
    """Cliente para crear hojas de cálculo y escribir datos tabulares."""

    def __init__(self, service_account_file: str) -> None:
        credentials = Credentials.from_service_account_file(
            service_account_file,
            scopes=SCOPES,
        )
        self._sheets = build("sheets", "v4", credentials=credentials)
        self._drive = build("drive", "v3", credentials=credentials)

    def create_spreadsheet(self, title_prefix: str, folder_id: str | None = None) -> dict:
        title = f"{title_prefix} - {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC"
        spreadsheet = (
            self._sheets.spreadsheets()
            .create(body={"properties": {"title": title}}, fields="spreadsheetId,spreadsheetUrl")
            .execute()
        )

        if folder_id:
            file_id = spreadsheet["spreadsheetId"]
            current_parents = (
                self._drive.files()
                .get(fileId=file_id, fields="parents")
                .execute()
                .get("parents", [])
            )
            self._drive.files().update(
                fileId=file_id,
                addParents=folder_id,
                removeParents=",".join(current_parents),
                fields="id, parents",
            ).execute()

        return spreadsheet

    def write_rows(self, spreadsheet_id: str, rows: Iterable[list[str | int]]) -> None:
        self._sheets.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range="A1",
            valueInputOption="RAW",
            body={"values": list(rows)},
        ).execute()

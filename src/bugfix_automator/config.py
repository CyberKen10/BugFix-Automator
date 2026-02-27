"""Configuración de la aplicación vía variables de entorno."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class JiraConfig:
    base_url: str
    email: str
    api_token: str


@dataclass(frozen=True)
class GoogleConfig:
    service_account_file: str
    drive_folder_id: Optional[str] = None


@dataclass(frozen=True)
class AppConfig:
    jira: JiraConfig
    google: GoogleConfig
    jira_status: str = "For Review"
    time_field_priority: tuple[str, ...] = (
        "timespent",
        "timeoriginalestimate",
    )


def load_env_file(path: str = ".env") -> None:
    """Carga variables simples KEY=VALUE desde .env sin dependencias externas."""
    env_path = Path(path)
    if not env_path.exists():
        candidate = Path("..") / path
        if candidate.exists():
            env_path = candidate
    if not env_path.exists():
        return

    env_dir = str(env_path.resolve().parent)

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key == "GOOGLE_SERVICE_ACCOUNT_FILE" and not Path(value).is_absolute():
            value = str(Path(env_dir) / value)
        os.environ.setdefault(key, value)


def load_config_from_env() -> AppConfig:
    """Carga configuración obligatoria desde variables de entorno."""
    missing = []
    for key in ["JIRA_BASE_URL", "JIRA_EMAIL", "JIRA_API_TOKEN", "GOOGLE_SERVICE_ACCOUNT_FILE"]:
        if not os.getenv(key):
            missing.append(key)

    if missing:
        raise ValueError(
            f"Faltan variables de entorno requeridas: {', '.join(missing)}"
        )

    jira = JiraConfig(
        base_url=os.environ["JIRA_BASE_URL"].rstrip("/"),
        email=os.environ["JIRA_EMAIL"],
        api_token=os.environ["JIRA_API_TOKEN"],
    )
    google = GoogleConfig(
        service_account_file=os.environ["GOOGLE_SERVICE_ACCOUNT_FILE"],
        drive_folder_id=os.getenv("GOOGLE_DRIVE_FOLDER_ID"),
    )

    return AppConfig(
        jira=jira,
        google=google,
        jira_status=os.getenv("JIRA_STATUS", "For Review"),
    )

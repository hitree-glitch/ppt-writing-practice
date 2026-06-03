from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class KiwoomConfig:
    base_url: str
    mock_base_url: str
    use_mock: bool
    app_key: str
    secret_key: str
    account_aliases: dict[str, str]
    endpoints: dict[str, str]
    tr_ids: dict[str, str]
    field_map: dict[str, list[str]]

    @property
    def active_base_url(self) -> str:
        return self.mock_base_url if self.use_mock else self.base_url


@dataclass(frozen=True)
class GoogleConfig:
    spreadsheet_id: str
    spreadsheet_title: str
    service_account_file: str
    access_token: str


@dataclass(frozen=True)
class ReportConfig:
    include_samsung_unlinked: bool
    default_currency: str
    mask_accounts: bool


@dataclass(frozen=True)
class AppConfig:
    kiwoom: KiwoomConfig
    google: GoogleConfig
    report: ReportConfig


def load_config(path: str | Path) -> AppConfig:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    kiwoom = raw.get("kiwoom", {})
    google = raw.get("google", {})
    report = raw.get("report", {})
    return AppConfig(
        kiwoom=KiwoomConfig(
            base_url=kiwoom.get("base_url", "https://api.kiwoom.com").rstrip("/"),
            mock_base_url=kiwoom.get("mock_base_url", "https://mockapi.kiwoom.com").rstrip("/"),
            use_mock=bool(kiwoom.get("use_mock", False)),
            app_key=kiwoom.get("app_key", ""),
            secret_key=kiwoom.get("secret_key", ""),
            account_aliases=dict(kiwoom.get("account_aliases", {})),
            endpoints=dict(kiwoom.get("endpoints", {})),
            tr_ids=dict(kiwoom.get("tr_ids", {})),
            field_map=_normalize_field_map(kiwoom.get("field_map", {})),
        ),
        google=GoogleConfig(
            spreadsheet_id=google.get("spreadsheet_id", ""),
            spreadsheet_title=google.get("spreadsheet_title", "월별 실현손익 리포트"),
            service_account_file=google.get("service_account_file", ""),
            access_token=google.get("access_token", ""),
        ),
        report=ReportConfig(
            include_samsung_unlinked=bool(report.get("include_samsung_unlinked", True)),
            default_currency=report.get("default_currency", "KRW"),
            mask_accounts=bool(report.get("mask_accounts", True)),
        ),
    )


def validate_config(config: AppConfig, require_google: bool = True) -> list[str]:
    missing: list[str] = []
    if not config.kiwoom.app_key:
        missing.append("kiwoom.app_key")
    if not config.kiwoom.secret_key:
        missing.append("kiwoom.secret_key")
    if not config.kiwoom.endpoints.get("token"):
        missing.append("kiwoom.endpoints.token")
    if not config.kiwoom.endpoints.get("account_list"):
        missing.append("kiwoom.endpoints.account_list")
    if not config.kiwoom.endpoints.get("realized_pnl"):
        missing.append("kiwoom.endpoints.realized_pnl")
    if not config.kiwoom.tr_ids.get("account_list"):
        missing.append("kiwoom.tr_ids.account_list")
    if not config.kiwoom.tr_ids.get("realized_pnl"):
        missing.append("kiwoom.tr_ids.realized_pnl")
    if require_google and not (
        config.google.service_account_file or config.google.access_token
    ):
        missing.append("google.service_account_file or google.access_token")
    return missing


def _normalize_field_map(raw: dict[str, Any]) -> dict[str, list[str]]:
    normalized: dict[str, list[str]] = {}
    for key, value in raw.items():
        if isinstance(value, str):
            normalized[key] = [value]
        else:
            normalized[key] = [str(item) for item in value]
    return normalized

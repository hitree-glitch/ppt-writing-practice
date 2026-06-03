from __future__ import annotations

import json
from typing import Any
from urllib import error, parse, request

from .config import GoogleConfig
from .report import SheetPayload


class GoogleSheetsError(RuntimeError):
    pass


class GoogleSheetsClient:
    def __init__(self, config: GoogleConfig) -> None:
        self.config = config
        self._token: str | None = None

    def ensure_spreadsheet(self) -> str:
        if self.config.spreadsheet_id:
            return self.config.spreadsheet_id
        body = {"properties": {"title": self.config.spreadsheet_title}}
        response = self._request(
            "POST",
            "https://sheets.googleapis.com/v4/spreadsheets",
            body,
        )
        spreadsheet_id = response.get("spreadsheetId")
        if not spreadsheet_id:
            raise GoogleSheetsError(f"Google Sheet 생성 실패: {response}")
        return str(spreadsheet_id)

    def replace_report(self, spreadsheet_id: str, payload: SheetPayload) -> None:
        self._ensure_sheets(spreadsheet_id, list(payload.keys()))
        data = []
        clear_ranges = []
        for sheet_name, values in payload.items():
            quoted = _quote_sheet(sheet_name)
            clear_ranges.append(f"{quoted}!A:Z")
            data.append({"range": f"{quoted}!A1", "values": values})
        self._request(
            "POST",
            f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}/values:batchClear",
            {"ranges": clear_ranges},
        )
        self._request(
            "POST",
            f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}/values:batchUpdate",
            {"valueInputOption": "USER_ENTERED", "data": data},
        )

    def _ensure_sheets(self, spreadsheet_id: str, sheet_names: list[str]) -> None:
        metadata = self._request(
            "GET",
            f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}?fields=sheets.properties.title",
        )
        existing = {
            sheet["properties"]["title"]
            for sheet in metadata.get("sheets", [])
            if sheet.get("properties", {}).get("title")
        }
        requests = [
            {"addSheet": {"properties": {"title": name}}}
            for name in sheet_names
            if name not in existing
        ]
        if requests:
            self._request(
                "POST",
                f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}:batchUpdate",
                {"requests": requests},
            )

    def _request(self, method: str, url: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
        headers = {"Authorization": f"Bearer {self._access_token()}"}
        data = None
        if body is not None:
            headers["Content-Type"] = "application/json"
            data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        req = request.Request(url, data=data, headers=headers, method=method)
        try:
            with request.urlopen(req, timeout=30) as res:
                raw = res.read().decode("utf-8")
                return json.loads(raw) if raw else {}
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise GoogleSheetsError(f"Google Sheets HTTP 오류 {exc.code}: {detail}") from exc
        except error.URLError as exc:
            raise GoogleSheetsError(f"Google Sheets 네트워크 오류: {exc.reason}") from exc

    def _access_token(self) -> str:
        if self.config.access_token:
            return self.config.access_token
        if self._token:
            return self._token
        if not self.config.service_account_file:
            raise GoogleSheetsError("google.service_account_file 또는 google.access_token이 필요합니다.")
        try:
            from google.oauth2 import service_account
            from google.auth.transport.requests import Request
        except ImportError as exc:
            raise GoogleSheetsError(
                "서비스 계정 인증에는 google-auth 패키지가 필요합니다. "
                "설치가 어렵다면 google.access_token을 설정하세요."
            ) from exc
        scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        credentials = service_account.Credentials.from_service_account_file(
            self.config.service_account_file,
            scopes=scopes,
        )
        credentials.refresh(Request())
        self._token = credentials.token
        return str(self._token)


def _quote_sheet(name: str) -> str:
    return "'" + name.replace("'", "''") + "'"

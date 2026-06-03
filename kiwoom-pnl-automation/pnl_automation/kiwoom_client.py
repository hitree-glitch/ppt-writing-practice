from __future__ import annotations

import json
from datetime import date
from typing import Any
from urllib import error, request

from .config import KiwoomConfig


class KiwoomApiError(RuntimeError):
    pass


class KiwoomClient:
    def __init__(self, config: KiwoomConfig) -> None:
        self.config = config
        self._token: str | None = None

    def get_token(self) -> str:
        if self._token:
            return self._token
        body = {
            "grant_type": "client_credentials",
            "appkey": self.config.app_key,
            "secretkey": self.config.secret_key,
        }
        response = self._post(self.config.endpoints["token"], body, auth=False)
        token = response.get("token")
        if not token:
            raise KiwoomApiError(f"키움 토큰 발급 실패: {response}")
        self._token = str(token)
        return self._token

    def get_accounts(self) -> list[str]:
        response = self._post_tr(
            self.config.endpoints["account_list"],
            self.config.tr_ids["account_list"],
            {},
        )
        accounts = _extract_values(response, ("account_no", "acct_no", "계좌번호"))
        return [str(item) for item in accounts if item]

    def get_realized_pnl(self, account: str, start: date, end: date) -> list[dict[str, Any]]:
        payload = {
            "account_no": account,
            "acct_no": account,
            "start_dt": start.strftime("%Y%m%d"),
            "end_dt": end.strftime("%Y%m%d"),
            "inq_strt_dt": start.strftime("%Y%m%d"),
            "inq_end_dt": end.strftime("%Y%m%d"),
        }
        response = self._post_tr(
            self.config.endpoints["realized_pnl"],
            self.config.tr_ids["realized_pnl"],
            payload,
        )
        records = _extract_records(response)
        for record in records:
            record.setdefault("account_no", account)
        return records

    def _post_tr(self, endpoint: str, tr_id: str, body: dict[str, Any]) -> dict[str, Any]:
        headers = {
            "authorization": f"Bearer {self.get_token()}",
            "api-id": tr_id,
            "Content-Type": "application/json;charset=UTF-8",
        }
        return self._post(endpoint, body, headers=headers)

    def _post(
        self,
        endpoint: str,
        body: dict[str, Any],
        auth: bool = True,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        url = f"{self.config.active_base_url}{endpoint}"
        merged_headers = {"Content-Type": "application/json;charset=UTF-8"}
        if auth and headers:
            merged_headers.update(headers)
        elif headers:
            merged_headers.update(headers)
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        req = request.Request(url, data=data, headers=merged_headers, method="POST")
        try:
            with request.urlopen(req, timeout=30) as res:
                return json.loads(res.read().decode("utf-8"))
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise KiwoomApiError(f"키움 HTTP 오류 {exc.code}: {detail}") from exc
        except error.URLError as exc:
            raise KiwoomApiError(f"키움 네트워크 오류: {exc.reason}") from exc


def _extract_records(response: dict[str, Any]) -> list[dict[str, Any]]:
    for value in response.values():
        if isinstance(value, list) and all(isinstance(item, dict) for item in value):
            return value
    if all(isinstance(value, (str, int, float, type(None))) for value in response.values()):
        return [response]
    return []


def _extract_values(response: dict[str, Any], keys: tuple[str, ...]) -> list[Any]:
    values: list[Any] = []
    for key in keys:
        value = response.get(key)
        if isinstance(value, list):
            values.extend(value)
        elif value:
            values.append(value)
    for records in response.values():
        if isinstance(records, list):
            for record in records:
                if isinstance(record, dict):
                    for key in keys:
                        if record.get(key):
                            values.append(record[key])
    return values

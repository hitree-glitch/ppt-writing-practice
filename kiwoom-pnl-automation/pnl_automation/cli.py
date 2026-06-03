from __future__ import annotations

import argparse
import json
import sys
from datetime import date, timedelta
from pathlib import Path

from .config import load_config, validate_config
from .google_sheets import GoogleSheetsClient, GoogleSheetsError
from .kiwoom_client import KiwoomApiError, KiwoomClient
from .models import AccountStatus, CheckIssue
from .normalizer import normalize_kiwoom_records
from .report import build_report_payload
from .sample_data import sample_rows
from .utils import mask_account, parse_date


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="키움 월별 실현손익 Google Sheets 자동화")
    parser.add_argument("--config", default="config.json", help="설정 JSON 경로")
    parser.add_argument("--from", dest="date_from", help="조회 시작일 YYYY-MM-DD")
    parser.add_argument("--to", dest="date_to", help="조회 종료일 YYYY-MM-DD")
    parser.add_argument("--validate-config", action="store_true", help="설정 누락만 확인")
    parser.add_argument("--dry-run", action="store_true", help="Google Sheets에 쓰지 않고 JSON 미리보기 출력")
    parser.add_argument("--sample-data", action="store_true", help="키움 API 대신 샘플 데이터 사용")
    parser.add_argument("--create-spreadsheet", action="store_true", help="spreadsheet_id가 없으면 새 Google Sheet 생성")
    args = parser.parse_args(argv)

    config = load_config(args.config)
    missing = validate_config(config, require_google=not args.dry_run)
    if args.validate_config:
        if missing:
            print("설정 누락:")
            for item in missing:
                print(f"- {item}")
            return 2
        print("설정 OK")
        return 0

    if missing and not args.sample_data:
        print("설정이 부족해서 자동 수집을 시작하지 않습니다.")
        for item in missing:
            print(f"- {item}")
        return 2

    date_from, date_to = _date_range(args.date_from, args.date_to)
    checks: list[CheckIssue] = []
    accounts: list[AccountStatus] = []

    if args.sample_data:
        rows = sample_rows()
        accounts.append(AccountStatus("키움증권", "123****890", "키움-국내", "연동됨", "샘플 데이터"))
        accounts.append(AccountStatus("키움증권", "987****210", "키움-해외", "연동됨", "샘플 데이터"))
    else:
        try:
            rows, account_statuses, api_checks = _collect_kiwoom(config, date_from, date_to)
            accounts.extend(account_statuses)
            checks.extend(api_checks)
        except KiwoomApiError as exc:
            checks.append(CheckIssue("error", "키움증권", "", str(exc)))
            rows = []

    if config.report.include_samsung_unlinked:
        accounts.append(AccountStatus("삼성증권", "", "삼성증권", "미연동", "공개 개인용 계좌 API 미확인"))
        checks.append(CheckIssue("info", "삼성증권", "", "완전 무인 조건에서는 1차 자동 수집 제외"))

    payload = build_report_payload(rows, accounts, checks)

    if args.dry_run:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0 if not any(check.severity == "error" for check in checks) else 1

    try:
        sheets = GoogleSheetsClient(config.google)
        spreadsheet_id = sheets.ensure_spreadsheet() if args.create_spreadsheet else config.google.spreadsheet_id
        if not spreadsheet_id:
            print("google.spreadsheet_id가 없습니다. 새 시트를 만들려면 --create-spreadsheet를 사용하세요.")
            return 2
        sheets.replace_report(spreadsheet_id, payload)
        print(f"Google Sheets 갱신 완료: https://docs.google.com/spreadsheets/d/{spreadsheet_id}")
        return 0 if not any(check.severity == "error" for check in checks) else 1
    except GoogleSheetsError as exc:
        print(str(exc))
        return 1


def _collect_kiwoom(config, date_from: date, date_to: date):
    client = KiwoomClient(config.kiwoom)
    raw_accounts = client.get_accounts()
    if not raw_accounts and config.kiwoom.account_aliases:
        raw_accounts = list(config.kiwoom.account_aliases.keys())
    rows = []
    checks: list[CheckIssue] = []
    statuses: list[AccountStatus] = []

    for account in raw_accounts:
        display = mask_account(account) if config.report.mask_accounts else account
        alias = config.kiwoom.account_aliases.get(account, display)
        statuses.append(AccountStatus("키움증권", display, alias, "연동됨"))
        records = client.get_realized_pnl(account, date_from, date_to)
        normalized, row_checks = normalize_kiwoom_records(records, config)
        rows.extend(normalized)
        checks.extend(row_checks)

    if not raw_accounts:
        checks.append(CheckIssue("warn", "키움증권", "", "조회된 계좌가 없습니다. account_aliases fallback도 비어 있습니다."))
    return rows, statuses, checks


def _date_range(raw_from: str | None, raw_to: str | None) -> tuple[date, date]:
    today = date.today()
    default_from = date(today.year, 1, 1)
    parsed_from = parse_date(raw_from) if raw_from else default_from
    parsed_to = parse_date(raw_to) if raw_to else today
    if not parsed_from or not parsed_to:
        raise SystemExit("날짜는 YYYY-MM-DD 형식으로 입력하세요.")
    if parsed_from > parsed_to:
        raise SystemExit("조회 시작일이 종료일보다 늦습니다.")
    return parsed_from, parsed_to


if __name__ == "__main__":
    raise SystemExit(main())

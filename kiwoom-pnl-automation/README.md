# Kiwoom Monthly PnL Automation

키움증권 REST API에서 실현손익 데이터를 가져와 월별/계좌별 Google Sheets 리포트를 갱신하는 로컬 CLI입니다.

삼성증권은 공개 개인용 계좌 API가 확인되지 않아 1차 범위에서는 자동 수집하지 않고, 리포트의 `Accounts` 탭에 `미연동` 상태로 표시합니다.

## 1. 설정

`config.example.json`을 `config.json`으로 복사한 뒤 값을 채웁니다.

```powershell
Copy-Item config.example.json config.json
```

필수값:

- `kiwoom.app_key`, `kiwoom.secret_key`: 키움 REST API 앱키/시크릿키
- `google.spreadsheet_id`: 갱신할 Google Sheets ID. 비우면 `--create-spreadsheet` 실행 시 새 시트를 생성합니다.
- `google.service_account_file` 또는 `google.access_token`: Google Sheets API 인증 정보

서비스 계정 방식을 쓰는 경우 Google Sheet를 서비스 계정 이메일에 공유해야 합니다.

## 2. 실행

설정만 검사:

```powershell
python -m pnl_automation.cli --config config.json --validate-config
```

샘플 데이터로 리포트 구조 확인:

```powershell
python -m pnl_automation.cli --config config.json --sample-data --dry-run
```

키움 API에서 가져와 Google Sheets 갱신:

```powershell
python -m pnl_automation.cli --config config.json --from 2026-01-01 --to 2026-12-31
```

키움 API 키가 아직 없으면 `--validate-config`에서 누락 항목을 알려주고, Google Sheets를 덮어쓰지 않습니다.

## 3. Windows 작업 스케줄러

`scripts/register_task.ps1`의 경로와 실행 시간을 확인한 뒤 관리자 PowerShell에서 실행합니다.

```powershell
powershell -ExecutionPolicy Bypass -File scripts/register_task.ps1
```

## 4. 리포트 탭

- `Dashboard`: 전체 월별 순손익, 증권사/계좌별 요약
- `Monthly`: `YYYY-MM` 기준 월별/계좌별 피벗 요약
- `Raw`: API 응답을 표준화한 상세 내역
- `Accounts`: 계좌 별칭과 연동 상태
- `Checks`: 누락값, API 오류, 미연동 증권사 등 확인 사항

## 5. 키움 API 메모

키움 REST API는 OAuth 토큰 발급 후 TR별 API를 호출합니다. 이 프로젝트는 기본적으로 계좌 조회 `ka00001`, 당일 실현손익 상세 `ka10077` 계열을 사용하도록 설정되어 있지만, 실제 발급 계정의 API 명세가 다르면 `config.json`의 `kiwoom.endpoints`와 `kiwoom.field_map`만 조정하면 됩니다.

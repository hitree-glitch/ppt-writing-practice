# 260326_aiposting.exe 분해 결과

## 대상

- 원본: `C:\Users\user\바탕화면\N 자동화\260326_aiposting.exe`
- SHA256: `68141AD73B29C5F2F4DB11CFE97203B696CCDBB7E224BB0C664A515244548E89`
- 크기: `128,625,685` bytes

## 판별 결과

- 패키징 방식: PyInstaller
- Python 런타임: Python 3.13 (`python313.dll`)
- PyInstaller TOC entries: `4,355`
- 추출된 전체 파일: `7,722`
- PYZ 내부 추출 `.pyc` 모듈: `3,365`

## 사용자 코드 엔트리

- 메인 스크립트: `extracted_260326_aiposting/AI글쓰기자동화봇_ChatGPT3.pyc`
- 코드 객체 수: `121`
- 문자열 상수 수: `962`
- 주요 top-level 객체:
  `generate_unique_title`, `IMAGE_PROMPT_PRESETS`, `DEFAULT_IMAGE_PROMPT_TEMPLATE`,
  `CopySuccessPopup`, `PromptEditorDialog`, `ImagePromptEditorDialog`,
  `PublishSetupDialog`, `normalize_markdown_for_post`, `BlogWriterBotTab`,
  `AutomationWorkerTab`, `LicenseCheckWorker`, `get_online_time`,
  `check_license`, `main`

## 생성 산출물

- `pyi_extract.py`
  - PyInstaller CArchive/PYZ 추출 스크립트
- `extracted_260326_aiposting/`
  - exe 내부 파일 전체 추출본
- `extracted_260326_aiposting/manifest.tsv`
  - PyInstaller 목차
- `extracted_260326_aiposting/PYZ-00.pyz_extracted/`
  - PYZ 내부 `.pyc` 모듈 추출본
- `recovered_depyo/decompiled/AI글쓰기자동화봇_ChatGPT3.py`
  - depyo 기반 best-effort 소스 복원본
- `recovered_byteripper_main.py`
  - byteripper 기반 비교 복원본
- `bytecode_report/AI글쓰기자동화봇_ChatGPT3.dis.txt`
  - 원본 `.pyc`에서 생성한 손실 없는 Python bytecode disassembly
- `bytecode_report/AI글쓰기자동화봇_ChatGPT3.code_map.txt`
  - 함수/클래스 코드 객체 지도
- `bytecode_report/AI글쓰기자동화봇_ChatGPT3.strings.txt`
  - 문자열 상수 목록
- `bytecode_report/AI글쓰기자동화봇_ChatGPT3.summary.txt`
  - 요약 정보

## 디컴파일러 검증

- `depyo 1.2.5`
  - Python 3.13 `.pyc`를 읽고 약 140KB의 소스형 결과를 생성함
  - 일부 `LOAD_SUPER_ATTR`, closure/cellvar, generator expression 복원 오류가 남아 `py_compile` 실패
- `byteripper 1.0.0`
  - 소스형 결과를 생성했으나 자체 검증에서 문법 오류 발생
  - `--ai-cleanup` 옵션은 외부 AI 호출 가능성이 있어 사용하지 않음
- `decompyle3/uncompyle6 3.9.3`
  - Python 3.13 bytecode 미지원으로 복원 불가

## 중요한 한계

`.exe` 안에는 원본 `.py` 파일이 아니라 Python 3.13 bytecode가 들어 있습니다. Bytecode에는 주석, 원래 줄바꿈, 일부 표현 방식이 저장되지 않습니다. 따라서 원본 `.py`와 1:1로 완전히 같은 코드를 자동 생성하는 것은 원본 파일이 없으면 보장할 수 없습니다.

다만 `bytecode_report/*.txt`는 원본 `.pyc`에서 직접 만든 자료라서 실행 의미를 추적하는 기준 자료로 사용할 수 있습니다. 실제로 다시 실행 가능한 `.py`를 만들려면 `recovered_depyo` 결과를 바탕으로 `bytecode_report`와 대조하면서 함수 단위로 수동 복구하는 절차가 필요합니다.

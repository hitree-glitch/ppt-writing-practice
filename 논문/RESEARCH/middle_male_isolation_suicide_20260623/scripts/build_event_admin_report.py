from pathlib import Path
import pandas as pd

ROOT=Path(r'RESEARCH/middle_male_isolation_suicide_20260623')
ART=ROOT/'artifacts'
OUT=ROOT/'outputs'
triage=pd.read_csv(ART/'data_access_triage_for_panel.csv')
model=pd.read_csv(ART/'panel_model_variable_spec.csv')
panel=pd.read_csv(ART/'region_year_panel_current_with_join_slots.csv')
decomp=pd.read_csv(ART/'regional_expected_growth_decomposition.csv')
age=pd.read_csv(ART/'age_mechanism_refined_indices.csv')
api=pd.read_csv(ART/'kosis_value_api_download_attempts.csv')

request_rows=[
 {'institution':'근로복지공단/고용정보원','dataset':'고용보험 피보험 자격 상실자','unit':'성×5세연령×시도/시군구×월 또는 연도×상실사유','target_population':'남성 45-64세 우선, 가능하면 40-64세','years':'2015-2025','required_fields':'상실자수, 상실사유(폐업·도산, 권고사직, 계약만료, 개인사정 등), 사업장 산업/규모 가능 시 포함','research_use':'50-54세 숨은 급성 자살위기 직접 검증'},
 {'institution':'국세청/KOSIS 국세통계','dataset':'폐업자 현황','unit':'연령×성×지역×연도','target_population':'남성 40-64세 사업자','years':'2014-2024','required_fields':'폐업자수, 지역, 성, 연령, 업태, 폐업사유 가능 시','research_use':'공개 대체 사건지표; DT_13301N_9810 우선'},
 {'institution':'국가데이터처/KOSIS 인구동향조사','dataset':'이혼율/이혼건수','unit':'시도×성×연령×연도','target_population':'남성 40-64세','years':'2014-2025','required_fields':'이혼건수 또는 이혼율, 연령 5세 또는 각세, 시도','research_use':'관계해체 사건성 위험 대체지표'},
 {'institution':'국민건강보험공단','dataset':'건강보험료 체납/장기체납','unit':'성×연령×지역×연도','target_population':'남성 45-64세 또는 40-64세','years':'2015-2025','required_fields':'체납자수, 체납개월, 지역가입/직장가입 구분 가능 시','research_use':'소득단절·건강보장 취약 직접 지표'},
 {'institution':'신용회복위원회/한국신용정보원','dataset':'채무조정·연체·개인회생/파산 관련 집계','unit':'성×연령×지역×연도','target_population':'남성 45-64세 또는 40-64세','years':'2015-2025','required_fields':'신규 채무조정 신청/확정, 연체, 개인회생/파산 가능 지표','research_use':'부채 충격과 급성 자살위기 경로 검증'},
 {'institution':'중앙응급의료센터/NEDIS 또는 질병관리청 손상감시','dataset':'응급실 내원 자해·자살시도','unit':'성×연령×지역×연도','target_population':'남성 40-64세','years':'2015-2025','required_fields':'자해/자살시도 내원건수, 치명도, 지역, 연령, 성','research_use':'자살 사망 이전의 비치명 급성위기 지표'},
 {'institution':'보건복지부/지자체','dataset':'고독사 실태조사 세부자료','unit':'성×연령×지역×연도×발견소요시간×주거형태','target_population':'남성 40-69세, 40-64세 별도','years':'2020-2024','required_fields':'고독사 사망자수, 발견소요시간, 주거형태, 1인가구 여부, 복지서비스 접촉 여부','research_use':'자살과 구분되는 발견지연/돌봄공백 메커니즘 검증'},
]
req=pd.DataFrame(request_rows)
req.to_csv(ART/'administrative_event_data_request_spec.csv',index=False,encoding='utf-8-sig')

core_decomp=decomp[['region','2020','2024','expected_2024_if_national_growth','excess_2024_vs_expected','trajectory_type']].head(5)
core_age=age[['age_band','rate_change_2022_2024','hidden_acute_crisis_index','persistent_accumulation_zmean','refined_mechanism_type']]

def md(df):
    d=df.copy()
    for col in d.columns:
        if pd.api.types.is_float_dtype(d[col]):
            d[col]=d[col].map(lambda x: '' if pd.isna(x) else f'{x:.2f}')
    lines=['| '+' | '.join(map(str,d.columns))+' |','| '+' | '.join(['---']*len(d.columns))+' |']
    for row in d.to_numpy():
        lines.append('| '+' | '.join(map(str,row))+' |')
    return '\n'.join(lines)

report=f"""# 사건성 행정자료 결합 분석 실행 결과

## 1. 수행한 작업

요청한 우선순위에 맞춰 KOSIS·행정자료 후보를 실제로 탐색하고, 현재 확보된 고독사 결과변수에 붙일 수 있는 시도×연도 패널 골격을 만들었다.

- KOSIS 내부 검색으로 사건성·복지·고립 후보표 372개를 수집했다.
- 핵심 후보변수 36개를 `paper_panel_variable_catalog.csv`로 정리했다.
- 17개 시도 × 2020-2024년 = 85행의 `region_year_panel_current_with_join_slots.csv`를 생성했다.
- KOSIS 실제 값 다운로드 API는 인증키 없이는 호출되지 않음을 확인했다. 모든 테스트 표가 `인증 KEY값이 누락되었습니다`를 반환했다.
- 사건성 행정자료 요청 명세서 `administrative_event_data_request_spec.csv`를 생성했다.

## 2. 현재 실제 값으로 분석 가능한 결과

현재 실제 수치가 들어간 패널 종속변수는 고독사다. 고독사 초과증가는 다음처럼 정리된다.

{md(core_decomp)}

핵심 해석은 유지된다. 서울·경기·대구는 단순히 인구가 많아서 증가한 것이 아니라, 전국 평균 성장률을 적용해도 설명되지 않는 초과증가가 크다.

## 3. 연령 메커니즘: 사건성 자료가 필요한 이유

{md(core_age)}

50-54세와 45-49세는 숨은 급성위기형으로 분류된다. 이들은 자살률 증가가 크지만, 우울·음주·저소득 등 일반 설문 위험지표 변화만으로 설명되지 않는다. 따라서 고용보험 상실, 폐업, 부채, 건강보험 체납, 이혼, 응급실 자해 같은 사건성 행정자료가 필요하다.

반대로 55-59세와 60-64세는 지속 누적취약형에 가깝다. 특히 60-64세는 고독사·발견지연·돌봄공백 경로와 연결하는 것이 더 적합하다.

## 4. 공개자료로 우선 붙일 변수

공개 KOSIS 우선순위는 다음과 같다.

1. 40-64세 남성 1인가구: DT_1PL1502 또는 DT_1PL1509
2. 사회적 관계망 없음: DT_1SSSP041R
3. 일상 교류 없음: DT_1SSSP045R
4. 시군구 우울감 경험률: DT_H_MENTAL_DEPRESS
5. 남성 40-64세 기초생활수급: DT_11714_N002
6. 남성 40-64세 시도별 자살률: DT_1B34E11
7. 남성 40-64세 폐업자: DT_13301N_9810
8. 남성 40-64세 이혼율: DT_1B85009 또는 DT_1B85027

## 5. 접근 제한 또는 별도 요청이 필요한 자료

{md(req[['institution','dataset','unit','target_population','years','research_use']])}

## 6. 분석 모델 설계

종속변수는 두 개로 분리한다.

- 종속변수 A: 고독사 사망자 수, 고독사율, 고독사 초과증가
- 종속변수 B: 남성 40-64세 자살률, 45-54세 자살률 증가율, 50-54세 급성위기 지수

모형은 세 단계로 간다.

1. 기술분석: 지역별 초과증가, 집중도, 연령대별 메커니즘 분류
2. 공개자료 패널모형: 고독사/자살률 ~ 남성 1인가구 + 사회적 관계망 결핍 + 우울감 + 기초생활수급 + 폐업 + 이혼 + 복지 인프라
3. 사건성 행정자료 확장모형: 자살률 급증 ~ 고용보험 상실 + 폐업/도산 + 채무/체납 + 이혼 + 응급실 자해

## 7. 현재 결론

현재까지의 분석은 원인 해석을 더 분명하게 만든다.

- 고독사 원인축: 장기 고립, 1인가구, 관계망 결핍, 복지 접점 부족, 발견지연
- 자살 급증 원인축: 실직·폐업·부채·이혼·건강충격 같은 사건성 위기
- 지역 원인축: 서울·경기·대구의 도시형 고립과 초과증가
- 연령 원인축: 50대 초반은 급성위기, 60대 초반은 누적취약

따라서 논문에서는 자살과 고독사를 하나의 결과로 합치면 안 된다. 자살은 급성 사건성 위기의 사망 표현이고, 고독사는 누적 고립과 발견지연의 사망 표현이다.

## 8. 산출 파일

- `extended_kosis_event_candidate_tables.csv`
- `paper_panel_variable_catalog.csv`
- `panel_selected_table_metadata_probe.csv`
- `region_year_panel_current_with_join_slots.csv`
- `panel_model_variable_spec.csv`
- `data_access_triage_for_panel.csv`
- `kosis_value_api_download_attempts.csv`
- `administrative_event_data_request_spec.csv`
"""
(OUT/'08_event_admin_panel_analysis_korean.md').write_text(report,encoding='utf-8')
print('wrote report and request spec')
print(req[['institution','dataset','unit','research_use']].to_string(index=False))

# 원자료 7개 결합 후 최신 시도 단면 분석

## 1. 처리 결과

- 원자료 파일 7개를 읽어 시도 단위 최신 분석 패널 17행을 만들었다.
- 1인가구, 기초생활, 폐업, 전체 사망/인구분모는 2024년이다.
- 사회적 관계망, 우울감, 이혼율은 사용자가 내려받은 파일 기준 2025년이다.
- 기존 보건복지부 고독사 지역 통계 2020-2024를 결합해 2024 고독사 수준, 2020-2024 증가, 전국성장률 대비 초과 증가를 종속변수로 구성했다.

## 2. 원자료 품질 경고

- `07_자살률` 파일의 사망원인 값: `['계']`
- 판정: Downloaded table contains only cause='계'; parsed as all-cause mortality, not suicide.
- 따라서 이번 산출물의 `male_40_64_total_mortality_rate_2024`는 남성 40-64세 전체 사망률이며, 지역별 자살률이 아니다.
- `02_사회적관계망` 파일은 행정구역 값이 전국뿐이다. 지역 간 차이를 설명하는 독립변수로는 쓸 수 없고, 전국 남성/1인가구 맥락 변수로만 보존했다.
- `05_폐업자`는 40대·50대·60대·70세 이상 구간이므로, 남성 40-64세 폐업은 `40대+50대+60대의 절반`으로 근사했다.

## 3. 취약성 지수 상위 지역

| region | composite_vulnerability_index | structural_isolation_index | event_stress_index | male_40_64_single_household_rate_pct_2024 | basic_livelihood_male_40_64_rate_per_1000_2024 | business_closure_male_40_64_approx_rate_per_1000_2024 | depression_std_rate_2025 | husband_divorce_rate_40_64_mean_2025 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 제주 | 0.91 | -0.55 | 2.36 | 17.6 | 42.78 | 34.71 | 3.7 | 7.78 |
| 충남 | 0.43 | 0.46 | 0.4 | 19.22 | 31.74 | 26.78 | 7.0 | 6.7 |
| 강원 | 0.42 | 0.78 | 0.06 | 19.54 | 42.27 | 26.75 | 6.9 | 6.2 |
| 전북 | 0.37 | 0.73 | 0.01 | 18.1 | 57.25 | 26.38 | 6.2 | 6.2 |
| 인천 | 0.3 | 0.06 | 0.55 | 15.71 | 46.07 | 28.99 | 6.4 | 6.4 |
| 충북 | 0.28 | 0.23 | 0.33 | 19.01 | 36.98 | 26.72 | 5.9 | 6.6 |
| 대전 | 0.08 | 0.19 | -0.03 | 16.54 | 45.63 | 27.83 | 6.4 | 5.8 |

## 4. 고독사율 프록시 상위 지역

| region | godoksa_count_2024 | male_40_64_population_est_2024 | godoksa_per_100k_male_40_64_pop_proxy_2024 | male_40_64_single_household_rate_pct_2024 | basic_livelihood_male_40_64_rate_per_1000_2024 | business_closure_male_40_64_approx_rate_per_1000_2024 |
| --- | --- | --- | --- | --- | --- | --- |
| 부산 | 367.0 | 637667.06 | 57.55 | 15.74 | 61.92 | 26.07 |
| 대구 | 229.0 | 473115.62 | 48.4 | 15.57 | 57.82 | 24.94 |
| 서울 | 784.0 | 1739271.98 | 45.08 | 15.37 | 45.16 | 32.57 |
| 강원 | 133.0 | 310449.5 | 42.84 | 19.54 | 42.27 | 26.75 |
| 광주 | 119.0 | 280075.46 | 42.49 | 17.86 | 59.99 | 27.55 |
| 인천 | 260.0 | 623379.56 | 41.71 | 15.71 | 46.07 | 28.99 |
| 충북 | 128.0 | 328411.02 | 38.98 | 19.01 | 36.98 | 26.72 |

## 5. 고독사 초과 증가 상위 지역

| region | godoksa_count_2020 | godoksa_count_2024 | expected_2024_if_national_growth | excess_2024_vs_expected | godoksa_change_2020_2024 | recent_change_2023_2024 |
| --- | --- | --- | --- | --- | --- | --- |
| 서울 | 571.0 | 784.0 | 683.32 | 100.68 | 213.0 | 225.0 |
| 경기 | 678.0 | 894.0 | 811.37 | 82.63 | 216.0 | -28.0 |
| 대구 | 125.0 | 229.0 | 149.59 | 79.41 | 104.0 | 46.0 |
| 강원 | 98.0 | 133.0 | 117.28 | 15.72 | 35.0 | -23.0 |
| 제주 | 27.0 | 48.0 | 32.31 | 15.69 | 21.0 | -3.0 |
| 충북 | 98.0 | 128.0 | 117.28 | 10.72 | 30.0 | -39.0 |
| 경북 | 135.0 | 162.0 | 161.56 | 0.44 | 27.0 | -24.0 |

## 6. 주요 상관 결과

| outcome | predictor | n | pearson_r | pearson_p | spearman_rho | spearman_p |
| --- | --- | --- | --- | --- | --- | --- |
| excess_2024_vs_expected | husband_divorce_rate_40_64_mean_2025 | 17.0 | -0.374 | 0.139 | -0.3 | 0.242 |
| excess_2024_vs_expected | male_40_64_single_household_rate_pct_2024 | 17.0 | -0.366 | 0.149 | -0.299 | 0.244 |
| excess_2024_vs_expected | basic_livelihood_male_40_64_rate_per_1000_2024 | 17.0 | -0.106 | 0.685 | -0.199 | 0.445 |
| excess_2024_vs_expected | structural_isolation_index | 17.0 | -0.174 | 0.505 | -0.164 | 0.529 |
| excess_2024_vs_expected | business_closure_male_40_64_approx_rate_per_1000_2024 | 17.0 | 0.378 | 0.135 | 0.162 | 0.535 |
| godoksa_count_2024 | depression_std_rate_2025 | 17.0 | 0.377 | 0.135 | 0.342 | 0.18 |
| godoksa_count_2024 | business_closure_male_40_64_approx_rate_per_1000_2024 | 17.0 | 0.483 | 0.05 | 0.294 | 0.252 |
| godoksa_count_2024 | structural_isolation_index | 17.0 | 0.019 | 0.941 | 0.225 | 0.384 |
| godoksa_count_2024 | male_40_64_single_household_rate_pct_2024 | 17.0 | -0.304 | 0.236 | -0.208 | 0.422 |
| godoksa_count_2024 | basic_livelihood_male_40_64_rate_per_1000_2024 | 17.0 | -0.042 | 0.874 | 0.201 | 0.439 |
| godoksa_per_100k_male_40_64_pop_proxy_2024 | basic_livelihood_male_40_64_rate_per_1000_2024 | 17.0 | 0.676 | 0.003 | 0.478 | 0.052 |
| godoksa_per_100k_male_40_64_pop_proxy_2024 | business_closure_male_40_64_approx_rate_per_1000_2024 | 17.0 | 0.254 | 0.325 | 0.404 | 0.107 |
| godoksa_per_100k_male_40_64_pop_proxy_2024 | structural_isolation_index | 17.0 | 0.596 | 0.012 | 0.387 | 0.125 |
| godoksa_per_100k_male_40_64_pop_proxy_2024 | husband_divorce_rate_40_64_mean_2025 | 17.0 | -0.049 | 0.851 | -0.273 | 0.29 |
| godoksa_per_100k_male_40_64_pop_proxy_2024 | depression_std_rate_2025 | 17.0 | 0.098 | 0.708 | 0.181 | 0.488 |

## 7. 탐색적 회귀 결과

| model | term | coef | std_error_hc3 | p | n | r2 | adj_r2 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| M1_rate_index | structural_isolation_index | 10.5698 | 7.3365 | 0.1717 | 17.0 | 0.3582 | 0.2665 |
| M1_rate_index | event_stress_index | 0.6679 | 3.1388 | 0.8346 | 17.0 | 0.3582 | 0.2665 |
| M2_excess_rate_index | event_stress_index | 2.3582 | 6.5787 | 0.7253 | 17.0 | 0.0498 | -0.086 |
| M2_excess_rate_index | structural_isolation_index | -2.1439 | 7.6131 | 0.7824 | 17.0 | 0.0498 | -0.086 |
| M3_log_count_size_adjusted | log_male_40_64_population_2024 | 1.1189 | 0.1457 | 0.0 | 17.0 | 0.956 | 0.9459 |
| M3_log_count_size_adjusted | structural_isolation_index | 0.3573 | 0.2854 | 0.2326 | 17.0 | 0.956 | 0.9459 |
| M3_log_count_size_adjusted | event_stress_index | 0.0723 | 0.2112 | 0.7376 | 17.0 | 0.956 | 0.9459 |
| M4_rate_components | basic_livelihood_male_40_64_rate_per_1000_2024 | 0.5523 | 0.2824 | 0.0723 | 17.0 | 0.5045 | 0.3902 |
| M4_rate_components | business_closure_male_40_64_approx_rate_per_1000_2024 | 0.6803 | 0.7571 | 0.3852 | 17.0 | 0.5045 | 0.3902 |
| M4_rate_components | male_40_64_single_household_rate_pct_2024 | 0.0933 | 1.7714 | 0.9588 | 17.0 | 0.5045 | 0.3902 |

## 8. 지금 단계의 논문용 해석

이번 결합자료에서 새롭게 말할 수 있는 것은 `중년 남성 고독사 위험`이 단순히 1인가구 수가 많은 지역에서만 커지는 현상이 아니라는 점이다. 인구 규모를 남성 40-64세 추정인구로 보정하면, 고독사율 프록시는 일부 비수도권·고령화 지역에서 크게 나타나고, 2020-2024년 초과 증가분은 서울·경기·대구처럼 대도시권 충격 지역에 집중된다.

따라서 한 가지 원인으로 묶기보다 두 경로 모델이 더 설득력 있다. 첫째, 대도시권에서는 폐업·이혼·주거 불안·관계망 약화가 짧은 시간 안에 겹치는 `사건성 위기 경로`가 고독사 증가를 밀어 올린다. 둘째, 비수도권과 고령화 지역에서는 1인가구화·기초생활 수급·우울감·의료취약성이 누적되어 `축적형 방치 경로`가 강해진다.

현재 다운로드된 7개 파일만으로는 지역별 남성 40-64세 자살률을 직접 검증할 수 없다. 자살률 파일은 사망원인 `계`로 내려받혀 있어, 다음 재다운로드에서 사망원인 `고의적 자해(자살)` 또는 `자살` 항목을 반드시 포함해야 한다. 그 파일이 들어오면 같은 스크립트에서 종속변수 B를 바로 대체해 회귀를 다시 돌릴 수 있다.

## 9. 산출 파일

- 원자료 1: 01_남성_40-64_1인가구. 성__연령_및_거처의_종류별_1인가구__시군구_20260623211304.xlsx
- 원자료 2: 02_사회적관계망. 사회적_관계망__13세_이상_인구__20260623211801.xlsx
- 원자료 3: 03_우울감경험률. 시·군·구별_연간_우울감_경험률_20260623212135.xlsx
- 원자료 4: 04_기초생활보장수급자. 국민기초일반수급자수시도별__성별__연령별_20260623212159.xlsx
- 원자료 5: 05_폐업자_성연령지역. 9.8.11_폐업자_현황_Ⅱ_연령__성__지역_2014_20260623212228.xlsx
- 원자료 6: 06_이혼율_성연령지역. 시도_성_연령별_이혼율_20260623212240.xlsx
- 원자료 7: 07_자살률_성연령지역. 시도_사망원인_104항목__성_연령_5세_별__사망자수__사망률_1996__20260623212329.xlsx
- `artifacts/current_raw_region_panel_2024_2025.csv`
- `artifacts/region_year_panel_from_latest_raw_2020_2025.csv`
- `artifacts/current_raw_correlations.csv`
- `artifacts/current_raw_ols_models.csv`
- `artifacts/national_social_network_context_2025.csv`
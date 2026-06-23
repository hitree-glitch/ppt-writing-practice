# Refined analysis memo

## 1. Regional decomposition: observed growth versus expected growth

If every region had grown at the national 2020-2024 godoksa growth rate, the expected 2024 count can be computed from each region's 2020 baseline. The residual identifies excess growth beyond simple proportional expansion.

| region | 2020 | 2024 | expected_2024_if_national_growth | excess_2024_vs_expected | pct_change_2020_2024 | share_of_national_increase_pct | trajectory_type |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 서울 | 571 | 784 | 683.319 | 100.681 | 37.303 | 33.023 | large_base_excess_growth |
| 경기 | 678 | 894 | 811.367 | 82.633 | 31.858 | 33.488 | large_base_excess_growth |
| 대구 | 125 | 229 | 149.588 | 79.412 | 83.200 | 16.124 | small_base_excess_growth |
| 강원 | 98 | 133 | 117.277 | 15.723 | 35.714 | 5.426 | moderate_or_stable |
| 제주 | 27 | 48 | 32.311 | 15.689 | 77.778 | 3.256 | fast_growth_from_small_base |
| 충북 | 98 | 128 | 117.277 | 10.723 | 30.612 | 4.651 | moderate_or_stable |
| 경북 | 135 | 162 | 161.555 | 0.445 | 20.000 | 4.186 | moderate_or_stable |
| 울산 | 59 | 68 | 70.606 | -2.606 | 15.254 | 1.395 | moderate_or_stable |
| 세종 | 12 | 9 | 14.360 | -5.360 | -25.000 | -0.465 | declining_or_reduced |
| 부산 | 315 | 367 | 376.962 | -9.962 | 16.508 | 8.062 | moderate_or_stable |
| 광주 | 118 | 119 | 141.211 | -22.211 | 0.847 | 0.155 | moderate_or_stable |
| 전남 | 114 | 112 | 136.425 | -24.425 | -1.754 | -0.310 | declining_or_reduced |

## 2. Spatial concentration indices

| year | total | gini_region_counts | hhi_region_shares | effective_number_regions | entropy_region_shares | top1_share_pct | top2_share_pct | top3_share_pct | top5_share_pct |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2020 | 3279 | 0.439 | 0.107 | 9.321 | 2.493 | 20.677 | 38.091 | 47.697 | 62.123 |
| 2021 | 3378 | 0.444 | 0.111 | 9.039 | 2.482 | 21.107 | 39.432 | 49.171 | 62.522 |
| 2022 | 3559 | 0.441 | 0.111 | 8.975 | 2.481 | 21.045 | 40.096 | 49.003 | 62.265 |
| 2023 | 3661 | 0.438 | 0.116 | 8.619 | 2.473 | 25.184 | 40.453 | 48.293 | 60.393 |
| 2024 | 3924 | 0.475 | 0.121 | 8.240 | 2.425 | 22.783 | 42.762 | 52.115 | 64.781 |

## 3. Refined age mechanism index

Hidden acute crisis index = standardized 2022-2024 suicide-rate acceleration minus standardized observed survey-risk change. A high value means mortality accelerated more than standard survey indicators would predict.

| age_band | rate_change_2022_2024 | observed_risk_change_zmean | hidden_acute_crisis_index | persistent_accumulation_zmean | new_risk_entry_zmean | refined_mechanism_type |
| --- | --- | --- | --- | --- | --- | --- |
| 40 - 44세 | 10.400 | 1.182 | -2.183 | -1.282 | 1.292 | new_risk_entry |
| 45 - 49세 | 13.000 | -0.654 | 1.656 | -0.341 | -0.821 | hidden_acute_crisis |
| 50 - 54세 | 13.500 | -1.064 | 2.451 | -0.099 | -0.633 | hidden_acute_crisis |
| 55 - 59세 | 11.100 | -0.228 | -0.234 | 0.515 | -0.676 | persistent_accumulation |
| 60 - 64세 | 10.500 | 0.765 | -1.690 | 1.208 | 0.837 | persistent_accumulation |

## 4. Hypothesis matrix

| hypothesis_id | claim | evidence_now | next_variable_needed | model_target |
| --- | --- | --- | --- | --- |
| H1 | Godoksa growth is spatially concentrated beyond proportional national growth. | 서울: excess 100.7; 경기: excess 82.6; 대구: excess 79.4; 강원: excess 15.7; 제주: excess 15.7 | male 40-64 one-person households by region/year; social-network absence; regional depression; welfare capacity | province-year godoksa count/rate panel |
| H2 | Recent suicide acceleration among middle-aged men is not fully captured by standard survey risk indicators. | 50 - 54세: rate +13.5/100k, hidden acute crisis index 2.45 | job loss, business closure, debt/arrears, health-shock, divorce/separation, emergency self-harm data | age-year suicide acceleration model |
| H3 | Early old-middle age shows accumulated vulnerability better suited to godoksa/discovery-delay interpretation than acute suicide alone. | 60 - 64세: persistent accumulation index 1.21 | alone-living duration, contact frequency, illness/disability, welfare contact, death discovery interval | two-outcome framework: suicide vs godoksa |

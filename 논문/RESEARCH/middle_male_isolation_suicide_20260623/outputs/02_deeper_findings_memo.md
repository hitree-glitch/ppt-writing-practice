# Deeper findings memo

This memo is generated from official godoksa summary tables, the local middle-male age-year suicide panel, and derived paper-ready indices.

## Core conclusion

The more novel claim is not that middle-aged men are vulnerable. The stronger claim is that the problem has two separable structures:

1. Godoksa growth is spatially concentrated.
2. Male midlife suicide risk is age-structured, not a single 40-64 pattern.
3. Suicide and godoksa should be modeled as related but different outcomes: acute crisis expression versus accumulated isolation and delayed discovery.

## Finding 1: regional concentration

National godoksa increased by 645 cases from 2020 to 2024. Seoul and Gyeonggi account for 429 of those additional cases (66.5%). Seoul, Gyeonggi, and Daegu together account for 533 cases (82.6%).

Top increase regions:

| region | 2020 | 2024 | change_2020_2024 | pct_change_2020_2024 | share_of_national_increase_pct | share_2024_pct |
| --- | --- | --- | --- | --- | --- | --- |
| 경기 | 678 | 894 | 216 | 31.9 | 33.5 | 22.8 |
| 서울 | 571 | 784 | 213 | 37.3 | 33.0 | 20.0 |
| 대구 | 125 | 229 | 104 | 83.2 | 16.1 | 5.8 |
| 부산 | 315 | 367 | 52 | 16.5 | 8.1 | 9.4 |
| 강원 | 98 | 133 | 35 | 35.7 | 5.4 | 3.4 |
| 충북 | 98 | 128 | 30 | 30.6 | 4.7 | 3.3 |
| 경북 | 135 | 162 | 27 | 20.0 | 4.2 | 4.1 |
| 제주 | 27 | 48 | 21 | 77.8 | 3.3 | 1.2 |

## Finding 2: middle-aged men are not one group

The age-band index shows a split between acute mortality excess and accumulated psychosocial vulnerability.

| age_band | suicide_rate | depression_high_wm | low_income_wm | problem_drinking_wm | psychosocial_vulnerability_zmean | mismatch_suicide_minus_psychosocial | paper_interpretation |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 40 - 44세 | 40.5 | 0.1 | 0.1 | 0.5 | -0.8 | -1.0 | younger_middle_age_baseline |
| 45 - 49세 | 45.3 | 0.2 | 0.2 | 0.5 | -0.4 | 0.3 | transition_and_drinking_risk |
| 50 - 54세 | 45.9 | 0.2 | 0.2 | 0.5 | -0.1 | 0.1 | transition_and_drinking_risk |
| 55 - 59세 | 49.2 | 0.2 | 0.2 | 0.5 | 0.4 | 0.9 | acute_mortality_excess |
| 60 - 64세 | 47.2 | 0.2 | 0.3 | 0.5 | 0.8 | -0.3 | latent_accumulated_vulnerability |

## Finding 3: 2024 deterioration is strongest in the early 50s

From 2022 to 2024, the largest male suicide-rate acceleration is in 50 - 54세 (+13.5 per 100,000).

| age_band | rate_change_2022_2024 | death_change_2022_2024 | rate_2024 | deaths_2024 | acceleration_rank_2022_2024 |
| --- | --- | --- | --- | --- | --- |
| 50 - 54세 | 13.5 | 294.0 | 54.5 | 1223.0 | 1 |
| 45 - 49세 | 13.0 | 201.0 | 54.9 | 1066.0 | 2 |
| 55 - 59세 | 11.1 | 259.0 | 55.4 | 1166.0 | 3 |
| 60 - 64세 | 10.5 | 229.0 | 51.3 | 1065.0 | 4 |
| 40 - 44세 | 10.4 | 201.0 | 47.5 | 953.0 | 5 |

## Finding 4: bridge table for the paper

| age_decade | godoksa_deaths_2024_allsex | share_of_total_godoksa_pct | male_suicide_deaths_2024 | male_suicide_rate_aggregate_2024 | share_of_male_40_64_suicide_deaths_pct | comparability_note |
| --- | --- | --- | --- | --- | --- | --- |
| 40s | 509 | 13.0 | 2019 | 51.1 | 36.9 | godoksa all sex; suicide male only |
| 50s | 1197 | 30.5 | 2389 | 54.9 | 43.7 | godoksa all sex; suicide male only |
| 60s | 1271 | 32.4 | 1065 | 51.3 | 19.5 | godoksa all sex; suicide male only; 60s suicide covers 60-64 only |

## Paper-ready framing

| finding_id | finding | core_number | paper_use | next_model |
| --- | --- | --- | --- | --- |
| F1 | Spatial increase concentration | 82.6% of the 2020-2024 national increase is concentrated in Seoul, Gyeonggi, and Daegu. | Turns godoksa from a general aging/isolation problem into an urban-regional concentration hypothesis. | province-year panel with single-person household, suicide, social-network, depression, welfare capacity variables |
| F2 | Fastest recent suicide deterioration | 50 - 54세 male suicide rate rose 13.5 per 100k from 2022 to 2024. | Separates recent crisis acceleration from long-run vulnerability. | age-year crisis acceleration model |
| F3 | Mortality-vulnerability mismatch | 55 - 59세 has the largest suicide-over-psychosocial mismatch; 60 - 64세 has the largest accumulated psychosocial vulnerability. | Argues that middle-aged men are not one homogeneous category. | two-outcome framework: suicide as acute expression, godoksa as accumulated isolation/discovery-delay expression |

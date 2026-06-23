# Individual profile deep dive

Source person-year data: C:\Users\user\OneDrive\D 대학원 박사\A 아주대\2. 사회심리학과 빅데이터 (박현준)\데이터\(남보라) Bigdata_middle_male.csv
Rows used after age filtering: 13,827; persons: 3,190; years: 2019-2024.

## Top profile shares by age, pooled years

| age_band | profile | weighted_share | n |
| --- | --- | --- | --- |
| 40 - 44세 | lower_observed_risk | 0.468 | 1078 |
| 50 - 54세 | lower_observed_risk | 0.435 | 1266 |
| 45 - 49세 | lower_observed_risk | 0.423 | 1183 |
| 55 - 59세 | lower_observed_risk | 0.408 | 1032 |
| 60 - 64세 | lower_observed_risk | 0.369 | 1051 |
| 40 - 44세 | alcohol_only | 0.280 | 705 |
| 45 - 49세 | alcohol_only | 0.276 | 775 |
| 50 - 54세 | alcohol_only | 0.262 | 777 |
| 55 - 59세 | alcohol_only | 0.229 | 603 |
| 60 - 64세 | alcohol_only | 0.207 | 595 |
| 60 - 64세 | psych_only | 0.109 | 297 |
| 60 - 64세 | low_income_only | 0.106 | 376 |

## Correlations between profile/flag shares and male suicide rate

| type | variable | pearson_r | spearman_r | permutation_p | n_cells |
| --- | --- | --- | --- | --- | --- |
| profile_share | psych_only | 0.382 | 0.410 | 0.038 | 30 |
| flag_or_mean | psych_any_share | 0.370 | 0.408 | 0.050 | 30 |
| flag_or_mean | depression_high_share | 0.370 | 0.466 | 0.049 | 30 |
| flag_or_mean | SELF_ESTEEM_mean | -0.369 | -0.420 | 0.045 | 30 |
| profile_share | low_income_only | 0.353 | 0.389 | 0.055 | 30 |
| profile_share | alcohol_only | -0.342 | -0.354 | 0.070 | 30 |
| profile_share | lower_observed_risk | -0.326 | -0.281 | 0.079 | 30 |
| flag_or_mean | self_esteem_low_share | 0.323 | 0.412 | 0.080 | 30 |
| flag_or_mean | low_income_share | 0.286 | 0.380 | 0.123 | 30 |
| flag_or_mean | CES_D_mean | 0.267 | 0.382 | 0.157 | 30 |
| flag_or_mean | income_mean | 0.255 | 0.311 | 0.167 | 30 |
| flag_or_mean | compound_psych_low_income_share | 0.244 | 0.283 | 0.194 | 30 |

## 2022-2024 risk-share changes by age band

| age_band | suicide_rate_change_2022_2024 | depression_high_share_change_2022_2024 | problem_drinking_share_change_2022_2024 | psych_any_share_change_2022_2024 | compound_psych_alcohol_share_change_2022_2024 | triple_psych_alcohol_low_income_share_change_2022_2024 |
| --- | --- | --- | --- | --- | --- | --- |
| 40 - 44세 | 10.400 | 0.042 | 0.035 | 0.049 | 0.010 | 0.000 |
| 45 - 49세 | 13.000 | 0.002 | 0.032 | -0.038 | -0.019 | -0.012 |
| 50 - 54세 | 13.500 | -0.008 | -0.035 | -0.033 | -0.056 | -0.004 |
| 55 - 59세 | 11.100 | -0.012 | -0.012 | 0.008 | 0.012 | -0.016 |
| 60 - 64세 | 10.500 | 0.017 | 0.037 | 0.042 | 0.011 | -0.003 |

## 2022-2024 persistence/new-entry risk by 2024 age band

| age_band_2024 | n_linked | weight_sum | persistent_depression_high_share | new_depression_high_share | remitted_depression_high_share | persistent_problem_drinking_share | new_problem_drinking_share | remitted_problem_drinking_share | persistent_psych_any_share | new_psych_any_share | remitted_psych_any_share | persistent_low_income_share | new_low_income_share | remitted_low_income_share | persistent_compound_psych_alcohol_share | new_compound_psych_alcohol_share | remitted_compound_psych_alcohol_share | persistent_triple_psych_alcohol_low_income_share | new_triple_psych_alcohol_low_income_share | remitted_triple_psych_alcohol_low_income_share |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 40 - 44세 | 342 | 432.629 | 0.025 | 0.135 | 0.062 | 0.140 | 0.198 | 0.078 | 0.046 | 0.165 | 0.063 | 0.048 | 0.093 | 0.045 | 0.013 | 0.092 | 0.049 | 0.002 | 0.014 | 0.011 |
| 45 - 49세 | 432 | 455.914 | 0.041 | 0.104 | 0.106 | 0.243 | 0.134 | 0.125 | 0.078 | 0.125 | 0.133 | 0.093 | 0.019 | 0.049 | 0.018 | 0.060 | 0.070 | 0.003 | 0.006 | 0.010 |
| 50 - 54세 | 510 | 513.707 | 0.053 | 0.103 | 0.084 | 0.178 | 0.121 | 0.125 | 0.109 | 0.125 | 0.120 | 0.123 | 0.049 | 0.050 | 0.024 | 0.045 | 0.062 | 0.010 | 0.010 | 0.012 |
| 55 - 59세 | 471 | 509.389 | 0.055 | 0.099 | 0.092 | 0.240 | 0.099 | 0.118 | 0.134 | 0.130 | 0.103 | 0.149 | 0.060 | 0.058 | 0.047 | 0.068 | 0.070 | 0.003 | 0.016 | 0.029 |
| 60 - 64세 | 473 | 430.583 | 0.083 | 0.146 | 0.131 | 0.188 | 0.127 | 0.107 | 0.176 | 0.169 | 0.142 | 0.187 | 0.081 | 0.096 | 0.043 | 0.070 | 0.063 | 0.028 | 0.018 | 0.027 |

## Most common profile transitions, 2022 to 2024

| profile_2022 | profile_2024 | n | weighted_share |
| --- | --- | --- | --- |
| lower_observed_risk | lower_observed_risk | 561 | 0.276 |
| alcohol_only | alcohol_only | 277 | 0.129 |
| lower_observed_risk | alcohol_only | 157 | 0.077 |
| alcohol_only | lower_observed_risk | 143 | 0.065 |
| lower_observed_risk | psych_only | 93 | 0.046 |
| psych_only | lower_observed_risk | 65 | 0.038 |
| low_income_only | low_income_only | 75 | 0.037 |
| psych_only | psych_only | 51 | 0.027 |
| low_income_only | lower_observed_risk | 50 | 0.024 |
| psych_low_income | psych_low_income | 47 | 0.023 |
| depression_alcohol | alcohol_only | 33 | 0.019 |
| psych_low_income | low_income_only | 29 | 0.016 |
| alcohol_only | depression_alcohol | 33 | 0.016 |
| lower_observed_risk | depression_alcohol | 30 | 0.015 |
| lower_observed_risk | low_income_only | 31 | 0.014 |

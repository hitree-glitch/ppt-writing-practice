# 2021-2023 Sido-Level NIA-CHS Joined Analysis

- Unit: year x 17 Korean provinces/cities, rows=51.
- Digital indicators: regional internet use, mobile internet use, smartphone use from NIA Internet Usage Survey Korean statistical tables.
- Mental-health indicators: CHS health determinant DB standardized rates such as stress recognition and depressive symptom experience.
- Controls included as candidates: aged population rate, elderly living-alone household rate, unemployment rate, psychiatry specialist count.

## NIA PDF Extraction Checks
- 2021 internet_use_rate: PDF page 33, candidates=1, status=ok
- 2021 mobile_internet_use_rate: PDF page 45, candidates=1, status=ok
- 2021 smartphone_use_rate: PDF page 49, candidates=1, status=ok
- 2022 internet_use_rate: PDF page 33, candidates=1, status=ok
- 2022 mobile_internet_use_rate: PDF page 45, candidates=1, status=ok
- 2022 smartphone_use_rate: PDF page 49, candidates=1, status=ok
- 2023 internet_use_rate: PDF page 35, candidates=1, status=ok
- 2023 mobile_internet_use_rate: PDF page 47, candidates=1, status=ok
- 2023 smartphone_use_rate: PDF page 51, candidates=1, status=ok

## Pooled Correlations
- internet_use_rate vs depression_counseling_std: r=0.050, n=34
- mobile_internet_use_rate vs depression_counseling_std: r=-0.001, n=34
- smartphone_use_rate vs depression_counseling_std: r=-0.095, n=34
- internet_use_rate vs depression_std: r=0.266, n=51
- mobile_internet_use_rate vs depression_std: r=0.152, n=51
- smartphone_use_rate vs depression_std: r=0.111, n=51
- internet_use_rate vs stress_std: r=0.001, n=51
- mobile_internet_use_rate vs stress_std: r=-0.121, n=51
- smartphone_use_rate vs stress_std: r=-0.189, n=51

## Two-Way Fixed-Effects Coefficients
### stress_std
- internet_use_rate: b=0.294, robust_se=0.103, p_norm=0.004, n=51
- mobile_internet_use_rate: b=0.141, robust_se=0.069, p_norm=0.040, n=51
- smartphone_use_rate: b=0.143, robust_se=0.066, p_norm=0.031, n=51
### depression_std
- internet_use_rate: b=0.127, robust_se=0.073, p_norm=0.080, n=51
- mobile_internet_use_rate: b=0.070, robust_se=0.049, p_norm=0.149, n=51
- smartphone_use_rate: b=0.075, robust_se=0.047, p_norm=0.114, n=51
### depression_counseling_std
- internet_use_rate: b=-0.269, robust_se=0.504, p_norm=0.594, n=34
- mobile_internet_use_rate: b=-0.190, robust_se=0.407, p_norm=0.641, n=34
- smartphone_use_rate: b=-0.234, robust_se=0.392, p_norm=0.550, n=34

## Caution
- This is ecological/aggregate analysis, not individual-level causal inference.
- 2018-2020 and 2024-2025 Korean statistical tables need OCR or official microdata/table access because their body tables are image-like in the downloaded PDFs.
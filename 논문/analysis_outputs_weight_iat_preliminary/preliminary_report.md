# Weight IAT Korea 2009-2019 Preliminary Analysis

## Data

- Wide data rows: 11,335
- IAT D2 usable rows: 6,854
- IAT D2 rows after simple quality flags (<=10% faster than 300ms and <=30% error): 6,828
- Years covered: 2009-2019

## Main Descriptive Findings

- Mean IAT D2 Thin-Good score: 0.297 (SD = 0.414)
- Mean IAT D6 Thin-Good score: 0.294
- D2-D6 correlation: r = 0.978
- Mean explicit thermometer difference (Tthin - Tfat): -0.642
- IAT-explicit thermometer correlation: r = 0.072

## Working Interpretation

Positive IAT values indicate stronger Thin-Good than Fat-Good associations. The average
IAT score is positive, so the data show a clear implicit thin-positive association.

The thermometer difference is coded as Tthin - Tfat. Its average is negative in this
dataset, which means participants rated fat people warmer than thin people on average.
That makes this dataset especially interesting for an implicit-explicit dissociation
paper: implicit responses favor thin people, while explicit warmth ratings do not show
the same simple pattern.

## Suggested Paper Frame

Title candidate:
Implicit-explicit dissociation in weight stigma among Korean participants:
Evidence from the 2009-2019 Weight IAT dataset

Core question:
Do Korean participants show implicit thin-positive bias even when explicit evaluations
are weak, absent, or reversed?

Recommended primary outcome:
IAT D2 Thin-Good score. D6 can be reported as a robustness check.

Recommended predictors:
explicit thermometer difference, perceived weight controllability, self/other body
perception, identification with thin/fat people, age, sex, and survey year.

## Files

- `01_descriptives.csv`: variable descriptives and missingness
- `02_counts.csv`: year, sex, and session status counts
- `03_correlations.csv`: correlation matrix
- `04_yearly_trends.csv`: yearly means
- `05_regression_models.csv`: robust OLS regression summaries
- `06_quality_counts.csv`: basic IAT quality-rule counts

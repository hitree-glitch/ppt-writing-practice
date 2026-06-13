# IAT Domain Comparison Preliminary Analysis

## What Was Combined

This analysis stacks three Korean IAT datasets into one long-format table:

- Age IAT: higher scores mean stronger Young-Good than Old-Good associations.
- Weight IAT: higher scores mean stronger Thin-Good than Fat-Good associations.
- Korea-USA IAT: higher scores mean stronger Korea-Good than USA-Good associations.

The datasets were not person-matched because usable user identifiers barely overlap.
This is a domain-comparison analysis, not a within-person multi-IAT analysis.

## Domain Means

              n  quality_n  iat_mean  iat_sd  explicit_thermo_mean  first_year  last_year
domain                                                                                   
age        6823       6680     0.499   0.384                -0.639      2006.0     2017.0
korea_usa  5377       5295     0.439   0.366                 1.590      2006.0     2017.0
weight     6854       6828     0.297   0.414                -0.597      2009.0     2019.0

## Main Interpretation

Age IAT shows the largest average D score among the three domains, followed by
Korea-USA IAT, then Weight IAT. That means the strongest average automatic association
in these public Korean datasets is Young-Good over Old-Good.

This makes a useful paper frame:
not just whether ageism exists, but whether age-related implicit bias is unusually
strong compared with other socially meaningful IAT domains in the same Korean public
IAT archive.

## Suggested Paper Frame

Title candidate:
Comparing implicit biases in Korea: Age, body weight, and national-group IAT evidence

Core question:
Is implicit age bias stronger than other public IAT domains in Korean samples, and do
demographic/political predictors generalize across bias domains?

## Generated Files

- `00_long_iat_domain_data.csv`: stacked analytic data
- `01_domain_summary.csv`: domain-level means
- `02_yearly_by_domain.csv`: yearly trends by domain
- `03_demographic_group_summary.csv`: sex and age-group summaries
- `04_political_group_summary.csv`: political-orientation summaries
- `05_correlations_by_domain.csv`: within-domain correlations
- `06_regression_models.csv`: pooled and within-domain regressions

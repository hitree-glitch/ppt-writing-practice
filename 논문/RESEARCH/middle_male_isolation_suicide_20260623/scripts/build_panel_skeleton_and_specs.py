from pathlib import Path
import pandas as pd
import numpy as np
import json

ROOT=Path(r'RESEARCH/middle_male_isolation_suicide_20260623')
ART=ROOT/'artifacts'
OUT=ROOT/'outputs'
ART.mkdir(parents=True, exist_ok=True)
OUT.mkdir(parents=True, exist_ok=True)

region=pd.read_csv(ART/'godoksa_region_year_2020_2024.csv')
decomp=pd.read_csv(ART/'regional_expected_growth_decomposition.csv')
catalog=pd.read_csv(ART/'paper_panel_variable_catalog.csv')

panel=region.copy()
panel=panel.rename(columns={'count':'godoksa_count','share_pct':'godoksa_share_pct'})
panel=panel.sort_values(['region','year'])
panel['godoksa_yoy_change']=panel.groupby('region')['godoksa_count'].diff()
panel['godoksa_yoy_pct']=panel.groupby('region')['godoksa_count'].pct_change()*100
panel=panel.merge(decomp[['region','expected_2024_if_national_growth','excess_2024_vs_expected','trajectory_type']], on='region', how='left')
panel['is_seoul_gyeonggi_daegu']=panel['region'].isin(['서울','경기','대구']).astype(int)
panel['is_positive_excess_region']=(panel['excess_2024_vs_expected']>0).astype(int)
panel['godoksa_2024_excess_applies_to_year']=np.where(panel['year']==2024,panel['excess_2024_vs_expected'],np.nan)

placeholder_cols={
 'male_40_64_single_person_households':'DT_1PL1502_or_DT_1PL1509',
 'male_40_64_single_person_household_rate':'DT_1PL1502_denominator_needed',
 'single_household_dwelling_non_apartment_share':'DT_1PL1509',
 'social_network_no_help_sick_pct':'DT_1SSSP041R',
 'social_network_no_money_help_pct':'DT_1SSSP041R',
 'social_network_no_depressed_talk_pct':'DT_1SSSP041R',
 'daily_no_family_relative_exchange_pct':'DT_1SSSP045R',
 'daily_no_nonkin_exchange_pct':'DT_1SSSP045R',
 'depression_experience_std_rate':'DT_H_MENTAL_DEPRESS',
 'basic_livelihood_male_40_64_count':'DT_11714_N002',
 'social_welfare_facility_count':'DT_110001_A043',
 'male_40_64_suicide_deaths':'DT_1B34E11',
 'male_40_64_suicide_rate':'DT_1B34E11',
 'business_closure_male_40_64_count':'DT_13301N_9810',
 'business_closure_total_count':'DT_133001N_9816_or_TX_13301_A169',
 'divorce_male_40_64_rate':'DT_1B85009_or_DT_1B85027',
 'employment_loss_male_45_64_count':'restricted_employment_insurance',
 'health_insurance_arrears_male_45_64_count':'restricted_nhis',
 'debt_arrears_male_45_64_count':'restricted_credit',
 'emergency_self_harm_male_45_64_count':'restricted_nedis_or_injury_surveillance',
 'death_discovery_delay_days':'restricted_godoksa_microdata'
}
for c in placeholder_cols:
    panel[c]=np.nan
panel.to_csv(ART/'region_year_panel_current_with_join_slots.csv', index=False, encoding='utf-8-sig')

model_rows=[]
def spec(var, role, source, level, transform, expected, hypothesis, status):
    model_rows.append({'variable':var,'role':role,'source_table_or_institution':source,'level':level,'transform_for_model':transform,'expected_direction':expected,'hypothesis_link':hypothesis,'current_status':status})

spec('godoksa_count','outcome_A','MOHW godoksa survey summary','시도×연도','negative binomial/Poisson; offset population when available','dependent','H1 spatial concentration','available_2020_2024')
spec('godoksa_2024_excess_applies_to_year','outcome_A_derived','MOHW godoksa survey summary','시도','actual 2024 minus expected if national growth applied','dependent or descriptive','H1 spatial excess','available_derived')
spec('male_40_64_suicide_rate','outcome_B','KOSIS DT_1B34E11','시도×연도','aggregate 40-44~60-64 male suicide deaths/population','dependent','H2 acute suicide crisis','download_needed')
spec('male_40_64_single_person_household_rate','exposure','KOSIS DT_1PL1502/1509','시군구→시도×연도','male 40-64 one-person households / male 40-64 population','positive','H1/H3 isolation exposure','download_needed')
spec('social_network_no_depressed_talk_pct','mediator','KOSIS DT_1SSSP041R','시도×사회조사연도','pct no person to talk when discouraged/depressed','positive','social isolation mechanism','download_needed')
spec('social_network_no_help_sick_pct','mediator','KOSIS DT_1SSSP041R','시도×사회조사연도','pct no person to ask housework help when sick','positive','care gap mechanism','download_needed')
spec('depression_experience_std_rate','mediator','KOSIS DT_H_MENTAL_DEPRESS','시군구→시도×연도','population-weighted or simple mean standardized rate','positive','mental health burden','download_needed')
spec('basic_livelihood_male_40_64_count','need','KOSIS DT_11714_N002','시도×연도','male 40-64 recipients per male 40-64 population','positive','economic vulnerability','download_needed')
spec('social_welfare_facility_count','capacity','KOSIS DT_110001_A043','시군구/시도','facilities per 100k or per high-risk single-person households','negative if protective; positive if need-driven','welfare capacity','download_needed_single_year_or_limited')
spec('business_closure_male_40_64_count','event_proxy','KOSIS DT_13301N_9810','시도×연도','male 40-64 closures per businesses/population','positive','H2 acute event proxy','public_kosis_candidate_download_needed')
spec('divorce_male_40_64_rate','event_proxy','KOSIS DT_1B85009/DT_1B85027','시도×연도','male 40-64 divorce rate/count','positive','relationship rupture event','public_kosis_candidate_download_needed')
spec('employment_loss_male_45_64_count','event','근로복지공단/고용행정통계','시도×월/연도','loss count by reason, age, sex, region','positive','H2 acute event direct','restricted_or_custom_request')
spec('health_insurance_arrears_male_45_64_count','event','국민건강보험공단','시도×연도','premium arrears by sex-age-region','positive','income/health security shock','restricted_or_custom_request')
spec('debt_arrears_male_45_64_count','event','신용회복위원회/한국신용정보원','시도×연도','debt adjustment/default/arrears by sex-age-region','positive','debt shock','restricted_or_custom_request')
spec('emergency_self_harm_male_45_64_count','event/outcome_proxy','NEDIS/질병관리청 손상감시','시도×연도','self-harm/suicide attempt emergency cases','positive','pre-fatal self-harm','restricted_or_report_based')
model_spec=pd.DataFrame(model_rows)
model_spec.to_csv(ART/'panel_model_variable_spec.csv', index=False, encoding='utf-8-sig')

triage=catalog.copy()
triage['analysis_tier']=np.select([
    triage['access_status'].str.contains('metadata_verified|kosis_candidate',na=False) & triage['priority'].le(1),
    triage['access_status'].str.contains('metadata_verified|kosis_candidate',na=False),
    triage['access_status'].str.contains('restricted',na=False),
],['Tier1_public_core','Tier2_public_supplement','Tier3_restricted_direct_event'],default='Tier4_weak_or_review')
triage.to_csv(ART/'data_access_triage_for_panel.csv', index=False, encoding='utf-8-sig')

summary={
 'panel_rows': int(len(panel)),
 'regions': int(panel['region'].nunique()),
 'years': [int(panel['year'].min()), int(panel['year'].max())],
 'available_outcomes': ['godoksa_count','godoksa_share_pct','godoksa_yoy_change','excess_2024_vs_expected'],
 'join_slots': placeholder_cols,
 'tier_counts': triage['analysis_tier'].value_counts().to_dict(),
}
(ART/'panel_build_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')

memo=f"""# 시도×연도 패널 구축 상태

## 현재 완성된 부분

- 행 구조: 17개 시도 × 2020-2024년 = {len(panel)}행
- 현재 실제 값이 들어간 종속변수 A: 고독사 사망자 수, 고독사 전국 점유율, 전년 대비 변화, 2024년 기대증가 대비 초과증가
- 설명변수와 종속변수 B는 KOSIS·행정자료 다운로드 후 같은 행 구조에 결합하도록 join slot을 생성했다.

## 우선 붙일 공개 KOSIS 변수

1. 40-64세 남성 1인가구: DT_1PL1502 또는 DT_1PL1509
2. 사회적 관계망 없음: DT_1SSSP041R
3. 일상 교류 없음: DT_1SSSP045R
4. 시군구 우울감 경험률: DT_H_MENTAL_DEPRESS
5. 남성 40-64세 기초생활수급: DT_11714_N002
6. 남성 40-64세 시도별 자살률: DT_1B34E11
7. 폐업자 현황: DT_13301N_9810
8. 시도·연령별 이혼율: DT_1B85009 또는 DT_1B85027

## 직접 행정자료 또는 승인자료가 필요한 변수

- 고용보험 상실: 성×연령×지역×상실사유 자료가 필요하다. 공개 KOSIS 후보는 일부 산업/지역 통계에 치우쳐 있어 전국 시도×연도 패널에는 약하다.
- 채무/연체: 신용회복위원회·한국신용정보원 집계자료가 필요하다.
- 건강보험 체납: 국민건강보험공단의 성×연령×지역 체납 집계가 필요하다.
- 응급실 자해/자살시도: NEDIS 또는 손상감시자료의 성×연령×지역 집계가 필요하다.
- 고독사 발견지연: 보건복지부 또는 지자체 고독사 실태조사 세부표/원자료가 필요하다.

## 산출 파일

- `region_year_panel_current_with_join_slots.csv`: 실제 고독사 값과 모든 join slot이 포함된 패널 골격
- `panel_model_variable_spec.csv`: 변수별 역할, 출처, 변환식, 예상방향
- `data_access_triage_for_panel.csv`: 공개자료/보완자료/승인자료 분류
- `paper_panel_variable_catalog.csv`: 전체 후보변수 카탈로그
"""
(OUT/'07_panel_build_status_korean.md').write_text(memo,encoding='utf-8')
print('panel rows',len(panel))
print(model_spec[['variable','role','source_table_or_institution','current_status']].to_string(index=False))
print('triage counts', triage['analysis_tier'].value_counts().to_dict())

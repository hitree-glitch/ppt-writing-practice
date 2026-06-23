from pathlib import Path
import pandas as pd
import re

ROOT=Path(r'RESEARCH/middle_male_isolation_suicide_20260623')
ART=ROOT/'artifacts'
base=pd.read_csv(ART/'priority_kosis_table_metadata.csv')
ext=pd.read_csv(ART/'extended_kosis_event_candidate_tables.csv')

manual=[]

def add(category, variable, org_id, tbl_id, table_name, stat_name, geography, time, dimensions, role, access, priority, rationale, official_url=None):
    manual.append({
        'category':category,'variable':variable,'org_id':org_id,'tbl_id':tbl_id,'table_name':table_name,'stat_name':stat_name,
        'geography':geography,'time_coverage':time,'needed_dimensions':dimensions,'model_role':role,
        'access_status':access,'priority':priority,'rationale':rationale,
        'official_url': official_url or (f'https://kosis.kr/statHtml/statHtml.do?orgId={org_id}&tblId={tbl_id}&conn_path=I2' if org_id and tbl_id else '')
    })

# Core KOSIS tables already verified in metadata.
core_rows = {
 'DT_1PL1502': ('exposure','male_40_64_single_person_households','시군구','2015-2024','행정구역×연령; items: 남자/여자/1인가구','exposure',1,'40-64세 남성 1인가구 핵심 노출변수'),
 'DT_1PL1509': ('exposure','male_40_64_single_person_households_by_dwelling','시군구','2015-2024','행정구역×성×연령×거처','exposure',1,'주거유형까지 붙일 수 있는 고립/주거취약 보강변수'),
 'DT_1SSSP041R': ('mediator','social_network_no_help_available','시도','사회조사 격년/주기','행정구역×특성; 아플 때/돈 빌릴 때/우울할 때 도움 없음','mediator',1,'사회적 고립 직접 지표'),
 'DT_1SSSP045R': ('mediator','daily_exchange_absence','시도','사회조사 격년/주기','행정구역×특성; 가족/친척 외 교류 없음','mediator',2,'일상 교류망 결핍 지표'),
 'DT_H_MENTAL_DEPRESS': ('mediator','annual_depression_experience_rate','시군구','2008-2025','시군구; 조율/표준화율','mediator',1,'지역사회건강조사 기반 지역 우울감 지표'),
 'DT_11714_N002': ('need','basic_livelihood_recipient_male_40_64','시도','2001-2024','행정구역×성×연령','need',1,'경제취약/복지수요 지표'),
 'DT_11714_N001': ('need','basic_livelihood_recipients_total','시도','2001-2024','행정구역','need',2,'총 복지수요 보조 지표'),
 'DT_110001_A043': ('capacity','social_welfare_facilities','시군구/도시통계','2023','행정구역×시설유형','capacity',3,'복지 인프라이나 단년도라 패널보다는 단면 보정'),
 'DT_1B34E11': ('outcome','male_40_64_suicide_rate_by_region','시도','1996-2024','시도×사망원인×성×연령','outcome_B',1,'남성 40-64세 자살률 지역 패널 핵심 종속변수'),
 'DT_1B34E13': ('outcome','sex_specific_suicide_rate_city_county','시군구','1998-2024','시군구×사망원인×성','outcome_B_proxy',2,'연령은 없지만 시군구 성별 자살률 보조분석 가능'),
}
for tbl,(cat,var,geo,time,dim,role,prio,rat) in core_rows.items():
    row=base[base['tbl_id'].eq(tbl)]
    if len(row):
        r=row.iloc[0]
        add(cat,var,int(r['org_id']),tbl,r['title'],r['stat_name'],geo,time,dim,role,'metadata_verified_api_or_manual_download_needed',prio,rat,r['official_url'].replace('statHtmlContent','statHtml'))
    else:
        add(cat,var,'',tbl,'','',geo,time,dim,role,'candidate',prio,rat)

# Event/admin variables from extended search candidates.
selected_ids = {
 'DT_13301N_9810': ('event','business_closure_by_age_sex_region','국세통계','시도','2014-2024','연령×성×지역','event_proxy',1,'폐업은 50대 초반 급성위기 가설의 가장 강한 공개 행정 대체지표'),
 'DT_133N_987': ('event','business_closure_by_age_sex_industry','국세통계','전국/업태','2013-2024','연령×성×업태','event_proxy',2,'지역은 약하지만 연령·성별 폐업 충격 확인 가능'),
 'TX_13301_A169': ('event','business_closure_reason_region_industry','국세통계','시도','2005-2024','폐업사유×지역×업태','event_proxy',2,'지역별 폐업사유 구조 보강'),
 'TX_13301_A171': ('event','business_duration_before_closure_region_industry','국세통계','시도','2005-2024','사업존속연수×지역×업태','event_proxy',3,'영세/단기 사업 실패 누적위험 보강'),
 'DT_133001N_9816': ('event','business_closure_city_county','국세통계','시군구','2016-2024','시군구','event_proxy',2,'고독사 초과증가 지역의 지역경제 충격 보조지표'),
}
for tbl,(cat,var,stat,geo,time,dim,role,prio,rat) in selected_ids.items():
    rows=ext[ext['tbl_id'].eq(tbl)]
    if len(rows):
        r=rows.iloc[0]
        add(cat,var,int(r['org_id']),tbl,r['table_name'],r['stat_name'],geo,time,dim,role,'kosis_candidate_metadata_collected',prio,rat,r['official_url'])
    else:
        add(cat,var,'',tbl,'',stat,geo,time,dim,role,'not_found_in_current_search',prio,rat)

# Divorce candidates: choose from search output by table name includes 이혼 and age/region.
div=ext[ext['table_name'].fillna('').str.contains('이혼') | ext['stat_name'].fillna('').str.contains('인구동향|혼인|이혼', regex=True)].copy()
for _,r in div.head(12).iterrows():
    name=str(r['table_name'])
    if any(k in name for k in ['이혼','혼인']):
        add('event','divorce_related_candidate',int(r['org_id']),r['tbl_id'],r['table_name'],r['stat_name'],'표별 확인 필요',f"{r['start_period']}-{r['end_period']}",str(r['item01'])[:120]+' / '+str(r['item02'])[:120],'event_proxy','candidate_needs_metadata_review',2,'가족해체/관계단절 사건성 위기의 공개 대체지표',r['official_url'])

# Employment insurance candidates: most are local/industry, not national panel.
for tbl in ['DT_434_STBL_1028670','DT_434_STBL_1028672','DT_434_STBL_1028671','DT_434_STBL_1028657']:
    rows=ext[ext['tbl_id'].eq(tbl)]
    if len(rows):
        r=rows.iloc[0]
        add('event','employment_insurance_loss_candidate',int(r['org_id']),tbl,r['table_name'],r['stat_name'],'제한적/표별 확인',f"{r['start_period']}-{r['end_period']}",str(r['item01'])[:120]+' / '+str(r['item02'])[:120],'event_proxy','weak_public_candidate_or_non_panel',3,'고용상실 사건 변수 후보이나 현재 검색 표는 문화체육관광산업/단년도 성격이 강해 전국 시도×연도 패널엔 약함',r['official_url'])

# Restricted event data rows.
restricted = [
 ('event_restricted','employment_insurance_loss_male_45_64_by_region','근로복지공단/고용행정통계','시도/시군구','월/연도','성×연령×지역×상실사유','event','restricted_or_custom_request_needed',1,'50대 초반 급성위기를 직접 검증할 핵심 사건자료'),
 ('event_restricted','debt_arrears_credit_recovery','신용회복위원회/한국신용정보원','시도 가능성','연도','연령×성×지역×채무조정/연체','event','restricted_or_custom_request_needed',1,'부채·연체 충격은 급성위기 가설의 핵심이지만 공개 집계 제한 가능성 큼'),
 ('event_restricted','health_insurance_premium_arrears','국민건강보험공단','시도/시군구 가능성','연도','성×연령×지역×체납','event','restricted_or_custom_request_needed',1,'소득단절·건강보장 취약의 직접 지표이나 공개 집계 제한 가능성 큼'),
 ('event_restricted','emergency_self_harm_attempts','중앙응급의료센터/NEDIS 또는 질병관리청 손상감시','시도 가능성','연도','성×연령×지역×자해/자살시도','event_or_outcome_proxy','restricted_or_annual_report_needed',1,'자살 사망 이전의 비치명 자해/시도 지표'),
 ('event_restricted','death_discovery_interval_or_living_alone_duration','보건복지부 고독사 실태조사 원자료/지자체','시도/시군구','연도','성×연령×발견소요일×주거형태','outcome_A_mechanism','restricted_or_report_table_needed',1,'고독사를 자살과 구분하는 발견지연 메커니즘의 직접 지표'),
]
for cat,var,stat,geo,time,dim,role,access,prio,rat in restricted:
    add(cat,var,'','',var,stat,geo,time,dim,role,access,prio,rat,'')

catalog=pd.DataFrame(manual)
catalog.to_csv(ART/'paper_panel_variable_catalog.csv',index=False,encoding='utf-8-sig')
print(catalog[['category','variable','tbl_id','table_name','geography','time_coverage','model_role','access_status','priority']].to_string(index=False))

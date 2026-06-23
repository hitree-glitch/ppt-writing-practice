from urllib.parse import urlencode
from urllib.request import Request, urlopen
from pathlib import Path
import json, pandas as pd
ROOT=Path(r'RESEARCH/middle_male_isolation_suicide_20260623')
ART=ROOT/'artifacts'
tests=[
 ('single_household','101','DT_1PL1502'),
 ('social_network','101','DT_1SSSP041R'),
 ('depression','177','DT_H_MENTAL_DEPRESS'),
 ('basic_livelihood','117','DT_11714_N002'),
 ('business_closure','133','DT_13301N_9810'),
 ('divorce_rate','101','DT_1B85009'),
]
rows=[]
for name,org,tbl in tests:
    params={'method':'getList','apiKey':'','format':'json','jsonVD':'Y','userStatsId':'','prdSe':'Y','newEstPrdCnt':'1','orgId':org,'tblId':tbl}
    url='https://kosis.kr/openapi/Param/statisticsParameterData.do?'+urlencode(params)
    try:
        req=Request(url,headers={'User-Agent':'Mozilla/5.0'})
        with urlopen(req,timeout=15) as resp:
            text=resp.read().decode('utf-8','replace')
            rows.append({'name':name,'org_id':org,'tbl_id':tbl,'status':resp.status,'response_head':text[:300]})
    except Exception as e:
        rows.append({'name':name,'org_id':org,'tbl_id':tbl,'status':'error','response_head':repr(e)})
pd.DataFrame(rows).to_csv(ART/'kosis_value_api_download_attempts.csv',index=False,encoding='utf-8-sig')
print(pd.DataFrame(rows).to_string(index=False))

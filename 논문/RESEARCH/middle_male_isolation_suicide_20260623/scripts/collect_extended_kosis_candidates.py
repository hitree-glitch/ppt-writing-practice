from urllib.parse import urlencode
from urllib.request import Request, urlopen
from pathlib import Path
import json, re, html
import pandas as pd

ROOT=Path(r'RESEARCH/middle_male_isolation_suicide_20260623')
ART=ROOT/'artifacts'
ART.mkdir(parents=True, exist_ok=True)
keywords=[
 '고용보험 상실자','고용보험 피보험자 상실자 시도','고용보험 상실자 연령',
 '폐업자 현황','폐업률 시도','사업자 폐업 시도',
 '이혼 남편 연령','이혼 시도 남편 연령','혼인 이혼 시도 연령',
 '건강보험 체납','건강보험료 체납','건강보험 지역가입자 체납',
 '응급실 자해','자살시도 응급실','자해 자살시도 지역',
 '정신건강복지센터','정신건강증진시설','자살예방센터',
 '사회복지전담공무원','사회복지시설 수','사회복지시설 시도',
 '기초생활수급자 성별 연령별 시도','국민기초생활보장 수급자 성별 연령별',
 '1인가구 성 연령 시군구','사회적 관계망 도움 받을 사람 없음','우울감 경험률 시군구'
]

def clean(s):
    if s is None: return ''
    s=html.unescape(str(s))
    s=re.sub(r'<[^>]+>','',s)
    s=re.sub(r'\s+',' ',s).strip()
    return s

def search(q, start=0, count=20):
    url='https://kosis.kr/search/searchStatDBAjax.do'
    params={
        'query':q,'collection':'statDB','startCount':str(start),'resultCount':str(count),'sort':'RANK','reQuery':'','realQuery':q,
        'range':'ALL','startDate':'','endDate':'','searchField':'ALL','detailViewStatus':'N','detailQuery':q,
        'gbn':'L','categoryPath':'','categoryIdxField':'','categorySort':'kosis'
    }
    data=urlencode(params).encode('utf-8')
    req=Request(url,data=data,headers={'User-Agent':'Mozilla/5.0','Content-Type':'application/x-www-form-urlencoded; charset=UTF-8','X-Requested-With':'XMLHttpRequest'})
    with urlopen(req,timeout=20) as resp:
        text=resp.read().decode('utf-8','replace')
    return json.loads(text)

rows=[]
raw={}
for q in keywords:
    try:
        data=search(q)
        raw[q]=data
        for rank,item in enumerate(data.get('resultList',[]),1):
            rows.append({
                'keyword':q,
                'rank':rank,
                'org_id':item.get('ORG_ID'),
                'tbl_id':item.get('TBL_ID'),
                'table_name':clean(item.get('TBL_NM')),
                'stat_name':clean(item.get('STAT_NM_KMA') or item.get('STAT_NM')),
                'org_name':clean(item.get('ORG_NM')),
                'start_period':item.get('STRT_PRD_DE'),
                'end_period':item.get('END_PRD_DE'),
                'item01':clean(item.get('ITEM01')),
                'item02':clean(item.get('ITEM02')),
                'item03':clean(item.get('ITEM03')),
                'path':clean(item.get('MT_ATITLE')),
                'vw_cd':item.get('VW_CD'),
                'list_id':item.get('LIST_ID'),
                'stat_status':item.get('STAT_SE'),
                'official_url': f"https://kosis.kr/statHtml/statHtml.do?orgId={item.get('ORG_ID')}&tblId={item.get('TBL_ID')}&conn_path=I2" if item.get('ORG_ID') and item.get('TBL_ID') else ''
            })
    except Exception as e:
        rows.append({'keyword':q,'rank':None,'error':repr(e)})

df=pd.DataFrame(rows)
df.to_csv(ART/'extended_kosis_event_candidate_tables.csv',index=False,encoding='utf-8-sig')
(ART/'extended_kosis_event_candidate_tables_raw.json').write_text(json.dumps(raw,ensure_ascii=False,indent=2),encoding='utf-8')
print('rows',len(df),'unique tables',df['tbl_id'].nunique())
print(df[['keyword','rank','org_id','tbl_id','table_name','stat_name','start_period','end_period']].head(80).to_string(index=False))

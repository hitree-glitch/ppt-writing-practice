from urllib.request import Request, urlopen
from urllib.parse import urlencode
from pathlib import Path
import re, json, html
import pandas as pd

ROOT=Path(r'RESEARCH/middle_male_isolation_suicide_20260623')
ART=ROOT/'artifacts'
selected=pd.read_csv(ART/'paper_panel_variable_catalog.csv')
# Only KOSIS tables with tbl_id.
tables=selected[selected['tbl_id'].notna() & selected['tbl_id'].astype(str).ne('')][['org_id','tbl_id','variable','category','official_url']].drop_duplicates()

def fetch_meta(org_id,tbl_id):
    url=f'https://kosis.kr/statHtml/statHtmlContent.do?orgId={org_id}&tblId={tbl_id}&conn_path=I2'
    req=Request(url,headers={'User-Agent':'Mozilla/5.0'})
    with urlopen(req,timeout=20) as resp:
        text=resp.read().decode('utf-8','replace')
    return text,url

def find_json_var(text,var):
    # Handle var x = {...}; or var x = [...]; with rough balanced braces.
    idx=text.find(var)
    if idx<0: return None
    eq=text.find('=',idx)
    if eq<0: return None
    start=None
    for i in range(eq+1,len(text)):
        if text[i] in '[{':
            start=i; break
    if start is None: return None
    open_ch=text[start]; close_ch=']' if open_ch=='[' else '}'
    depth=0; in_str=False; esc=False
    for i in range(start,len(text)):
        ch=text[i]
        if in_str:
            if esc: esc=False
            elif ch=='\\': esc=True
            elif ch=='"': in_str=False
        else:
            if ch=='"': in_str=True
            elif ch==open_ch: depth+=1
            elif ch==close_ch:
                depth-=1
                if depth==0:
                    return text[start:i+1]
    return None

def clean(s):
    return re.sub(r'\s+',' ',html.unescape(str(s))).strip() if s is not None else ''

rows=[]
for _,r in tables.iterrows():
    org_id=str(r['org_id']).split('.')[0]
    tbl_id=str(r['tbl_id'])
    try:
        text,url=fetch_meta(org_id,tbl_id)
        # Save selected html for inspection only if concise? no.
        title=''; stat=''; org=''; unit=''; period=''; axes=[]; items=[]; renewal=''
        # The page often has JS variables. Pull common literals with regex fallback.
        for pat,name in [(r'"TBL_NM"\s*:\s*"([^"]+)"','title'),(r'"STAT_NM"\s*:\s*"([^"]+)"','stat'),(r'"ORG_NM"\s*:\s*"([^"]+)"','org')]:
            m=re.search(pat,text)
            if m:
                if name=='title': title=clean(m.group(1))
                elif name=='stat': stat=clean(m.group(1))
                elif name=='org': org=clean(m.group(1))
        # g_jsonStatInfo may include metadata.
        js=find_json_var(text,'g_jsonStatInfo')
        if js:
            try:
                info=json.loads(js)
                if isinstance(info,dict):
                    title=title or clean(info.get('TBL_NM') or info.get('tblNm'))
                    stat=stat or clean(info.get('STAT_NM') or info.get('statNm'))
                    org=org or clean(info.get('ORG_NM') or info.get('orgNm'))
                    unit=clean(info.get('UNIT_NM') or info.get('unitNm'))
                    renewal=clean(info.get('ORG_CHG_DT') or info.get('CHG_DT') or info.get('prdDe'))
            except Exception:
                pass
        # pull classification names from JSON fragments / html.
        axes=sorted(set(clean(x) for x in re.findall(r'"(?:CLS_NM|UP_ITM_NM|ITM_NM|OBJ_NM|CHAR_ITM_NM)"\s*:\s*"([^"]+)"',text)))[:30]
        items=sorted(set(clean(x) for x in re.findall(r'"(?:UNIT_NM|ITM_NM|C1_NM|C2_NM|C3_NM)"\s*:\s*"([^"]+)"',text)))[:50]
        years=re.findall(r'(?:19|20)\d{2}',text)
        period=f'{min(years)}-{max(years)}' if years else ''
        rows.append({'variable':r['variable'],'category':r['category'],'org_id':org_id,'tbl_id':tbl_id,'title':title,'stat_name':stat,'org_name':org,'unit':unit,'period_detected':period,'renewal_hint':renewal,'axes_detected':' | '.join(axes),'items_detected':' | '.join(items[:20]),'parse_status':'ok','official_url':url})
    except Exception as e:
        rows.append({'variable':r['variable'],'category':r['category'],'org_id':org_id,'tbl_id':tbl_id,'parse_status':'error','error':repr(e),'official_url':f'https://kosis.kr/statHtml/statHtmlContent.do?orgId={org_id}&tblId={tbl_id}&conn_path=I2'})

out=pd.DataFrame(rows)
out.to_csv(ART/'panel_selected_table_metadata_probe.csv',index=False,encoding='utf-8-sig')
print(out[['variable','tbl_id','parse_status','title','period_detected','axes_detected']].to_string(index=False))

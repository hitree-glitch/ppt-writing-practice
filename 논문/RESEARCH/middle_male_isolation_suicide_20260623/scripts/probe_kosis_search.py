from urllib.parse import quote
from urllib.request import Request, urlopen
from pathlib import Path
queries=['고용보험 상실자','폐업자 현황','이혼 남편 연령','응급실 자해','건강보험 체납','정신건강복지센터','사회복지전담공무원']
out=[]
for q in queries:
    url='https://kosis.kr/search/search.do?query='+quote(q)
    try:
        req=Request(url,headers={'User-Agent':'Mozilla/5.0'})
        with urlopen(req,timeout=10) as resp:
            body=resp.read()
            text=body.decode('utf-8','replace')
            out.append('\nQUERY '+q+' status '+str(resp.status)+' len '+str(len(text))+' url '+resp.url)
            # print likely table-id fragments
            import re
            hits=[]
            for m in re.finditer(r'(?:tblId|tbl_id|TBL_ID)[^A-Za-z0-9_]{0,20}([A-Z0-9_]{4,})', text):
                hits.append(m.group(1))
            out.append('table ids: '+', '.join(sorted(set(hits))[:30]))
            idx=text.find(q)
            out.append('contains query at '+str(idx))
            out.append(text[max(0,idx-300):idx+500].replace('\n',' ') if idx!=-1 else text[:800].replace('\n',' '))
    except Exception as e:
        out.append('ERR '+q+' '+repr(e))
Path(r'RESEARCH/middle_male_isolation_suicide_20260623/artifacts/kosis_search_probe.txt').write_text('\n'.join(out), encoding='utf-8')
print('\n'.join(out[:8]))

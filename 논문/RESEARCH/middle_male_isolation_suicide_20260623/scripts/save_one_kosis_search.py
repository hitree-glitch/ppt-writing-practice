from urllib.parse import quote
from urllib.request import Request, urlopen
from pathlib import Path
q='고용보험 상실자'
url='https://kosis.kr/search/search.do?query='+quote(q)
req=Request(url,headers={'User-Agent':'Mozilla/5.0'})
with urlopen(req,timeout=10) as resp:
    text=resp.read().decode('utf-8','replace')
Path(r'RESEARCH/middle_male_isolation_suicide_20260623/artifacts/kosis_search_employment_loss.html').write_text(text,encoding='utf-8')
for term in ['DT_11702_N001','statHtml','result','resultList','searchList','fnSearch','statDB']:
    print(term, text.find(term))
print(text[70000:78000])

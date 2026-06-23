from urllib.parse import urlencode
from urllib.request import Request, urlopen
from pathlib import Path
import json
q='고용보험 상실자'
url='https://kosis.kr/search/searchStatDBAjax.do'
params={
 'query':q,'collection':'statDB','startCount':'0','resultCount':'20','sort':'RANK','reQuery':'','realQuery':q,
 'range':'ALL','startDate':'','endDate':'','searchField':'ALL','detailViewStatus':'N','detailQuery':q,
 'gbn':'L','categoryPath':'','categoryIdxField':'','categorySort':'kosis'
}
data=urlencode(params).encode('utf-8')
req=Request(url,data=data,headers={'User-Agent':'Mozilla/5.0','Content-Type':'application/x-www-form-urlencoded; charset=UTF-8','X-Requested-With':'XMLHttpRequest'})
try:
 with urlopen(req,timeout=10) as resp:
  text=resp.read().decode('utf-8','replace')
  print('status',resp.status,'len',len(text),resp.headers.get('content-type'))
  print(text[:2000])
  Path(r'RESEARCH/middle_male_isolation_suicide_20260623/artifacts/kosis_search_ajax_employment_loss.json').write_text(text,encoding='utf-8')
except Exception as e:
 print('ERR',repr(e))

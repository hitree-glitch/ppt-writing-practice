from pathlib import Path
import json
ROOT=Path(r'RESEARCH/middle_male_isolation_suicide_20260623')
SRC=ROOT/'sources'/'sources.jsonl'
SRC.parent.mkdir(parents=True, exist_ok=True)
new_sources=[
 {'id':'src_kosis_1pl1502','url':'https://kosis.kr/statHtml/statHtml.do?orgId=101&tblId=DT_1PL1502&conn_path=I2','title':'성 및 연령별 1인가구 - 시군구','organization':'KOSIS/국가데이터처','type':'official_stat_table','quality_rating':'A','claims':['시군구 단위 성·연령별 1인가구 자료 후보']},
 {'id':'src_kosis_1sssp041r','url':'https://kosis.kr/statHtml/statHtml.do?orgId=101&tblId=DT_1SSSP041R&conn_path=I2','title':'사회적 관계망 (13세 이상 인구)','organization':'KOSIS/국가데이터처','type':'official_stat_table','quality_rating':'A','claims':['아플 때, 돈이 필요할 때, 우울할 때 도움 받을 사람 유무를 제공하는 사회적 관계망 후보표']},
 {'id':'src_kosis_mental_depress','url':'https://kosis.kr/statHtml/statHtml.do?orgId=177&tblId=DT_H_MENTAL_DEPRESS&conn_path=I2','title':'시·군·구별 연간 우울감 경험률','organization':'KOSIS/질병관리청 지역사회건강조사','type':'official_stat_table','quality_rating':'A','claims':['시군구 단위 연간 우울감 경험률 후보표']},
 {'id':'src_kosis_basic_livelihood','url':'https://kosis.kr/statHtml/statHtml.do?orgId=117&tblId=DT_11714_N002&conn_path=I2','title':'국민기초일반수급자수-시도별, 성별, 연령별','organization':'KOSIS/보건복지부','type':'official_stat_table','quality_rating':'A','claims':['시도·성·연령별 기초생활보장 수급자수 후보표']},
 {'id':'src_kosis_business_closure','url':'https://kosis.kr/statHtml/statHtml.do?orgId=133&tblId=DT_13301N_9810&conn_path=I2','title':'9.8.11 폐업자 현황 Ⅱ(연령, 성, 지역)[2014~]','organization':'KOSIS/국세통계','type':'official_stat_table','quality_rating':'A','claims':['연령·성·지역별 폐업자 현황 후보표']},
 {'id':'src_kosis_divorce_rate','url':'https://kosis.kr/statHtml/statHtml.do?orgId=101&tblId=DT_1B85009&conn_path=I2','title':'시도/성/연령별 이혼율','organization':'KOSIS/인구동향조사','type':'official_stat_table','quality_rating':'A','claims':['시도·성·연령별 이혼율 후보표']},
 {'id':'src_kosis_suicide_region','url':'https://kosis.kr/statHtml/statHtml.do?orgId=101&tblId=DT_1B34E11&conn_path=I2','title':'시도/사망원인(104항목)/성/연령(5세)별 사망자수, 사망률','organization':'KOSIS/국가데이터처 사망원인통계','type':'official_stat_table','quality_rating':'A','claims':['시도·성·5세 연령대별 자살 사망자수와 사망률 후보표']},
]
existing=[]
if SRC.exists():
    for line in SRC.read_text(encoding='utf-8').splitlines():
        if line.strip():
            try: existing.append(json.loads(line))
            except Exception: pass
ids={x.get('id') for x in existing}
with SRC.open('a',encoding='utf-8') as f:
    for s in new_sources:
        if s['id'] not in ids:
            f.write(json.dumps(s,ensure_ascii=False)+'\n')
print('sources', sum(1 for _ in SRC.open(encoding='utf-8')))

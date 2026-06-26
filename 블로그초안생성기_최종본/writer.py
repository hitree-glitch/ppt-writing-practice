"""Gemini API 또는 로컬 규칙으로 네이버 블로그 초안을 생성하는 모듈입니다."""

from __future__ import annotations

import json
import re
import textwrap

import requests

from analyzer import analyze_articles, clean_title
from config import DEFAULT_ARTICLE_PROMPT, DEFAULT_IMAGE_PROMPT, GEMINI_API_URL
from crawler import Article
from plagiarism_checker import check_plagiarism


def _clip(text: str, limit: int = 5000) -> str:
    return text[:limit]


def _call_gemini(api_key: str, prompt: str, temperature: float = 0.75) -> str:
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": temperature, "topP": 0.9},
    }
    response = requests.post(f"{GEMINI_API_URL}?key={api_key}", json=payload, timeout=90)
    response.raise_for_status()
    data = response.json()
    candidates = data.get("candidates", [])
    if not candidates:
        raise ValueError("Gemini 응답에 생성 후보가 없습니다.")
    parts = candidates[0].get("content", {}).get("parts", [])
    return "\n".join(part.get("text", "") for part in parts).strip()


def _build_prompt(
    articles: list[Article],
    analysis: dict,
    style: str,
    target_length: str,
    keyword: str,
    mode_name: str,
    article_prompt: str,
    publish_type: str,
) -> str:
    sources = "\n\n".join(
        f"[자료 {index}]\n제목: {clean_title(article.title)}\nURL: {article.url}\n본문 발췌:\n{_clip(article.text)}"
        for index, article in enumerate(articles, start=1)
    )
    analysis_text = json.dumps(analysis, ensure_ascii=False, indent=2)

    return textwrap.dedent(
        f"""
        {article_prompt or DEFAULT_ARTICLE_PROMPT}

        작성 방식: {mode_name}
        문체: {style}
        목표 글자 수: {target_length or "약 2000"}자
        검색/작성 키워드: {keyword or analysis.get("core_topic", "")}
        발행 유형 선택값: {publish_type}

        절대 조건:
        - 작성 지침이나 분석 메모를 쓰지 말고, 바로 발행 전 검토 가능한 블로그 본문을 작성하세요.
        - "참고 자료를 보면", "새 글에서는", "보완하면 좋습니다" 같은 메타 문장을 피하세요.
        - 참고 원문 문장을 복사하지 말고 완전히 새 표현으로 재구성하세요.
        - 제목 후보 5개, 선택 제목, 본문, 참고자료 순서로 출력하세요.
        - 본문에는 소제목과 짧은 문단을 넣으세요.
        - 의료/건강 주제라면 개인 상태에 따라 전문가 상담이 필요하다는 문장을 자연스럽게 포함하세요.

        참고 자료 분석:
        {analysis_text}

        참고 자료:
        {sources}
        """
    ).strip()


def _numbers_summary(text: str) -> str:
    numbers = re.findall(r"\d[\d,]*(?:\.\d+)?\s*(?:mg/dL|㎎/dL|%|분|시간|일|주|개월|년|가지|회|kg|킬로|만장|조원|억달러)?", text)
    unique: list[str] = []
    for number in numbers:
        clean = number.strip()
        if clean and clean not in unique:
            unique.append(clean)
    return ", ".join(unique[:10])


def _sentences(text: str, limit: int = 8) -> list[str]:
    parts = re.split(r"(?<=[.!?。！？])\s+|\n+", text)
    cleaned: list[str] = []
    for part in parts:
        line = re.sub(r"\s+", " ", part).strip()
        if 25 <= len(line) <= 180 and not any(word in line for word in ("공감", "댓글", "블로그", "안부글")):
            cleaned.append(line)
    return cleaned[:limit]


def _topic(analysis: dict, keyword: str, articles: list[Article]) -> str:
    if keyword:
        return clean_title(keyword)
    core = analysis.get("core_topic") or ""
    if core:
        return clean_title(core)
    if articles:
        return clean_title(articles[0].title)
    return "핵심 주제"


def _is_health_topic(text: str) -> bool:
    health_words = ("중성지방", "콜레스테롤", "혈당", "혈압", "지질", "혈관", "대사", "간수치", "건강검진")
    return any(word in text for word in health_words)


def _fallback_health_draft(topic: str, source_text: str, urls: str, analysis: dict) -> str:
    keywords = analysis.get("repeated_keywords", [])
    numbers = _numbers_summary(source_text)
    has_carbs = any(word in source_text for word in ("정제", "탄수화물", "당", "설탕", "음료"))
    has_alcohol = any(word in source_text for word in ("술", "음주", "알코올"))
    has_exercise = any(word in source_text for word in ("운동", "걷기", "유산소", "근력"))
    has_weight = any(word in source_text for word in ("체중", "복부", "허리", "비만"))

    point1 = "첫 번째로 볼 것은 식사입니다. 특히 정제 탄수화물과 단 음료가 자주 반복된다면 중성지방 관리가 어려워질 수 있습니다." if has_carbs else "첫 번째로 볼 것은 식사 패턴입니다. 한 끼를 거창하게 바꾸기보다, 자주 먹는 음식부터 점검하는 편이 현실적입니다."
    point2 = "음주가 잦다면 양과 횟수를 줄이는 것도 중요합니다. 술은 식욕과 야식으로 이어지기 쉬워 중성지방 관리에 방해가 될 수 있습니다." if has_alcohol else "야식과 과식이 잦은지도 함께 확인해야 합니다. 늦은 시간의 과한 섭취는 다음 날 컨디션과 식사 리듬까지 흔들 수 있습니다."
    point3 = "운동은 거창한 계획보다 꾸준함이 먼저입니다. 빠르게 걷기처럼 숨이 조금 차는 활동을 정기적으로 넣고, 가능하다면 근력운동을 함께 하는 방식이 좋습니다." if has_exercise else "활동량을 늘리는 것도 필요합니다. 엘리베이터 대신 계단을 이용하거나 식후 산책을 하는 작은 습관부터 시작할 수 있습니다."
    point4 = "체중, 특히 복부 지방이 고민이라면 식사와 활동량을 함께 조정해야 합니다. 특정 음식 하나보다 생활 패턴 전체를 보는 편이 오래 갑니다." if has_weight else "수면 부족과 스트레스도 생활 리듬을 무너뜨릴 수 있습니다. 몸 상태가 흐트러지면 식사 선택도 함께 흔들리기 쉽습니다."

    return f"""1. 제목 후보 5개
- 중성지방 낮추는 법, 생활습관부터 다시 점검하기
- 건강검진에서 중성지방이 높게 나왔다면 먼저 볼 것
- 의사들이 자주 말하는 중성지방 관리의 기본
- 중성지방을 낮추고 싶을 때 피해야 할 습관
- 식사와 운동으로 시작하는 중성지방 관리법

2. 선택 제목
중성지방 낮추는 법, 생활습관부터 다시 점검하기

3. 본문
## 건강검진 수치가 신경 쓰일 때
건강검진 결과에서 중성지방 수치가 높게 나오면 괜히 마음이 무거워집니다. 당장 큰 문제가 생긴 것은 아니더라도, 혈관 건강이나 대사 상태를 점검하라는 신호일 수 있기 때문입니다.

중성지방은 식사, 음주, 활동량, 체중 변화와 밀접하게 연결됩니다. 그래서 관리 방법도 특별한 비법 하나보다 매일 반복되는 생활습관을 조정하는 쪽에 가깝습니다.

## 중성지방은 왜 올라갈까
중성지방은 우리 몸이 에너지로 쓰고 남은 것을 저장하는 과정과 관련이 있습니다. 문제는 필요 이상으로 에너지가 들어오고, 쓰는 양은 적을 때입니다. 이 흐름이 반복되면 혈액 속 지질 관리가 어려워질 수 있습니다.

참고 자료에서 함께 볼 만한 단서는 {numbers or "식사, 대사, 지질, 혈류, 혈관 같은 키워드"}입니다. 숫자 하나만 보는 것보다 생활 패턴 전체를 함께 보는 것이 중요합니다.

## 1. 정제 탄수화물과 단 음료부터 줄이기
{point1}

밥, 빵, 면을 완전히 끊어야 한다는 뜻은 아닙니다. 다만 흰빵, 과자, 달달한 음료처럼 빠르게 많이 먹기 쉬운 음식은 빈도를 줄이는 편이 좋습니다. 대신 단백질, 채소, 통곡물처럼 포만감을 오래 주는 음식을 함께 구성하면 식사 조절이 조금 수월해집니다.

## 2. 술과 야식은 따로 봐야 합니다
{point2}

중성지방 관리는 “무엇을 먹느냐”만큼 “언제, 얼마나 먹느냐”도 중요합니다. 특히 늦은 시간의 야식은 식사량을 늘리고 다음 날 리듬까지 깨뜨릴 수 있어 주의가 필요합니다.

## 3. 운동은 짧게라도 꾸준히
{point3}

처음부터 무리한 운동 계획을 세우면 오래가기 어렵습니다. 일주일에 며칠이라도 정해진 시간에 걷고, 익숙해지면 강도나 시간을 조금씩 늘리는 방식이 현실적입니다.

## 4. 체중과 허리둘레도 같이 확인하기
{point4}

체중계 숫자만 볼 필요는 없지만, 복부 지방이 늘어나는 흐름은 가볍게 넘기기 어렵습니다. 식사량, 활동량, 수면을 함께 조정해야 변화가 안정적으로 이어집니다.

## 5. 약이나 영양제보다 먼저 확인할 것
영양제나 특정 식품을 먼저 찾기보다 현재 식사와 생활 리듬을 보는 것이 우선입니다. 이미 약을 복용 중이거나 당뇨, 고혈압, 간 질환 같은 기저질환이 있다면 임의로 판단하지 말고 진료를 통해 본인에게 맞는 기준을 확인하는 것이 안전합니다.

## 마무리
중성지방을 낮추는 방법은 결국 매일 반복되는 선택을 조금씩 바꾸는 일입니다. 단 음료를 줄이고, 술과 야식을 조절하고, 움직이는 시간을 늘리는 것부터 시작해도 충분히 의미가 있습니다. 수치가 계속 높거나 다른 검사 결과가 함께 걱정된다면 의료진과 상담해 정확한 원인과 관리 방향을 확인해 보세요.

4. 참고자료
{urls}
"""


def _fallback_openai_draft(source_text: str, urls: str, analysis: dict, style: str) -> str:
    numbers = _numbers_summary(source_text)
    return f"""1. 제목 후보 5개
- 오픈AI 주문은 삼성전자와 SK하이닉스에 기회일까 부담일까
- HBM 투자 경쟁, 진짜 변수는 오픈AI의 현금흐름이다
- 삼성전자와 SK하이닉스가 오픈AI를 신중히 봐야 하는 이유
- AI 메모리 슈퍼사이클 뒤에 숨은 수요 리스크
- 오픈AI, HBM, 대규모 투자: 식당 주인이라면 어떤 선택을 할까

2. 선택 제목
오픈AI 수요가 삼성전자와 SK하이닉스에 던지는 질문

3. 본문
## 큰 주문은 언제나 좋은 소식일까
삼성전자와 SK하이닉스 입장에서 오픈AI는 매력적인 고객입니다. AI 서비스가 커질수록 고성능 메모리와 데이터센터 인프라 수요가 늘어날 가능성이 크기 때문입니다.

하지만 큰 주문이 항상 좋은 주문은 아닙니다. 그 주문을 맞추기 위해 생산능력을 먼저 늘려야 한다면 이야기가 달라집니다. 고객의 수요가 흔들렸을 때 투자 부담은 공급자에게 남을 수 있습니다.

## 핵심은 오픈AI의 수요 지속성
참고 자료에서 눈에 띄는 숫자는 {numbers or "손실 규모, 이용자 수, 웨이퍼 공급량, 설비투자 규모"}입니다. 이 숫자들이 가리키는 질문은 하나입니다. 오픈AI가 장기간 안정적으로 물량을 가져갈 만큼 수익 구조를 만들 수 있느냐는 점입니다.

## HBM 투자는 되돌리기 어렵다
HBM은 일반 제품보다 고객 요구와 기술 조건이 더 까다로운 영역입니다. 특정 고객을 보고 설비를 크게 늘렸는데 수요가 꺾이면, 그 물량을 다른 고객에게 바로 돌리기 어렵습니다.

## 식당 비유로 보면 더 선명하다
평소 하루 100인분을 만들던 식당이 갑자기 큰 단체 주문을 받았다고 생각해 볼 수 있습니다. 매출만 보면 좋은 일입니다. 하지만 그 주문을 맞추려고 냉장고와 주방을 새로 들였는데 몇 달 뒤 주문이 끊기면 투자는 부담으로 바뀝니다.

## 마무리
삼성전자와 SK하이닉스의 고민도 결국 같은 질문으로 돌아옵니다. 큰 주문은 기회지만, 그 기회가 설비투자 이후에도 계속될 때 진짜 기회가 됩니다. 지금 봐야 할 것은 주문의 크기만이 아니라 그 수요가 얼마나 오래 이어질 수 있느냐입니다.

4. 참고자료
{urls}
"""


def _fallback_generic_draft(topic: str, source_text: str, urls: str, analysis: dict) -> str:
    keywords = analysis.get("repeated_keywords", [])[:6]
    keyword_text = ", ".join(keywords) if keywords else topic
    numbers = _numbers_summary(source_text)
    examples = _sentences(source_text, limit=3)
    example_text = "\n\n".join(f"이 대목은 {sentence[:80]}...라는 흐름으로 이해할 수 있습니다." for sentence in examples)
    if not example_text:
        example_text = "핵심은 정보를 그대로 옮기는 것이 아니라, 독자가 바로 이해할 수 있는 순서로 다시 설명하는 것입니다."

    return f"""1. 제목 후보 5개
- {topic} 핵심만 쉽게 정리
- {topic}을 이해하기 전에 알아야 할 것
- 처음 읽는 사람을 위한 {topic} 안내
- {topic}, 놓치기 쉬운 포인트 정리
- {topic}을 볼 때 확인할 기준

2. 선택 제목
{topic} 핵심만 쉽게 정리

3. 본문
## 왜 이 주제를 다시 봐야 할까
{topic}은 겉으로 보기에는 단순해 보여도, 막상 알아보면 여러 기준이 함께 얽혀 있습니다. 그래서 먼저 큰 흐름을 잡고, 그다음 세부 내용을 확인하는 편이 이해하기 쉽습니다.

## 핵심 키워드로 보는 흐름
이 주제에서 함께 봐야 할 키워드는 {keyword_text}입니다. 각각을 따로 보면 흩어진 정보처럼 보이지만, 실제로는 하나의 흐름 안에서 연결됩니다.

## 숫자와 사례는 맥락이 중요하다
{f"자료에서 확인되는 주요 숫자는 {numbers}입니다. " if numbers else ""}숫자는 그 자체보다 왜 등장했는지, 독자의 판단에 어떤 의미가 있는지를 함께 설명해야 합니다.

{example_text}

## 실천하거나 판단할 때의 기준
첫째, 한 가지 정보만 보고 결론 내리지 않는 것이 좋습니다. 둘째, 내 상황에 실제로 적용 가능한지 확인해야 합니다. 셋째, 최신 정보인지와 출처가 분명한지도 함께 보는 편이 안전합니다.

## 마무리
{topic}은 한 번에 정답을 찾기보다 핵심 기준을 잡고 차근차근 확인하는 주제입니다. 아래 참고자료를 바탕으로 내용을 더 검토하고, 실제 적용 전에는 최신 정보와 사실관계를 한 번 더 확인해 주세요.

4. 참고자료
{urls}
"""


def _fallback_draft(articles: list[Article], analysis: dict, style: str, keyword: str) -> str:
    source_text = "\n".join(article.text for article in articles)
    urls = "\n".join(f"- {article.url}" for article in articles)
    topic = _topic(analysis, keyword, articles)

    if _is_health_topic(f"{topic}\n{source_text}"):
        return _fallback_health_draft(topic, source_text, urls, analysis)
    if "삼성전자" in source_text and "SK하이닉스" in source_text and ("오픈AI" in source_text or "OpenAI" in source_text):
        return _fallback_openai_draft(source_text, urls, analysis, style)
    return _fallback_generic_draft(topic, source_text, urls, analysis)


def generate_blog_draft(
    articles: list[Article],
    api_key: str,
    style: str,
    target_length: str,
    keyword: str = "",
    mode_name: str = "참고 자료 기반 작성",
    article_prompt: str = DEFAULT_ARTICLE_PROMPT,
    publish_type: str = "임시 저장",
    log=None,
) -> tuple[str, dict]:
    if log:
        log("[분석] 참고 자료를 분석하는 중입니다.")
    analysis = analyze_articles(articles, user_keyword=keyword)
    prompt = _build_prompt(articles, analysis, style, target_length, keyword, mode_name, article_prompt, publish_type)

    try:
        if api_key:
            if log:
                log("[생성] Gemini API로 블로그 초안을 작성하는 중입니다.")
            draft = _call_gemini(api_key, prompt)
        else:
            if log:
                log("[안내] Gemini API 키가 없어 로컬 초안 생성 모드로 진행합니다.")
            draft = _fallback_draft(articles, analysis, style, keyword)
    except Exception as exc:
        if log:
            log(f"[경고] Gemini 호출 실패: {exc}")
            log("[안내] 로컬 초안 생성 모드로 전환합니다.")
        draft = _fallback_draft(articles, analysis, style, keyword)

    if publish_type != "임시 저장":
        draft += (
            "\n\n---\n발행 유형 안내\n"
            f"- 선택값: {publish_type}\n"
            "- 자동 저장/예약은 브라우저 상태에 따라 실패할 수 있으니 최종 화면을 확인해 주세요.\n"
        )

    if log:
        log("[점검] 참고 원문과 생성 글의 유사 표현을 점검하는 중입니다.")
    plagiarism = check_plagiarism(articles, draft)
    report = "\n\n---\n표절 점검 결과\n"
    report += f"- 결과: {plagiarism['message']}\n"
    if plagiarism["long_matches"]:
        report += "- 12단어 이상 연속 일치 후보:\n"
        report += "\n".join(f"  - {item}" for item in plagiarism["long_matches"])
        report += "\n"
    if plagiarism["similar_sentences"]:
        report += "- 유사 문장 후보:\n"
        report += "\n".join(f"  - {item}" for item in plagiarism["similar_sentences"])
        report += "\n"
    return draft + report, plagiarism


def _local_image_prompt_for_section(section_title: str) -> str:
    if any(word in section_title for word in ("중성지방", "혈관", "건강", "운동", "식사")):
        return "A clean realistic health blog image with healthy meal, walking shoes, and medical checkup paper, no text, no logos"
    if any(word in section_title for word in ("오픈AI", "HBM", "삼성전자", "SK하이닉스", "메모리")):
        return "A realistic editorial image of semiconductor wafers and AI data center servers, no logos, no text"
    return f"A clean realistic editorial blog image about {section_title}, natural lighting, no logos, no text"


def _extract_section_titles(draft: str) -> list[str]:
    titles = re.findall(r"^##\s+(.+)$", draft, flags=re.MULTILINE)
    if titles:
        return titles[:8]
    lines = [line.strip("- ").strip() for line in draft.splitlines() if len(line.strip()) > 20]
    return lines[:5]


def generate_image_prompts(
    draft: str,
    api_key: str = "",
    image_prompt: str = DEFAULT_IMAGE_PROMPT,
    log=None,
) -> str:
    titles = _extract_section_titles(draft)
    if not titles:
        return "No sections found for image prompt generation."

    if api_key:
        try:
            if log:
                log("[이미지] Gemini로 영문 이미지 프롬프트를 생성하는 중입니다.")
            prompt = textwrap.dedent(
                f"""
                {image_prompt or DEFAULT_IMAGE_PROMPT}

                Blog draft:
                {draft[:8000]}
                """
            ).strip()
            return _call_gemini(api_key, prompt, temperature=0.55)
        except Exception as exc:
            if log:
                log(f"[경고] 이미지 프롬프트 Gemini 호출 실패: {exc}")
                log("[이미지] 로컬 이미지 프롬프트 생성으로 전환합니다.")

    return "\n\n".join(f"{index}. {title}\n{_local_image_prompt_for_section(title)}" for index, title in enumerate(titles, start=1))

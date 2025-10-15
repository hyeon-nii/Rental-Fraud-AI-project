"""
Useful Links Provider

키워드 기반 관련 링크 제공
"""

# 키워드별 유용한 링크
LINKS_DATABASE = {
    "주거": {
        "title": "🏠 주거 지원 관련 링크",
        "links": [
            ("LH 청년전세임대주택", "https://apply.lh.or.kr"),
            ("서울시 긴급주거지원", "https://housing.seoul.go.kr"),
            ("공공임대주택 정보", "https://www.lh.or.kr")
        ]
    },
    "금융": {
        "title": "💳 금융 지원 관련 링크",
        "links": [
            ("주택도시기금 디딤돌 대출", "https://nhuf.molit.go.kr"),
            ("HUG 전세피해지원센터", "https://www.khug.or.kr"),
            ("안심전세포털", "https://ansim.khug.or.kr")
        ]
    },
    "법률": {
        "title": "⚖️ 법률 지원 관련 링크",
        "links": [
            ("대한법률구조공단", "https://www.klac.or.kr"),
            ("법률구조 신청", "https://www.klac.or.kr/apply"),
            ("전세사기 법률지원", "https://www.khug.or.kr/legal")
        ]
    },
    "생계": {
        "title": "🆘 긴급 생계 지원 관련 링크",
        "links": [
            ("긴급복지지원", "https://www.129.go.kr"),
            ("서울시 긴급생계비", "https://welfare.seoul.go.kr"),
            ("국민기초생활보장", "https://www.129.go.kr/info")
        ]
    },
    "신청": {
        "title": "📋 신청 및 절차 관련 링크",
        "links": [
            ("전세사기 피해자 신청", "https://www.khug.or.kr/victim"),
            ("서울시 전세사기 지원", "https://housing.seoul.go.kr/support"),
            ("피해자 결정 신청", "https://www.khug.or.kr/apply")
        ]
    }
}


def get_relevant_links(keywords: list) -> str:
    """
    키워드에 맞는 관련 링크 반환
    
    Args:
        keywords: 추출된 키워드 리스트 (예: ["주거", "금융"])
    
    Returns:
        포맷팅된 링크 문자열
    """
    if not keywords:
        return ""
    
    result = []
    
    for keyword in keywords:
        if keyword in LINKS_DATABASE:
            link_info = LINKS_DATABASE[keyword]
            result.append(f"\n{link_info['title']}")
            for name, url in link_info["links"]:
                result.append(f"{name} 👉 {url}")
    
    return "\n".join(result) if result else ""


def get_all_links() -> str:
    """모든 링크를 문자열로 반환"""
    result = []
    
    for keyword, link_info in LINKS_DATABASE.items():
        result.append(f"\n{link_info['title']}")
        for name, url in link_info["links"]:
            result.append(f"{name} 👉 {url}")
    
    return "\n".join(result)

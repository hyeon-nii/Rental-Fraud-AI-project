# rag_engine/useful_links.py

USEFUL_LINKS = {
    "법률지원": {
        "제목": "⚖️ 법률 지원 관련 링크",
        "링크들": [
            ("대한법률구조공단 (전세사기 특별지원)", "https://www.klac.or.kr"),
            ("서울시 법률상담센터", "https://legal.seoul.go.kr"),
            ("법률홈 (무료 법률정보)", "https://www.lawmobile.kr"),
        ]
    },
    "금융지원": {
        "제목": "💳 금융 지원 관련 링크",
        "링크들": [
            ("주택도시기금 디딤돌 대출", "https://nhuf.molit.go.kr"),
            ("HUG 전세피해지원센터", "https://www.khug.or.kr"),
            ("안심전세포털", "https://ansim.khug.or.kr"),
        ]
    },
    "주거지원": {
        "제목": "🏠 주거 지원 관련 링크",
        "링크들": [
            ("LH 청약센터", "https://apply.lh.or.kr"),
            ("서울주거포털", "https://housing.seoul.go.kr"),
            ("긴급주거지원 신청", "https://www.bokjiro.go.kr"),
        ]
    },
    "전세사기": {
        "제목": "🛡️ 전세사기 피해자 지원",
        "링크들": [
            ("전세사기피해자 지원관리시스템", "https://jeonse.kgeop.go.kr"),
            ("국토교통부 전세피해지원단", "https://www.molit.go.kr"),
            ("안심전세포털", "https://ansim.khug.or.kr"),
        ]
    },
    "긴급복지": {
        "제목": "📋 긴급복지 지원",
        "링크들": [
            ("복지로 (긴급복지지원)", "https://www.bokjiro.go.kr"),
            ("희망복지지원단", "https://www.129.go.kr"),
        ]
    }
}


def get_related_links(query: str) -> str:
    """
    사용자 질문에서 키워드를 찾아 관련 링크 반환
    """
    query_lower = query.lower().replace(" ", "")
    found_links = []
    
    # 키워드 매칭
    for keyword, link_info in USEFUL_LINKS.items():
        if keyword in query_lower or keyword.replace(" ", "") in query_lower:
            found_links.append(link_info)
    
    # 링크가 없으면 빈 문자열
    if not found_links:
        return ""
    
    # 링크 포맷팅
    result = "\n\n" + "="*70 + "\n"
    result += "🔗 관련 유용한 링크\n"
    result += "="*70 + "\n\n"
    
    for link_info in found_links:
        result += f"### {link_info['제목']}\n\n"
        for name, url in link_info['링크들']:
            result += f"- **{name}**\n  👉 {url}\n\n"
    
    return result

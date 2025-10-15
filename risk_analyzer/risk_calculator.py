# risk_analyzer/risk_calculator.py
from typing import Dict

try:
    # API에서 호출될 때 (패키지로 사용)
    from .dummy_data import get_lien_data, get_nearby_fraud_cases
except ImportError:
    # CLI에서 직접 실행될 때
    from dummy_data import get_lien_data, get_nearby_fraud_cases


def calculate_risk_score(
    address: str,
    deposit: int,
    price_data: Dict
) -> Dict:
    """논문 기반 전세사기 위험도 계산"""
    
    매매가 = price_data.get("매매가", 0)
    전세가 = price_data.get("전세가", deposit * 10000)
    
    # 1. 전세가율 위험도 (40%)
    전세가율 = (전세가 / 매매가 * 100) if 매매가 > 0 else 0
    
    if 전세가율 >= 90:
        전세가율_점수 = 40
        전세가율_등급 = "극도 위험"
    elif 전세가율 >= 85:
        전세가율_점수 = 35
        전세가율_등급 = "매우 위험 (깡통전세)"
    elif 전세가율 >= 80:
        전세가율_점수 = 30
        전세가율_등급 = "위험"
    elif 전세가율 >= 70:
        전세가율_점수 = 20
        전세가율_등급 = "주의"
    elif 전세가율 >= 60:
        전세가율_점수 = 10
        전세가율_등급 = "보통"
    else:
        전세가율_점수 = 0
        전세가율_등급 = "안전"
    
    # 2. 시장 상황 (20%)
    시장과열도 = price_data.get("시장과열도", "보통")
    거래량 = price_data.get("거래량", 0)
    
    if 시장과열도 == "과열" and 거래량 > 100:
        시장상황_점수 = 15
    elif 시장과열도 == "과열":
        시장상황_점수 = 10
    elif 거래량 < 20:
        시장상황_점수 = 12
    else:
        시장상황_점수 = 5
    
    # 3. 건물/소유주 요인 (30%)
    lien_info = get_lien_data(address)
    
    체납_점수 = 0
    if lien_info["체납액"] > 50000000:
        체납_점수 = 15
    elif lien_info["체납액"] > 20000000:
        체납_점수 = 10
    elif lien_info["체납액"] > 0:
        체납_점수 = 5
    
    근저당비율 = lien_info["근저당비율"]
    if 근저당비율 >= 85:
        근저당_점수 = 15
    elif 근저당비율 >= 75:
        근저당_점수 = 12
    elif 근저당비율 >= 65:
        근저당_점수 = 8
    else:
        근저당_점수 = 0
    
    건물요인_점수 = 체납_점수 + 근저당_점수
    
    # 4. 주변 환경 (10%)
    nearby_fraud = get_nearby_fraud_cases(address)
    
    if nearby_fraud >= 5:
        주변환경_점수 = 10
    elif nearby_fraud >= 3:
        주변환경_점수 = 7
    elif nearby_fraud >= 1:
        주변환경_점수 = 4
    else:
        주변환경_점수 = 0
    
    # 종합 점수
    total_score = (
        전세가율_점수 +
        시장상황_점수 +
        건물요인_점수 +
        주변환경_점수
    )
    
    # 위험 요소
    risk_factors = []
    
    if 전세가율 >= 70:
        risk_factors.append(
            f"• 전세가율 {전세가율:.1f}% ({전세가율_등급}) [+{전세가율_점수}점]"
        )
    
    if lien_info["체납액"] > 0:
        risk_factors.append(
            f"• 건물주 {lien_info['체납종류']} 체납 {lien_info['체납액']:,}원 [+{체납_점수}점]"
        )
    
    if 근저당비율 >= 65:
        risk_factors.append(
            f"• 근저당 설정 {근저당비율}% [+{근저당_점수}점]"
        )
    
    if nearby_fraud > 0:
        risk_factors.append(
            f"• 반경 500m 내 전세사기 {nearby_fraud}건 [+{주변환경_점수}점]"
        )
    
    if 시장과열도 == "과열" or 거래량 < 20:
        risk_factors.append(
            f"• 시장 상황: {시장과열도} (거래량: {거래량}건) [+{시장상황_점수}점]"
        )
    
    # 위험 등급
    if total_score >= 80:
        level = "매우 위험 (1등급)"
        emoji = "🚨"
        recommendation = "✗ 계약 절대 비추천"
        action_level = "즉시 중단"
    elif total_score >= 60:
        level = "위험 (2등급)"
        emoji = "⚠️"
        recommendation = "△ 신중한 검토 필수"
        action_level = "전문가 상담"
    elif total_score >= 40:
        level = "주의 (3등급)"
        emoji = "💛"
        recommendation = "○ 보증보험 가입 필수"
        action_level = "안전장치 필요"
    elif total_score >= 20:
        level = "낮은 위험 (4등급)"
        emoji = "✅"
        recommendation = "○ 계약 가능"
        action_level = "기본 확인"
    else:
        level = "안전 (5등급)"
        emoji = "✅"
        recommendation = "○ 안전한 계약"
        action_level = "정상 진행"
    
    return {
        "점수": total_score,
        "등급": level,
        "이모지": emoji,
        "전세가율": 전세가율,
        "전세가율등급": 전세가율_등급,
        "위험요소": risk_factors,
        "추천사항": recommendation,
        "조치수준": action_level,
        "매매가": 매매가,
        "전세가": 전세가,
        "데이터출처": price_data.get("데이터출처", "알 수 없음"),
        "세부점수": {
            "전세가율": 전세가율_점수,
            "시장상황": 시장상황_점수,
            "건물요인": 건물요인_점수,
            "주변환경": 주변환경_점수
        }
    }

import random


def get_lien_data(address: str) -> dict:
    """근저당 및 체납 정보 (더미 데이터)"""
    high_risk_areas = ["강남구", "송파구", "마포구", "용산구"]
    
    is_high_risk = any(area in address for area in high_risk_areas)
    
    if is_high_risk:
        체납액 = random.choice([0, 0, 2300, 5400, 8900, 12000]) * 10000
        근저당비율 = random.randint(60, 95)
    else:
        체납액 = random.choice([0, 0, 0, 0, 1200, 3400]) * 10000
        근저당비율 = random.randint(30, 75)
    
    return {
        "체납액": 체납액,
        "근저당비율": 근저당비율,
        "체납종류": "국세" if 체납액 > 0 else None
    }


def get_nearby_fraud_cases(address: str) -> int:
    """주변 전세사기 건수 (더미 데이터)"""
    high_risk_areas = ["강남구", "송파구", "마포구", "용산구", "서초구"]
    
    if any(area in address for area in high_risk_areas):
        return random.randint(2, 7)
    return random.randint(0, 3)

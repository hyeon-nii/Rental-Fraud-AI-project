# risk_analyzer/main.py
import sys
import os

sys.path.append(os.path.dirname(__file__))

from seoul_api_client import search_similar_property
from risk_calculator import calculate_risk_score


def run_risk_analysis():
    """전세사기 위험도 AI 진단"""
    print("\n" + "="*70)
    print("🔍 전세사기 위험도 AI 진단 (서울시 실거래가 기반)")
    print("="*70 + "\n")
    
    address = input("📍 주소를 입력하세요 (예: 서울 중구 신당동): ").strip()
    
    try:
        deposit_input = input("💰 보증금을 입력하세요 (만원, 예: 17000): ").strip()
        deposit = int(deposit_input)
    except ValueError:
        print("❌ 보증금은 숫자만 입력해주세요.")
        return
    
    print("\n⏳ 서울시 부동산 실거래가 데이터 조회 중...\n")
    
    price_data = search_similar_property(address, deposit)
    
    if not price_data:
        print("❌ 데이터 조회 실패")
        return
    
    print("\n⏳ 위험도 분석 중...\n")
    result = calculate_risk_score(address, deposit, price_data)
    
    # 결과 출력
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"{result['이모지']} 위험도: {result['점수']}점 ({result['등급']})")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
    
    print("📊 거래 정보:")
    print(f"  • 추정 매매가: {result['매매가']:,}원")
    print(f"  • 입력 보증금: {result['전세가']:,}원")
    print(f"  • 전세가율: {result['전세가율']:.1f}% ({result['전세가율등급']})")
    print(f"  • 데이터: {result['데이터출처']}\n")
    
    if result['위험요소']:
        print("⚠️ 위험 요소:")
        for factor in result['위험요소']:
            print(f"  {factor}")
        print()
    
    print("📈 세부 점수:")
    print(f"  ├─ 전세가율 위험도: {result['세부점수']['전세가율']}/40점")
    print(f"  ├─ 시장 상황: {result['세부점수']['시장상황']}/20점")
    print(f"  ├─ 건물 요인: {result['세부점수']['건물요인']}/30점")
    print(f"  └─ 주변 환경: {result['세부점수']['주변환경']}/10점\n")
    
    print(f"💡 추천: {result['추천사항']}")
    print(f"🚨 조치 수준: {result['조치수준']}\n")
    
    if result['점수'] >= 60:
        print("🔗 추천 조치:")
        print("  → 계약 진행 중단 권장")
        print("  → 등기부등본 정밀 확인")
        print("  → 전세보증보험 가입 필수")
        print("  → HUG 전세피해지원센터 상담 (☎ 1588-1663)\n")
    
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")


if __name__ == "__main__":
    run_risk_analysis()

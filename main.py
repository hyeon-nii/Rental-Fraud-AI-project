import sys
import os

# 경로 추가
sys.path.append(os.path.join(os.path.dirname(__file__), 'classifier'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'rag_engine'))

from classifier.classifier_logic import start_diagnosis_flow, analyze_user_query, CRISIS_KEYWORDS
from rag_engine.run_chain import get_rag_response


def main():
    """AI 담당 2 + AI 담당 1 통합 실행"""
    
    print("="*70)
    print("🏠 전세사기 피해자 지원 통합 상담 시스템")
    print("="*70 + "\n")
    
    # 1단계: AI 담당 2 - 요건 판별
    user_situation = start_diagnosis_flow()
    print(f"\n📊 [1단계 완료] 진단 결과: '{user_situation}'")
    
    # 제외 대상이나 미충족이면 종료
    if user_situation in ["지원 제외 대상", "지원 요건 미충족"]:
        print("\n⚠️ 추가 상담이 필요합니다. 가까운 지원센터에 문의해주세요.")
        return
    
    # 2단계: 사용자 질문 받기
    user_query = input("\n💬 [2단계 진행] 궁금하신 점을 자세히 말씀해주세요: ").strip()
    
    # 위기 키워드 체크
    query_analysis = analyze_user_query(user_query)
    if query_analysis["status"] == "crisis":
        print("\n🚨 [긴급 상황 감지]")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("🆘 자살예방 상담전화: 1393 (24시간 무료)")
        print("🆘 정신건강 위기상담: 1577-0199")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("혼자 감당하지 마시고 전문가와 상담하시길 간곡히 부탁드립니다.")
        return
    
    # 3단계: AI 담당 1 - RAG 답변 생성
    print("\n💭 [3단계 진행] 답변을 생성 중입니다...\n")
    
    response = get_rag_response(user_situation, user_query)
    
    print("\n" + "="*70)
    print("📝 상담 결과")
    print("="*70 + "\n")
    print(response)
    print("\n" + "="*70)
    print("✅ 상담이 완료되었습니다.")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()

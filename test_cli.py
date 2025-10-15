"""
Chatbot Test Console (Enhanced with Conversation History)

콘솔에서 대화 이력 기반 RAG 챗봇을 테스트할 수 있는 스크립트
"""

import sys
from pathlib import Path
from typing import List, Dict
from datetime import datetime

# AI 모듈 경로 추가
ai_modules_path = Path(__file__).resolve().parent / "ai_modules"
sys.path.insert(0, str(ai_modules_path))

from classifier.classifier_logic import (
    start_initial_conversation,
    determine_victim_status,
    analyze_user_query
)
from rag_engine.run_chain import get_rag_response
from rag_engine.contact_info import get_contact_info_text
from rag_engine.useful_links import get_relevant_links


# ==============================================================================
# 대화 이력 관리 클래스 (메모리 기반)
# ==============================================================================
class ConversationMemory:
    """메모리 기반 대화 이력 관리"""
    
    def __init__(self):
        self.messages: List[Dict] = []
        self.context: Dict = {}
    
    def add_message(self, role: str, content: str):
        """메시지 추가"""
        self.messages.append({
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    def get_history(self, limit: int = 10) -> List[Dict]:
        """최근 N개 메시지 조회"""
        return self.messages[-limit:]
    
    def set_context(self, diagnosis: str, district: str):
        """사용자 맥락 저장"""
        self.context = {
            "diagnosis": diagnosis,
            "district": district
        }
    
    def get_context(self) -> Dict:
        """사용자 맥락 조회"""
        return self.context


# ==============================================================================
# RAG 서비스
# ==============================================================================
class ConversationAnalyzer:
    """대화 이력 분석 및 RAG 답변 생성"""
    
    @staticmethod
    def format_history(messages: List[Dict], limit: int = 3) -> str:
        """대화 이력 포맷팅"""
        if not messages:
            return "이전 대화 없음"
        
        recent = messages[-(limit * 2):]
        lines = []
        for msg in recent:
            role = "사용자" if msg["role"] == "user" else "AI"
            content = msg["content"][:200]
            lines.append(f"{role}: {content}")
        
        return "\n".join(lines)
    
    @staticmethod
    def extract_keywords(messages: List[Dict], current_query: str) -> List[str]:
        """키워드 추출"""
        keyword_map = {
            "주거": ["주거", "집", "임대", "전세", "긴급주거비", "공공임대"],
            "금융": ["금융", "대출", "이자", "상환", "디딤돌", "버팀목", "금리"],
            "법률": ["법률", "변호사", "소송", "경매", "대항력"],
            "생계": ["생계", "생활비", "긴급", "복지"],
            "신청": ["신청", "절차", "서류", "방법"],
        }
        
        all_text = " ".join([m["content"] for m in messages if m["role"] == "user"]) + " " + current_query
        
        keywords = []
        for category, words in keyword_map.items():
            if any(word in all_text for word in words):
                keywords.append(category)
        
        return keywords
    
    @staticmethod
    def detect_specific_focus(query: str) -> str | None:
        """
        사용자가 특정 주제만 요청했는지 판단
        
        Returns:
            특정 주제명 (주거, 금융, 법률, 생계) 또는 None
        """
        query_lower = query.lower()
        
        # "주거지원만", "금융만", "주거에 대해서만" 같은 표현 감지
        focus_patterns = {
            "주거": ["주거지원", "주거 지원", "주거만", "집", "임대"],
            "금융": ["금융지원", "금융 지원", "금융만", "대출", "금리"],
            "법률": ["법률지원", "법률 지원", "법률만", "소송", "변호사"],
            "생계": ["생계지원", "생계 지원", "생계만", "생활비", "복지"],
        }
        
        # 특정 주제에 대한 자세한 정보 요청 감지
        detail_keywords = ["자세히", "구체적", "더", "상세히", "대해", "관해"]
        has_detail_request = any(kw in query_lower for kw in detail_keywords)
        
        if has_detail_request:
            for topic, patterns in focus_patterns.items():
                if any(pattern in query_lower for pattern in patterns):
                    # 다른 주제가 언급되지 않았는지 확인
                    other_topics = [t for t in focus_patterns.keys() if t != topic]
                    if not any(any(p in query_lower for p in focus_patterns[other]) for other in other_topics):
                        return topic
        
        return None
    
    @staticmethod
    def is_follow_up(query: str, history: List[Dict]) -> bool:
        """후속 질문 판단"""
        follow_up_keywords = [
            "더", "자세히", "구체적", "추가", "또", "다른", "그럼",
            "그거", "그것", "이것", "그건", "말고"
        ]
        
        has_follow_up = any(kw in query for kw in follow_up_keywords)
        has_history = len(history) > 0
        
        return has_follow_up and has_history
    
    def generate_answer(
        self,
        query: str,
        conversation_memory: ConversationMemory
    ) -> str:
        """대화 이력 기반 RAG 답변 생성"""
        
        history = conversation_memory.get_history(limit=10)
        context = conversation_memory.get_context()
        
        history_text = self.format_history(history[:-1], limit=3)
        keywords = self.extract_keywords(history[:-1], query)
        is_follow_up = self.is_follow_up(query, history[:-1])
        
        # ⭐ 특정 주제 집중 요청 감지
        focused_topic = self.detect_specific_focus(query)
        
        enhanced_query = self._build_prompt(
            query, history_text, keywords, is_follow_up, focused_topic
        )
        
        diagnosis = context.get("diagnosis", "알 수 없음")
        district = context.get("district", "서울")
        
        try:
            response = get_rag_response(
                user_situation=diagnosis,
                user_query=enhanced_query,
                district=district
            )
            
            links = get_relevant_links(keywords)
            if links:
                response += "\n\n" + "="*70
                response += "\n🔗 관련 유용한 링크\n"
                response += "="*70 + "\n"
                response += links
            
            if district and district != "서울":
                contact_info = get_contact_info_text(district)
                if contact_info:
                    response += "\n\n" + "="*70
                    response += f"\n📞 {district} 연락처\n"
                    response += "="*70 + "\n"
                    response += contact_info
            
            return response
            
        except Exception as e:
            return f"죄송합니다. 답변 생성 중 오류가 발생했습니다: {str(e)}"
    
    def _build_prompt(
        self,
        query: str,
        history_text: str,
        keywords: List[str],
        is_follow_up: bool,
        focused_topic: str | None = None  # ⭐ 새로 추가
    ) -> str:
        """프롬프트 생성"""
        
        keyword_hint = f"사용자 관심사: {', '.join(keywords)}" if keywords else ""
        
        # ⭐ 특정 주제에만 집중하라는 지시 추가
        if focused_topic:
            focus_instruction = f"""
⚠️ **중요**: 사용자는 **{focused_topic}지원**에 대해서만 알고 싶어합니다.
- {focused_topic}지원 외의 다른 지원 내용은 **완전히 생략**하세요
- {focused_topic}지원에 대해 **가능한 한 자세하게** 설명하세요
- 구체적인 금액, 금리, 한도, 신청 절차를 모두 포함하세요
"""
        else:
            focus_instruction = ""
        
        if is_follow_up:
            return f"""
[이전 대화 맥락]
{history_text}

[현재 후속 질문]
{query}

{keyword_hint}

{focus_instruction}

📝 답변 가이드:
- 이전 대화에서 이미 설명한 내용은 간략히 언급만 하세요
- 사용자가 추가로 궁금해하는 구체적인 부분에 집중하세요
- 금액, 금리, 기간, 절차, 연락처 등 상세 정보를 제공하세요
"""
        else:
            return f"""
[이전 대화 맥락]
{history_text}

[현재 질문]
{query}

{keyword_hint}

{focus_instruction}

📝 답변 가이드:
- 새로운 질문이므로 전체적인 설명부터 시작하세요
- 구체적인 금액, 절차, 연락처를 포함하세요
"""


# ==============================================================================
# 유틸리티 함수
# ==============================================================================
def print_separator():
    """구분선 출력"""
    print("\n" + "="*70)


def get_yes_no_input(question: str) -> bool:
    """예/아니오 질문"""
    while True:
        answer = input(f"❓ {question} (예/아니오): ").strip().lower()
        if answer in ["예", "y", "yes"]:
            return True
        elif answer in ["아니오", "아니요", "n", "no"]:
            return False
        else:
            print("⚠️ '예' 또는 '아니오'로만 답변해주세요.")


def run_diagnosis() -> dict:
    """7개 질문으로 진단"""
    questions = [
        ("주택 인도, 전입신고, 확정일자를 모두 갖추셨나요? (임차권 등기 포함)", "요건1_대항력"),
        ("임대차 보증금이 5억 원 이하인가요?", "요건2_보증금액"),
        ("집주인의 파산, 경매 등으로 2인 이상 임차인에게 피해가 발생했나요?", "요건3_다수피해"),
        ("임대인이 보증금을 돌려줄 의사나 능력이 없었다고 의심되나요?", "요건4_사기의도"),
        ("전세보증금 반환 보증보험에 가입되어 있나요?", "제외_보증보험"),
        ("소액임차인 최우선변제 제도로 보증금 '전액'을 돌려받을 수 있나요?", "제외_최우선변제"),
        ("대항력(경매 신청 등)을 통해 보증금 '전액'을 직접 회수할 수 있나요?", "제외_자력회수")
    ]
    
    user_data = {}
    print("\nAI 붱: 아래 질문에 '예' 또는 '아니오'로 답해주세요.\n")
    
    for q_text, q_key in questions:
        user_data[q_key] = get_yes_no_input(q_text)
    
    return user_data


# ==============================================================================
# 메인 실행
# ==============================================================================
def main():
    """메인 챗봇 실행"""
    
    memory = ConversationMemory()
    analyzer = ConversationAnalyzer()
    
    print_separator()
    print("🏠 전세사기 피해자 지원 통합 상담 시스템")
    print_separator()
    
    # 1. 초기 상담
    print("\nAI 붱: 안녕하세요, 전세사기에서 당신을 구원해줄 '붱'입니다.")
    print("지금 어떤 상황이신가요? 편하게 말씀해 주세요.\n")
    
    user_input = input("사용자: ").strip()
    
    # 2. 감정 분석
    init_result = start_initial_conversation(user_input)
    
    if init_result.get("status") == "crisis":
        print(f"\nAI 붱: {init_result.get('message', '')}")
        print("\n상담을 종료합니다. 힘내세요. 🙏")
        return
    
    print(f"\nAI 붱: {init_result['message']}")
    
    # 3. 진단 질문
    print_separator()
    user_data = run_diagnosis()
    
    # 4. 진단 결과
    diagnosis_result = determine_victim_status(user_data)
    print(f"\n📊 [진단 결과] 붱의 판단: {diagnosis_result}")
    
    # 5. 자치구 입력 (대화 기록에도 저장)
    print_separator()
    district_question = "📍 [추가 정보] 거주하시는 자치구를 알려주세요 (예: 종로구, 강남구)"
    print(f"\nAI 붱: {district_question}")
    
    # AI의 질문을 대화 기록에 저장
    memory.add_message("assistant", district_question)
    
    district = input("\n사용자: ").strip()
    
    # 사용자의 답변도 대화 기록에 저장
    memory.add_message("user", district)
    
    memory.set_context(diagnosis_result, district)
    
    # 자치구 연락처 출력
    contact_info = get_contact_info_text(district)
    if contact_info:
        print_separator()
        print(f"📞 {district} 연락처")
        print_separator()
        print(contact_info)
    
    # ⭐ 6. 초기 상황 안내 (자동으로 RAG 답변 생성)
    print_separator()
    print("\n💭 현재 상황을 분석하고 있습니다...\n")
    
    initial_query = "나는 이제 뭘해야돼? 받을 수 있는 지원이 뭐가 있어?"
    
    try:
        initial_response = get_rag_response(
            user_situation=diagnosis_result,
            user_query=initial_query,
            district=district
        )
        
        # 초기 안내 메시지 저장
        memory.add_message("assistant", initial_response)
        
        # 출력
        print_separator()
        print("📝 현재 상황 안내")
        print_separator()
        print(initial_response)
        print_separator()
        
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        print("연락처를 통해 직접 상담받으시길 권장합니다.")
    
    # 7. 추가 질문 대화 루프
    print("\n💬 추가로 궁금하신 점을 자유롭게 질문해주세요.")
    print("💡 언제든지 '종료', 'exit', '그만' 을 입력하시면 상담이 종료됩니다.")
    
    question_count = 0
    
    while True:
        print(f"\nAI 붱: 질문: ", end="")
        user_query = input().strip()
        
        # 종료 조건
        if user_query.lower() in ['종료', 'exit', '그만', 'quit', 'q']:
            print(f"\n✅ 상담을 종료합니다. 힘내세요! 🙏")
            print(f"총 {question_count}번의 추가 질문에 답변해드렸습니다.")
            break
        
        if not user_query:
            print("⚠️ 질문을 입력해주세요.")
            continue
        
        # 위기 키워드 체크
        crisis_check = analyze_user_query(user_query)
        if crisis_check["status"] == "crisis":
            print("""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚨 지금 즉시 전화하세요
자살예방상담전화 ☎️ 1393
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            """)
            break
        
        # 사용자 메시지 저장
        memory.add_message("user", user_query)
        
        # RAG 답변 생성
        print("\n💭 답변을 생성 중입니다...")
        
        try:
            response = analyzer.generate_answer(user_query, memory)
            memory.add_message("assistant", response)
            
            # 답변 출력
            print_separator()
            print("📝 답변")
            print_separator()
            print(response)
            print_separator()
            
            question_count += 1
            
            print("\n💬 추가로 궁금하신 점이 있으신가요?")
            print("   (종료하려면 '종료' 입력)")
            
        except Exception as e:
            print(f"\n❌ 오류 발생: {e}")
            print("다시 시도해주세요.")
    
    # 8. 상담 요약
    print("\n" + "="*70)
    print("📊 상담 요약")
    print("="*70)
    print(f"진단 결과: {diagnosis_result}")
    print(f"거주 자치구: {district}")
    print(f"추가 질문 횟수: {question_count}")
    print(f"총 대화 메시지: {len(memory.messages)}개")
    print("="*70)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n상담이 중단되었습니다.")
    except Exception as e:
        print(f"\n오류 발생: {e}")
        import traceback
        traceback.print_exc()

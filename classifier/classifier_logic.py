# classifier/classifier_logic.py
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage
from prompt_utils import load_prompt # 2번 파일에서 만든 함수를 가져옵니다.

# ==============================================================================
# 1. 핵심 판별 로직 및 대화 흐름 관리
# ==============================================================================
def determine_victim_status(user_data: dict) -> str:
    req1 = user_data.get("요건1_대항력", False)
    req2 = user_data.get("요건2_보증금액", False)
    req3 = user_data.get("요건3_다수피해", False)
    req4 = user_data.get("요건4_사기의도", False)
    exc1 = user_data.get("제외_보증보험", False)
    exc2 = user_data.get("제외_최우선변제", False)
    exc3 = user_data.get("제외_자력회수", False)

    if exc1 or exc2 or exc3: return "지원 제외 대상"
    if req1 and req2 and req3 and req4: return "피해자 결정 (모든 지원 가능)"
    if not req1 and req2 and req4: return "피해자 결정 (금융지원 및 긴급복지 가능)"
    if req1 and not req2 and req3 and req4: return "피해자 결정 (조세채권 안분 지원 가능)"
    return "지원 요건 미충족"

def start_diagnosis_flow() -> str:
    print("🤖 안녕하세요, 전세사기 피해자 지원 특별법 대상자 진단을 시작하겠습니다.")
    print("정확한 진단을 위해 몇 가지 질문에 '예' 또는 '아니오'로 답변해주세요.\n")
    
    user_data = {}
    questions = [
        ("주택 인도, 전입신고, 확정일자를 모두 갖추셨나요? (임차권 등기 포함)", "요건1_대항력"),
        ("임대차 보증금이 5억 원 이하인가요?", "요건2_보증금액"),
        ("집주인의 파산, 경매 등으로 2인 이상 임차인에게 피해가 발생했나요?", "요건3_다수피해"),
        ("임대인이 보증금을 돌려줄 의사나 능력이 없었다고 의심되나요?", "요건4_사기의도"),
        ("전세보증금 반환 보증보험에 가입되어 있나요?", "제외_보증보험"),
        ("소액임차인 최우선변제 제도로 보증금 '전액'을 돌려받을 수 있나요?", "제외_최우선변제"),
        ("대항력(경매 신청 등)을 통해 보증금 '전액'을 직접 회수할 수 있나요?", "제외_자력회수")
    ]
    
    def ask(question, key):
        while True:
            answer = input(f"❓ {question} (예/아니오): ").strip().lower()
            if answer in ["예", "y", "yes"]: user_data[key] = True; break
            elif answer in ["아니오", "아니요", "n", "no"]: user_data[key] = False; break
            else: print("⚠️ '예' 또는 '아니오'로만 답변해주세요.")

    for q_text, q_key in questions: ask(q_text, q_key)
    return determine_victim_status(user_data)

# ==============================================================================
# 2. 키워드 및 감정 분석 모듈
# ==============================================================================
CRISIS_KEYWORDS = ["죽고 싶", "자살", "극단적", "끝내고 싶", "너무 힘들어"]

def analyze_user_query(text: str) -> dict:
    processed_text = text.replace(" ", "")
    for keyword in CRISIS_KEYWORDS:
        if keyword in processed_text:
            return {"status": "crisis", "keyword": keyword}
    return {"status": "normal"}

# ==============================================================================
# 3. AI 담당 2 파이프라인 통합 및 프롬프트 생성
# ==============================================================================
def run_ai2_and_create_prompt():
    user_situation = start_diagnosis_flow()
    print(f"\n📊 [1단계 완료] 사용자 상황 진단 결과: '{user_situation}'")

    user_query = input("\n💬 [2단계 진행] 마지막으로, 가장 궁금하신 점을 자세히 말씀해주세요: ")
    query_analysis = analyze_user_query(user_query)
    
    if query_analysis["status"] == "crisis":
        print("\n🚨 [최종 판단] 위기 상황 감지! AI 호출을 중단합니다.")
        return None

    print("\n✅ [최종 판단] 일반 문의 확인. LangChain 프롬프트를 생성합니다.")
    
    # 1번 파일의 내용을 2번 파일의 함수를 이용해 불러옵니다.
    system_prompt_template = load_prompt("system_prompt.txt")
    
    final_prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt_template),
        ("human", "{user_query}")
    ])
    
    formatted_messages = final_prompt.format_messages(
        user_situation=user_situation,
        user_query=user_query
    )

    print("\n--------------------------------------")
    print("📤 AI 담당 1에게 전달할 최종 프롬프트 객체 내용:")
    for msg in formatted_messages:
        print(f"**{msg.type.upper()}:**\n{msg.content}")
    print("--------------------------------------")
    
    return final_prompt

if __name__ == "__main__":
    run_ai2_and_create_prompt()
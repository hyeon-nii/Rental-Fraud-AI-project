from langchain_core.prompts import ChatPromptTemplate

# ==============================================================================
# 0. 설정 및 상수
# ==============================================================================
EMOTION_KEYWORDS = {
    "crisis": [
        "죽고싶어", "죽고싶다", "죽고 싶어", "죽고 싶다", "극단적", "끝내고싶다", "끝내고 싶다",
        "살기싫다", "살기 싫다", "자살", "극단적", "끝내고 싶", "살기 싫어", "없어지고 싶어", "포기하고 싶다",
        "사라지고 싶다", "다 그만두고 싶다", "살 이유를 모르겠다", "너무 괴롭다", "죽을까봐 무섭다"
    ],
    "shock": [
        "방금", "오늘", "갑자기", "미쳤다", "어떡해", "큰일났다", "패닉", "멘붕",
        "제정신이 아니다", "실수했다", "헉", "쇼크", "하루 아침에", "이럴 수가", "믿기지 않는다"
    ],
    "confused": [
        "모르겠어", "복잡해", "어디서부터", "정보가 너무 많아", "무슨 말인지 모르겠어",
        "헷갈려", "정리가 안 돼", "뭐부터 해야 돼", "혼란스러워", "답답해", "처음이라 몰라",
        "이게 맞는지 모르겠어", "질문이 너무 많아", "너무 어렵다"
    ]
}


SYSTEM_PROMPT_PATH = "classifier/system_prompt.txt"

# ==============================================================================
# 1. 감정 감지
# ==============================================================================
def analyze_user_query(text: str) -> dict:
    """사용자의 입력에서 위기/충격/혼란 상황을 감지합니다."""
    processed = text.replace(" ", "")  # 띄어쓰기 제거

    # EMOTION_KEYWORDS 딕셔너리를 순회하도록 수정
    for status, keywords in EMOTION_KEYWORDS.items():
        for keyword in keywords:
            if keyword.replace(" ", "") in processed:
                # status 변수('crisis', 'shock', 'confused')를 그대로 사용
                return {"status": status, "keyword": keyword}

    return {"status": "normal"}


# ==============================================================================
# 2. 초기 상담
# ==============================================================================
def start_initial_conversation(user_input: str = None) -> dict:
    """상담 시작: 감정 상태에 따른 메시지 출력"""
    if user_input is None:
        print("AI 붱: 안녕하세요, 전세사기에서 당신을 구원해줄 '붱'입니다.")
        print("지금 어떤 상황이신가요? 편하게 말씀해 주세요.\n")
        user_input = input("사용자: ").strip()
    
    emotion = analyze_user_query(user_input)

    # 각 감정 단계별 안내
    if emotion["status"] == "crisis":
        crisis_message = """
말씀해주셔서 감사해요.

지금 당장 할 일은 당신의 마음을 돌보는 거예요.

━━━━━━━━━━━━━━━━━━
🚨 지금 즉시 전화하세요
자살예방상담전화 ☎️ 1393
• 24시간 운영
• 무료
• 익명 가능
━━━━━━━━━━━━━━━━━━

전화하시기 어려우시면
카카오톡 '마음터' 채팅상담 (24시간 운영)

전세사기 문제는 당신의 마음이 안정된 다음에 천천히 해결하면 돼요.
제가 여기 있을게요. 언제든 다시 오세요.
        """
        print(f"\nAI 붱: {crisis_message}")
        return {"status": "crisis", "message": crisis_message}

    elif emotion["status"] == "shock":
        message = "당황스러우셨죠. 그럴 수 있어요.\n천천히 숨 쉬고, 저와 함께 상황부터 하나씩 정리해볼까요?"
        print(f"\nAI 붱: {message}")
        return {"status": "normal", "message": message, "text": user_input}

    elif emotion["status"] == "confused":
        message = "혼란스러우시겠지만 괜찮아요.\n제가 단계별로 차근차근 도와드릴게요."
        print(f"\nAI 붱: {message}")
        return {"status": "normal", "message": message, "text": user_input}

    else:
        message = "전세 사기를 당하셨군요. 정말 속상하셨겠어요.\n몇 가지만 확인하고, 어떤 지원이 가능한지 알려드릴게요."
        print(f"\nAI 붱: {message}")
        return {"status": "normal", "message": message, "text": user_input}

# ==============================================================================
# 3. 피해자 요건 진단
# ==============================================================================
def determine_victim_status(user_data: dict) -> str:
    req1 = user_data.get("요건1_대항력", False)
    req2 = user_data.get("요건2_보증금액", False)
    req3 = user_data.get("요건3_다수피해", False)
    req4 = user_data.get("요건4_사기의도", False)
    exc1 = user_data.get("제외_보증보험", False)
    exc2 = user_data.get("제외_최우선변제", False)
    exc3 = user_data.get("제외_자력회수", False)

    if exc1 or exc2 or exc3:
        return "지원 제외 대상"
    if req1 and req2 and req3 and req4:
        return "피해자 결정 (모든 지원 가능)"
    if not req1 and req2 and req4:
        return "피해자 결정 (금융지원 및 긴급복지 가능)"
    if req1 and not req2 and req3 and req4:
        return "피해자 결정 (조세채권 안분 지원 가능)"
    return "지원 요건 미충족"

def start_diagnosis_flow() -> str:
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

    def ask(question, key):
        while True:
            answer = input(f"❓ {question} (예/아니오): ").strip().lower()
            if answer in ["예", "y", "yes"]:
                user_data[key] = True
                break
            elif answer in ["아니오", "아니요", "n", "no"]:
                user_data[key] = False
                break
            else:
                print("⚠️ '예' 또는 '아니오'로만 답변해주세요.")

    for q_text, q_key in questions:
        ask(q_text, q_key)

    result = determine_victim_status(user_data)
    print(f"\n📊 [진단 결과] 붱의 판단: {result}")
    return result

# ==============================================================================
# 4. 프롬프트 생성
# ==============================================================================
def create_prompt(user_situation: str, user_query: str):
    with open(SYSTEM_PROMPT_PATH, "r", encoding="utf-8") as f:
        system_text = f.read()

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_text),
        ("human", "{user_query}")
    ])

    formatted = prompt.format_messages(
        user_situation=user_situation,
        user_query=user_query
    )
    return formatted

# ==============================================================================
# 5. 전체 실행
# ==============================================================================
def run_ai2_pipeline(initial_input: str, diagnosis_answers: dict, final_query: str = ""):
    """
    API 호출용 파이프라인
    
    Args:
        initial_input: 초기 사용자 입력
        diagnosis_answers: 진단 질문에 대한 답변 딕셔너리
        final_query: 추가 질문 (선택사항)
    
    Returns:
        dict: 처리 결과
    """
    # 1. 초기 상담
    init_result = start_initial_conversation(initial_input)
    if init_result["status"] == "crisis":
        return {
            "status": "crisis",
            "message": init_result["message"],
            "final_prompt": None
        }

    # 2. 피해자 진단
    user_situation = start_diagnosis_flow(diagnosis_answers)

    # 3. 최종 프롬프트 생성
    query_to_use = final_query if final_query else initial_input
    final_prompt = create_prompt(user_situation, query_to_use)

    return {
        "status": "success",
        "message": init_result["message"],
        "diagnosis": user_situation,
        "final_prompt": final_prompt
    }


# ==============================================================================
# 6. 콘솔 실행용 함수 (기존 방식 유지)
# ==============================================================================
def run_ai2_pipeline_console():
    """콘솔에서 실행할 때 사용하는 함수"""
    print("AI 붱: 안녕하세요, 전세사기에서 당신을 구원해줄 '붱'입니다.")
    print("지금 어떤 상황이신가요? 편하게 말씀해 주세요.\n")

    user_input = input("사용자: ").strip()
    init_result = start_initial_conversation(user_input)
    
    print(f"\nAI 붱: {init_result['message']}")
    
    if init_result["status"] == "crisis":
        return None

    user_situation = start_diagnosis_flow()

    user_query = input("\nAI 붱: 마지막으로 궁금한 점을 자유롭게 말씀해주세요.\n사용자: ")

    final_prompt = create_prompt(user_situation, user_query)

    print("\n━━━━━━━━━━━━━━━━━━━━━━")
    print("📤 [AI-1 전달용 프롬프트]")
    for msg in final_prompt:
        print(f"**{msg.type.upper()}**\n{msg.content}\n")
    print("━━━━━━━━━━━━━━━━━━━━━━")

    return final_prompt

# ==============================================================================
# 6. 실행
# ==============================================================================
if __name__ == "__main__":
    run_ai2_pipeline()

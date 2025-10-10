# ==============================================================================
# 1. 핵심 판별 로직 함수
# ==============================================================================
def determine_victim_status(user_data: dict) -> dict:
    """
    사용자 데이터를 기반으로 전세사기 피해자 지원 자격을 판별하는 핵심 로직 함수.
    이 함수는 사용자 입력 함수('start_diagnosis')에 의해 호출됩니다.

    Args:
        user_data (dict): 사용자의 상황을 담은 딕셔너리.
    
    Returns:
        dict: 판별 결과 (상태, 사유, 충족/미충족 요건 등)
    """
    # 사용자 데이터에서 각 요건 충족 여부를 변수로 할당
    req1 = user_data.get("대항력_및_확정일자_보유", False)
    req2 = user_data.get("보증금_5억_이하", False)
    req3 = user_data.get("다수_피해_발생", False)
    req4 = user_data.get("임대인_사기_의도", False)
    
    # 적용 제외 대상 여부를 변수로 할당
    exc1 = user_data.get("보증보험_가입", False)
    exc2 = user_data.get("최우선변제로_전액_회수_가능", False)
    exc3 = user_data.get("자력으로_전액_회수_가능", False)

    # --- 판별 로직 시작 ---
    # 1. 적용 제외 대상인지 최우선으로 확인
    if exc1:
        return {"status": "지원 제외 대상", "reason": "보증보험에 가입되어 있어 특별법 지원 대상에서 제외됩니다."}
    if exc2:
        return {"status": "지원 제외 대상", "reason": "보증금이 최우선변제 대상에 해당하여 전액 보호 가능하므로 지원 대상에서 제외됩니다."}
    if exc3:
        return {"status": "지원 제외 대상", "reason": "대항력 등으로 보증금 전액을 직접 회수 가능하다고 판단되어 지원 대상에서 제외됩니다."}

    # 2. 모든 요건 충족 시 (가장 유리한 경우)
    if req1 and req2 and req3 and req4:
        return {
            "status": "피해자 결정 (모든 지원 가능)",
            "reason": "전세사기 피해자 4가지 요건을 모두 충족하여 특별법상 모든 지원을 신청할 수 있습니다.",
            "met_requirements": ["요건1: 대항력", "요건2: 보증금액", "요건3: 다수피해", "요건4: 사기의도"]
        }

    # 3. 일부 요건 충족 시 (차선 지원)
    if req2 and req4:
        return {
            "status": "피해자 결정 (일부 지원 가능)",
            "reason": "대항력은 없으나 보증금액, 임대인 사기 의도 요건(2, 4)을 충족하여 일반 금융 및 긴급 복지 지원이 가능합니다.",
            "unmet_requirements": ["요건1: 대항력", "요건3: 다수피해"]
        }
    if req1 and req3 and req4:
        return {
            "status": "피해자 결정 (조세채권 안분 지원)",
            "reason": "보증금액 요건(2)을 제외한 1, 3, 4번 요건을 충족하여 조세채권 안분 지원을 신청할 수 있습니다.",
            "unmet_requirements": ["요건2: 보증금액"]
        }

    # 4. 위 경우에 모두 해당하지 않으면 지원 불가
    unmet_list = []
    if not req1: unmet_list.append("요건1: 대항력")
    if not req2: unmet_list.append("요건2: 보증금액")
    if not req3: unmet_list.append("요건3: 다수피해")
    if not req4: unmet_list.append("요건4: 사기의도")
    return {
        "status": "지원 요건 미충족",
        "reason": "전세사기 피해자로 인정받기 위한 필수 요건을 충족하지 못했습니다.",
        "unmet_requirements": unmet_list
    }


# ==============================================================================
# 2. 사용자 입력 및 전체 실행 함수
# ==============================================================================
def start_diagnosis():
    """사용자에게 질문하여 피해자 지원 자격을 진단하는 전체 프로세스를 실행합니다."""
    
    print("📋 지금부터 전세사기 피해자 지원 대상 자가진단을 시작하겠습니다.")
    print("각 질문에 '예' 또는 '아니오'로 답변해주세요.\n")
    
    user_data = {}

    # 사용자에게 예/아니오 질문을 던지는 보조 함수
    def ask_question(question_text):
        while True:
            answer = input(f"❓ {question_text} (예/아니오): ").strip().lower()
            if answer in ["예", "y", "yes"]:
                return True
            elif answer in ["아니오", "아니요", "n", "no"]:
                return False
            else:
                print("⚠️ '예' 또는 '아니오'로만 답변해주세요.")

    # --- 사용자에게 순서대로 질문하여 user_data 딕셔너리 구성 ---
    # 1. 필수 요건 질문
    user_data["대항력_및_확정일자_보유"] = ask_question("주택 인도와 전입신고를 마치고, 계약서에 확정일자를 받으셨나요?")
    
    while True: # 숫자만 입력받도록 반복 확인
        try:
            deposit_str = input("❓ 임대차 보증금은 얼마인가요? (숫자만 입력, 예: 300000000): ").strip()
            deposit = int(deposit_str)
            user_data["보증금_5억_이하"] = (deposit <= 500_000_000)
            break
        except ValueError:
            print("⚠️ 숫자만 정확하게 입력해주세요.")

    user_data["다수_피해_발생"] = ask_question("집주인의 파산, 경매 개시 등 2인 이상의 임차인에게 피해가 발생했거나 예상되나요?")
    user_data["임대인_사기_의도"] = ask_question("집주인이 보증금을 반환할 의도 없이 계약했다고 의심할 만한 이유가 있나요?")
    
    # 2. 적용 제외 요건 질문
    print("\n--- 추가 확인 사항 ---")
    user_data["보증보험_가입"] = ask_question("전세보증금 반환 보증보험에 가입되어 있나요?")
    user_data["최우선변제로_전액_회수_가능"] = ask_question("소액임차인 최우선변제 제도로 보증금 '전액'을 돌려받을 수 있나요?")
    user_data["자력으로_전액_회수_가능"] = ask_question("경매 배당 등을 통해 스스로 보증금 '전액'을 회수할 수 있나요?")

    # --- 최종 결과 판별 및 출력 ---
    print("\n--------------------")
    print("🔍 진단 결과를 알려드립니다.")
    print("--------------------")
    
    # 위에서 정의한 핵심 판별 함수(determine_victim_status)를 호출
    result = determine_victim_status(user_data)
    
    print(f"**진단 상태:** {result['status']}")
    print(f"**상세 내용:** {result['reason']}")
    
    # 미충족 요건이 있을 경우 함께 표시
    if result.get("unmet_requirements"):
        print(f"**미충족 요건:** {', '.join(result['unmet_requirements'])}")
        
    print("\n※ 본 진단은 제공된 정보를 바탕으로 한 예비 결과이며, 최종 결정은 국토교통부 심의를 통해 이루어집니다.")


# ==============================================================================
# 3. 프로그램 실행
# ==============================================================================
# 이 스크립트 파일을 직접 실행했을 때만 자가진단을 시작합니다.
if __name__ == "__main__":
    start_diagnosis()
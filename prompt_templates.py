from langchain_core.prompts import ChatPromptTemplate

# 피해 유형 정의 텍스트
VICTIM_TYPE_DESCRIPTION = """
당신은 전세사기 전문가입니다. 피해 유형을 4가지 중 하나로 분류해 주세요:

1. 경매/공매 통지: 임차 주택이 경매/공매 절차에 들어감
2. 보증금 미반환: 계약 만료 후 집주인이 돈을 안 돌려줌
3. 신탁사기: 신탁등기 등으로 보증금 반환이 어려움
4. 조세채권 과다: 체납 세금 때문에 배당금을 못 받음
+ 위기 상황: "죽고싶다", "포기", "끝내고 싶다" 등은 즉시 개입 대상입니다.
"""

# 시스템 프롬프트 정의
SYSTEM_PROMPT = """
당신은 전세사기 피해자 지원 AI입니다.
아래 내용을 바탕으로 피해자의 상황을 분류하고, 필요한 문서 키워드를 제안하고, 공감하며 대응 방안을 3단계로 제안해주세요.
"""

# 템플릿 생성
prompt_template = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT + "\n\n" + VICTIM_TYPE_DESCRIPTION),
    ("human", """
[사용자 입력]
{text}

[피해 유형 키워드]
{keywords}

[예측된 피해 유형]
{victim_type}
""")
])

import os
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.runnables import RunnableParallel, RunnableLambda
from langchain.prompts import ChatPromptTemplate
from .contact_info import get_district_contact, get_contact_info_text
from .useful_links import get_relevant_links  # ← 수정: get_related_links → get_relevant_links


# ⭐ .env 파일 로드
load_dotenv()


# --- 프롬프트 템플릿 정의 ---
SYSTEM_TEMPLATE = """
당신은 전세사기 피해자 지원센터의 친절한 상담원입니다.


## 답변 형식 (3개 섹션만)


### 🎯 1. 고객님의 상황
- 진단 결과를 1-2문장으로 간단히 설명
- 받으실 수 있는 지원 등급 명시


### 💰 2. 받으실 수 있는 지원
**구체적인 금액, 금리, 한도를 <context>에서 찾아 반드시 포함**:


#### 🏠 주거 지원
- 긴급 주거비, 공공임대주택 등 (금액 명시)


#### 💳 금융 지원
- 대출 상품별 금리, 한도 명시
- 예: 디딤돌 대출 연 1.85~2.70%, 최대 3억원


#### 📋 기타 지원
- 생계비, 법률지원 등


### 📝 3. 신청 방법 및 서류


**단계별로 설명**:
1️⃣ 필요한 서류 (체크리스트 형식)
2️⃣ 신청 절차 (간단히 3단계 이내)


## 말투 규칙
- 짧고 명확한 문장 (한 문장 2줄 이내)
- 따뜻한 존댓말
- 이모지로 가독성 향상
- 번호와 체크박스로 구조화


<context>
{context}
</context>
"""


RAG_PROMPT = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_TEMPLATE),
    ("human", "사용자 상황: {user_situation}\n\n질문: {user_query}"),
])


# 현재 파일의 디렉토리 기준으로 경로 설정
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(CURRENT_DIR, "index")
DB_NAME = "jeonse_vector_index"
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


# ⭐ 환경변수에서 API 키 로드
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")


if not GOOGLE_API_KEY:
    raise ValueError("❌ GOOGLE_API_KEY가 설정되지 않았습니다. .env 파일을 확인하세요.")


# ----------------------------------------------------
# RAG 체인 구성 함수
# ----------------------------------------------------


def create_rag_chain():
    """커스텀 RAG 체인 객체를 생성하여 반환합니다."""
    
    print("  -> 임베딩 모델 로드 중...")
    embeddings = HuggingFaceEmbeddings(model_name=MODEL_NAME)
    
    print("  -> FAISS 벡터스토어 로드 중...")
    vectorstore = FAISS.load_local(
        folder_path=DB_PATH, 
        index_name=DB_NAME, 
        embeddings=embeddings, 
        allow_dangerous_deserialization=True
    )
    
    retriever = vectorstore.as_retriever(search_kwargs={"k": 5})

    print("  -> Google Gemini API 연결 중...")
    llm = ChatGoogleGenerativeAI(
        model="models/gemini-2.5-flash",
        temperature=0.2,
        google_api_key=GOOGLE_API_KEY
    )
    
    def format_docs(docs):
        """검색된 문서들을 하나의 문자열로 결합합니다."""
        return "\n\n".join(doc.page_content for doc in docs)
    
    rag_chain = (
        RunnableParallel({
            "context": RunnableLambda(
                lambda x: format_docs(
                    retriever.invoke(f"{x['user_situation']} {x['user_query']}")
                )
            ),
            "user_situation": RunnableLambda(lambda x: x["user_situation"]),
            "user_query": RunnableLambda(lambda x: x["user_query"])
        })
        | RAG_PROMPT
        | llm
    )
    
    print("  -> RAG 체인 생성 완료")
    return rag_chain


# ----------------------------------------------------
# 키워드 추출 함수 (관련 링크용)
# ----------------------------------------------------


def extract_keywords_from_query(query: str) -> list:
    """
    질문에서 키워드 추출
    
    Args:
        query: 사용자 질문
        
    Returns:
        추출된 키워드 리스트
    """
    keyword_map = {
        "주거": ["주거", "집", "임대", "전세", "긴급주거비", "공공임대"],
        "금융": ["금융", "대출", "이자", "상환", "디딤돌", "버팀목", "금리"],
        "법률": ["법률", "변호사", "소송", "경매", "대항력"],
        "생계": ["생계", "생활비", "긴급", "복지"],
        "신청": ["신청", "절차", "서류", "방법"],
    }
    
    keywords = []
    for category, words in keyword_map.items():
        if any(word in query for word in words):
            keywords.append(category)
    
    return keywords


# ----------------------------------------------------
# RAG 응답 생성 함수
# ----------------------------------------------------


def get_rag_response(user_situation: str, user_query: str, district: str = None) -> str:
    """
    AI 담당 2에서 호출할 수 있는 인터페이스 함수
    
    Args:
        user_situation: AI 담당 2가 판별한 상황
        user_query: 사용자의 질문
        district: 사용자의 거주 자치구 (선택사항)
    
    Returns:
        AI 담당 1의 답변 (문자열)
    """
    faiss_file_path = os.path.join(DB_PATH, f"{DB_NAME}.faiss")
    if not os.path.exists(faiss_file_path):
        return f"🚨 오류: 벡터 DB 파일이 없습니다.\n경로: {faiss_file_path}"
    
    rag_chain = create_rag_chain()
    
    try:
        response = rag_chain.invoke({
            "user_situation": user_situation,
            "user_query": user_query
        })
        
        # 기본 답변
        answer = response.content
        
        # ⭐ 관련 링크 추가 (키워드 기반)
        keywords = extract_keywords_from_query(user_query)
        if keywords:
            related_links = get_relevant_links(keywords)  # ← 수정
            if related_links:
                answer += "\n\n" + "="*70
                answer += "\n🔗 관련 유용한 링크\n"
                answer += "="*70 + "\n"
                answer += related_links
        
        # 자치구 정보가 있으면 연락처 추가
        if district:
            contact_info = get_contact_info_text(district)  # ← 수정: 통일된 함수명 사용
            if contact_info:
                answer += "\n\n" + "="*70
                answer += f"\n📞 {district} 연락처\n"
                answer += "="*70 + "\n"
                answer += contact_info
        
        return answer
        
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        return f"❌ 오류 발생: {e}\n\n상세:\n{error_detail}"


# ----------------------------------------------------
# 메인 실행 함수 (테스트용)
# ----------------------------------------------------


if __name__ == "__main__":
    
    faiss_file_path = os.path.join(DB_PATH, f"{DB_NAME}.faiss")
    if not os.path.exists(faiss_file_path):
        print(f"🚨 오류: 벡터 DB 파일이 없습니다.\n경로: {faiss_file_path}")
    else:
        print("\n" + "="*60)
        print("🚀 RAG 체인 로드 및 테스트 시작")
        print("💡 사용 모델: Google Gemini 2.5 Flash (API)")
        print("="*60 + "\n")
        
        # 테스트 입력
        test_input = {
            "user_situation": "피해자 결정 (모든 지원 가능). 경매 진행 중. 종로구 거주.",
            "user_query": "지금 당장 해야 할 3가지 조치와 경매로 집을 뺏기지 않고 계속 살 방법이 궁금합니다."
        }
        
        print("\n💬 Google Gemini API를 호출하여 답변을 생성 중입니다...\n")
        
        response = get_rag_response(
            test_input["user_situation"], 
            test_input["user_query"],
            district="종로구"  # ← 테스트에 자치구 추가
        )
        
        print("\n" + "="*60)
        print(f"📝 테스트 질문: {test_input['user_query']}")
        print("="*60 + "\n")
        print(response)
        print("\n" + "="*60)
        print("✅ 답변 생성 완료!")
        print("="*60 + "\n")

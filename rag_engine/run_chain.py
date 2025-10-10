import os
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.runnables import RunnableParallel, RunnableLambda
from langchain.prompts import ChatPromptTemplate

# ⭐ .env 파일 로드
load_dotenv()

# --- 프롬프트 템플릿 정의 ---
SYSTEM_TEMPLATE = """
당신은 전세사기 피해자 지원센터의 상담원입니다. 
사용자에게 공감하고, 침착하며, 지원 정보를 명확하게 제공해야 합니다.

1. 사용자의 상황과 질문에 가장 적합한 정보를 <context>에서 검색합니다.
2. 답변은 반드시 다음 4가지 섹션을 H2 마크다운 헤딩으로 구분하여 제공해야 합니다.
   - ## 1. 사용자 상황 판단 및 지원 등급
   - ## 2. 지원 가능한 혜택 목록
   - ## 3. 신청 조건 및 제출 서류
   - ## 4. 관할 자치구 연락처
3. 지원 혜택 목록은 <context>의 정보를 활용하여 디딤돌 금리, 대출 한도 등 구체적인 수치를 반드시 포함해야 합니다.
4. 사용자가 '죽고싶다', '포기' 등 위기 키워드를 사용하면, 다른 모든 정보보다 1393 자살 예방 상담 전화 번호를 최우선으로 안내해야 합니다.

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


# ⭐ AI 담당 2에서 호출할 수 있도록 함수로 분리
def get_rag_response(user_situation: str, user_query: str) -> str:
    """
    AI 담당 2에서 호출할 수 있는 인터페이스 함수
    
    Args:
        user_situation: AI 담당 2가 판별한 상황 (예: "피해자 결정 (모든 지원 가능)")
        user_query: 사용자의 질문
    
    Returns:
        AI 담당 1의 답변 (문자열)
    """
    if not os.path.exists(f"{DB_PATH}/{DB_NAME}.faiss"):
        return "🚨 오류: 벡터 DB 파일이 없습니다."
    
    rag_chain = create_rag_chain()
    
    try:
        response = rag_chain.invoke({
            "user_situation": user_situation,
            "user_query": user_query
        })
        return response.content
    except Exception as e:
        return f"❌ 오류 발생: {e}"


# ----------------------------------------------------
# 메인 실행 함수 (테스트용)
# ----------------------------------------------------

if __name__ == "__main__":
    
    if not os.path.exists(f"{DB_PATH}/{DB_NAME}.faiss"):
        print("🚨 오류: 벡터 DB 파일이 없습니다.")
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
            test_input["user_query"]
        )
        
        print("\n" + "="*60)
        print(f"📝 테스트 질문: {test_input['user_query']}")
        print("="*60 + "\n")
        print(response)
        print("\n" + "="*60)
        print("✅ 답변 생성 완료!")
        print("="*60 + "\n")

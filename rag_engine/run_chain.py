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

# --- 환경 및 경로 설정 ---
DB_PATH = "index"
DB_NAME = "jeonse_vector_index"
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

# ⭐ 환경변수에서 API 키 로드
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# API 키 검증
if not GOOGLE_API_KEY:
    raise ValueError("❌ GOOGLE_API_KEY가 설정되지 않았습니다. .env 파일을 확인하세요.")

# ----------------------------------------------------
# RAG 체인 구성 함수
# ----------------------------------------------------

def create_rag_chain():
    """커스텀 RAG 체인 객체를 생성하여 반환합니다."""
    
    # 1. FAISS DB 로드 및 검색기 연결
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

    # 2. Google Gemini LLM 로드
    print("  -> Google Gemini API 연결 중...")
    llm = ChatGoogleGenerativeAI(
        model="models/gemini-2.5-flash",
        temperature=0.2,
        google_api_key=GOOGLE_API_KEY
    )
    
    # 3. 문서 포맷팅 함수
    def format_docs(docs):
        """검색된 문서들을 하나의 문자열로 결합합니다."""
        return "\n\n".join(doc.page_content for doc in docs)
    
    # 4. 커스텀 RAG 체인 구성
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
# 메인 실행 함수
# ----------------------------------------------------

if __name__ == "__main__":
    
    if not os.path.exists(f"{DB_PATH}/{DB_NAME}.faiss"):
        print("🚨 오류: 벡터 DB 파일이 없습니다. 먼저 'create_db.py'를 실행해주세요.")
    else:
        print("\n" + "="*60)
        print("🚀 RAG 체인 로드 및 테스트 시작")
        print("💡 사용 모델: Google Gemini 2.5 Flash (API)")
        print("="*60 + "\n")
        
        # 1. RAG 체인 생성
        rag_chain = create_rag_chain()
        
        # 2. 테스트 입력
        test_input = {
            "user_situation": "4가지 요건 모두 충족함. 거주하던 집이 경매 통지서를 받았고, 저는 계속 살고 싶습니다. 저는 종로구에 거주하고 있습니다.",
            "user_query": "지금 당장 해야 할 3가지 조치와 경매로 집을 뺏기지 않고 계속 살 방법이 궁금합니다."
        }
        
        # 3. 체인 실행
        print("\n💬 Google Gemini API를 호출하여 답변을 생성 중입니다...\n")
        
        try:
            response = rag_chain.invoke(test_input)
            
            print("\n" + "="*60)
            print(f"📝 테스트 질문: {test_input['user_query']}")
            print("="*60 + "\n")
            print(response.content)
            print("\n" + "="*60)
            print("✅ 답변 생성 완료!")
            print("="*60 + "\n")
            
        except Exception as e:
            print(f"\n❌ RAG 체인 실행 중 오류 발생: {e}")
            import traceback
            traceback.print_exc()
            print("\n🚨 오류 해결 방법:")
            print("  1. GOOGLE_API_KEY가 .env 파일에 올바르게 입력되었는지 확인")
            print("  2. .env 파일이 run_chain.py와 같은 폴더에 있는지 확인")
            print("  3. pip install python-dotenv 실행")

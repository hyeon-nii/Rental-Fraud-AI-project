# 01_create_db.py

import os
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from typing import List
from langchain_core.documents import Document

# --- 환경 및 경로 설정 ---
KB_PATH = "knowledge_base"
DB_PATH = "index"
DB_NAME = "jeonse_vector_index"
# ❗ B단계 수정: 안정적인 공개 임베딩 모델로 변경 (오류 해결)
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2" 

# ----------------------------------------------------
# A 단계: 문서 로딩 및 청킹 함수
# ----------------------------------------------------

def load_and_split_documents(data_folder_path: str) -> List[Document]:
    """PDF와 MD 파일을 모두 로드하고 청크로 분할하며 메타데이터를 태깅합니다."""
    all_chunks = []
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=700,
        chunk_overlap=100,
        separators=["\n\n", "\n", "."], 
        length_function=len
    )

    for filename in os.listdir(data_folder_path):
        file_path = os.path.join(data_folder_path, filename)
        documents = []

        if filename.endswith(".pdf"):
            print(f"  -> Loading PDF: {filename}")
            loader = PyPDFLoader(file_path)
            documents = loader.load()
            file_tag = "법규_법률"
        
        elif filename.endswith((".md", ".txt")):
            print(f"  -> Loading MD/TXT: {filename}")
            loader = TextLoader(file_path, encoding='utf-8') 
            documents = loader.load()
            file_tag = "지원_실무"
        
        else:
            continue

        # 청킹 및 메타데이터 태깅
        chunks = text_splitter.split_documents(documents)
        
        for chunk in chunks:
            chunk.metadata["source"] = filename
            chunk.metadata["file_type"] = file_tag

            # 핵심 내용 기반의 필터링 태그 추가 (AI-2의 분류와 연계)
            content = chunk.page_content
            if "금융지원" in content or "대환대출" in content or "분할상환" in content:
                chunk.metadata["action_type"] = "금융"
            elif "경매" in content or "공매" in content or "법률전문가" in content:
                chunk.metadata["action_type"] = "경공매_법률"
            elif "생계비" in content or "심리 상담" in content:
                chunk.metadata["action_type"] = "복지_심리"
            elif "종로구" in content or "강남구" in content or "자치구" in content:
                chunk.metadata["action_type"] = "연락처_행정"
            else:
                 chunk.metadata["action_type"] = "일반_요건"

            all_chunks.extend(chunks)
            
    return all_chunks


# ----------------------------------------------------
# B 단계: 벡터 DB 생성 및 저장 함수
# ----------------------------------------------------

def create_vector_db(chunks: List[Document]):
    """문서 청크를 벡터화하여 FAISS DB로 저장합니다."""
    
    print(f"  -> 임베딩 모델 로드: {MODEL_NAME}")
    
    embeddings = HuggingFaceEmbeddings(model_name=MODEL_NAME)
    
    if not os.path.exists(DB_PATH):
        os.makedirs(DB_PATH)
        
    vectorstore = FAISS.from_documents(chunks, embeddings)
    vectorstore.save_local(folder_path=DB_PATH, index_name=DB_NAME)
    
    print(f"\n✅ 벡터 DB가 '{DB_PATH}/{DB_NAME}.faiss'에 {len(chunks)}개 청크로 저장 완료되었습니다.")


# ----------------------------------------------------
# 메인 실행
# ----------------------------------------------------
if __name__ == "__main__":
    if os.path.exists(f"{DB_PATH}/{DB_NAME}.faiss"):
        print(f"✅ 벡터 DB가 이미 존재합니다. 'index' 폴더를 삭제하고 재실행하세요.")
    else:
        print("--- 1. 문서 로드 및 청킹 시작 (A 단계) ---")
        documents_to_embed = load_and_split_documents(KB_PATH)
        print(f"   -> 총 {len(documents_to_embed)}개 청크 생성 완료.")
        
        print("\n--- 2. 벡터 인덱스 생성 시작 (B 단계) ---")
        create_vector_db(documents_to_embed)
        print("\n[01_create_db.py 실행 완료: RAG 두뇌 구축 완료]")
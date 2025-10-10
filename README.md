## 🏠 전세사기 피해자 지원 AI 모델

<br  />

### 1. RAG 기반 상담 시스템

<br />

**기술 스택**
- 임베딩: HuggingFace `all-MiniLM-L6-v2` (384차원)
- 벡터 DB: FAISS (Facebook AI Similarity Search)
- LLM: Google Gemini 1.5 Flash (128K context)
- 프레임워크: LangChain (LCEL)

**핵심 기술**
- 문서 청크 분할 (512자) → 벡터 임베딩 → FAISS 인덱싱
- 의미 기반 유사도 검색 (cosine similarity, Top-K=5)
- RAG 체인: Retriever → PromptTemplate → Gemini → Parser
- 대화 메모리: ConversationBufferWindowMemory (최근 5개)

<br  />

### 2. 위험도 분석 시스템

<br />

**기술 스택**
- 데이터: 서울시 부동산 실거래가 Open API (XML)
- 알고리즘: 논문 기반 규칙 시스템 (Rule-based)
- 파싱: requests + xml.etree.ElementTree

**핵심 기술**
- API 호출: GET /tbLnOpendataRtmsV → 200건 실거래가 조회
- 전세가율 계산: LTV = (전세가 / 매매가) × 100
- 위험도 산정: 가중 합산 (전세가율 40% + 시장 20% + 건물 30% + 주변 10%)
- 5등급 분류: 80점↑ 매우위험 ~ 20점↓ 안전


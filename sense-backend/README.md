# SENSE Backend - 재난 대응 행동 에이전트 시스템

재난 문자 및 사용자 질문을 처리하여 즉시 행동 지침을 제공하는 에이전트 시스템입니다.

## 아키텍처

### 에이전트 파이프라인 (순서 보장)
1. **ProfileAgent**: 사용자 프로필 및 상황 분석
2. **PlanningAgent**: 분석 계획 수립
3. **AnalystAgent**: Hybrid RAG 기반 정보 분석
4. **AdvisorAgent**: 행동 지침 제시 (immediate/next/caution)

### Hybrid RAG
- **Graph RAG**: Neo4j 그래프 DB에서 구조화된 정보 검색
- **Vector RAG**: Chroma 벡터 DB에서 문서 검색

### LLM 지원
- **Ollama** (로컬 모델): Gemma3:4b, Qwen3:4b 등
- **Gemini** (Google API): gemini-2.0-flash-exp 등

## 설치

### 1. 의존성 설치
```bash
pip install -r ../requirements.txt
```

### 2. 환경 변수 설정 (.env)
```env
# Neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password

# Chroma
CHROMA_PERSIST_DIR=data/chroma
CHROMA_COLLECTION_NAME=disaster_docs

# LLM (Ollama 또는 Gemini 중 선택)
LLM_PROVIDER=ollama  # 또는 "gemini"
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=gemma3:4b

# Gemini (LLM_PROVIDER=gemini인 경우)
GEMINI_API_KEY=your-api-key
GEMINI_MODEL=gemini-2.0-flash-exp

# API
API_HOST=0.0.0.0
API_PORT=8000
```

### 3. Ollama 설정 (로컬 모델 사용 시)
```bash
# Ollama 설치 및 실행
curl https://ollama.ai/install.sh | sh
ollama serve

# 모델 다운로드
ollama pull gemma3:4b
# 또는
ollama pull qwen3:4b
```

### 4. Neo4j 및 데이터 준비
- Neo4j 실행 (Docker 또는 로컬)
- `3_preprocessing.ipynb` 실행하여 Neo4j 데이터 적재
- Chroma 컬렉션에 문서 적재

## 실행

### API 서버 실행
```bash
# 방법 1: 직접 실행
python -m backend.api

# 방법 2: uvicorn 사용
uvicorn backend.api:app --host 0.0.0.0 --port 8000 --reload

# 방법 3: run_server.py 사용 (프로젝트 루트에서)
python run_server.py
```

### API 엔드포인트

#### 1. 헬스 체크
```bash
curl http://localhost:8000/health
```

#### 2. 재난 문자 처리
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "[긴급재난문자] 지진 경보 발령. 서초구 강남대로 지역 주민은 즉시 대피하세요.",
    "message_type": "disaster_alert"
  }'
```

#### 3. 사용자 질문 처리
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "강남구에 있는 대피소는 몇 개인가요?",
    "message_type": "user_question",
    "conversation_id": "test-conv-123"
  }'
```

#### 4. 대화 히스토리 조회
```bash
curl http://localhost:8000/conversation/{conversation_id}
```

## 응답 형식

```json
{
  "conversation_id": "uuid",
  "message": "사용자 메시지",
  "final_response": "## 🚨 즉시 행동\n1. ...\n\n## 📋 다음 단계\n1. ...\n\n## ⚠️ 주의사항\n1. ...",
  "immediate_actions": ["즉시 행동 1", "즉시 행동 2"],
  "next_actions": ["다음 행동 1", "다음 행동 2"],
  "caution_notes": ["주의사항 1", "주의사항 2"],
  "explanation_path": [
    "ProfileAgent: 사용자 상황 분석 근거",
    "PlanningAgent: 분석 계획 근거",
    "AnalystAgent: 검색 결과 분석 근거",
    "AdvisorAgent: 행동 지침 근거"
  ],
  "metadata": {
    "user_profile": {...},
    "analysis_plan": {...},
    "graph_results_count": 10,
    "vector_results_count": 5,
    ...
  }
}
```

## Explainability (추론 근거)

모든 에이전트의 추론 근거가 `explanation_path`에 저장됩니다:
- **ProfileAgent**: 사용자 상황 분석 근거
- **PlanningAgent**: 분석 계획 수립 근거
- **AnalystAgent**: RAG 검색 결과 분석 근거
- **AdvisorAgent**: 행동 지침 생성 근거

각 단계의 근거는 `metadata`에도 상세 정보가 포함됩니다.

## 대화 관리

### 단일 대화
- `conversation_id`를 제공하지 않으면 자동 생성
- 각 요청은 독립적으로 처리

### 멀티턴 대화
- 동일한 `conversation_id`를 사용하여 연속 대화
- `user_context`에 이전 대화 정보 포함 가능
- 대화 히스토리는 `/conversation/{conversation_id}`로 조회

## 코드 구조

```
backend/
├── __init__.py          # 패키지 초기화
├── config.py            # 설정 관리
├── types.py             # 타입 정의 (AgentState, AgentStateModel 등)
├── db.py                # DB 연결 관리 (Neo4j, Chroma)
├── llm.py               # LLM 클라이언트 (Ollama/Gemini)
├── rag.py               # Hybrid RAG 모듈
├── orchestrator.py      # LangGraph 기반 오케스트레이터
├── api.py               # FastAPI 엔드포인트
└── agents/
    ├── __init__.py
    ├── profile.py       # ProfileAgent
    ├── planning.py      # PlanningAgent
    ├── analyst.py       # AnalystAgent
    └── advisor.py        # AdvisorAgent
```

## 주요 특징

1. **순서 보장**: LangGraph를 사용하여 에이전트 실행 순서 보장
2. **Hybrid RAG**: Graph RAG와 Vector RAG 결합으로 정확한 정보 제공
3. **Explainability**: 모든 추론 단계의 근거 추적
4. **멀티턴 대화**: 단일 및 멀티턴 대화 모두 지원
5. **재난 문자 지원**: 재난 문자와 일반 질문 모두 처리 가능
6. **LLM 유연성**: Ollama(로컬) 또는 Gemini(API) 선택 가능

## 문제 해결

### Neo4j 연결 실패
- Neo4j가 실행 중인지 확인: `neo4j status`
- 환경 변수 확인: `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`

### Chroma 컬렉션 없음
- `data/chroma` 디렉토리 확인
- `docs/` 폴더의 마크다운 파일 적재 확인

### Ollama 연결 실패
- Ollama 실행 확인: `ollama serve`
- 모델 다운로드 확인: `ollama list`
- 환경 변수 확인: `OLLAMA_BASE_URL`, `OLLAMA_MODEL`

### Gemini API 오류
- API 키 확인: `GEMINI_API_KEY`
- 모델명 확인: `GEMINI_MODEL`
- `LLM_PROVIDER=gemini` 설정 확인


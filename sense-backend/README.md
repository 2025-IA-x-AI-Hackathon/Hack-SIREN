# SENSE Backend - 재난 대응 행동 에이전트

재난 문자와 사용자 질문을 모두 처리하는 에이전트 시스템입니다.

## 아키텍처

- **ProfileAgent**: 입력 분석 (재난 문자 또는 사용자 질문)
- **PlanningAgent**: 검색 계획 수립
- **AnalystAgent**: Graph RAG + Vector RAG 검색 실행
- **AdvisorAgent**: 행동지침 생성 (immediate/next/caution)
- **Orchestrator**: LangGraph를 사용한 에이전트 순서 보장

## 설치

```bash
pip install -r requirements.txt
```

## 환경 변수 설정

`.env` 파일 생성:

```env
GOOGLE_API_KEY=your_gemini_api_key
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password
```

## 실행

```bash
python backend/main.py
```

또는:

```bash
uvicorn api:app --host 0.0.0.0 --port 8000
```

## API 엔드포인트

### POST /chat

채팅 요청:

```json
{
  "message": "지진 발생 시 어떻게 해야 하나요?",
  "conversation_id": "user123",
  "history": []
}
```

응답:

```json
{
  "answer": "## 즉시 행동 (IMMEDIATE)\n1. ...",
  "immediate": ["즉시 행동 1", "즉시 행동 2"],
  "next": ["다음 단계 1"],
  "caution": ["주의사항 1"],
  "explanation": {
    "profile": {...},
    "planning": {...},
    "analysis": {...},
    "advisory": {...}
  },
  "conversation_id": "user123"
}
```

### GET /health

헬스 체크

### GET /conversations/{conversation_id}

대화 히스토리 조회

### DELETE /conversations/{conversation_id}

대화 히스토리 삭제

## 특징

- 재난 문자와 사용자 질문 모두 처리 가능
- 단일 대화 및 멀티턴 대화 지원
- Explainability 추적 (각 에이전트의 추론 과정 기록)
- LLM 기반 생성 (루틴베이스 최소화)
- LangGraph를 사용한 엄격한 순서 보장

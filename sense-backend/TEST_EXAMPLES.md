# 테스트 예시

## 1. 재난 문자 처리

### 예시 1: 지진 경보
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "[긴급재난문자] 지진 경보 발령. 서초구 강남대로 지역 주민은 즉시 대피하세요.",
    "message_type": "disaster_alert"
  }'
```

**예상 응답 구조:**
- `immediate_actions`: 즉시 대피 행동
- `next_actions`: 대피 후 행동
- `caution_notes`: 안전 주의사항
- `explanation_path`: 각 에이전트의 추론 근거

### 예시 2: 공습 경보
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "[공습경보] 공습 경보가 발령되었습니다. 가까운 지하 대피소로 이동하세요.",
    "message_type": "disaster_alert"
  }'
```

## 2. 사용자 질문 처리

### 예시 1: 대피소 위치 문의
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "강남구에 있는 대피소는 몇 개인가요?",
    "message_type": "user_question"
  }'
```

### 예시 2: 대피소 찾기
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "지진이 발생했을 때 가까운 대피소를 찾고 싶어요. 서초구 근처 대피소를 알려주세요.",
    "message_type": "user_question"
  }'
```

### 예시 3: 행동 요령 문의
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "지진 발생 시 어떻게 행동해야 하나요?",
    "message_type": "user_question"
  }'
```

## 3. 멀티턴 대화

### 첫 번째 메시지
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "강남구 대피소 위치를 알려주세요.",
    "message_type": "user_question",
    "conversation_id": "multi-turn-123"
  }'
```

### 두 번째 메시지 (같은 conversation_id 사용)
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "가장 가까운 대피소는 어디인가요?",
    "message_type": "user_question",
    "conversation_id": "multi-turn-123",
    "user_context": {
      "previous_location": "강남구"
    }
  }'
```

### 대화 히스토리 조회
```bash
curl http://localhost:8000/conversation/multi-turn-123
```

## 4. Explainability 확인

응답의 `explanation_path`와 `metadata`를 통해 각 에이전트의 추론 근거를 확인할 수 있습니다:

```json
{
  "explanation_path": [
    "ProfileAgent: 재난 유형(지진)과 긴급도(긴급) 분석",
    "PlanningAgent: 위치 기반 대피소 검색과 행동 요령 검색 계획",
    "AnalystAgent: Graph RAG에서 10개 대피소 발견, Vector RAG에서 행동 요령 문서 검색",
    "AdvisorAgent: 즉시 대피 행동 지침 생성"
  ],
  "metadata": {
    "user_profile": {
      "disaster_type": "지진",
      "urgency": "긴급",
      "location": "서초구"
    },
    "analysis_plan": {
      "search_strategy": "hybrid",
      "graph_queries": ["서초구 대피소 위치"],
      "vector_queries": ["지진 행동 요령"]
    },
    "graph_results_count": 10,
    "vector_results_count": 3,
    "profile_reasoning": "...",
    "planning_reasoning": "...",
    "analyst_reasoning": "...",
    "advisor_reasoning": "..."
  }
}
```

## 5. Python 클라이언트 예시

```python
import requests
import json

BASE_URL = "http://localhost:8000"

# 재난 문자 처리
def process_disaster_alert(message: str):
    response = requests.post(
        f"{BASE_URL}/chat",
        json={
            "message": message,
            "message_type": "disaster_alert"
        }
    )
    return response.json()

# 사용자 질문 처리
def process_user_question(message: str, conversation_id: str = None):
    data = {
        "message": message,
        "message_type": "user_question"
    }
    if conversation_id:
        data["conversation_id"] = conversation_id
    
    response = requests.post(f"{BASE_URL}/chat", json=data)
    return response.json()

# 테스트
if __name__ == "__main__":
    # 재난 문자 테스트
    result1 = process_disaster_alert(
        "[긴급재난문자] 지진 경보 발령. 서초구 강남대로 지역 주민은 즉시 대피하세요."
    )
    print("재난 문자 처리 결과:")
    print(json.dumps(result1, ensure_ascii=False, indent=2))
    
    # 사용자 질문 테스트
    result2 = process_user_question("강남구에 있는 대피소는 몇 개인가요?")
    print("\n사용자 질문 처리 결과:")
    print(json.dumps(result2, ensure_ascii=False, indent=2))
```


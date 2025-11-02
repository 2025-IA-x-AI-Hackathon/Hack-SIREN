# SENSE Backend

재난 대응 행동 에이전트 백엔드 시스템

## 환경 설정

### Docker Compose 사용 (권장)

1. 환경 변수 설정:
```bash
cp .env.example .env
# .env 파일을 편집하여 GOOGLE_API_KEY 설정
```

2. Docker Compose로 모든 서비스 실행:
```bash
docker compose up -d
```

3. 서비스 상태 확인:
```bash
docker compose ps
```

4. 로그 확인:
```bash
docker compose logs -f api
```

### 로컬 개발 환경

1. Python 가상환경 설정:
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

2. 환경 변수 설정:
```bash
cp .env.example .env
# .env 파일을 편집하여 필요한 변수 설정
```

3. Neo4j 및 Chroma 로컬 실행:
- Neo4j: Docker 또는 로컬 설치
- Chroma: 로컬 실행 (PersistentClient 사용)

4. API 서버 실행:
```bash
python main.py
```

## 서비스 포트

- **API**: http://localhost:8000
- **Neo4j Browser**: http://localhost:7474
- **Neo4j Bolt**: bolt://localhost:7687
- **Chroma**: http://localhost:8001

## API 엔드포인트

### POST /chat
채팅 메시지 전송

```json
{
  "message": "지진이 발생했을 때 가까운 대피소를 찾고 싶어요",
  "user_info": {
    "lat": 37.5665,
    "lon": 126.9780,
    "floor": 3
  },
  "conversation_id": "user123"
}
```

### GET /health
헬스 체크

### GET /conversations/{conversation_id}
대화 히스토리 조회

## Docker 명령어

```bash
# 서비스 시작
docker compose up -d

# 서비스 중지
docker compose down

# 서비스 재시작
docker compose restart

# 특정 서비스 재빌드
docker compose build api
docker compose up -d api

# 로그 확인
docker compose logs -f api
docker compose logs -f neo4j
docker compose logs -f chroma

# 데이터 볼륨 확인
docker volume ls

# 데이터 볼륨 삭제 (주의: 모든 데이터 삭제됨)
docker compose down -v
```

## 개발 팁

1. **API 코드 수정 후 재시작**:
   ```bash
   docker compose restart api
   ```

2. **Neo4j 데이터 초기화**:
   ```bash
   docker compose down neo4j
   docker volume rm backend_neo4j_data
   docker compose up -d neo4j
   ```

3. **Chroma 데이터 확인**:
   ```bash
   docker compose exec chroma ls -la /chroma/chroma
   ```

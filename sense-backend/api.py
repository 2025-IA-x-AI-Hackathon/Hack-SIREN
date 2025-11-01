"""FastAPI 엔드포인트"""
from typing import Optional, Dict, Any, List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from orchestrator import orchestrator
from types import MessageType, AgentStateModel
from db import db_manager


# 요청/응답 모델
class ChatRequest(BaseModel):
    """채팅 요청"""
    message: str
    message_type: str  # "disaster_alert" or "user_question"
    conversation_id: Optional[str] = None
    user_context: Optional[Dict[str, Any]] = None


class ShelterInfo(BaseModel):
    """대피소 정보"""
    name: str
    address: str
    lat: float
    lon: float
    shelter_type: Optional[str] = None


class ChatResponse(BaseModel):
    """채팅 응답 (간소화)"""
    immediate_actions: List[str]  # 즉시 취해야 할 행동 지침
    shelters: List[ShelterInfo]  # 대피소 지도 좌표
    urgency: str  # 긴급도
    situation_description: str  # 현재 상황에 대한 설명


# FastAPI 앱 생성
app = FastAPI(
    title="SENSE API",
    description="재난 대응 행동 에이전트 API",
    version="0.1.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 대화 히스토리 저장 (메모리 기반, 실제로는 Redis 등 사용)
conversation_history: Dict[str, List[Dict[str, Any]]] = {}


def get_or_create_conversation_id(request: ChatRequest) -> str:
    """대화 ID 가져오기 또는 생성"""
    if request.conversation_id:
        return request.conversation_id
    
    # 새 대화 ID 생성
    import uuid
    return str(uuid.uuid4())


def update_conversation_history(conversation_id: str, message: str, response: AgentStateModel):
    """대화 히스토리 업데이트"""
    if conversation_id not in conversation_history:
        conversation_history[conversation_id] = []
    
    conversation_history[conversation_id].append({
        "message": message,
        "response": response.final_response,
        "immediate_actions": response.immediate_actions or [],
        "next_actions": response.next_actions or [],
        "caution_notes": response.caution_notes or [],
        "explanation_path": response.explanation_path or []
    })


@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "message": "SENSE API",
        "version": "0.1.0",
        "endpoints": {
            "/chat": "POST - 메시지 처리",
            "/conversation/{conversation_id}": "GET - 대화 히스토리",
            "/health": "GET - 헬스 체크"
        }
    }


@app.get("/health")
async def health_check():
    """헬스 체크"""
    try:
        # Neo4j 연결 확인
        with db_manager.get_neo4j_session() as session:
            session.run("RETURN 1 as test")
        
        # Chroma 연결 확인
        db_manager.get_chroma_collection()
        
        return {
            "status": "healthy",
            "neo4j": "connected",
            "chroma": "connected"
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")


def extract_shelters_from_graph_results(graph_results: Dict[str, Any]) -> List[ShelterInfo]:
    """Graph RAG 결과에서 대피소 정보 추출 (노트북 로직 참고)"""
    shelters = []
    
    if not graph_results or not graph_results.get("results"):
        return shelters
    
    results = graph_results["results"]
    
    for record in results:
        # record는 딕셔너리 형태: {'s': <Node ...>} 또는 {'name': '...', 'address': '...'} 등
        for key, value in record.items():
            # Neo4j Node 객체인 경우 (properties 속성이 있음)
            if hasattr(value, 'properties'):
                try:
                    props = value.properties
                    # Shelter 노드인지 확인 (labels 확인)
                    is_shelter = False
                    if hasattr(value, '_labels'):
                        labels = value._labels
                        is_shelter = 'Shelter' in labels or isinstance(labels, frozenset) and 'Shelter' in labels
                    elif hasattr(value, 'labels'):
                        labels = value.labels
                        is_shelter = 'Shelter' in labels
                    else:
                        # labels 속성이 없으면 문자열로 확인
                        value_str = str(value)
                        is_shelter = 'Shelter' in value_str or 'shelter' in key.lower()
                    
                    if is_shelter or ('name' in props and 'address' in props):
                        shelter_name = props.get('name', '이름 없음')
                        shelter_address = props.get('address', '주소 없음')
                        shelter_lat = props.get('lat', 0)
                        shelter_lon = props.get('lon', 0)
                        shelter_type = props.get('shelter_type', '')
                        
                        # 실제 값이 있는 경우만 추가
                        if shelter_name != '이름 없음' and shelter_address != '주소 없음' and shelter_lat and shelter_lon:
                            try:
                                shelters.append({
                                    'name': shelter_name,
                                    'address': shelter_address,
                                    'lat': float(shelter_lat),
                                    'lon': float(shelter_lon),
                                    'type': shelter_type
                                })
                            except (ValueError, TypeError):
                                pass
                except Exception:
                    # properties 접근 실패 시 무시
                    pass
            
            # 딕셔너리인 경우 (직접 속성이 있는 경우 또는 dict(record)로 변환된 경우)
            elif isinstance(value, dict):
                if ('name' in value or 'address' in value or 'shelter_type' in value) and \
                   ('lat' in value or 'lon' in value):
                    shelter_name = value.get('name', value.get('s.name', '이름 없음'))
                    shelter_address = value.get('address', value.get('s.address', '주소 없음'))
                    shelter_lat = value.get('lat', value.get('s.lat', 0))
                    shelter_lon = value.get('lon', value.get('s.lon', 0))
                    shelter_type = value.get('shelter_type', value.get('s.shelter_type', ''))
                    
                    if shelter_name != '이름 없음' and shelter_address != '주소 없음' and shelter_lat and shelter_lon:
                        try:
                            shelters.append({
                                'name': shelter_name,
                                'address': shelter_address,
                                'lat': float(shelter_lat),
                                'lon': float(shelter_lon),
                                'type': shelter_type
                            })
                        except (ValueError, TypeError):
                            pass
        
        # record 자체가 속성 딕셔너리인 경우 (RETURN s.name, s.address 같은 쿼리)
        if isinstance(record, dict):
            if ('name' in record or 'address' in record) and ('lat' in record or 'lon' in record):
                record_name = record.get('name', record.get('s.name', ''))
                record_address = record.get('address', record.get('s.address', ''))
                record_lat = record.get('lat', record.get('s.lat', 0))
                record_lon = record.get('lon', record.get('s.lon', 0))
                record_type = record.get('shelter_type', record.get('s.shelter_type', ''))
                
                if record_name and record_address and record_lat and record_lon:
                    # 중복 체크
                    is_duplicate = any(
                        s.get('name') == record_name and s.get('address') == record_address 
                        for s in shelters
                    )
                    if not is_duplicate:
                        try:
                            shelters.append({
                                'name': record_name if record_name else '이름 없음',
                                'address': record_address if record_address else '주소 없음',
                                'lat': float(record_lat),
                                'lon': float(record_lon),
                                'type': record_type
                            })
                        except (ValueError, TypeError):
                            pass
    
    # 중복 제거 (이름과 주소 기준)
    unique_shelters = []
    seen = set()
    for shelter in shelters:
        # '이름 없음'이나 '주소 없음'은 제외
        if shelter['name'] != '이름 없음' and shelter['address'] != '주소 없음':
            key = (shelter['name'], shelter['address'])
            if key not in seen:
                seen.add(key)
                unique_shelters.append(ShelterInfo(
                    name=shelter['name'],
                    address=shelter['address'],
                    lat=shelter['lat'],
                    lon=shelter['lon'],
                    shelter_type=shelter.get('type', '')
                ))
    
    # 최대 10개만 반환
    return unique_shelters[:10]


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """채팅 엔드포인트: 메시지 처리"""
    
    # 메시지 타입 변환
    try:
        message_type = MessageType(request.message_type)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid message_type: {request.message_type}. Must be 'disaster_alert' or 'user_question'"
        )
    
    # 대화 ID 가져오기 또는 생성
    conversation_id = get_or_create_conversation_id(request)
    
    # 오케스트레이터로 처리
    try:
        state = orchestrator.process(
            message=request.message,
            message_type=message_type,
            conversation_id=conversation_id,
            user_context=request.user_context
        )
        
        # 대화 히스토리 업데이트
        update_conversation_history(conversation_id, request.message, state)
        
        # 대피소 정보 추출
        shelters = extract_shelters_from_graph_results(state.graph_search_results or {})
        
        # 긴급도 추출
        urgency = "보통"
        if state.user_profile:
            urgency = state.user_profile.get("urgency", "보통")
        
        # 상황 설명 생성
        situation_description = ""
        if state.user_profile:
            disaster_type = state.user_profile.get("disaster_type", "")
            location = state.user_profile.get("location", "")
            if disaster_type and location:
                situation_description = f"{location}에 {disaster_type} 상황이 발생했습니다."
            elif disaster_type:
                situation_description = f"{disaster_type} 상황이 발생했습니다."
            else:
                situation_description = "재난 상황이 발생했습니다."
        else:
            situation_description = "재난 상황이 발생했습니다."
        
        # 응답 생성 (필요한 정보만)
        return ChatResponse(
            immediate_actions=state.immediate_actions or [],
            shelters=shelters,
            urgency=urgency,
            situation_description=situation_description
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")


@app.get("/conversation/{conversation_id}")
async def get_conversation(conversation_id: str):
    """대화 히스토리 조회"""
    if conversation_id not in conversation_history:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return {
        "conversation_id": conversation_id,
        "history": conversation_history[conversation_id],
        "total_messages": len(conversation_history[conversation_id])
    }


@app.delete("/conversation/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """대화 히스토리 삭제"""
    if conversation_id in conversation_history:
        del conversation_history[conversation_id]
        return {"message": "Conversation deleted", "conversation_id": conversation_id}
    else:
        raise HTTPException(status_code=404, detail="Conversation not found")


if __name__ == "__main__":
    import uvicorn
    from config import Config
    
    uvicorn.run(
        "api:app",
        host=Config.API_HOST,
        port=Config.API_PORT,
        reload=True
    )


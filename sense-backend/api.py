"""FastAPI 엔드포인트"""
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import html

from graph import Orchestrator
from models import Response

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


app = FastAPI(title="SENSE API", version="1.0.0")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Orchestrator 인스턴스
orchestrator = Orchestrator()


class UserInfo(BaseModel):
    """사용자 정보"""
    lat: float  # 위도
    lon: float  # 경도
    floor: int  # 층수


class ChatRequest(BaseModel):
    """채팅 요청"""
    message: str
    user_info: Optional[UserInfo] = None  # 초기 유저 정보 (좌표, 층수)
    conversation_id: Optional[str] = None
    history: Optional[List[Dict[str, str]]] = None


class ChatResponse(BaseModel):
    """채팅 응답"""
    answer: str
    conclusion: str
    evidence: str
    explanation: Dict[str, Any]
    places_reference: Optional[Dict[str, Dict[str, Any]]] = None  # 결론에 언급된 장소 레퍼런스
    places_html: Optional[str] = None  # 장소 HTML 시각화
    conversation_id: Optional[str] = None


# 대화 히스토리 저장 (메모리 기반, 프로덕션에서는 Redis 등 사용)
conversations: Dict[str, List[Dict[str, str]]] = {}


def generate_places_html(places_reference: Dict[str, Dict[str, Any]]) -> str:
    """장소 레퍼런스를 HTML로 시각화
    
    Args:
        places_reference: 장소 레퍼런스 딕셔너리
        
    Returns:
        HTML 문자열
    """
    if not places_reference:
        return None
    
    html_parts = []
    
    # CSS 스타일
    html_parts.append("""
    <style>
        .places-container {
            margin: 20px 0;
            padding: 15px;
            background-color: #f8f9fa;
            border-radius: 8px;
            border: 1px solid #dee2e6;
        }
        .places-header {
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 15px;
            color: #212529;
        }
        .place-card {
            background-color: white;
            border: 1px solid #dee2e6;
            border-radius: 6px;
            padding: 15px;
            margin-bottom: 12px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .place-name {
            font-size: 16px;
            font-weight: 600;
            color: #0d6efd;
            margin-bottom: 8px;
        }
        .place-info {
            font-size: 14px;
            color: #6c757d;
            margin: 4px 0;
        }
        .place-address {
            color: #495057;
        }
        .place-type {
            display: inline-block;
            background-color: #e9ecef;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 12px;
            margin-top: 4px;
        }
        .place-distance {
            color: #0d6efd;
            font-weight: 500;
        }
        .place-link {
            margin-top: 8px;
            font-size: 13px;
        }
        .place-link a {
            color: #0d6efd;
            text-decoration: none;
            margin-right: 10px;
        }
        .place-link a:hover {
            text-decoration: underline;
        }
    </style>
    """)
    
    # 컨테이너 시작
    html_parts.append('<div class="places-container">')
    html_parts.append('<div class="places-header">📍 주변 안전 거점</div>')
    
    # 장소별 카드 생성
    for place_key, place_info in places_reference.items():
        name = place_info.get('name', '이름 없음')
        address = place_info.get('address', '')
        place_type = place_info.get('type', '')
        distance_km = place_info.get('distance_km')
        lat = place_info.get('lat')
        lon = place_info.get('lon')
        
        # HTML 이스케이프
        name_escaped = html.escape(str(name))
        address_escaped = html.escape(str(address)) if address else ''
        place_type_escaped = html.escape(str(place_type)) if place_type else ''
        
        html_parts.append('<div class="place-card">')
        html_parts.append(f'<div class="place-name">{name_escaped}</div>')
        
        # 주소
        if address_escaped:
            html_parts.append(f'<div class="place-info place-address">📍 {address_escaped}</div>')
        
        # 타입
        if place_type_escaped:
            html_parts.append(f'<div class="place-info"><span class="place-type">{place_type_escaped}</span></div>')
        
        # 거리 정보
        if distance_km is not None:
            html_parts.append(f'<div class="place-info place-distance">거리: {distance_km:.2f}km</div>')
        
        # 지도 링크 (좌표가 있는 경우)
        if lat and lon:
            html_parts.append('<div class="place-link">')
            # Google Maps 링크
            google_maps_url = f"https://www.google.com/maps?q={lat},{lon}"
            html_parts.append(f'<a href="{google_maps_url}" target="_blank">🗺️ Google Maps로 보기</a>')
            # Kakao Map 링크
            kakao_map_url = f"https://map.kakao.com/?q={lat},{lon}"
            html_parts.append(f'<a href="{kakao_map_url}" target="_blank">📍 Kakao Map으로 보기</a>')
            html_parts.append('</div>')
        elif address_escaped:
            # 좌표가 없어도 주소로 검색 가능
            html_parts.append('<div class="place-link">')
            google_maps_url = f"https://www.google.com/maps/search/?api=1&query={html.escape(address)}"
            html_parts.append(f'<a href="{google_maps_url}" target="_blank">🗺️ Google Maps로 보기</a>')
            html_parts.append('</div>')
        
        html_parts.append('</div>')
    
    html_parts.append('</div>')
    
    return '\n'.join(html_parts)


@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "message": "SENSE API - 재난 대응 행동 에이전트",
        "version": "1.0.0"
    }


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """채팅 엔드포인트 (단일/멀티턴 대화 지원)"""
    logger.info(f"[API] 채팅 요청 수신: {request.message[:100]}...")
    try:
        # 대화 히스토리 가져오기
        history = []
        if request.conversation_id and request.conversation_id in conversations:
            history = conversations[request.conversation_id]
        elif request.history:
            history = request.history
        
        # 유저 정보 변환
        user_info = None
        if request.user_info:
            user_info = {
                "lat": request.user_info.lat,
                "lon": request.user_info.lon,
                "floor": request.user_info.floor
            }
        
        # Orchestrator 실행
        logger.info(f"[API] Orchestrator 실행 시작 (user_info: {user_info is not None})")
        result = await orchestrator.process(request.message, history, user_info)
        logger.info("[API] Orchestrator 실행 완료")
        
        # 대화 히스토리 업데이트
        conversation_id = request.conversation_id or "default"
        if conversation_id not in conversations:
            conversations[conversation_id] = []
        
        # 사용자 메시지 추가
        conversations[conversation_id].append({
            "role": "user",
            "content": request.message
        })
        
        # 어시스턴트 메시지 추가
        conversations[conversation_id].append({
            "role": "assistant",
            "content": result["answer"]
        })
        
        # 장소 레퍼런스가 있으면 HTML 시각화 생성
        places_html = None
        if result.get("places_reference"):
            places_html = generate_places_html(result.get("places_reference"))
        
        return ChatResponse(
            answer=result["answer"],
            conclusion=result["conclusion"],
            evidence=result["evidence"],
            explanation=result["explanation"],
            places_reference=result.get("places_reference"),
            places_html=places_html,
            conversation_id=conversation_id
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health():
    """헬스 체크"""
    return {"status": "ok"}


@app.get("/conversations/{conversation_id}")
async def get_conversation(conversation_id: str):
    """대화 히스토리 조회"""
    if conversation_id not in conversations:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return {
        "conversation_id": conversation_id,
        "messages": conversations[conversation_id]
    }


@app.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """대화 히스토리 삭제"""
    if conversation_id in conversations:
        del conversations[conversation_id]
        return {"message": "Conversation deleted"}
    else:
        raise HTTPException(status_code=404, detail="Conversation not found")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


"""FastAPI 엔드포인트"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

from graph import Orchestrator
from models import Response


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


class ChatRequest(BaseModel):
    """채팅 요청"""
    message: str
    conversation_id: Optional[str] = None
    history: Optional[List[Dict[str, str]]] = None


class ChatResponse(BaseModel):
    """채팅 응답"""
    answer: str
    conclusion: str
    evidence: str
    explanation: Dict[str, Any]
    conversation_id: Optional[str] = None


# 대화 히스토리 저장 (메모리 기반, 프로덕션에서는 Redis 등 사용)
conversations: Dict[str, List[Dict[str, str]]] = {}


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
    try:
        # 대화 히스토리 가져오기
        history = []
        if request.conversation_id and request.conversation_id in conversations:
            history = conversations[request.conversation_id]
        elif request.history:
            history = request.history
        
        # Orchestrator 실행
        result = orchestrator.process(request.message, history)
        
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
        
        return ChatResponse(
            answer=result["answer"],
            conclusion=result["conclusion"],
            evidence=result["evidence"],
            explanation=result["explanation"],
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


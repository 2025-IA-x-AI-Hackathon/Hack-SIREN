"""데이터 모델"""
from typing import List, Dict, Optional, Any
from pydantic import BaseModel
from enum import Enum


class MessageRole(str, Enum):
    """메시지 역할"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Message(BaseModel):
    """대화 메시지"""
    role: MessageRole
    content: str


class UserInfo(BaseModel):
    """사용자 정보"""
    lat: float  # 위도
    lon: float  # 경도
    floor: int  # 층수


class PlanningResult(BaseModel):
    """PlanningAgent 결과"""
    search_plan: Dict[str, Any]
    reasoning: str


class AnalysisResult(BaseModel):
    """AnalystAgent 결과"""
    graph_results: Dict[str, Any]
    vector_results: Dict[str, Any]
    reasoning: str


class AdvisoryResult(BaseModel):
    """AdvisorAgent 결과"""
    conclusion: str  # 핵심 결론 (3-5문장)
    evidence: str    # 추론한 증거만
    places_reference: Optional[Dict[str, Dict[str, Any]]] = None  # 결론에 언급된 장소들의 레퍼런스


class ConversationState(BaseModel):
    """대화 상태 (LangGraph용)"""
    messages: List[Message]
    input: str
    user_info: Optional[UserInfo] = None
    planning: Optional[PlanningResult] = None
    analysis: Optional[AnalysisResult] = None
    advisory: Optional[AdvisoryResult] = None
    explanation: Dict[str, Any] = {}


class Response(BaseModel):
    """최종 응답"""
    answer: str
    conclusion: str
    evidence: str
    explanation: Dict[str, Any]


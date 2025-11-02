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


class DisasterMessageType(str, Enum):
    """재난 메시지 유형"""
    DISASTER_ALERT = "disaster_alert"  # 재난 문자
    USER_QUESTION = "user_question"    # 사용자 질문


class ProfileResult(BaseModel):
    """ProfileAgent 결과"""
    message_type: DisasterMessageType
    extracted_info: Dict[str, Any]
    reasoning: str


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


class ConversationState(BaseModel):
    """대화 상태 (LangGraph용)"""
    messages: List[Message]
    input: str
    profile: Optional[ProfileResult] = None
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


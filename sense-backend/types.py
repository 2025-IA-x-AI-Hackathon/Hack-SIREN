"""타입 정의"""
from typing import Dict, List, Optional, Any, Literal, TypedDict
from pydantic import BaseModel
from enum import Enum


class MessageType(str, Enum):
    """메시지 타입"""
    DISASTER_ALERT = "disaster_alert"  # 재난 문자
    USER_QUESTION = "user_question"     # 사용자 질문


class AgentState(TypedDict, total=False):
    """에이전트 상태 (LangGraph 호환용 TypedDict)"""
    # 입력
    message: str
    message_type: MessageType
    conversation_id: Optional[str]
    user_context: Optional[Dict[str, Any]]
    
    # ProfileAgent 출력
    user_profile: Optional[Dict[str, Any]]
    profile_reasoning: Optional[str]
    
    # PlanningAgent 출력
    analysis_plan: Optional[Dict[str, Any]]
    planning_reasoning: Optional[str]
    
    # AnalystAgent 출력
    graph_search_results: Optional[Dict[str, Any]]
    vector_search_results: Optional[Dict[str, Any]]
    analysis_summary: Optional[str]
    analyst_reasoning: Optional[str]
    
    # AdvisorAgent 출력
    immediate_actions: Optional[List[str]]
    next_actions: Optional[List[str]]
    caution_notes: Optional[List[str]]
    advisor_reasoning: Optional[str]
    
    # 최종 응답
    final_response: Optional[str]
    
    # 메타데이터
    explanation_path: Optional[List[str]]
    metadata: Optional[Dict[str, Any]]


class AgentStateModel(BaseModel):
    """에이전트 상태 모델 (Pydantic, API 응답용)"""
    # 입력
    message: str
    message_type: MessageType
    conversation_id: Optional[str] = None
    user_context: Optional[Dict[str, Any]] = None
    
    # ProfileAgent 출력
    user_profile: Optional[Dict[str, Any]] = None
    profile_reasoning: Optional[str] = None
    
    # PlanningAgent 출력
    analysis_plan: Optional[Dict[str, Any]] = None
    planning_reasoning: Optional[str] = None
    
    # AnalystAgent 출력
    graph_search_results: Optional[Dict[str, Any]] = None
    vector_search_results: Optional[Dict[str, Any]] = None
    analysis_summary: Optional[str] = None
    analyst_reasoning: Optional[str] = None
    
    # AdvisorAgent 출력
    immediate_actions: Optional[List[str]] = None
    next_actions: Optional[List[str]] = None
    caution_notes: Optional[List[str]] = None
    advisor_reasoning: Optional[str] = None
    
    # 최종 응답
    final_response: Optional[str] = None
    
    # 메타데이터
    explanation_path: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
    
    @classmethod
    def from_dict(cls, state_dict: Dict[str, Any]) -> "AgentStateModel":
        """TypedDict에서 모델 생성"""
        return cls(**state_dict)


class ConversationHistory(BaseModel):
    """대화 히스토리"""
    conversation_id: str
    messages: List[Dict[str, Any]]
    user_profile: Optional[Dict[str, Any]] = None


class RAGResults(BaseModel):
    """RAG 검색 결과"""
    graph_results: Dict[str, Any]
    vector_results: Dict[str, Any]
    combined_context: str


class AgentResponse(BaseModel):
    """에이전트 응답"""
    agent_name: str
    output: Dict[str, Any]
    reasoning: str
    metadata: Optional[Dict[str, Any]] = None


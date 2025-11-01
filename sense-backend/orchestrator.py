"""LangGraph 기반 Orchestrator"""
from typing import Dict, Any, List, Optional
from langgraph.graph import StateGraph, END

from backend.types import AgentState, AgentStateModel, MessageType
from backend.agents import ProfileAgent, PlanningAgent, AnalystAgent, AdvisorAgent


class Orchestrator:
    """에이전트 오케스트레이터 (LangGraph 기반)"""
    
    def __init__(self):
        self.profile_agent = ProfileAgent()
        self.planning_agent = PlanningAgent()
        self.analyst_agent = AnalystAgent()
        self.advisor_agent = AdvisorAgent()
        
        # LangGraph 그래프 생성
        self.graph = self._create_graph()
    
    def _create_graph(self) -> StateGraph:
        """LangGraph 그래프 생성"""
        
        # 그래프 생성
        workflow = StateGraph(AgentState)
        
        # 노드 추가 (순서 중요: Profile -> Planning -> Analyst -> Advisor)
        workflow.add_node("profile", self._profile_node)
        workflow.add_node("planning", self._planning_node)
        workflow.add_node("analyst", self._analyst_node)
        workflow.add_node("advisor", self._advisor_node)
        
        # 엣지 정의 (순서 보장)
        workflow.set_entry_point("profile")
        workflow.add_edge("profile", "planning")
        workflow.add_edge("planning", "analyst")
        workflow.add_edge("analyst", "advisor")
        workflow.add_edge("advisor", END)
        
        return workflow.compile()
    
    def _profile_node(self, state: AgentState) -> AgentState:
        """ProfileAgent 노드"""
        # TypedDict를 AgentStateModel로 변환
        state_model = AgentStateModel.from_dict(state)
        # 에이전트 처리
        updated_state = self.profile_agent.process(state_model)
        # 다시 dict로 변환
        return updated_state.model_dump(exclude_none=True)
    
    def _planning_node(self, state: AgentState) -> AgentState:
        """PlanningAgent 노드"""
        state_model = AgentStateModel.from_dict(state)
        updated_state = self.planning_agent.process(state_model)
        return updated_state.model_dump(exclude_none=True)
    
    def _analyst_node(self, state: AgentState) -> AgentState:
        """AnalystAgent 노드"""
        state_model = AgentStateModel.from_dict(state)
        updated_state = self.analyst_agent.process(state_model)
        return updated_state.model_dump(exclude_none=True)
    
    def _advisor_node(self, state: AgentState) -> AgentState:
        """AdvisorAgent 노드"""
        state_model = AgentStateModel.from_dict(state)
        updated_state = self.advisor_agent.process(state_model)
        return updated_state.model_dump(exclude_none=True)
    
    def process(
        self,
        message: str,
        message_type: MessageType,
        conversation_id: Optional[str] = None,
        user_context: Optional[Dict[str, Any]] = None
    ) -> AgentStateModel:
        """메시지 처리: 전체 에이전트 파이프라인 실행"""
        
        # 초기 상태 생성 (dict)
        initial_state: AgentState = {
            "message": message,
            "message_type": message_type,
            "conversation_id": conversation_id,
            "user_context": user_context,
            "explanation_path": []
        }
        
        # 그래프 실행 (순서 보장)
        try:
            final_state_dict = self.graph.invoke(initial_state)
            # AgentStateModel로 변환
            return AgentStateModel.from_dict(final_state_dict)
        except Exception as e:
            print(f"Orchestrator 실행 오류: {e}")
            # 오류 시 기본 상태 반환
            initial_state["final_response"] = f"처리 중 오류 발생: {str(e)}"
            return AgentStateModel.from_dict(initial_state)
    
    def get_explanation_path(self, state: AgentStateModel) -> List[str]:
        """추론 근거 경로 반환"""
        return state.explanation_path or []


# 전역 인스턴스
orchestrator = Orchestrator()


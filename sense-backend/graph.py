"""LangGraph Orchestrator - 에이전트 흐름 제어"""
from typing import TypedDict, Annotated, Optional
from langgraph.graph import StateGraph, END
import operator

from models import (
    ConversationState, ProfileResult, PlanningResult,
    AnalysisResult, AdvisoryResult, Message, MessageRole
)
from agents.profile_agent import ProfileAgent
from agents.planning_agent import PlanningAgent
from agents.analyst_agent import AnalystAgent
from agents.advisor_agent import AdvisorAgent


class State(TypedDict):
    """LangGraph 상태"""
    messages: Annotated[list, operator.add]
    input: str
    profile: Optional[ProfileResult]
    planning: Optional[PlanningResult]
    analysis: Optional[AnalysisResult]
    advisory: Optional[AdvisoryResult]
    explanation: dict


class Orchestrator:
    """Orchestrator - 에이전트 순서 보장"""
    
    def __init__(self):
        self.profile_agent = ProfileAgent()
        self.planning_agent = PlanningAgent()
        self.analyst_agent = AnalystAgent()
        self.advisor_agent = AdvisorAgent()
        
        # LangGraph 생성
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """LangGraph 생성"""
        workflow = StateGraph(State)
        
        # 노드 추가 (순서 보장)
        workflow.add_node("profile", self._profile_node)
        workflow.add_node("planning", self._planning_node)
        workflow.add_node("analysis", self._analysis_node)
        workflow.add_node("advisor", self._advisor_node)
        
        # 엣지 추가 (순차 실행)
        workflow.set_entry_point("profile")
        workflow.add_edge("profile", "planning")
        workflow.add_edge("planning", "analysis")
        workflow.add_edge("analysis", "advisor")
        workflow.add_edge("advisor", END)
        
        return workflow.compile()
    
    def _profile_node(self, state: State) -> State:
        """ProfileAgent 노드"""
        conversation_history = [
            {"role": msg.role.value, "content": msg.content}
            for msg in state.get("messages", [])
        ]
        
        profile_result = self.profile_agent.analyze(
            state["input"],
            conversation_history
        )
        
        # Explanation 업데이트
        explanation = state.get("explanation", {})
        explanation["profile"] = {
            "message_type": profile_result.message_type.value,
            "extracted_info": profile_result.extracted_info,
            "reasoning": profile_result.reasoning
        }
        
        return {
            "profile": profile_result,
            "explanation": explanation
        }
    
    def _planning_node(self, state: State) -> State:
        """PlanningAgent 노드"""
        profile = state["profile"]
        
        planning_result = self.planning_agent.plan(
            state["input"],
            profile
        )
        
        # Explanation 업데이트
        explanation = state.get("explanation", {})
        explanation["planning"] = {
            "search_plan": planning_result.search_plan,
            "reasoning": planning_result.reasoning
        }
        
        return {
            "planning": planning_result,
            "explanation": explanation
        }
    
    def _analysis_node(self, state: State) -> State:
        """AnalystAgent 노드"""
        profile = state["profile"]
        planning = state["planning"]
        
        analysis_result = self.analyst_agent.analyze(
            state["input"],
            profile,
            planning
        )
        
        # Explanation 업데이트
        explanation = state.get("explanation", {})
        explanation["analysis"] = {
            "graph_count": analysis_result.graph_results.get("count", 0),
            "vector_count": analysis_result.vector_results.get("count", 0),
            "reasoning": analysis_result.reasoning
        }
        
        return {
            "analysis": analysis_result,
            "explanation": explanation
        }
    
    def _advisor_node(self, state: State) -> State:
        """AdvisorAgent 노드"""
        profile = state["profile"]
        planning = state["planning"]
        analysis = state["analysis"]
        
        advisory_result = self.advisor_agent.advise(
            state["input"],
            profile,
            planning,
            analysis
        )
        
        # Explanation 업데이트
        explanation = state.get("explanation", {})
        explanation["advisory"] = {
            "conclusion": advisory_result.conclusion,
            "evidence": advisory_result.evidence
        }
        
        # 응답 메시지 생성
        response_text = self._format_response(advisory_result)
        assistant_msg = Message(
            role=MessageRole.ASSISTANT,
            content=response_text
        )
        
        return {
            "advisory": advisory_result,
            "explanation": explanation,
            "messages": [assistant_msg]
        }
    
    def _format_response(self, advisory: AdvisoryResult) -> str:
        """최종 응답 포맷팅"""
        parts = []
        
        # 결론 추가
        if advisory.conclusion:
            parts.append("## 결론")
            parts.append(advisory.conclusion)
            parts.append("")
        
        # 증거 추가
        if advisory.evidence:
            parts.append("## 증거")
            parts.append(advisory.evidence)
        
        return "\n".join(parts)
    
    def process(self, input_text: str, conversation_history: list = None) -> dict:
        """대화 처리 (단일/멀티턴 지원)"""
        # 초기 상태 설정
        messages = []
        if conversation_history:
            for msg in conversation_history:
                messages.append(
                    Message(
                        role=MessageRole(msg.get("role", "user")),
                        content=msg.get("content", "")
                    )
                )
        
        # 사용자 메시지 추가
        user_msg = Message(
            role=MessageRole.USER,
            content=input_text
        )
        messages.append(user_msg)
        
        initial_state = State(
            messages=messages,
            input=input_text,
            profile=None,
            planning=None,
            analysis=None,
            advisory=None,
            explanation={}
        )
        
        # Graph 실행
        result = self.graph.invoke(initial_state)
        
        # 최종 응답 생성
        advisory = result["advisory"]
        response_text = result["messages"][-1].content if result["messages"] else ""
        
        return {
            "answer": response_text,
            "conclusion": advisory.conclusion,
            "evidence": advisory.evidence,
            "explanation": result["explanation"]
        }


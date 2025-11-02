"""LangGraph Orchestrator - 에이전트 흐름 제어"""
from typing import TypedDict, Annotated, Optional
from langgraph.graph import StateGraph, END
import operator
import asyncio

from models import (
    ConversationState, UserInfo, PlanningResult,
    AnalysisResult, AdvisoryResult, Message, MessageRole
)
from agents.planning_agent import PlanningAgent
from agents.analyst_agent import AnalystAgent
from agents.advisor_agent import AdvisorAgent


class State(TypedDict):
    """LangGraph 상태"""
    messages: Annotated[list, operator.add]
    input: str
    user_info: Optional[dict]  # {"lat": float, "lon": float, "floor": int}
    planning: Optional[PlanningResult]
    analysis: Optional[AnalysisResult]
    advisory: Optional[AdvisoryResult]
    explanation: dict


class Orchestrator:
    """Orchestrator - 에이전트 순서 보장"""
    
    def __init__(self):
        self.planning_agent = PlanningAgent()
        self.analyst_agent = AnalystAgent()
        self.advisor_agent = AdvisorAgent()
        
        # LangGraph 생성
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """LangGraph 생성"""
        workflow = StateGraph(State)
        
        # 노드 추가 (순서 보장)
        workflow.add_node("planning", self._planning_node)
        workflow.add_node("analysis", self._analysis_node)
        workflow.add_node("advisor", self._advisor_node)
        
        # 엣지 추가 (순차 실행)
        workflow.set_entry_point("planning")
        workflow.add_edge("planning", "analysis")
        workflow.add_edge("analysis", "advisor")
        workflow.add_edge("advisor", END)
        
        return workflow.compile()
    
    async def _planning_node(self, state: State) -> State:
        """PlanningAgent 노드"""
        user_info = state.get("user_info")
        
        planning_result = await self.planning_agent.plan(
            state["input"],
            user_info
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
    
    async def _analysis_node(self, state: State) -> State:
        """AnalystAgent 노드"""
        user_info = state.get("user_info")
        planning = state["planning"]
        
        analysis_result = await self.analyst_agent.analyze(
            state["input"],
            user_info,
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
    
    async def _advisor_node(self, state: State) -> State:
        """AdvisorAgent 노드"""
        user_info = state.get("user_info")
        planning = state["planning"]
        analysis = state["analysis"]
        
        # location_info 생성 (user_info가 있는 경우)
        location_info = None
        if user_info:
            location_info = {
                "lat": user_info.get("lat"),
                "lon": user_info.get("lon"),
                "floor": user_info.get("floor"),
                "radius_km": 5.0  # 기본 반경 5km
            }
        
        advisory_result = await self.advisor_agent.infer(
            state["input"],
            None,  # profile 제거
            planning,
            analysis,
            location_info
        )
        
        # Explanation 업데이트
        explanation = state.get("explanation", {})
        explanation["advisory"] = {
            "conclusion": advisory_result.conclusion,
            "evidence": advisory_result.evidence,
            "places_reference": advisory_result.places_reference
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
    
    async def process(self, input_text: str, conversation_history: list = None, user_info: dict = None) -> dict:
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
            user_info=user_info,  # 좌표와 층수 정보
            planning=None,
            analysis=None,
            advisory=None,
            explanation={}
        )
        
        # Graph 실행 (async 지원 여부에 따라)
        try:
            # LangGraph가 async를 지원하는 경우
            result = await self.graph.ainvoke(initial_state)
        except AttributeError:
            # async를 지원하지 않는 경우 동기 함수를 비동기로 실행
            result = await asyncio.to_thread(self.graph.invoke, initial_state)
        
        # 최종 응답 생성
        advisory = result["advisory"]
        response_text = result["messages"][-1].content if result["messages"] else ""
        
        return {
            "answer": response_text,
            "conclusion": advisory.conclusion,
            "evidence": advisory.evidence,
            "explanation": result["explanation"],
            "places_reference": advisory.places_reference
        }


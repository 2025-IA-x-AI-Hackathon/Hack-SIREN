"""PlanningAgent: 분석 계획 수립"""
from typing import Dict, Any
from llm import llm_client
from types import AgentStateModel


class PlanningAgent:
    """분석 계획 수립 에이전트"""
    
    def __init__(self):
        self.name = "PlanningAgent"
    
    def process(self, state: AgentStateModel) -> AgentStateModel:
        """상태 처리: 분석 계획 수립"""
        
        user_profile = state.user_profile or {}
        message = state.message
        
        prompt = f"""
당신은 재난 대응 계획 수립 전문가입니다. 사용자 프로필과 메시지를 바탕으로 정보 분석 계획을 수립하세요.

사용자 프로필:
{user_profile}

메시지:
{message}

다음 JSON 형식으로 분석 계획을 수립하세요:
{{
    "search_strategy": "검색 전략 (graph_focused/vector_focused/hybrid)",
    "graph_queries": ["Neo4j에서 검색할 내용 목록"],
    "vector_queries": ["문서에서 검색할 내용 목록"],
    "priority_areas": ["우선적으로 확인할 영역"],
    "expected_outputs": ["기대되는 출력 정보"]
}}

지침:
1. 재난 문자인 경우: 위치 기반 대피소 검색과 행동 요령 검색 모두 필요
2. 사용자 질문인 경우: 질문 유형에 따라 적절한 검색 전략 선택
3. 긴급도가 높으면 즉시 행동 지침 우선
4. 구체적이고 실행 가능한 계획 수립

계획만 반환하세요. 설명은 필요 없습니다.
"""
        
        try:
            response = llm_client.generate(prompt, temperature=0.2)
            
            # JSON 파싱
            import json
            import re
            
            json_match = re.search(r'\{[^{}]*\}', response, re.DOTALL)
            if json_match:
                plan_data = json.loads(json_match.group())
            else:
                # 기본 계획
                plan_data = {
                    "search_strategy": "hybrid",
                    "graph_queries": ["대피소 위치", "임시주거시설"],
                    "vector_queries": ["행동 요령"],
                    "priority_areas": ["긴급 대응"],
                    "expected_outputs": ["대피소 위치", "행동 지침"]
                }
            
            # 추론 근거 생성
            reasoning_prompt = f"""
위에서 수립한 분석 계획의 근거를 간단히 설명하세요 (1-2문장):

분석 계획:
{json.dumps(plan_data, ensure_ascii=False, indent=2)}

근거:
"""
            reasoning = llm_client.generate(reasoning_prompt, temperature=0.3)
            
            # 상태 업데이트
            state.analysis_plan = plan_data
            state.planning_reasoning = reasoning
            
            if state.explanation_path is None:
                state.explanation_path = []
            state.explanation_path.append(f"{self.name}: {reasoning}")
            
        except Exception as e:
            print(f"PlanningAgent 오류: {e}")
            state.analysis_plan = {
                "search_strategy": "hybrid",
                "graph_queries": [],
                "vector_queries": [],
                "priority_areas": ["분석 필요"],
                "expected_outputs": []
            }
            state.planning_reasoning = f"계획 수립 중 오류 발생: {str(e)}"
        
        return state


"""AdvisorAgent: 행동 지침 제시 (immediate/next/caution)"""
from typing import Dict, Any, List
from backend.llm import llm_client
from backend.types import AgentStateModel


class AdvisorAgent:
    """행동 지침 제시 에이전트"""
    
    def __init__(self):
        self.name = "AdvisorAgent"
    
    def process(self, state: AgentStateModel) -> AgentStateModel:
        """상태 처리: 행동 지침 생성 (immediate/next/caution)"""
        
        user_profile = state.user_profile or {}
        analysis_summary = state.analysis_summary or ""
        graph_results = state.graph_search_results or {}
        vector_results = state.vector_search_results or {}
        
        # RAG 결과 요약
        graph_text = ""
        if graph_results:
            from backend.rag import hybrid_rag
            graph_text = hybrid_rag.format_graph_results(graph_results, max_length=1000)
        
        vector_text = ""
        if vector_results:
            from backend.rag import hybrid_rag
            vector_text = hybrid_rag.format_vector_results(vector_results, max_length=1000)
        
        prompt = f"""
당신은 재난 대응 행동 지침 전문가입니다. 다음 정보를 바탕으로 시민에게 필요한 행동 지침을 단계별로 제시하세요.

사용자 프로필:
{user_profile}

분석 요약:
{analysis_summary}

Graph RAG 결과:
{graph_text}

Vector RAG 결과:
{vector_text}

다음 JSON 형식으로 행동 지침을 생성하세요:
{{
    "immediate_actions": [
        "즉시 취해야 할 행동 1",
        "즉시 취해야 할 행동 2",
        ...
    ],
    "next_actions": [
        "다음에 해야 할 행동 1",
        "다음에 해야 할 행동 2",
        ...
    ],
    "caution_notes": [
        "주의사항 1",
        "주의사항 2",
        ...
    ]
}}

지침:
1. immediate_actions: 지금 당장 해야 할 긴급 행동 (최대 5개)
2. next_actions: 즉시 행동 후 다음 단계 행동 (최대 5개)
3. caution_notes: 주의해야 할 사항 및 금지 행동 (최대 5개)
4. 구체적이고 실행 가능한 지침만 포함
5. 검색 결과에 있는 구체적 정보(대피소 위치 등)를 활용
6. 각 행동은 간결하게 한 문장으로 표현

JSON만 반환하세요. 설명은 필요 없습니다.
"""
        
        try:
            response = llm_client.generate(prompt, temperature=0.3)
            
            # JSON 파싱
            import json
            import re
            
            json_match = re.search(r'\{[^{}]*\}', response, re.DOTALL)
            if json_match:
                actions_data = json.loads(json_match.group())
                
                # 리스트가 문자열인 경우 처리
                immediate = actions_data.get("immediate_actions", [])
                next_actions = actions_data.get("next_actions", [])
                caution = actions_data.get("caution_notes", [])
                
                # 문자열 리스트로 변환
                if isinstance(immediate, str):
                    immediate = [immediate]
                if isinstance(next_actions, str):
                    next_actions = [next_actions]
                if isinstance(caution, str):
                    caution = [caution]
                
                state.immediate_actions = immediate
                state.next_actions = next_actions
                state.caution_notes = caution
                
            else:
                # JSON 파싱 실패 시 기본값
                state.immediate_actions = ["정보 확인 중"]
                state.next_actions = ["상황 모니터링"]
                state.caution_notes = ["안전을 우선시하세요"]
            
            # 추론 근거 생성
            reasoning_prompt = f"""
위에서 생성한 행동 지침의 근거를 간단히 설명하세요 (1-2문장):

행동 지침:
- 즉시 행동: {len(state.immediate_actions)}개
- 다음 행동: {len(state.next_actions)}개
- 주의사항: {len(state.caution_notes)}개

근거:
"""
            reasoning = llm_client.generate(reasoning_prompt, temperature=0.3)
            state.advisor_reasoning = reasoning
            
            if state.explanation_path is None:
                state.explanation_path = []
            state.explanation_path.append(f"{self.name}: {reasoning}")
            
        except Exception as e:
            print(f"AdvisorAgent 오류: {e}")
            state.immediate_actions = ["상황 파악 중"]
            state.next_actions = ["정보 수집"]
            state.caution_notes = ["안전을 최우선으로 하세요"]
            state.advisor_reasoning = f"행동 지침 생성 중 오류 발생: {str(e)}"
        
        # 최종 응답 생성
        state.final_response = self._generate_final_response(state)
        
        return state
    
    def _generate_final_response(self, state: AgentStateModel) -> str:
        """최종 응답 메시지 생성"""
        parts = []
        
        # 즉시 행동
        if state.immediate_actions:
            parts.append("## 🚨 즉시 행동")
            for i, action in enumerate(state.immediate_actions, 1):
                parts.append(f"{i}. {action}")
            parts.append("")
        
        # 다음 행동
        if state.next_actions:
            parts.append("## 📋 다음 단계")
            for i, action in enumerate(state.next_actions, 1):
                parts.append(f"{i}. {action}")
            parts.append("")
        
        # 주의사항
        if state.caution_notes:
            parts.append("## ⚠️ 주의사항")
            for i, note in enumerate(state.caution_notes, 1):
                parts.append(f"{i}. {note}")
            parts.append("")
        
        # 분석 결과 요약이 있으면 추가
        if state.analysis_summary:
            parts.append("## 📊 분석 요약")
            parts.append(state.analysis_summary)
            parts.append("")
        
        # 근거 경로
        if state.explanation_path:
            parts.append("## 🔍 추론 근거")
            for step in state.explanation_path:
                parts.append(f"- {step}")
        
        return "\n".join(parts) if parts else "분석 완료. 행동 지침을 확인하세요."


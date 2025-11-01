"""ProfileAgent: 사용자 프로필 및 상황 분석"""
from typing import Dict, Any
from backend.llm import llm_client
from backend.types import AgentStateModel, MessageType


class ProfileAgent:
    """사용자 프로필 및 상황 분석 에이전트"""
    
    def __init__(self):
        self.name = "ProfileAgent"
    
    def process(self, state: AgentStateModel) -> AgentStateModel:
        """상태 처리: 사용자 프로필 및 상황 분석"""
        
        # 메시지 타입에 따라 다른 프롬프트 사용
        if state.message_type == MessageType.DISASTER_ALERT:
            prompt = f"""
당신은 재난 상황 분석 전문가입니다. 다음 재난 문자를 분석하여 다음 정보를 추출하세요:

재난 문자:
{state.message}

다음 JSON 형식으로 응답하세요:
{{
    "disaster_type": "재난 유형 (지진, 공습, 화재 등)",
    "severity": "심각도 (경보/주의보/일반)",
    "location": "위치 정보 (지역, 구, 동)",
    "urgency": "긴급도 (긴급/보통/낮음)",
    "affected_area": "영향 지역",
    "timeframe": "시간 범위 또는 시점",
    "specific_instructions": "특별 지시사항"
}}

추출된 정보만 반환하세요. 설명은 필요 없습니다.
"""
        else:  # USER_QUESTION
            prompt = f"""
당신은 시민 상황 분석 전문가입니다. 다음 사용자 질문을 분석하여 다음 정보를 추출하세요:

사용자 질문:
{state.message}

이전 대화 맥락:
{state.user_context or "없음"}

다음 JSON 형식으로 응답하세요:
{{
    "question_type": "질문 유형 (정보 요청/행동 지침/위치 찾기/긴급 도움 등)",
    "location_mentioned": "언급된 위치 (있는 경우)",
    "urgency": "긴급도 (긴급/보통/낮음)",
    "disaster_context": "관련 재난 유형",
    "user_needs": "사용자가 원하는 것",
    "background_info": "추가 배경 정보"
}}

추출된 정보만 반환하세요. 설명은 필요 없습니다.
"""
        
        try:
            # LLM으로 프로필 추출 (JSON 형식)
            response = llm_client.generate(prompt, temperature=0.1)
            
            # JSON 파싱 시도
            import json
            import re
            
            # JSON 부분 추출
            json_match = re.search(r'\{[^{}]*\}', response, re.DOTALL)
            if json_match:
                profile_data = json.loads(json_match.group())
            else:
                # JSON 형식이 아니면 기본값 사용
                profile_data = {
                    "disaster_type" if state.message_type == MessageType.DISASTER_ALERT else "question_type": "분석 필요",
                    "urgency": "보통"
                }
            
            # 추론 근거 생성
            reasoning_prompt = f"""
위에서 추출한 프로필 정보의 근거를 간단히 설명하세요 (1-2문장):

프로필 정보:
{json.dumps(profile_data, ensure_ascii=False, indent=2)}

근거:
"""
            reasoning = llm_client.generate(reasoning_prompt, temperature=0.3)
            
            # 상태 업데이트
            state.user_profile = profile_data
            state.profile_reasoning = reasoning
            
            if state.explanation_path is None:
                state.explanation_path = []
            state.explanation_path.append(f"{self.name}: {reasoning}")
            
        except Exception as e:
            print(f"ProfileAgent 오류: {e}")
            # 기본 프로필 설정
            state.user_profile = {
                "urgency": "보통",
                "analysis_needed": True
            }
            state.profile_reasoning = f"프로필 추출 중 오류 발생: {str(e)}"
        
        return state


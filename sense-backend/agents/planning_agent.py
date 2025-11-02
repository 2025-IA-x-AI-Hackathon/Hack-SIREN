"""PlanningAgent - 검색 계획 수립"""
from typing import Dict, Any
from google import genai
from config import GOOGLE_API_KEY, GEMINI_MODEL
from models import PlanningResult, ProfileResult


class PlanningAgent:
    """검색 계획 수립 에이전트"""
    
    def __init__(self):
        self.client = genai.Client(api_key=GOOGLE_API_KEY)
    
    def plan(self, input_text: str, profile: ProfileResult) -> PlanningResult:
        """검색 계획 수립"""
        
        prompt = f"""
당신은 재난대응 정보 검색 계획 전문가입니다.
ProfileAgent의 분석 결과를 바탕으로, Graph RAG와 Vector RAG에서 어떤 정보를 검색할지 계획을 수립하세요.

입력 텍스트:
{input_text}

ProfileAgent 분석 결과:
- 메시지 유형: {profile.message_type.value}
- 추출 정보: {profile.extracted_info}
- 판단 근거: {profile.reasoning}

다음 JSON 형식으로 검색 계획을 수립하세요:
{{
    "graph_search": {{
        "focus": "검색할 그래프 노드/관계 타입 (예: Shelter, Hazard, Policy 등)",
        "queries": ["검색할 주요 쿼리 키워드"],
        "reasoning": "왜 이 정보를 검색해야 하는지"
    }},
    "vector_search": {{
        "focus": "검색할 문서 유형 (예: 행동요령, 대피소 정보 등)",
        "keywords": ["검색 키워드"],
        "reasoning": "왜 이 문서를 검색해야 하는지"
    }},
    "reasoning": "전체 검색 계획의 근거"
}}

JSON만 응답하고 설명은 제외하세요.
"""
        
        try:
            response = self.client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt.strip()
            )
            
            from utils import extract_text_from_response, parse_json_from_text
            
            text = extract_text_from_response(response).strip()
            result_dict = parse_json_from_text(text)
            
            if not result_dict:
                # 기본 계획
                result_dict = {
                    "graph_search": {"focus": "일반 검색", "queries": [], "reasoning": ""},
                    "vector_search": {"focus": "일반 검색", "keywords": [], "reasoning": ""},
                    "reasoning": "계획 수립 실패"
                }
            
            return PlanningResult(
                search_plan=result_dict,
                reasoning=result_dict.get("reasoning", "")
            )
        except Exception as e:
            return PlanningResult(
                search_plan={
                    "graph_search": {"focus": "오류", "queries": [], "reasoning": str(e)},
                    "vector_search": {"focus": "오류", "keywords": [], "reasoning": str(e)},
                },
                reasoning=f"계획 수립 오류: {str(e)}"
            )


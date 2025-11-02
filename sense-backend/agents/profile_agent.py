"""ProfileAgent - 입력 분석 (재난 문자 또는 사용자 질문)"""
from typing import Dict, Any
from google import genai
from config import GOOGLE_API_KEY, GEMINI_MODEL
from models import ProfileResult, DisasterMessageType


class ProfileAgent:
    """입력 분석 에이전트"""
    
    def __init__(self):
        self.client = genai.Client(api_key=GOOGLE_API_KEY)
    
    def analyze(self, input_text: str, conversation_history: list = None) -> ProfileResult:
        """입력을 분석하여 재난 문자인지 사용자 질문인지 판단"""
        
        history_context = ""
        if conversation_history:
            recent_msgs = conversation_history[-5:]  # 최근 5개만
            history_context = "\n".join([
                f"{msg.get('role', 'user')}: {msg.get('content', '')}"
                for msg in recent_msgs
            ])
        
        prompt = f"""
당신은 재난대응 전문가입니다. 사용자의 입력을 분석하여 다음을 판단하세요:

1. 재난 문자 (재난 발생 알림): 날짜/시간, 위치, 재난 유형, 규모 등이 포함된 공식 발송 메시지
2. 사용자 질문: 대피소 위치, 행동요령 등 일반적인 질문

입력 텍스트:
{input_text}

{('대화 히스토리:\n' + history_context) if history_context else ''}

다음 JSON 형식으로 응답하세요:
{{
    "message_type": "disaster_alert" 또는 "user_question",
    "extracted_info": {{
        "disaster_type": "지진/공습/산사태 등" (재난 문자의 경우),
        "location": "위치 정보",
        "magnitude": "규모" (있는 경우),
        "date_time": "날짜/시간" (있는 경우),
        "keywords": ["키워드1", "키워드2"],
        "intent": "질문 의도" (사용자 질문의 경우)
    }},
    "reasoning": "판단 근거"
}}

JSON만 응답하고 설명은 제외하세요.
"""
        
        try:
            response = self.client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt.strip()
            )
            
            # JSON 파싱 시도
            from utils import extract_text_from_response, parse_json_from_text
            
            text = extract_text_from_response(response).strip()
            result_dict = parse_json_from_text(text)
            
            if not result_dict:
                # 기본값
                result_dict = {
                    "message_type": "user_question",
                    "extracted_info": {"intent": "일반 질문"},
                    "reasoning": "분석 실패"
                }
            
            return ProfileResult(
                message_type=DisasterMessageType(result_dict.get("message_type", "user_question")),
                extracted_info=result_dict.get("extracted_info", {}),
                reasoning=result_dict.get("reasoning", "")
            )
        except Exception as e:
            # Fallback
            return ProfileResult(
                message_type=DisasterMessageType.USER_QUESTION,
                extracted_info={"error": str(e)},
                reasoning=f"분석 오류: {str(e)}"
            )


"""유틸리티 함수"""
import json
import re
from typing import Any, Dict, Optional, Union


def extract_text_from_response(response: Any) -> str:
    """Gemini 응답에서 텍스트 추출"""
    try:
        # response.text가 있는 경우 (최신 SDK)
        if hasattr(response, 'text'):
            return response.text
        # response.candidates를 사용하는 경우
        elif hasattr(response, 'candidates') and response.candidates:
            candidate = response.candidates[0]
            if hasattr(candidate, 'content') and candidate.content:
                parts = candidate.content.parts
                if parts:
                    return parts[0].text if hasattr(parts[0], 'text') else str(parts[0])
        # 문자열인 경우
        elif isinstance(response, str):
            return response
        else:
            return str(response)
    except Exception:
        return str(response)


def parse_json_from_text(text: str) -> Optional[Dict[str, Any]]:
    """텍스트에서 JSON 추출"""
    try:
        # JSON 블록 추출
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        # 전체가 JSON인 경우
        return json.loads(text)
    except Exception:
        return None


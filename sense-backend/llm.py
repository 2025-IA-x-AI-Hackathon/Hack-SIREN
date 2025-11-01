"""LLM 클라이언트 모듈"""
import os
import requests
from typing import Optional, Dict, Any

from backend.config import Config


class LLMClient:
    """LLM 클라이언트 (Ollama 사용, 노트북 구현 참고)"""
    
    def __init__(self):
        self.provider = Config.LLM_PROVIDER
    
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> Optional[str]:
        """텍스트 생성 (노트북의 ollama_generate 함수 참고)"""
        if self.provider == "ollama":
            result = self._ollama_generate(prompt, system_prompt, temperature)
            # None인 경우 빈 문자열 반환 (호환성)
            return result if result is not None else ""
        else:
            raise ValueError(f"지원하지 않는 LLM 프로바이더: {self.provider}. 현재는 'ollama'만 지원합니다.")
    
    def _ollama_generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7
    ) -> Optional[str]:
        """Ollama를 사용하여 텍스트를 생성합니다 (노트북 구현 참고)"""
        url = f"{Config.OLLAMA_BASE_URL}/api/generate"
        
        # 시스템 프롬프트와 사용자 프롬프트 결합
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"
        
        payload = {
            "model": Config.OLLAMA_MODEL,
            "prompt": full_prompt,
            "stream": False
        }
        
        # temperature가 0.7이 아닌 경우에만 options 추가
        if temperature != 0.7:
            payload["options"] = {
                "temperature": temperature
            }
        
        try:
            response = requests.post(url, json=payload, timeout=120)
            response.raise_for_status()
            result = response.json()
            answer = result.get("response", "").strip()
            
            # 응답이 비어있으면 None 반환
            if not answer:
                return None
            
            return answer
        except requests.exceptions.RequestException as e:
            # 에러 발생 시에만 출력 (사용자 요청: 답변만 리턴)
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Ollama API 호출 오류: {e}. Ollama가 실행 중인지 확인하세요: ollama serve")
            return None
    


# 전역 인스턴스
llm_client = LLMClient()


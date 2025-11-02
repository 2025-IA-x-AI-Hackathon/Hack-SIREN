"""AnalystAgent - RAG 검색 실행 및 분석"""
from typing import Dict, Any
from google import genai
from config import GOOGLE_API_KEY, GEMINI_MODEL
from services.rag_service import HybridRAGService
from models import AnalysisResult, PlanningResult, ProfileResult


class AnalystAgent:
    """RAG 검색 및 분석 에이전트"""
    
    def __init__(self):
        self.client = genai.Client(api_key=GOOGLE_API_KEY)
        self.rag_service = HybridRAGService()
    
    def analyze(self, input_text: str, profile: ProfileResult, planning: PlanningResult) -> AnalysisResult:
        """RAG 검색 실행 및 결과 분석"""
        
        # Hybrid RAG 검색 실행
        search_results = self.rag_service.search(input_text)
        print(search_results)
        
        graph_results = search_results["graph_results"]
        vector_results = search_results["vector_results"]
        print(graph_results)
        print(vector_results)
        
        # LLM을 사용하여 검색 결과 분석 및 요약
        graph_summary = self._format_graph_results(graph_results)
        vector_summary = self._format_vector_results(vector_results)
        print(graph_summary)
        print(vector_summary)
        
        prompt = f"""
당신은 재난대응 정보 분석 전문가입니다.
Graph RAG와 Vector RAG 검색 결과를 분석하여, 사용자 질문에 대한 핵심 정보를 추출하세요.

사용자 입력:
{input_text}

ProfileAgent 분석:
- 메시지 유형: {profile.message_type.value}
- 추출 정보: {profile.extracted_info}

PlanningAgent 계획:
{planning.search_plan}

Graph RAG 검색 결과:
{graph_summary}

Vector RAG 검색 결과:
{vector_summary}

다음 JSON 형식으로 분석 결과를 제공하세요:
{{
    "key_findings": ["주요 발견 사항 1", "주요 발견 사항 2"],
    "shelters": ["대피소 정보" (있는 경우)],
    "guidelines": ["행동요령 요약" (있는 경우)],
    "risks": ["위험 요소" (있는 경우)],
    "reasoning": "분석 근거 및 검색 결과 해석"
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
            analysis_dict = parse_json_from_text(text)
            
            if not analysis_dict:
                analysis_dict = {
                    "key_findings": [],
                    "reasoning": "분석 실패"
                }
        except Exception as e:
            analysis_dict = {
                "key_findings": [],
                "reasoning": f"분석 오류: {str(e)}"
            }
        
        return AnalysisResult(
            graph_results=graph_results,
            vector_results=vector_results,
            reasoning=analysis_dict.get("reasoning", "")
        )
    
    def _format_graph_results(self, graph_results: Dict) -> str:
        """Graph RAG 결과 포맷팅"""
        if graph_results.get("error"):
            return f"오류: {graph_results['error']}"
        
        count = graph_results.get('count', 0)
        results = graph_results.get("results", [])
        
        if not results:
            return f"검색 결과 없음 (count: {count})"
        
        # 결과 필터링: None이거나 빈 값이 아닌 결과만 포함
        valid_results = []
        for record in results:
            # 레코드에서 None이 아닌 값이 하나라도 있으면 유효한 결과로 간주
            has_valid_value = False
            filtered_record = {}
            for key, value in record.items():
                # None, 빈 문자열, 이상한 값들 필터링
                if value is not None:
                    value_str = str(value).strip()
                    # 이상한 값들 필터링 (>  > 같은 것)
                    if value_str and value_str not in [">  >", "> >", "None", "null", ""]:
                        filtered_record[key] = value
                        has_valid_value = True
            
            if has_valid_value:
                valid_results.append(filtered_record)
        
        # 유효한 결과가 없으면
        if not valid_results:
            return f"검색 결과 없음 (쿼리 결과는 {count}개이지만 유효한 데이터 없음)\n쿼리: {graph_results.get('query', 'N/A')}"
        
        # 최대 5개만 표시
        display_results = valid_results[:5]
        summary = f"Cypher 쿼리: {graph_results.get('query', 'N/A')}\n"
        summary += f"결과 개수: {count} (유효한 결과: {len(valid_results)}개)\n\n"
        
        for i, record in enumerate(display_results, 1):
            summary += f"결과 {i}:\n"
            for key, value in record.items():
                value_str = str(value)
                if len(value_str) > 200:
                    value_str = value_str[:200] + "..."
                summary += f"  {key}: {value_str}\n"
        
        if len(valid_results) > 5:
            summary += f"\n... 외 {len(valid_results) - 5}개 결과"
        
        return summary
    
    def _format_vector_results(self, vector_results: Dict) -> str:
        """Vector RAG 결과 포맷팅"""
        if vector_results.get("error"):
            return f"오류: {vector_results['error']}"
        
        results = vector_results.get("results", [])
        if not results:
            return "검색 결과 없음"
        
        summary = f"결과 개수: {len(results)}\n\n"
        
        for i, doc in enumerate(results, 1):
            doc_text = doc.get('text', '')
            if len(doc_text) > 400:
                doc_text = doc_text[:400] + "..."
            summary += f"문서 {i} (거리: {doc.get('distance', 'N/A')}):\n{doc_text}\n\n"
        
        return summary


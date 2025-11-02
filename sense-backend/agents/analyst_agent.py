"""AnalystAgent - RAG 검색 실행 및 분석"""
from typing import Dict, Any, Optional
import logging
import asyncio
from google import genai
from config import GOOGLE_API_KEY, GEMINI_MODEL
from services.rag_service import HybridRAGService
from models import AnalysisResult, PlanningResult

logger = logging.getLogger(__name__)


class AnalystAgent:
    """RAG 검색 및 분석 에이전트"""
    
    def __init__(self):
        self.client = genai.Client(api_key=GOOGLE_API_KEY)
        self.rag_service = HybridRAGService()
    
    async def analyze(self, input_text: str, user_info: Optional[dict] = None, planning: PlanningResult = None) -> AnalysisResult:
        """RAG 검색 실행 및 결과 분석
        
        PlanningAgent의 서브 문제를 활용하여 노트북 방식으로 각 서브 문제별 검색 수행
        """
        
        logger.info(f"[AnalystAgent] RAG 검색 시작: {input_text[:100]}...")
        
        # PlanningAgent의 서브 문제 추출
        sub_problems = []
        if planning and planning.search_plan:
            sub_problems = planning.search_plan.get("sub_problems", [])
        
        # 서브 문제가 있으면 노트북 방식으로 각 서브 문제별 검색
        if sub_problems:
            logger.info(f"[AnalystAgent] 서브 문제 {len(sub_problems)}개 검색 시작")
            
            with self.rag_service.get_neo4j_session() as session:
                # 스키마 가져오기
                schema = await asyncio.to_thread(
                    self.rag_service.get_neo4j_schema, session
                )
                if not self.rag_service._schema_cache:
                    self.rag_service._schema_cache = schema
                
                # 서브 문제별 검색 실행 (노트북 방식)
                search_results = await self.rag_service.search_sub_problems(
                    sub_problems, schema, session, use_cache=True
                )
                
                graph_results = search_results["graph_results"]
                vector_results = search_results["vector_results"]
                
                # 통합 결과에서 count 추출
                graph_count = graph_results.get("count", 0)
                vector_count = vector_results.get("count", 0)
                logger.info(f"[AnalystAgent] 서브 문제별 검색 완료: Graph RAG {graph_count}개, Vector RAG {vector_count}개")
        else:
            # 서브 문제가 없으면 기본 방식으로 검색
            logger.info("[AnalystAgent] 서브 문제 없음, 기본 검색 수행")
            search_results = await self.rag_service.search(input_text, use_cache=True)
            
            graph_results = search_results["graph_results"]
            vector_results = search_results["vector_results"]
            
            graph_count = graph_results.get("count", 0)
            vector_count = vector_results.get("count", 0)
            logger.info(f"[AnalystAgent] 검색 결과: Graph RAG {graph_count}개, Vector RAG {vector_count}개")
        
        # LLM을 사용하여 검색 결과 분석 및 요약
        graph_summary = self._format_graph_results(graph_results)
        vector_summary = self._format_vector_results(vector_results)
        
        prompt = f"""
당신은 재난대응 정보 분석 전문가입니다.
Graph RAG와 Vector RAG 검색 결과를 분석하여, 사용자 질문에 대한 핵심 정보를 추출하세요.

사용자 입력:
{input_text}

{('사용자 위치 정보:\n- 위도: ' + str(user_info.get('lat', 'N/A')) + '\n- 경도: ' + str(user_info.get('lon', 'N/A')) + '\n- 층수: ' + str(user_info.get('floor', 'N/A')) + '\n') if user_info else ''}

PlanningAgent 계획:
{planning.search_plan if planning else 'N/A'}

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
            # Gemini API는 동기식이므로 비동기로 실행
            response = await asyncio.to_thread(
                self.client.models.generate_content,
                model=GEMINI_MODEL,
                contents=prompt.strip()
            )
            
            from utils import extract_text_from_response, parse_json_from_text
            
            text = extract_text_from_response(response).strip()
            analysis_dict = parse_json_from_text(text)
            
            if not analysis_dict:
                analysis_dict = {
                    "key_findings": [],
                    "reasoning": "아직 분석할 정보가 확인되지 않았습니다."
                }
        except Exception as e:
            analysis_dict = {
                "key_findings": [],
                "reasoning": f"분석 과정에서 오류가 발생했습니다: {str(e)}. 아직 분석할 정보가 확인되지 않았습니다."
            }
        
        reasoning = analysis_dict.get("reasoning", "")
        logger.info(f"[AnalystAgent] 분석 완료: {reasoning[:100] if reasoning else '분석 완료'}...")
        
        return AnalysisResult(
            graph_results=graph_results,
            vector_results=vector_results,
            reasoning=reasoning
        )
    
    def _format_graph_results(self, graph_results: Dict) -> str:
        """Graph RAG 결과 포맷팅 (서브 문제별 결과 지원)"""
        if graph_results.get("error"):
            return f"오류: {graph_results['error']}"
        
        count = graph_results.get('count', 0)
        results = graph_results.get("results", [])
        sub_problem_results = graph_results.get("sub_problem_results", [])
        
        # 서브 문제별 결과가 있으면 더 상세히 포맷팅
        if sub_problem_results:
            summary_parts = ["# Graph RAG 검색 결과 (서브 문제별)\n"]
            
            for sub_result in sub_problem_results:
                sub_id = sub_result.get("sub_problem_id", 0)
                sub_question = sub_result.get("sub_question", "")
                sub_count = sub_result.get("count", 0)
                sub_query = sub_result.get("query", "N/A")
                sub_records = sub_result.get("results", [])
                
                summary_parts.append(f"\n## 서브 문제 {sub_id}: {sub_question[:50]}...")
                summary_parts.append(f"Cypher 쿼리: {sub_query}")
                summary_parts.append(f"결과 개수: {sub_count}")
                
                if sub_records:
                    # 유효한 결과만 필터링
                    valid_results = []
                    for record in sub_records[:3]:  # 각 서브 문제당 최대 3개
                        has_valid_value = False
                        filtered_record = {}
                        for key, value in record.items():
                            if value is not None:
                                value_str = str(value).strip()
                                if value_str and value_str not in [">  >", "> >", "None", "null", ""]:
                                    filtered_record[key] = value
                                    has_valid_value = True
                        if has_valid_value:
                            valid_results.append(filtered_record)
                    
                    for i, record in enumerate(valid_results, 1):
                        summary_parts.append(f"\n  결과 {i}:")
                        for key, value in record.items():
                            value_str = str(value)
                            if len(value_str) > 150:
                                value_str = value_str[:150] + "..."
                            summary_parts.append(f"    {key}: {value_str}")
                else:
                    summary_parts.append("  아직 검색 결과가 확인되지 않았습니다")
            
            summary_parts.append(f"\n### 통합 결과: 총 {count}개")
            return "\n".join(summary_parts)
        
        # 기본 포맷팅 (서브 문제별 결과가 없는 경우)
        if not results:
            return f"아직 검색 결과가 확인되지 않았습니다 (count: {count})"
        
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
            return f"아직 검색 결과가 확인되지 않았습니다 (쿼리 결과는 {count}개이지만 유효한 데이터 없음)\n쿼리: {graph_results.get('query', 'N/A')}"
        
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
        """Vector RAG 결과 포맷팅 (서브 문제별 결과 지원)"""
        if vector_results.get("error"):
            return f"오류: {vector_results['error']}"
        
        results = vector_results.get("results", [])
        sub_problem_results = vector_results.get("sub_problem_results", [])
        
        # 서브 문제별 결과가 있으면 더 상세히 포맷팅
        if sub_problem_results:
            summary_parts = ["# Vector RAG 검색 결과 (서브 문제별)\n"]
            
            for sub_result in sub_problem_results:
                sub_id = sub_result.get("sub_problem_id", 0)
                sub_question = sub_result.get("sub_question", "")
                sub_count = sub_result.get("count", 0)
                sub_docs = sub_result.get("results", [])
                
                summary_parts.append(f"\n## 서브 문제 {sub_id}: {sub_question[:50]}...")
                summary_parts.append(f"결과 개수: {sub_count}")
                
                if sub_docs:
                    for i, doc in enumerate(sub_docs[:2], 1):  # 각 서브 문제당 최대 2개
                        doc_text = doc.get('text', '')
                        if len(doc_text) > 300:
                            doc_text = doc_text[:300] + "..."
                        summary_parts.append(f"\n  문서 {i} (거리: {doc.get('distance', 'N/A')}):")
                        summary_parts.append(f"    {doc_text}")
                else:
                    summary_parts.append("  아직 검색 결과가 확인되지 않았습니다")
            
            summary_parts.append(f"\n### 통합 결과: 총 {len(results)}개")
            return "\n".join(summary_parts)
        
        # 기본 포맷팅 (서브 문제별 결과가 없는 경우)
        if not results:
            return "아직 검색 결과가 확인되지 않았습니다."
        
        summary = f"결과 개수: {len(results)}\n\n"
        
        for i, doc in enumerate(results, 1):
            doc_text = doc.get('text', '')
            if len(doc_text) > 400:
                doc_text = doc_text[:400] + "..."
            summary += f"문서 {i} (거리: {doc.get('distance', 'N/A')}):\n{doc_text}\n\n"
        
        return summary


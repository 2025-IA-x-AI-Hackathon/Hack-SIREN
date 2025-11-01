"""AnalystAgent: RAG 기반 정보 분석"""
from typing import Dict, Any
from llm import llm_client
from db import db_manager
from rag import hybrid_rag
from types import AgentStateModel


class AnalystAgent:
    """정보 분석 에이전트 (RAG 기반)"""
    
    def __init__(self):
        self.name = "AnalystAgent"
    
    def process(self, state: AgentStateModel) -> AgentStateModel:
        """상태 처리: RAG 기반 정보 분석"""
        
        message = state.message
        analysis_plan = state.analysis_plan or {}
        
        # Neo4j 세션 가져오기
        with db_manager.get_neo4j_session() as session:
            # Hybrid RAG 검색 실행
            rag_results = hybrid_rag.search(message, session)
            
            # 결과 저장
            state.graph_search_results = rag_results.graph_results
            state.vector_search_results = rag_results.vector_results
            
            # 분석 요약 생성
            summary_prompt = f"""
당신은 재난 정보 분석 전문가입니다. 다음 검색 결과를 바탕으로 종합 분석을 수행하세요.

검색 계획:
{analysis_plan}

Graph RAG 검색 결과:
{rag_results.graph_results.get('count', 0)}개 결과
{hybrid_rag.format_graph_results(rag_results.graph_results, max_length=1500)}

Vector RAG 검색 결과:
{rag_results.vector_results.get('count', 0)}개 결과
{hybrid_rag.format_vector_results(rag_results.vector_results, max_length=1500)}

다음 항목을 포함하여 분석 요약을 작성하세요:
1. 발견된 주요 정보
2. 사용자에게 중요한 점
3. 추가로 확인이 필요한 사항
4. 우선순위가 높은 정보

간결하고 구조화된 요약을 작성하세요 (3-5문장).
"""
            
            try:
                summary = llm_client.generate(summary_prompt, temperature=0.3)
                reasoning = f"Graph RAG: {rag_results.graph_results.get('count', 0)}개, Vector RAG: {rag_results.vector_results.get('count', 0)}개 검색 결과를 종합 분석"
                
                state.analysis_summary = summary
                state.analyst_reasoning = reasoning
                
                if state.explanation_path is None:
                    state.explanation_path = []
                state.explanation_path.append(f"{self.name}: {reasoning}")
                
            except Exception as e:
                print(f"AnalystAgent 분석 요약 생성 오류: {e}")
                state.analysis_summary = "검색 결과를 종합 분석했습니다."
                state.analyst_reasoning = f"검색 완료: Graph {rag_results.graph_results.get('count', 0)}개, Vector {rag_results.vector_results.get('count', 0)}개"
        
        return state


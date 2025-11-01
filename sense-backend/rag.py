"""Hybrid RAG 모듈 (Graph RAG + Vector RAG)"""
from typing import Dict, Any, Optional, List
from neo4j import Session

from backend.db import db_manager
from backend.llm import llm_client
from backend.config import Config
from backend.types import RAGResults


class HybridRAG:
    """Hybrid RAG: Graph RAG와 Vector RAG 결합"""
    
    def __init__(self):
        self.neo4j_schema: Optional[str] = None
        self._update_schema()
    
    def _update_schema(self):
        """Neo4j 스키마 업데이트"""
        self.neo4j_schema = db_manager.get_neo4j_schema()
    
    def generate_cypher_query(self, question: str) -> Optional[str]:
        """자연어 질문을 Cypher 쿼리로 변환"""
        if not self.neo4j_schema:
            self._update_schema()
        
        prompt = f"""
당신은 Neo4j Cypher 쿼리 전문가입니다.
다음 그래프 스키마 정보를 참고하여, 사용자의 자연어 질문을 Cypher 쿼리로 변환하세요.

# Graph Schema:
{self.neo4j_schema}

# 중요: 관계 타입은 'IN'만 사용하세요. 'LOCATED_IN'이나 'INTERSECTS'는 사용하지 마세요.
# 예시:
# - "몇 개" 질문: MATCH (s:Shelter)-[:IN]->(a:Admin {{gu: '강남구'}}) RETURN count(s)
# - "알려주세요" 질문: MATCH (s:Shelter) WHERE s.sigungu = '서초구' RETURN s LIMIT 10

# 사용자 질문:
{question}

지침:
1. 질문의 의도를 정확히 파악하여 적절한 Cypher 쿼리를 생성하세요.
2. 노드 라벨과 관계 타입을 정확히 사용하세요. 특히 관계는 'IN'만 사용해야 합니다.
3. **중요**: "알려주세요", "찾고 싶어요", "어디" 같은 질문이면 반드시 실제 대피소 정보를 반환하도록 RETURN 절을 작성하세요.
   - 예: MATCH (s:Shelter) WHERE s.sigungu = '서초구' RETURN s LIMIT 10
   - 또는: MATCH (s:Shelter) WHERE s.sigungu = '서초구' RETURN s.name, s.address, s.shelter_type LIMIT 10
   - COUNT()를 사용하지 마세요. 실제 노드 정보를 반환해야 합니다.
4. "몇 개" 또는 "개수" 질문이면 COUNT()를 사용하세요.
5. 쿼리만 반환하고 설명은 제외하세요.

Cypher 쿼리:
"""
        
        try:
            response = llm_client.generate(prompt.strip(), temperature=0.1)
            if not response:
                return None
            
            cypher_query = response.strip()
            # 코드 블록 제거 (```cypher 등)
            if cypher_query.startswith("```"):
                lines = cypher_query.split("\n")
                cypher_query = "\n".join(lines[1:-1]) if len(lines) > 2 else cypher_query
            
            return cypher_query
        except Exception as e:
            print(f"Cypher 쿼리 생성 오류: {e}")
            return None
    
    def graph_rag_search(self, question: str, session: Session) -> Dict[str, Any]:
        """Graph RAG 검색: Neo4j에서 구조화된 정보 검색"""
        # 1. Cypher 쿼리 생성
        cypher_query = self.generate_cypher_query(question)
        
        if not cypher_query:
            return {
                "query": None,
                "results": [],
                "count": 0,
                "error": "Cypher 쿼리 생성 실패"
            }
        
        # 2. 쿼리 실행
        try:
            result = session.run(cypher_query)
            records = [dict(record) for record in result]
            
            # COUNT 등의 집계 함수 결과 처리
            actual_count = len(records)
            if actual_count == 1 and records:
                # COUNT 쿼리 결과 추출 시도
                for key, value in records[0].items():
                    if 'count' in key.lower() or isinstance(value, (int, float)):
                        actual_count = int(value) if isinstance(value, (int, float)) else actual_count
            
            return {
                "query": cypher_query,
                "results": records,
                "count": actual_count
            }
        except Exception as e:
            print(f"  ⚠ Cypher 쿼리 실행 오류: {e}")
            return {
                "query": cypher_query,
                "results": [],
                "count": 0,
                "error": str(e)
            }
    
    def vector_rag_search(self, question: str, top_k: int = None) -> Dict[str, Any]:
        """Vector RAG 검색: Chroma에서 관련 문서 검색"""
        if top_k is None:
            top_k = Config.VECTOR_RAG_TOP_K
        
        collection = db_manager.get_chroma_collection()
        
        if collection is None:
            return {"results": [], "error": "Chroma 컬렉션이 없습니다."}
        
        try:
            # 질문을 임베딩으로 변환하여 검색 (Chroma가 자동으로 처리)
            results = collection.query(
                query_texts=[question],
                n_results=top_k
            )
            
            documents = []
            for i in range(len(results["ids"][0])):
                doc_id = results["ids"][0][i]
                doc_text = results["documents"][0][i] if results["documents"] else ""
                distance = results["distances"][0][i] if results["distances"] else None
                
                documents.append({
                    "id": doc_id,
                    "text": doc_text,
                    "distance": distance
                })
            
            return {
                "results": documents,
                "count": len(documents)
            }
        except Exception as e:
            return {
                "results": [],
                "error": str(e)
            }
    
    def format_graph_results(self, graph_results: Dict[str, Any], max_length: int = 2000) -> str:
        """Graph RAG 결과를 텍스트로 포맷팅"""
        if graph_results.get("error"):
            return f"오류: {graph_results['error']}"
        
        result_count = graph_results.get('count', 0)
        result_parts = ["# Graph RAG 검색 결과\n"]
        result_parts.append(f"Cypher 쿼리: {graph_results.get('query', 'N/A')}\n")
        result_parts.append(f"결과 개수: {result_count}\n")
        
        if not graph_results.get("results"):
            result_parts.append("\n검색 결과가 없습니다.")
        else:
            results = graph_results["results"]
            # 결과가 많으면 요약
            if len(results) > 20:
                result_parts.append(f"\n## 요약: 총 {len(results)}개 결과 중 처음 10개만 표시\n")
                results = results[:10]
            
            for i, record in enumerate(results, 1):
                result_parts.append(f"\n## 결과 {i}")
                for key, value in record.items():
                    # 값이 너무 길면 자르기
                    value_str = str(value)
                    if len(value_str) > 200:
                        value_str = value_str[:200] + "..."
                    result_parts.append(f"- {key}: {value_str}")
        
        text = "\n".join(result_parts)
        # 전체 길이 제한
        if len(text) > max_length:
            text = text[:max_length] + "\n\n[이하 생략 - 결과가 너무 많습니다]"
        
        return text
    
    def format_vector_results(self, vector_results: Dict[str, Any], max_length: int = 3000) -> str:
        """Vector RAG 결과를 텍스트로 포맷팅"""
        if vector_results.get("error"):
            return f"오류: {vector_results['error']}"
        
        if not vector_results.get("results"):
            return "검색 결과가 없습니다."
        
        result_parts = ["# Vector RAG 검색 결과\n"]
        result_parts.append(f"결과 개수: {vector_results.get('count', 0)}\n")
        
        for i, doc in enumerate(vector_results["results"], 1):
            result_parts.append(f"\n## 문서 {i} (거리: {doc.get('distance', 'N/A')})")
            doc_text = doc.get('text', '')
            # 문서가 너무 길면 자르기
            if len(doc_text) > 800:
                doc_text = doc_text[:800] + "..."
            result_parts.append(doc_text)
        
        text = "\n".join(result_parts)
        # 전체 길이 제한
        if len(text) > max_length:
            text = text[:max_length] + "\n\n[이하 생략]"
        
        return text
    
    def search(self, question: str, session: Session) -> RAGResults:
        """Hybrid RAG 검색 실행"""
        # Graph RAG 검색
        graph_results = self.graph_rag_search(question, session)
        
        # Vector RAG 검색
        vector_results = self.vector_rag_search(question)
        
        # 결과 포맷팅
        graph_text = self.format_graph_results(graph_results, max_length=2000)
        vector_text = self.format_vector_results(vector_results, max_length=3000)
        
        combined_context = f"{graph_text}\n\n{vector_text}"
        
        return RAGResults(
            graph_results=graph_results,
            vector_results=vector_results,
            combined_context=combined_context
        )


# 전역 인스턴스
hybrid_rag = HybridRAG()


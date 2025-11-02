"""Hybrid RAG 서비스 (노트북 코드 기반)"""
import os
import asyncio
import logging
from typing import List, Dict, Optional
from neo4j import GraphDatabase
import chromadb
from chromadb.config import Settings
from google import genai
from google.genai import types

from config import (
    NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD,
    CHROMA_PERSIST_DIR, CHROMA_HOST, CHROMA_PORT, CHROMA_USE_HTTP_CLIENT,
    GOOGLE_API_KEY,
    GEMINI_MODEL, GEMINI_EMBEDDING_MODEL, EMBEDDING_DIM
)

logger = logging.getLogger(__name__)


class GeminiEmbeddingFunction:
    """Chroma용 Gemini 임베딩 함수"""
    
    def __init__(self, client: genai.Client, model: str = GEMINI_EMBEDDING_MODEL):
        self.client = client
        self.model = model
    
    def __call__(self, input_texts: List[str]) -> List[List[float]]:
        """텍스트 리스트를 임베딩으로 변환"""
        try:
            result = self.client.models.embed_content(
                model=self.model,
                contents=input_texts,
                config=types.EmbedContentConfig(
                    output_dimensionality=EMBEDDING_DIM
                )
            )
            embeddings = []
            for embedding in result.embeddings:
                if hasattr(embedding, 'values'):
                    embeddings.append(list(embedding.values))
                elif isinstance(embedding, list):
                    embeddings.append(embedding)
                elif hasattr(embedding, '__iter__') and not isinstance(embedding, str):
                    embeddings.append(list(embedding))
                else:
                    embeddings.append([float(embedding)])
            return embeddings
        except Exception as e:
            raise Exception(f"임베딩 생성 오류: {e}")


class HybridRAGService:
    """Hybrid RAG 서비스"""
    
    def __init__(self):
        # Neo4j 연결
        self.neo4j_driver = GraphDatabase.driver(
            NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD)
        )
        
        # Gemini 클라이언트
        if not GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY 환경변수를 설정해주세요.")
        self.gemini_client = genai.Client(api_key=GOOGLE_API_KEY)
        
        # Chroma 연결 (Docker 환경에서는 HttpClient, 로컬에서는 PersistentClient)
        if CHROMA_USE_HTTP_CLIENT:
            # Docker Compose 환경: Chroma standalone server 사용
            self.chroma_client = chromadb.HttpClient(
                host=CHROMA_HOST,
                port=CHROMA_PORT,
                settings=Settings(anonymized_telemetry=False)
            )
            logger.info(f"[RAG Service] Chroma HttpClient 사용: {CHROMA_HOST}:{CHROMA_PORT}")
        else:
            # 로컬 환경: PersistentClient 사용
            self.chroma_client = chromadb.PersistentClient(
                path=CHROMA_PERSIST_DIR,
                settings=Settings(anonymized_telemetry=False)
            )
            logger.info(f"[RAG Service] Chroma PersistentClient 사용: {CHROMA_PERSIST_DIR}")
        
        self.gemini_embedding_fn = GeminiEmbeddingFunction(self.gemini_client)
        
        # 컬렉션 가져오기
        try:
            self.chroma_collection = self.chroma_client.get_collection("disaster_docs")
            logger.info("[RAG Service] 기존 Chroma 컬렉션 로드: disaster_docs")
        except:
            # 컬렉션이 없으면 생성
            # HttpClient는 embedding_function을 직접 지원하지 않으므로, 
            # 임베딩은 별도로 처리하도록 빈 컬렉션 생성
            try:
                if CHROMA_USE_HTTP_CLIENT:
                    # HttpClient는 embedding_function 파라미터 미지원
                    self.chroma_collection = self.chroma_client.create_collection("disaster_docs")
                else:
                    # PersistentClient는 embedding_function 지원
                    self.chroma_collection = self.chroma_client.create_collection(
                        name="disaster_docs",
                        embedding_function=self.gemini_embedding_fn
                    )
                logger.info("[RAG Service] 새 Chroma 컬렉션 생성: disaster_docs")
            except Exception as e:
                logger.error(f"[RAG Service] Chroma 컬렉션 생성 오류: {e}")
                raise
        
        # Neo4j 스키마 캐싱 (매번 조회하지 않도록)
        self._schema_cache = None
    
    def get_neo4j_session(self):
        """Neo4j 세션 가져오기"""
        return self.neo4j_driver.session()
    
    def get_neo4j_schema(self, session) -> str:
        """Neo4j 그래프 스키마 정보 가져오기"""
        node_labels_query = "CALL db.labels()"
        node_labels = [record["label"] for record in session.run(node_labels_query)]
        
        rel_types_query = "CALL db.relationshipTypes()"
        rel_types = [record["relationshipType"] for record in session.run(rel_types_query)]
        
        actual_rels = []
        for rel_type in rel_types:
            count = session.run(
                f"MATCH ()-[r:{rel_type}]->() RETURN count(r) as count"
            ).single()["count"]
            if count > 0:
                actual_rels.append(rel_type)
        
        node_properties = {}
        for label in node_labels:
            props_query = f"MATCH (n:{label}) RETURN keys(n) as props LIMIT 1"
            result = session.run(props_query)
            record = result.single()
            if record:
                node_properties[label] = record["props"]
        
        schema_parts = ["# Neo4j Graph Schema\n\n"]
        schema_parts.append("## Node Labels:\n")
        for label in sorted(node_labels):
            props = node_properties.get(label, [])
            key_props = [p for p in props if p not in ['id', 'type']][:10]
            props_str = ", ".join(key_props) if key_props else "id, type"
            schema_parts.append(f"- {label}: {{id, type, {props_str}...}}")
        
        schema_parts.append("\n## Relationship Types:\n")
        important_rels = ['GUIDES', 'TRIGGERS', 'CAUSES', 'INCREASES_RISK_OF', 'UPDATES', 'IN']
        for rel_type in important_rels:
            if rel_type in actual_rels:
                schema_parts.append(f"- {rel_type}")
        for rel_type in sorted(actual_rels):
            if rel_type not in important_rels:
                schema_parts.append(f"- {rel_type}")
        
        return "\n".join(schema_parts)
    
    def generate_cypher_query(self, question: str, schema: str) -> Optional[str]:
        """자연어 질문을 Cypher 쿼리로 변환"""
        prompt = f"""
당신은 Neo4j Cypher 쿼리 전문가입니다.
다음 그래프 스키마 정보를 참고하여, 사용자의 자연어 질문을 Cypher 쿼리로 변환하세요.

# Graph Schema:
{schema}

# 사용 가능한 노드 타입:
- Shelter, TemporaryHousing: 대피소 및 임시주거시설
- Admin: 행정구역 (gu, sigungu 속성)
- Hazard: 재난 유형 (지진, 산사태, 붕괴, 노화)
- Policy: 행동요령 정책
- Event: 재난 이벤트

# 사용 가능한 관계 타입:
- IN: Shelter/TemporaryHousing → Admin (위치 관계)
- GUIDES: Policy → Hazard (행동요령이 재난을 안내)
- TRIGGERS: Hazard → Hazard 또는 Event → Hazard (유발 관계)
- CAUSES: Hazard → Hazard (원인 관계)
- INCREASES_RISK_OF: Hazard → Hazard (위험 증가 관계)
- UPDATES: Event → Hazard (이벤트가 재난 정보 업데이트)

# 예시:
# - "몇 개" 질문: MATCH (s:Shelter)-[:IN]->(a:Admin {{gu: '강남구'}}) RETURN count(s)
# - "알려주세요" 질문: MATCH (s:Shelter)-[:IN]->(a:Admin {{gu: '서초구'}}) RETURN s.name, s.address LIMIT 10
# - "행동요령" 질문: MATCH (p:Policy)-[:GUIDES]->(h:Hazard {{hazard_type: '지진'}}) RETURN p.name, p.content LIMIT 5
# - "재난 관계" 질문: MATCH (h1:Hazard)-[:TRIGGERS]->(h2:Hazard) RETURN h1.name, h2.name

# 사용자 질문:
{question}

지침:
1. 질문의 의도를 정확히 파악하여 적절한 Cypher 쿼리를 생성하세요.
2. 노드 라벨과 관계 타입을 정확히 사용하세요. 위에 나열된 관계 타입을 활용하세요.
3. **중요**: "알려주세요", "찾고 싶어요", "어디" 같은 질문이면 반드시 실제 정보를 반환하도록 RETURN 절을 작성하세요.
   - 대피소: MATCH (s:Shelter)-[:IN]->(a:Admin {{gu: '서초구'}}) RETURN s.name, s.address, s.shelter_type LIMIT 10
   - 행동요령: MATCH (p:Policy)-[:GUIDES]->(h:Hazard) RETURN p.name, p.content LIMIT 5
   - COUNT()를 사용하지 마세요. 실제 노드 정보를 반환해야 합니다.
4. "몇 개" 또는 "개수" 질문이면 COUNT()를 사용하세요.
5. 재난 관련 질문은 Hazard, Policy, Event 노드를 활용하세요.
6. 쿼리만 반환하고 설명은 제외하세요.

Cypher 쿼리:
"""

        
        try:
            response = self.gemini_client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt.strip()
            )
            
            from utils import extract_text_from_response
            
            cypher_query = extract_text_from_response(response).strip()
            if cypher_query.startswith("```"):
                lines = cypher_query.split("\n")
                cypher_query = "\n".join(lines[1:-1]) if len(lines) > 2 else cypher_query
            
            return cypher_query
        except Exception as e:
            print(f"Cypher 쿼리 생성 오류: {e}")
            return None
    
    def graph_rag_search(self, question: str, schema: str, session) -> Dict:
        """Graph RAG 검색"""
        cypher_query = self.generate_cypher_query(question, schema)
        
        if not cypher_query:
            return {"query": None, "results": [], "count": 0, "error": "Cypher 쿼리 생성 실패"}
        
        try:
            result = session.run(cypher_query)
            records = [dict(record) for record in result]
            
            actual_count = len(records)
            if actual_count == 1 and records:
                for key, value in records[0].items():
                    if 'count' in key.lower() or isinstance(value, (int, float)):
                        actual_count = int(value) if isinstance(value, (int, float)) else actual_count
            
            return {
                "query": cypher_query,
                "results": records,
                "count": actual_count
            }
        except Exception as e:
            return {
                "query": cypher_query,
                "results": [],
                "count": 0,
                "error": str(e)
            }
    
    def vector_rag_search(self, question: str, top_k: int = 5) -> Dict:
        """Vector RAG 검색"""
        try:
            embedding_result = self.gemini_client.models.embed_content(
                model=GEMINI_EMBEDDING_MODEL,
                contents=[question],
                config=types.EmbedContentConfig(
                    output_dimensionality=EMBEDDING_DIM
                )
            )
            
            query_embedding = None
            if embedding_result.embeddings:
                embedding = embedding_result.embeddings[0]
                if hasattr(embedding, 'values'):
                    query_embedding = list(embedding.values)
                elif isinstance(embedding, list):
                    query_embedding = embedding
                elif hasattr(embedding, '__iter__') and not isinstance(embedding, str):
                    query_embedding = list(embedding)
                else:
                    query_embedding = [float(embedding)]
            
            if query_embedding is None:
                raise ValueError("임베딩 추출 실패")
            
            results = self.chroma_collection.query(
                query_embeddings=[query_embedding],
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
    
    async def search_sub_problems(self, sub_problems: List[Dict], schema: str, session, use_cache: bool = True) -> Dict:
        """서브 문제별 Hybrid RAG 검색 실행 (노트북 방식)
        
        Args:
            sub_problems: PlanningAgent가 생성한 서브 문제 리스트
            schema: Neo4j 스키마
            session: Neo4j 세션
            use_cache: 스키마 캐시 사용 여부 (기본값: True)
        
        Returns:
            각 서브 문제별 검색 결과
        """
        all_graph_results = []
        all_vector_results = []
        
        for sub_problem in sub_problems:
            sub_id = sub_problem.get("id", 0)
            sub_question = sub_problem.get("question", "")
            graph_search_info = sub_problem.get("graph_search", {})
            vector_search_info = sub_problem.get("vector_search", {})
            
            logger.info(f"[RAG Service] 서브 문제 {sub_id} 검색: {sub_question[:50]}...")
            
            # Graph RAG 검색: 서브 문제의 question + graph_search 정보 활용하여 질문 구성
            # graph_search_info의 query_intent, specific_info, region_filter 등을 활용
            graph_query = sub_question
            if graph_search_info.get("query_intent"):
                # query_intent가 있으면 더 구체적인 질문 구성
                query_intent = graph_search_info.get("query_intent", "")
                region_filter = graph_search_info.get("region_filter")
                specific_info = graph_search_info.get("specific_info", "")
                
                # 지역 필터가 있으면 질문에 명시
                if region_filter:
                    graph_query = f"{sub_question} (지역: {region_filter})"
                elif specific_info:
                    graph_query = f"{sub_question} ({specific_info})"
                
                logger.debug(f"[RAG Service] 서브 문제 {sub_id} Graph RAG 쿼리: {graph_query}")
            
            graph_results = await asyncio.to_thread(
                self.graph_rag_search, graph_query, schema, session
            )
            graph_results["sub_problem_id"] = sub_id
            graph_results["sub_question"] = sub_question
            graph_results["graph_search_info"] = graph_search_info
            all_graph_results.append(graph_results)
            
            # Vector RAG 검색: 서브 문제의 question + vector_search 정보 활용하여 질문 구성
            # vector_search_info의 keywords, focus, situation_context 등을 활용
            vector_query = sub_question
            if vector_search_info.get("keywords"):
                # keywords가 있으면 질문에 키워드 추가
                keywords = vector_search_info.get("keywords", [])
                if isinstance(keywords, list):
                    keyword_str = " ".join(keywords)
                    vector_query = f"{sub_question} {keyword_str}"
                elif isinstance(keywords, str):
                    vector_query = f"{sub_question} {keywords}"
            
            if vector_search_info.get("situation_context"):
                # 상황 정보가 있으면 추가
                situation = vector_search_info.get("situation_context")
                vector_query = f"{vector_query} 상황: {situation}"
            
            top_k = vector_search_info.get("top_k", 5)
            logger.debug(f"[RAG Service] 서브 문제 {sub_id} Vector RAG 쿼리: {vector_query} (top_k: {top_k})")
            
            vector_results = await asyncio.to_thread(
                self.vector_rag_search, vector_query, top_k
            )
            vector_results["sub_problem_id"] = sub_id
            vector_results["sub_question"] = sub_question
            vector_results["vector_search_info"] = vector_search_info
            all_vector_results.append(vector_results)
        
        # 모든 결과 통합 (평탄화)
        all_graph_records = []
        for r in all_graph_results:
            if r.get("results"):
                all_graph_records.extend(r["results"])
        
        all_vector_docs = []
        for r in all_vector_results:
            if r.get("results"):
                all_vector_docs.extend(r["results"])
        
        combined_graph_results = {
            "query": "서브 문제별 통합 쿼리",
            "results": all_graph_records,
            "count": len(all_graph_records),
            "sub_problem_results": all_graph_results  # 서브 문제별 상세 결과
        }
        
        combined_vector_results = {
            "results": all_vector_docs,
            "count": len(all_vector_docs),
            "sub_problem_results": all_vector_results  # 서브 문제별 상세 결과
        }
        
        return {
            "graph_results": combined_graph_results,
            "vector_results": combined_vector_results
        }
    
    async def search(self, question: str, use_cache: bool = True) -> Dict:
        """Hybrid RAG 검색 실행 (기본 방식 - 단일 질문)
        
        Args:
            question: 검색 질문
            use_cache: 스키마 캐시 사용 여부 (기본값: True)
        """
        with self.get_neo4j_session() as session:
            # 스키마 캐싱: 매번 조회하지 않고 캐시 사용
            if use_cache and self._schema_cache:
                schema = self._schema_cache
            else:
                schema = await asyncio.to_thread(self.get_neo4j_schema, session)
                if use_cache:
                    self._schema_cache = schema
            
            # 병렬 검색 (Graph RAG와 Vector RAG 동시 실행)
            graph_task = asyncio.to_thread(
                self.graph_rag_search, question, schema, session
            )
            vector_task = asyncio.to_thread(
                self.vector_rag_search, question
            )
            
            graph_results, vector_results = await asyncio.gather(
                graph_task, vector_task
            )
            
            return {
                "graph_results": graph_results,
                "vector_results": vector_results
            }


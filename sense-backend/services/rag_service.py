"""Hybrid RAG 서비스 (노트북 코드 기반)"""
import os
from typing import List, Dict, Optional
from neo4j import GraphDatabase
import chromadb
from chromadb.config import Settings
from google import genai
from google.genai import types

from config import (
    NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD,
    CHROMA_PERSIST_DIR, GOOGLE_API_KEY,
    GEMINI_MODEL, GEMINI_EMBEDDING_MODEL, EMBEDDING_DIM
)


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
        
        # Chroma 연결
        self.chroma_client = chromadb.PersistentClient(
            path=CHROMA_PERSIST_DIR,
            settings=Settings(anonymized_telemetry=False)
        )
        self.gemini_embedding_fn = GeminiEmbeddingFunction(self.gemini_client)
        
        # 컬렉션 가져오기
        try:
            self.chroma_collection = self.chroma_client.get_collection("disaster_docs")
        except:
            # 컬렉션이 없으면 생성 (임베딩 함수와 함께)
            self.chroma_collection = self.chroma_client.create_collection(
                name="disaster_docs",
                embedding_function=self.gemini_embedding_fn
            )
    
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
    
    def search(self, question: str) -> Dict:
        """Hybrid RAG 검색 실행"""
        with self.get_neo4j_session() as session:
            schema = self.get_neo4j_schema(session)
            
            graph_results = self.graph_rag_search(question, schema, session)
            vector_results = self.vector_rag_search(question)
            
            return {
                "graph_results": graph_results,
                "vector_results": vector_results
            }


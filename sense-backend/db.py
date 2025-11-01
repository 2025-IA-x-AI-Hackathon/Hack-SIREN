"""데이터베이스 연결 모듈"""
from typing import Optional, Any
from neo4j import GraphDatabase, Driver
import chromadb
from chromadb.config import Settings

from config import Config

# ChromaDB 타입 힌트
# ChromaDB 버전에 따라 타입 위치가 다를 수 있으므로 Any로 처리
# 실제 런타임에는 타입 import 없이 Any 사용
CollectionType = Any


class DatabaseManager:
    """데이터베이스 연결 관리"""
    
    def __init__(self):
        self.neo4j_driver: Optional[Driver] = None
        self.chroma_client: Optional[chromadb.ClientAPI] = None
        self.chroma_collection: Optional[CollectionType] = None
        
    def connect_neo4j(self) -> Driver:
        """Neo4j 연결"""
        if self.neo4j_driver is None:
            self.neo4j_driver = GraphDatabase.driver(
                Config.NEO4J_URI,
                auth=(Config.NEO4J_USER, Config.NEO4J_PASSWORD)
            )
        return self.neo4j_driver
    
    def get_neo4j_session(self):
        """Neo4j 세션 반환"""
        if self.neo4j_driver is None:
            self.connect_neo4j()
        return self.neo4j_driver.session()
    
    def connect_chroma(self) -> CollectionType:
        """Chroma 연결 및 컬렉션 반환"""
        if self.chroma_client is None:
            self.chroma_client = chromadb.PersistentClient(
                path=Config.CHROMA_PERSIST_DIR,
                settings=Settings(anonymized_telemetry=False)
            )
        
        # 컬렉션 가져오기 또는 생성
        try:
            self.chroma_collection = self.chroma_client.get_collection(
                Config.CHROMA_COLLECTION_NAME
            )
        except Exception:
            # 컬렉션이 없으면 생성
            self.chroma_collection = self.chroma_client.create_collection(
                name=Config.CHROMA_COLLECTION_NAME,
                metadata={"description": "재난 행동요령 문서"}
            )
        
        return self.chroma_collection
    
    def get_chroma_collection(self) -> CollectionType:
        """Chroma 컬렉션 반환"""
        if self.chroma_collection is None:
            self.connect_chroma()
        return self.chroma_collection
    
    def get_neo4j_schema(self) -> str:
        """Neo4j 스키마 정보 가져오기"""
        with self.get_neo4j_session() as session:
            # 노드 라벨 조회
            node_labels = [record["label"] for record in session.run("CALL db.labels()")]
            
            # 관계 타입 조회
            rel_types = [record["relationshipType"] for record in session.run("CALL db.relationshipTypes()")]
            
            # 실제로 사용되는 관계 타입만 필터링
            actual_rels = []
            for rel_type in rel_types:
                count = session.run(
                    f"MATCH ()-[r:{rel_type}]->() RETURN count(r) as count"
                ).single()["count"]
                if count > 0:
                    actual_rels.append(rel_type)
            
            # 노드별 속성 정보 조회
            node_properties = {}
            for label in node_labels:
                result = session.run(
                    f"MATCH (n:{label}) RETURN keys(n) as props LIMIT 1"
                ).single()
                if result:
                    node_properties[label] = result["props"]
            
            # 스키마 문자열 생성
            schema_parts = ["# Neo4j Graph Schema\n\n"]
            schema_parts.append("## Node Labels:\n")
            for label in node_labels:
                props = node_properties.get(label, [])
                props_str = ", ".join(props) if props else "(no properties)"
                schema_parts.append(f"- {label}: {{{props_str}}}")
            
            schema_parts.append("\n## Relationship Types:\n")
            for rel_type in actual_rels:
                schema_parts.append(f"- {rel_type}")
            
            return "\n".join(schema_parts)
    
    def close(self):
        """연결 종료"""
        if self.neo4j_driver:
            self.neo4j_driver.close()
            self.neo4j_driver = None


# 전역 인스턴스
db_manager = DatabaseManager()


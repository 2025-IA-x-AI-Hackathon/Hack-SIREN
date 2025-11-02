# 필요한 라이브러리 import
import os
from typing import List, Dict, Optional
from dotenv import load_dotenv
import pandas as pd
import warnings
warnings.filterwarnings('ignore')

# Neo4j
from neo4j import GraphDatabase

# Chroma
import chromadb
from chromadb.config import Settings

# Gemini API
from google import genai
from google.genai import types

load_dotenv()
print("라이브러리 로드 완료")


# Neo4j 연결 설정
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

neo4j_driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

def get_neo4j_session():
    return neo4j_driver.session()

# Neo4j 연결 확인
try:
    with get_neo4j_session() as session:
        result = session.run("RETURN 1 as test")
        print(f"✓ Neo4j 연결 성공: {NEO4J_URI}")
except Exception as e:
    print(f"✗ Neo4j 연결 실패: {e}")


# Chroma 벡터 DB 연결 (Gemini 임베딩 사용)
CHROMA_PERSIST_DIR = "data/chroma"
DOCS_DIR = "docs"

chroma_client = chromadb.PersistentClient(
    path=CHROMA_PERSIST_DIR,
    settings=Settings(anonymized_telemetry=False)
)

# Gemini 임베딩 함수는 Cell 7에서 초기화 후 사용
# 임시로 None으로 설정 (Cell 7 실행 후 업데이트 필요)
gemini_embedding_fn = None

# 컬렉션 가져오기 또는 생성
try:
    chroma_collection = chroma_client.get_collection("disaster_docs")
    print(f"✓ Chroma 컬렉션 로드 성공: {chroma_collection.count()} 문서")
except Exception as e:
    print(f"✗ Chroma 컬렉션 로드 실패: {e}")
    print("새 컬렉션 생성 및 문서 적재 중...")
    
    # Gemini 임베딩 함수가 아직 초기화되지 않았으면 임시 생성
    if gemini_embedding_fn is None:
        print("⚠ Gemini 임베딩 함수가 아직 초기화되지 않았습니다.")
        print("   Cell 7을 먼저 실행하거나, 아래 코드로 임시 초기화합니다...")
        # 임시 초기화
        GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
        if GOOGLE_API_KEY:
            temp_client = genai.Client(api_key=GOOGLE_API_KEY)
            class GeminiEmbeddingFunction:
                def __init__(self, client, model="gemini-embedding-001"):
                    self.client = client
                    self.model = model
                def __call__(self, input_texts):
                    result = self.client.models.embed_content(
                        model=self.model,
                        contents=input_texts,
                        config=types.EmbedContentConfig(
                            output_dimensionality=384  # 기존 컬렉션과 호환되도록 384차원 사용
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
            gemini_embedding_fn = GeminiEmbeddingFunction(temp_client)
            print("  ✓ 임시 Gemini 임베딩 함수 초기화 완료")
    
    # 새 컬렉션 생성 (Gemini 임베딩 함수 사용)
    chroma_collection = chroma_client.create_collection(
        name="disaster_docs",
        embedding_function=gemini_embedding_fn,
        metadata={"description": "재난 행동요령 문서 (Gemini 임베딩 사용)"}
    )
    
    # docs 폴더의 마크다운 파일 읽기 및 청킹 기반 적재
    import glob
    import re
    
    def chunk_markdown(content: str, chunk_size: int = 500, overlap: int = 100) -> List[Dict[str, str]]:
        """마크다운 파일을 청킹합니다.
        
        Args:
            content: 마크다운 내용
            chunk_size: 청크 크기 (문자 수)
            overlap: 청크 간 겹치는 부분 (문자 수)
        
        Returns:
            청크 리스트 (각 청크는 {"text": ..., "section": ...} 형태)
        """
        chunks = []
        
        # 헤더 기준으로 섹션 분할
        sections = re.split(r'(^#+\s+.+$)', content, flags=re.MULTILINE)
        
        current_section = "전체"
        current_text = ""
        
        for i, section in enumerate(sections):
            if not section.strip():
                continue
            
            # 헤더인 경우
            if re.match(r'^#+\s+.+$', section.strip()):
                # 이전 섹션이 있으면 청크로 저장
                if current_text.strip():
                    # 현재 텍스트를 청크로 분할
                    text_chunks = split_text(current_text, chunk_size, overlap)
                    for j, chunk in enumerate(text_chunks):
                        chunks.append({
                            "text": chunk,
                            "section": current_section
                        })
                
                # 새 섹션 시작
                current_section = section.strip()
                current_text = section + "\n\n"
            else:
                # 일반 텍스트 추가
                current_text += section + "\n\n"
        
        # 마지막 섹션 처리
        if current_text.strip():
            text_chunks = split_text(current_text, chunk_size, overlap)
            for j, chunk in enumerate(text_chunks):
                chunks.append({
                    "text": chunk,
                    "section": current_section
                })
        
        return chunks
    
    def split_text(text: str, chunk_size: int, overlap: int) -> List[str]:
        """텍스트를 고정 크기로 분할 (겹침 포함)
        
        Args:
            text: 분할할 텍스트
            chunk_size: 청크 크기
            overlap: 겹치는 크기
        
        Returns:
            청크 리스트
        """
        if len(text) <= chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            
            # 문장 경계에서 자르기 (가능한 경우)
            if end < len(text):
                # 문장 끝 마커 찾기
                sentence_end = max(
                    text.rfind('。', start, end),
                    text.rfind('.', start, end),
                    text.rfind('\n', start, end)
                )
                
                if sentence_end > start + chunk_size // 2:  # 너무 앞쪽이 아니면
                    end = sentence_end + 1
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            start = end - overlap  # 겹침 설정
        
        return chunks
    
    doc_files = glob.glob(f"{DOCS_DIR}/*.md")
    print(f"\n찾은 문서 파일: {len(doc_files)}개")
    
    documents = []
    ids = []
    metadatas = []
    
    chunk_counter = 0
    for doc_file in doc_files:
        try:
            with open(doc_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            filename = os.path.basename(doc_file)
            base_id = filename.replace('.md', '')
            
            # 마크다운 청킹
            chunks = chunk_markdown(content, chunk_size=500, overlap=100)
            print(f"  📄 {filename}: {len(content)}자 → {len(chunks)}개 청크")
            
            for i, chunk_info in enumerate(chunks):
                chunk_id = f"{base_id}_chunk_{i}"
                chunk_text = chunk_info["text"]
                chunk_section = chunk_info["section"]
                
                documents.append(chunk_text)
                ids.append(chunk_id)
                metadatas.append({
                    "source": filename,
                    "type": "disaster_guide",
                    "section": chunk_section,
                    "chunk_index": i,
                    "chunk_count": len(chunks)
                })
                chunk_counter += 1
                
        except Exception as e:
            print(f"  ✗ {doc_file} 적재 실패: {e}")
    
    # Chroma에 문서 추가 (Gemini 임베딩 자동 생성)
    if documents:
        # 배치 처리 (한 번에 너무 많이 추가하지 않도록)
        batch_size = 100
        for i in range(0, len(documents), batch_size):
            batch_docs = documents[i:i+batch_size]
            batch_ids = ids[i:i+batch_size]
            batch_metas = metadatas[i:i+batch_size]
            
            chroma_collection.add(
                documents=batch_docs,
                ids=batch_ids,
                metadatas=batch_metas
            )
            print(f"  ✓ 배치 {i//batch_size + 1} 적재 완료 ({len(batch_docs)}개 청크)")
        
        print(f"\n✓ 총 {chunk_counter}개 청크를 Chroma에 적재했습니다 (원본 {len(doc_files)}개 파일, Gemini 임베딩 사용).")
    else:
        print("\n✗ 적재할 문서가 없습니다.")


# Neo4j 데이터 적재 함수 (배치 처리로 성능 향상)
def load_neo4j_data(nodes_csv: str, relationships_csv: str, session):
    """CSV 파일에서 Neo4j로 데이터를 적재합니다."""
    
    # 기존 데이터 삭제
    session.run("MATCH (n) DETACH DELETE n")
    print("✓ 기존 데이터 삭제 완료")
    
    # 노드 CSV 읽기
    nodes_df = pd.read_csv(nodes_csv, encoding='utf-8-sig')
    print(f"\n노드 CSV 로드: {len(nodes_df)}개")
    
    # 노드 타입별로 배치 적재
    node_types = nodes_df['type'].unique()
    
    for node_type in node_types:
        type_nodes = nodes_df[nodes_df['type'] == node_type]
        print(f"\n{node_type} 노드 적재 중... ({len(type_nodes)}개)")
        
        # 배치 크기 설정
        batch_size = 100
        
        for batch_start in range(0, len(type_nodes), batch_size):
            batch_end = min(batch_start + batch_size, len(type_nodes))
            batch = type_nodes.iloc[batch_start:batch_end]
            
            # 배치별 쿼리 생성
            queries = []
            for _, row in batch.iterrows():
                props = {}
                for col in type_nodes.columns:
                    if col not in ['id', 'type'] and pd.notna(row[col]):
                        value = row[col]
                        # 숫자 변환 시도
                        try:
                            if isinstance(value, (int, float)) or (isinstance(value, str) and value.replace('.', '').replace('-', '').isdigit()):
                                value = float(value) if '.' in str(value) else int(float(value))
                        except:
                            pass
                        props[col] = value
                
                # CREATE 쿼리 작성
                prop_strs = [f"{k}: ${k}" for k in props.keys()]
                create_props = ", ".join(["id: $id"] + prop_strs)
                query = f"CREATE (n:{node_type} {{{create_props}}})"
                params = {"id": row['id'], **props}
                queries.append((query, params))
            
            # 배치 실행
            for query, params in queries:
                try:
                    session.run(query, **params)
                except Exception as e:
                    print(f"  ⚠ 오류: {params.get('id')} - {e}")
            
            if (batch_start // batch_size + 1) % 10 == 0:
                print(f"  진행 중: {batch_end}/{len(type_nodes)} ({batch_end*100//len(type_nodes)}%)")
        
        print(f"  ✓ {node_type} 노드 적재 완료")
    
    # 관계 CSV 읽기 및 배치 적재
    relationships_df = pd.read_csv(relationships_csv, encoding='utf-8-sig')
    print(f"\n관계 CSV 로드: {len(relationships_df)}개")
    
    batch_size = 500
    for batch_start in range(0, len(relationships_df), batch_size):
        batch_end = min(batch_start + batch_size, len(relationships_df))
        batch = relationships_df.iloc[batch_start:batch_end]
        
        for _, rel in batch.iterrows():
            query = f"""
            MATCH (from:{rel['from_type']} {{id: $from_id}})
            MATCH (to:{rel['to_type']} {{id: $to_id}})
            MERGE (from)-[:{rel['relationship_type']}]->(to)
            """
            try:
                session.run(query, from_id=rel['from_id'], to_id=rel['to_id'])
            except Exception as e:
                print(f"  ⚠ 관계 오류: {rel['from_id']} -> {rel['to_id']} - {e}")
        
        if (batch_start // batch_size + 1) % 5 == 0:
            print(f"  진행 중: {batch_end}/{len(relationships_df)} ({batch_end*100//len(relationships_df)}%)")
    
    print(f"  ✓ 관계 적재 완료: {len(relationships_df)}개")
    
    # 최종 통계
    node_count = session.run("MATCH (n) RETURN count(n) as count").single()["count"]
    rel_count = session.run("MATCH ()-[r]->() RETURN count(r) as count").single()["count"]
    print(f"\n✓ Neo4j 데이터 적재 완료: 노드 {node_count}개, 관계 {rel_count}개")

# 데이터 상태 확인 및 적재
with get_neo4j_session() as session:
    # 현재 상태 확인
    node_count = session.run("MATCH (n) RETURN count(n) as count").single()["count"]
    rel_count = session.run("MATCH ()-[r]->() RETURN count(r) as count").single()["count"]
    
    # 예상 데이터 개수 (CSV 확인) - preprocessing02.ipynb 결과 사용
    # preprocessing02.ipynb에서 생성한 완전한 그래프 스키마 사용
    NODES_CSV = "data/processed/neo4j_nodes_complete.csv"
    REL_CSV = "data/processed/neo4j_relationships_complete.csv"
    
    expected_nodes = 0
    expected_rels = 0
    
    if os.path.exists(NODES_CSV):
        nodes_df = pd.read_csv(NODES_CSV, encoding='utf-8-sig')
        expected_nodes = len(nodes_df)
    
    if os.path.exists(REL_CSV):
        rels_df = pd.read_csv(REL_CSV, encoding='utf-8-sig')
        expected_rels = len(rels_df)
    
    print(f"\n{'='*60}")
    print("Neo4j 데이터 상태 확인")
    print(f"{'='*60}")
    print(f"현재 노드: {node_count}개 (예상: {expected_nodes}개)")
    print(f"현재 관계: {rel_count}개 (예상: {expected_rels}개)")
    
    # 데이터가 없거나 불완전한 경우 적재
    if node_count == 0 or node_count < expected_nodes * 0.9:  # 90% 미만이면 재적재
        if node_count > 0:
            print(f"\n⚠ 데이터가 불완전합니다. 재적재를 진행합니다...")
        else:
            print(f"\n데이터 적재 시작...")
        
        if os.path.exists(NODES_CSV) and os.path.exists(REL_CSV):
            load_neo4j_data(NODES_CSV, REL_CSV, session)
        else:
            print(f"\n✗ CSV 파일을 찾을 수 없습니다:")
            print(f"  - {NODES_CSV}")
            print(f"  - {REL_CSV}")
            print("  먼저 preprocessing02.ipynb를 실행하여 데이터를 생성하세요.")
    else:
        print(f"\n✓ Neo4j 데이터가 정상적으로 적재되어 있습니다.")
        
        # 노드 타입별 통계
        print("\n노드 타입별 통계:")
        for label in session.run("CALL db.labels()").values():
            label_name = label[0]
            count = session.run(f"MATCH (n:{label_name}) RETURN count(n) as count").single()["count"]
            print(f"  - {label_name}: {count}개")
        
        # 관계 통계 확인
        print("\n관계 통계:")
        rel_stats = session.run("""
        MATCH ()-[r]->()
        RETURN type(r) as rel_type, count(r) as count
        ORDER BY count DESC
        """).data()
        for stat in rel_stats:
            print(f"  - {stat['rel_type']}: {stat['count']}개")
        
        # 예시: 강남구 관계 확인 (IN 관계)
        print("\n강남구 관계 확인 (예시):")
        gangnam_test = session.run("""
        MATCH (s:Shelter)-[r:IN]->(a:Admin {gu: '강남구'})
        RETURN count(s) as shelter_count
        """).single()
        if gangnam_test:
            print(f"  - 강남구 Shelter 노드 수 (IN 관계): {gangnam_test['shelter_count']}개")
        else:
            print("  - 강남구 관계를 찾을 수 없습니다.")


# Gemini API 클라이언트 설정
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY 환경변수를 설정해주세요.")

gemini_client = genai.Client(api_key=GOOGLE_API_KEY)
print("✓ Gemini API 클라이언트 초기화 완료")

# Gemini 임베딩 함수 정의
class GeminiEmbeddingFunction:
    """Chroma용 Gemini 임베딩 함수"""
    
    def __init__(self, client: genai.Client, model: str = "gemini-embedding-001"):
        self.client = client
        self.model = model
    
    def __call__(self, input_texts: List[str]) -> List[List[float]]:
        """텍스트 리스트를 임베딩으로 변환"""
        try:
            # 기존 Chroma 컬렉션이 384차원을 기대하므로 명시적으로 지정
            result = self.client.models.embed_content(
                model=self.model,
                contents=input_texts,
                config=types.EmbedContentConfig(
                    output_dimensionality=384  # 기존 컬렉션과 호환되도록 384차원 사용
                )
            )
            # embeddings 리스트 반환
            # result.embeddings는 임베딩 객체 리스트
            embeddings = []
            for embedding in result.embeddings:
                # 임베딩 객체에서 벡터 값 추출
                if hasattr(embedding, 'values'):
                    # Embedding 객체인 경우
                    embeddings.append(list(embedding.values))
                elif isinstance(embedding, list):
                    # 이미 리스트인 경우
                    embeddings.append(embedding)
                elif hasattr(embedding, '__iter__') and not isinstance(embedding, str):
                    # 반복 가능한 객체인 경우
                    embeddings.append(list(embedding))
                else:
                    # 기타 경우 (단일 값 등)
                    embeddings.append([float(embedding)])
            return embeddings
        except Exception as e:
            print(f"임베딩 생성 오류: {e}")
            raise

# Gemini 임베딩 함수 인스턴스 생성
gemini_embedding_fn = GeminiEmbeddingFunction(gemini_client)
print("✓ Gemini 임베딩 함수 초기화 완료")


def get_neo4j_schema(session) -> str:
    """Neo4j 그래프 스키마 정보를 가져옵니다 (preprocessing02.ipynb의 완전한 스키마 포함)."""
    
    # 노드 라벨 조회
    node_labels_query = "CALL db.labels()"
    node_labels = [record["label"] for record in session.run(node_labels_query)]
    
    # 관계 타입 조회
    rel_types_query = "CALL db.relationshipTypes()"
    rel_types = [record["relationshipType"] for record in session.run(rel_types_query)]
    
    # 실제로 사용되는 관계 타입만 필터링
    # preprocessing02.ipynb에서 생성한 관계 타입들: IN, GUIDES, TRIGGERS, CAUSES, INCREASES_RISK_OF, UPDATES 등
    actual_rels = []
    rel_counts = {}
    for rel_type in rel_types:
        count = session.run(f"MATCH ()-[r:{rel_type}]->() RETURN count(r) as count").single()["count"]
        if count > 0:  # 실제로 데이터가 있는 관계만 포함
            actual_rels.append(rel_type)
            rel_counts[rel_type] = count
    
    # 노드별 속성 정보 조회
    node_properties = {}
    for label in node_labels:
        props_query = f"""
        MATCH (n:{label})
        RETURN keys(n) as props
        LIMIT 1
        """
        result = session.run(props_query)
        record = result.single()
        if record:
            node_properties[label] = record["props"]
    
    # 스키마 문자열 생성
    schema_parts = ["# Neo4j Graph Schema (Complete from preprocessing02.ipynb)\n\n"]
    
    schema_parts.append("## Node Labels:\n")
    for label in sorted(node_labels):
        props = node_properties.get(label, [])
        # 주요 속성만 표시 (너무 길지 않도록)
        key_props = [p for p in props if p not in ['id', 'type']][:10]
        props_str = ", ".join(key_props) if key_props else "id, type"
        schema_parts.append(f"- {label}: {{id, type, {props_str}...}}")
    
    schema_parts.append("\n## Relationship Types:\n")
    # preprocessing02.ipynb에서 생성한 관계 타입들을 포함하여 표시
    # 중요 관계 타입 우선 표시
    important_rels = ['GUIDES', 'TRIGGERS', 'CAUSES', 'INCREASES_RISK_OF', 'UPDATES', 'IN']
    for rel_type in important_rels:
        if rel_type in actual_rels:
            schema_parts.append(f"- {rel_type} ({rel_counts[rel_type]}개)")
    
    # 나머지 관계 타입
    for rel_type in sorted(actual_rels):
        if rel_type not in important_rels:
            schema_parts.append(f"- {rel_type} ({rel_counts[rel_type]}개)")
    
    return "\n".join(schema_parts)

# 스키마 정보 확인
with get_neo4j_session() as session:
    schema = get_neo4j_schema(session)
    print(schema)


def generate_cypher_query(question: str, schema: str) -> str:
    """Ollama를 사용하여 자연어 질문을 Cypher 쿼리로 변환합니다 (preprocessing02.ipynb의 완전한 스키마 지원)."""
    
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
        response = gemini_client.models.generate_content(
            model='gemini-2.5-flash',
            config=types.GenerateContentConfig(
                thinking_config=types.ThinkingConfig(
                    include_thoughts=False
                )
            ),
            contents=prompt.strip()
        )
        cypher_query = response.text.strip()
        # 코드 블록 제거 (```cypher 등)
        if cypher_query.startswith("```"):
            lines = cypher_query.split("\n")
            cypher_query = "\n".join(lines[1:-1]) if len(lines) > 2 else cypher_query
        
        return cypher_query
    except Exception as e:
        print(f"Cypher 쿼리 생성 오류: {e}")
        return None


def graph_rag_search(question: str, schema: str, session) -> Dict:
    """Graph RAG 검색: Neo4j에서 구조화된 정보를 검색합니다."""
    
    # 1. Cypher 쿼리 생성
    cypher_query = generate_cypher_query(question, schema)
    
    if not cypher_query:
        return {"query": None, "results": [], "count": 0, "error": "Cypher 쿼리 생성 실패"}
    
    print(f"\n[생성된 Cypher 쿼리]\n{cypher_query}\n")
    
    # 2. 쿼리 실행
    try:
        result = session.run(cypher_query)
        records = [dict(record) for record in result]
        
        # COUNT 등의 집계 함수 결과 처리
        # 집계 쿼리는 단일 레코드를 반환하므로, 결과 값 자체를 카운트로 사용
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


def vector_rag_search(question: str, collection, client: genai.Client, top_k: int = 5) -> Dict:
    """Vector RAG 검색: Chroma에서 관련 문서를 검색합니다 (Gemini 임베딩 사용)."""
    
    if collection is None:
        return {"results": [], "error": "Chroma 컬렉션이 없습니다."}
    
    try:
        # Gemini를 사용하여 질문을 임베딩으로 변환
        try:
            embedding_result = client.models.embed_content(
                model="gemini-embedding-001",
                contents=[question],
                config=types.EmbedContentConfig(
                    output_dimensionality=384  # 기존 컬렉션과 호환되도록 384차원 사용
                )
            )
            
            # 임베딩 벡터 추출 (예제 코드 참고)
            query_embedding = None
            if embedding_result.embeddings:
                embedding = embedding_result.embeddings[0]
                # 임베딩 객체에서 벡터 값 추출
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
            
            # Chroma에서 임베딩 기반 검색
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k
            )
        except Exception as embed_error:
            # Gemini 임베딩 실패 시, Chroma의 기본 임베딩 함수 사용 (텍스트 기반)
            print(f"  ⚠ Gemini 임베딩 실패, 텍스트 기반 검색으로 전환: {embed_error}")
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


def format_graph_results(graph_results: Dict, max_length: int = 2000) -> str:
    """Graph RAG 결과를 텍스트로 포맷팅합니다."""
    
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


def format_vector_results(vector_results: Dict, max_length: int = 3000) -> str:
    """Vector RAG 결과를 텍스트로 포맷팅합니다."""
    
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


def extract_shelter_info(graph_results: Dict, question: str = "") -> str:
    """Graph RAG 결과에서 대피소 정보를 추출하여 형식화된 답변을 생성합니다."""
    
    if not graph_results.get("results"):
        return None
    
    results = graph_results["results"]
    count = graph_results.get("count", 0)
    
    # Shelter 노드 정보 추출
    shelters = []
    
    for record in results:
        # record는 딕셔너리 형태: {'s': <Node ...>} 또는 {'name': '...', 'address': '...'} 등
        for key, value in record.items():
            # Neo4j Node 객체인 경우 (properties 속성이 있음)
            if hasattr(value, 'properties'):
                try:
                    props = value.properties
                    # Shelter 노드인지 확인 (labels 확인)
                    is_shelter = False
                    if hasattr(value, '_labels'):
                        labels = value._labels
                        is_shelter = 'Shelter' in labels or isinstance(labels, frozenset) and 'Shelter' in labels
                    elif hasattr(value, 'labels'):
                        labels = value.labels
                        is_shelter = 'Shelter' in labels
                    else:
                        # labels 속성이 없으면 문자열로 확인
                        value_str = str(value)
                        is_shelter = 'Shelter' in value_str or 'shelter' in key.lower()
                    
                    if is_shelter or 'name' in props or 'address' in props:  # Shelter 속성이 있으면 추가
                        shelter_name = props.get('name', '이름 없음')
                        shelter_address = props.get('address', '주소 없음')
                        shelter_type = props.get('shelter_type', '')
                        # 실제 값이 있는 경우만 추가
                        if shelter_name != '이름 없음' or shelter_address != '주소 없음':
                            shelters.append({
                                'name': shelter_name,
                                'address': shelter_address,
                                'type': shelter_type
                            })
                except Exception as e:
                    # properties 접근 실패 시 무시
                    pass
            # 딕셔너리인 경우 (직접 속성이 있는 경우 또는 dict(record)로 변환된 경우)
            elif isinstance(value, dict):
                if 'name' in value or 'address' in value or 'shelter_type' in value:
                    shelters.append({
                        'name': value.get('name', value.get('s.name', '이름 없음')),
                        'address': value.get('address', value.get('s.address', '주소 없음')),
                        'type': value.get('shelter_type', value.get('s.shelter_type', ''))
                    })
        # record 자체가 속성 딕셔너리인 경우 (RETURN s.name, s.address 같은 쿼리)
        # 모든 값을 확인했는데도 shelters에 추가되지 않은 경우
        if isinstance(record, dict):
            # record의 직접 속성 확인 (RETURN s.name 같은 경우)
            if 'name' in record or 'address' in record:
                record_name = record.get('name', record.get('s.name', ''))
                record_address = record.get('address', record.get('s.address', ''))
                if record_name or record_address:
                    # 중복 체크
                    is_duplicate = any(
                        s.get('name') == record_name and s.get('address') == record_address 
                        for s in shelters
                    )
                    if not is_duplicate:
                        shelters.append({
                            'name': record_name if record_name else '이름 없음',
                            'address': record_address if record_address else '주소 없음',
                            'type': record.get('shelter_type', record.get('s.shelter_type', ''))
                        })
    
    # Shelter 정보가 없으면 None 반환
    if not shelters:
        # 디버깅: 결과 구조 확인
        if results:
            print(f"  ⚠ 대피소 정보 추출 실패: 결과 {len(results)}개, 첫 번째 결과 타입: {type(results[0])}")
            if isinstance(results[0], dict):
                print(f"    첫 번째 결과 키: {list(results[0].keys())}")
                for key, value in list(results[0].items())[:3]:  # 처음 3개만
                    print(f"    - {key}: {type(value)}")
        return None
    
    # 중복 제거 (name과 address가 같은 경우)
    unique_shelters = []
    seen = set()
    for shelter in shelters:
        # '이름 없음'이나 '주소 없음'은 제외
        if shelter['name'] != '이름 없음' and shelter['address'] != '주소 없음':
            key = (shelter['name'], shelter['address'])
            if key not in seen:
                seen.add(key)
                unique_shelters.append(shelter)
    
    # 중복 제거 후에도 없으면 None
    if not unique_shelters:
        return None
    
    # 최대 10개만 표시
    display_shelters = unique_shelters[:10]
    remaining_count = len(unique_shelters) - len(display_shelters)
    
    # 질문에서 구 이름 추출
    import re
    gu_match = re.search(r'(강남구|서초구|송파구|강동구|광진구|성동구|중랑구|동대문구|성북구|강북구|노원구|도봉구|은평구|서대문구|마포구|용산구|종로구|중구|영등포구|양천구|강서구|구로구|금천구|관악구)', question)
    gu_name = gu_match.group(1) if gu_match else ""
    
    # 답변 생성
    answer_parts = []
    
    if count > 0:
        if gu_name:
            answer_parts.append(f"{gu_name}에 총 {count}개의 대피소를 찾았습니다.\n")
        else:
            answer_parts.append(f"총 {count}개의 대피소를 찾았습니다.\n")
    elif len(unique_shelters) > 0:
        if gu_name:
            answer_parts.append(f"{gu_name}에 총 {len(unique_shelters)}개의 대피소를 찾았습니다.\n")
        else:
            answer_parts.append(f"총 {len(unique_shelters)}개의 대피소를 찾았습니다.\n")
    
    if display_shelters:
        answer_parts.append("주요 대피소 목록:")
        for i, shelter in enumerate(display_shelters, 1):
            shelter_type = shelter['type'] if shelter['type'] else '대피소'
            answer_parts.append(f"{i}. {shelter['name']} ({shelter_type})")
            if shelter['address'] and shelter['address'] != '주소 없음':
                answer_parts.append(f"   주소: {shelter['address']}")
        
        if remaining_count > 0:
            answer_parts.append(f"\n이 외에 {remaining_count}개의 대피소가 더 있습니다.")
    
    return "\n".join(answer_parts) if answer_parts else None


def hybrid_rag(question: str, schema: str, neo4j_session, chroma_collection) -> Dict:
    """Hybrid RAG: Graph RAG와 Vector RAG를 결합하여 검색하고 답변을 생성합니다."""
    
    # 1. Graph RAG 검색
    print("=" * 60)
    print("[Graph RAG 검색 중...]")
    graph_results = graph_rag_search(question, schema, neo4j_session)
    
    # 2. Vector RAG 검색
    print("\n" + "=" * 60)
    print("[Vector RAG 검색 중...]")
    vector_results = vector_rag_search(question, chroma_collection, gemini_client)
    
    # 3. 결과 포맷팅 (길이 제한)
    graph_text = format_graph_results(graph_results, max_length=2000)
    vector_text = format_vector_results(vector_results, max_length=3000)
    
    # 4. Ollama를 사용하여 최종 답변 생성
    print("\n" + "=" * 60)
    print("[Ollama를 통한 최종 답변 생성 중...]")
    print("  프롬프트 길이:", len(f"{question}\n{graph_text}\n{vector_text}"), "자")
    
    # 간결한 프롬프트 생성
    # 질문 유형에 따라 다른 지침 제공 (preprocessing02.ipynb의 완전한 스키마 활용)
    if '알려주세요' in question or '찾고 싶어요' in question or '어디' in question:
        instructions = """- Graph RAG 결과에 실제 대피소/시설 목록이 있으면 구체적인 이름과 주소를 제시하세요
- 대피소가 많으면 주요 대피소 몇 개를 예시로 제시하고, 총 개수를 알려주세요
- 간결하고 실행 가능한 답변 제공"""
    elif '행동' in question or '어떻게' in question or '요령' in question:
        instructions = """- Graph RAG 결과에 Policy(행동요령) 정보가 있으면 구체적으로 제시하세요
- Vector RAG 결과의 행동요령 문서를 참고하여 구체적인 행동 지침을 제공하세요
- 간결하고 실행 가능한 답변 제공"""
    elif '재난' in question or '위험' in question or 'Hazard' in question or '지진' in question or '산사태' in question:
        instructions = """- Graph RAG 결과에서 Hazard 노드와 관련 관계(TRIGGERS, CAUSES, INCREASES_RISK_OF)를 활용하세요
- 재난 간의 연쇄 관계를 명확히 설명하세요
- 구체적인 데이터와 근거를 제시하세요"""
    else:
        instructions = """- 구체적인 데이터(개수, 위치 등)를 명확히 제시
- Graph RAG와 Vector RAG 결과를 모두 활용하세요
- 간결하고 실행 가능한 답변 제공
- 근거를 간단히 명시"""
    
    final_prompt = f"""재난대응 전문가로서 아래 질문에 답변하세요.

질문: {question}

[Graph RAG 결과]
{graph_text}

[Vector RAG 결과]  
{vector_text}

지침:
{instructions}

답변:"""
    
    try:
        # "알려주세요", "찾고 싶어요" 같은 질문에 대해 먼저 extract_shelter_info로 구체적인 답변 생성
        graph_count = graph_results.get('count', 0)
        is_list_question = '알려주세요' in question or '찾고 싶어요' in question or ('어디' in question and graph_count > 0)
        
        extracted_info = None
        if is_list_question and graph_count > 0:
            # Graph RAG 결과에서 대피소 정보 추출
            extracted_info = extract_shelter_info(graph_results, question)
            if extracted_info:
                print(f"  ✓ 대피소 정보 추출 완료: {len(extracted_info)}자")
        
        final_answer = gemini_client.models.generate_content(
            model='gemini-2.5-flash',
            config=types.GenerateContentConfig(
                thinking_config=types.ThinkingConfig(
                    include_thoughts=False
                )
            ),
            contents=final_prompt.strip()
        )
        
        # Ollama 응답 검증: 구체적인 대피소 정보가 포함되어 있는지 확인
        if final_answer and is_list_question and extracted_info:
            # Ollama 답변에 구체적인 대피소 이름이나 주소가 포함되어 있는지 확인
            has_specific_info = any(keyword in final_answer for keyword in ['주소:', '위치:', '명', '곳', '서울', '구'])
            # Ollama 답변이 일반적인 설명만 포함하고 있으면 추출된 정보 사용
            if not has_specific_info or len(final_answer) < 100:
                print(f"  ⚠ Ollama 답변이 일반적입니다. 추출된 정보를 사용합니다.")
                final_answer = extracted_info
        
        # Ollama 응답이 None이거나 비어있는 경우 fallback 답변 생성
        if not final_answer or (isinstance(final_answer, str) and final_answer.strip() == ""):
            print("  ⚠ Ollama 응답 생성 실패: 응답이 None이거나 비어있습니다.")
            # Fallback: 추출된 정보 또는 Graph RAG 결과 기반으로 답변 생성
            
            # 질문에서 구 이름 및 키워드 추출
            import re
            gu_match = re.search(r'(강남구|서초구|송파구|강동구|광진구|성동구|중랑구|동대문구|성북구|강북구|노원구|도봉구|은평구|서대문구|마포구|용산구|종로구|중구|영등포구|양천구|강서구|구로구|금천구|관악구)', question)
            gu_name = gu_match.group(1) if gu_match else ""
            
            # 질문 유형에 따라 답변 생성
            if '몇 개' in question or '개수' in question or 'count' in question.lower():
                if graph_count > 0:
                    if gu_name:
                        final_answer = f"{gu_name}에 있는 대피소는 {graph_count}개입니다."
                    else:
                        final_answer = f"검색 결과: {graph_count}개를 찾았습니다."
                else:
                    final_answer = "검색 결과를 찾을 수 없습니다."
            elif '어디' in question or '위치' in question or '알려주세요' in question or '찾고 싶어요' in question:
                if extracted_info:
                    final_answer = extracted_info
                elif graph_count > 0:
                    final_answer = f"{gu_name if gu_name else '해당 지역'}에 있는 대피소는 총 {graph_count}개입니다. 상세 정보는 Graph RAG 결과를 참고하세요."
                else:
                    final_answer = "검색 결과를 찾을 수 없습니다."
            elif '어떻게' in question or '행동' in question:
                # Vector RAG 결과를 활용한 답변
                vector_count = vector_results.get('count', 0)
                if vector_count > 0:
                    final_answer = "Vector RAG 검색 결과에 관련 행동 요령이 포함되어 있습니다. 문서를 참고하세요."
                else:
                    final_answer = "검색 결과를 찾을 수 없습니다."
            else:
                if graph_count > 0:
                    final_answer = f"검색 결과를 {graph_count}개 찾았습니다. Graph RAG 결과를 참고하세요."
                else:
                    final_answer = "검색 결과를 찾을 수 없습니다."
            
            print(f"  ✓ Fallback 답변 생성: {final_answer[:50]}...")
        
        return {
            "question": question,
            "graph_results": graph_results,
            "vector_results": vector_results,
            "answer": final_answer
        }
    except Exception as e:
        print(f"  ⚠ 최종 답변 생성 오류: {e}")
        # Fallback 답변 생성
        graph_count = graph_results.get('count', 0)
        
        # 질문에서 구 이름 추출
        import re
        gu_match = re.search(r'(강남구|서초구|송파구|강동구|광진구|성동구|중랑구|동대문구|성북구|강북구|노원구|도봉구|은평구|서대문구|마포구|용산구|종로구|중구|영등포구|양천구|강서구|구로구|금천구|관악구)', question)
        gu_name = gu_match.group(1) if gu_match else "해당 구"
        
        if '몇 개' in question or '개수' in question:
            if graph_count > 0:
                fallback_answer = f"{gu_name}에 있는 대피소는 {graph_count}개입니다. (오류 발생으로 간단 답변)"
            else:
                fallback_answer = f"오류 발생: {str(e)}. Graph RAG 결과: {graph_count}개"
        else:
            if graph_count > 0:
                fallback_answer = f"검색 결과를 {graph_count}개 찾았습니다. (오류 발생으로 간단 답변)"
            else:
                fallback_answer = f"오류 발생: {str(e)}. Graph RAG 결과: {graph_count}개"
        
        return {
            "question": question,
            "graph_results": graph_results,
            "vector_results": vector_results,
            "answer": fallback_answer,
            "error": str(e)
        }


# 필요한 라이브러리 import
import os
import json
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Neo4j
from neo4j import GraphDatabase

# ChromaDB
import chromadb
from chromadb.config import Settings

# Gemini API
from google import genai

# 기타
import pandas as pd

# 환경 변수 로드
load_dotenv()

print("라이브러리 로드 완료")

# Neo4j 스키마 가져오기
with get_neo4j_session() as session:
    schema = get_neo4j_schema(session)
    
    # 시민 시나리오 테스트 질의 (preprocessing02.ipynb의 완전한 스키마를 활용)
    test_questions = [
        "강남구에 있는 대피소는 몇 개인가요?",
        "지진이 발생했을 때 가까운 대피소를 찾고 싶어요. 서초구 근처 대피소를 알려주세요.",
        "임시주거시설은 어디에 있나요?",
        "지진 발생 시 어떻게 행동해야 하나요?",
        "공습경보가 발령되면 어떻게 해야 하나요?",
        "서초구의 옥외대피소 중 가장 큰 시설은 어디인가요?",
        "지진이 다른 재난을 유발할 수 있나요?",
        "산사태 위험 지역 근처에 대피소가 있나요?",
        "노후 시설물이 붕괴 위험을 증가시킬 수 있나요?"
    ]
    
    # 첫 번째 질의 테스트
    question = test_questions[0]
    print(f"\n{'='*60}")
    print(f"질문: {question}")
    print(f"{'='*60}\n")
    
    result = hybrid_rag(
        question=question,
        schema=schema,
        neo4j_session=session,
        chroma_collection=chroma_collection
    )
    
    print("\n" + "=" * 60)
    print("=" * 60)
    print(result.get("answer", "답변 생성 실패"))


# Neo4j 스키마 가져오기
with get_neo4j_session() as session:
    schema = get_neo4j_schema(session)
    
    # 시민 시나리오 테스트 질의 (preprocessing02.ipynb의 완전한 스키마를 활용)
    test_questions = [
        "2025-11-02 15:00 서울특별시 동남쪽 2km 지역 M6.3 지진 / 낙하물, 여진주의  국민재난안전포털 참고 대응",
        "지진이 발생했을 때 가까운 대피소를 찾고 싶어요. 서초구 근처 대피소를 알려주세요.",
        "지진 발생 시 어떻게 행동해야 하나요?",
        "노후 시설물이 붕괴 위험을 증가시킬 수 있나요?"
    ]
    
    # 첫 번째 질의 테스트
    question = test_questions[0]
    print(f"\n{'='*60}")
    print(f"질문: {question}")
    print(f"{'='*60}\n")
    
    result = hybrid_rag(
        question=question,
        schema=schema,
        neo4j_session=session,
        chroma_collection=chroma_collection
    )
    
    print("\n" + "=" * 60)
    print("=" * 60)
    print(result.get("answer", "답변 생성 실패"))


# 여러 질의 일괄 실행
with get_neo4j_session() as session:
    schema = get_neo4j_schema(session)
    
    results = []
    for i, question in enumerate(test_questions, 1):
        print(f"\n\n{'#'*60}")
        print(f"질의 {i}/{len(test_questions)}: {question}")
        print(f"{'#'*60}\n")
        
        result = hybrid_rag(
            question=question,
            schema=schema,
            neo4j_session=session,
            chroma_collection=chroma_collection
        )
        
        results.append(result)
        
        print(f"\n{'='*60}")
        print("[최종 답변]")
        print(f"{'='*60}")
        print(result)
        print(result.get("answer", "답변 생성 실패"))
        print(f"\n{'='*60}\n")


# 결과 요약
print("\n" + "="*60)
print("# Hybrid RAG 검색 결과 요약")
print("="*60 + "\n")

for i, result in enumerate(results, 1):
    question = result.get("question", "N/A")
    graph_count = result.get("graph_results", {}).get("count", 0)
    vector_count = result.get("vector_results", {}).get("count", 0)
    has_answer = result.get("answer") is not None
    
    print(f"질의 {i}: {question}")
    print(f"  - Graph RAG: {graph_count}개 결과")
    print(f"  - Vector RAG: {vector_count}개 결과")
    print(f"  - 최종 답변: {'✓ 생성됨' if has_answer else '✗ 생성 실패'}")
    print(result.get("answer", "답변 생성 실패"))
    print()


# 필요한 라이브러리 import
import os
import json
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Neo4j
from neo4j import GraphDatabase

# ChromaDB
import chromadb
from chromadb.config import Settings

# Gemini API
from google import genai

# 기타
import pandas as pd

# 환경 변수 로드
load_dotenv()

print("라이브러리 로드 완료")

# Neo4j 연결 종료
neo4j_driver.close()
print("✓ Neo4j 연결 종료")

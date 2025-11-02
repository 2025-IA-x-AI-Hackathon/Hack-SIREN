"""AdvisorAgent - 관찰 및 추론 결과 생성 (노트북 기반)"""
from typing import Dict, List, Optional, Any
import logging
import asyncio
from google import genai
from config import GOOGLE_API_KEY, GEMINI_MODEL
from models import (
    AdvisoryResult,
    PlanningResult, AnalysisResult
)

logger = logging.getLogger(__name__)


class AdvisorAgent:
    """관찰 및 추론 결과 생성 에이전트"""
    
    def __init__(self):
        self.client = genai.Client(api_key=GOOGLE_API_KEY)
    
    async def infer(
        self,
        input_text: str,
        profile: Optional[Any] = None,
        planning: PlanningResult = None,
        analysis: AnalysisResult = None,
        location_info: Optional[Dict] = None
    ) -> AdvisoryResult:
        """검색 결과를 관찰하고 추론 수행 (노트북 기반)"""
        
        logger.info(f"[AdvisorAgent] 관찰 및 추론 시작: {input_text[:100]}...")
        
        # 노트북의 format_graph_results, format_vector_results 구조 사용
        graph_text = self._format_graph_results(analysis.graph_results, max_length=2000)
        vector_text = self._format_vector_results(analysis.vector_results, max_length=3000)
        
        # 위치 정보 추가
        location_context = ""
        if location_info:
            location_context = f"""
위치 정보:
- 위도: {location_info.get('lat')}
- 경도: {location_info.get('lon')}
- 검색 반경: {location_info.get('radius_km', 5.0)}km
"""
        
        # 노트북의 hybrid_rag 프롬프트 구조 사용 (행동 지침이 아닌 관찰과 추론만)
        prompt = f"""검색 결과를 관찰하고 추론만 수행하세요. 행동 지침이나 권장 사항을 제시하지 마세요.

사용자 입력:
{input_text}

{location_context}

[Graph RAG 검색 결과]
{graph_text}

[Vector RAG 검색 결과]  
{vector_text}

**작업:**
1. Graph RAG와 Vector RAG 검색 결과를 상세히 관찰
2. 관찰한 정보를 바탕으로 추론 수행
3. 직접 명시된 정보와 관계를 통한 간접 정보 모두 포함
4. 정보의 출처(Graph RAG인지 Vector RAG인지) 명시
5. 불완전하거나 불확실한 정보도 명시

**중요:**
- 행동 지침이나 권장 사항을 제시하지 마세요
- 관찰한 사실과 추론 결과만 제공하세요
- "~해야 합니다", "~하세요" 같은 지시문 사용 금지
- "~입니다", "~으로 확인됩니다", "~을 관찰했습니다" 같은 관찰/추론 표현 사용

다음 JSON 형식으로 응답하세요:
{{
    "conclusion": "관찰한 정보를 바탕으로 추론한 핵심 결과를 3-5문장으로 정리. 사실 기반 서술만 사용 (행동 지침 제외)",
    "evidence": "관찰한 구체적 정보와 추론 근거:\n1. Graph RAG에서 관찰한 정보: [구체적 데이터]\n2. Vector RAG에서 관찰한 정보: [구체적 내용]\n3. 추론 과정: [관찰한 정보를 어떻게 연결하여 추론했는지]\n각 근거는 검색 결과에서 직접 확인한 정보만 포함"
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
            result_dict = parse_json_from_text(text)
            
            if not result_dict:
                # 기본 추론 결과 (관찰할 정보가 아직 없는 경우)
                logger.warning("[AdvisorAgent] LLM 응답 파싱 실패, 기본 결과 사용")
                result_dict = {
                    "conclusion": "검색 결과에서 아직 관찰할 정보가 확인되지 않았습니다.",
                    "evidence": "Graph RAG와 Vector RAG 검색 결과에서 관찰할 수 있는 정보가 없었습니다."
                }
            else:
                conclusion_preview = result_dict.get("conclusion", "")[:100] if result_dict.get("conclusion") else ""
                logger.info(f"[AdvisorAgent] 추론 완료: {conclusion_preview}...")
            
            # conclusion을 문자열로 변환
            conclusion = result_dict.get("conclusion", "")
            if isinstance(conclusion, list):
                conclusion = "\n".join(str(item) for item in conclusion)
            elif not isinstance(conclusion, str):
                conclusion = str(conclusion)
            
            # evidence를 문자열로 변환
            evidence = result_dict.get("evidence", "")
            if isinstance(evidence, list):
                evidence = "\n".join(str(item) for item in evidence)
            elif not isinstance(evidence, str):
                evidence = str(evidence)
            
            # evidence에 대피소 정보 추가 (위치 정보가 있을 때)
            if location_info:
                nearby_shelters = self._find_nearby_shelters(
                    analysis.graph_results,
                    location_info["lat"],
                    location_info["lon"],
                    location_info.get("radius_km", 5.0)
                )
                if nearby_shelters:
                    shelter_info = "\n주변 안전 거점 (반경 내 대피소):\n"
                    for i, shelter in enumerate(nearby_shelters[:5], 1):
                        name = shelter.get('name', '대피소')
                        address = shelter.get('address', '')
                        distance = shelter.get('distance_km', '')
                        shelter_type = shelter.get('shelter_type', '대피소')
                        shelter_info += f"{i}. {name} ({shelter_type})"
                        if address:
                            shelter_info += f" - {address}"
                        if distance:
                            shelter_info += f" [거리: {distance}km]"
                        shelter_info += "\n"
                    evidence = evidence + "\n\n" + shelter_info if evidence else shelter_info
            
            logger.info(f"[AdvisorAgent] 관찰 및 추론 완료")
            return AdvisoryResult(
                conclusion=conclusion,
                evidence=evidence
            )
        except Exception as e:
            # Fallback 추론 결과 (오류 발생)
            logger.error(f"[AdvisorAgent] 추론 오류: {str(e)}")
            return AdvisoryResult(
                conclusion=f"관찰 및 추론 과정에서 오류가 발생했습니다: {str(e)}. 아직 관찰할 정보가 확인되지 않았습니다.",
                evidence=""
            )
    
    def _format_graph_results(self, graph_results: Dict, max_length: int = 2000) -> str:
        """Graph RAG 결과 포맷팅 (노트북 구조)"""
        if graph_results.get("error"):
            return f"오류: {graph_results['error']}"
        
        result_count = graph_results.get('count', 0)
        result_parts = ["# Graph RAG 검색 결과\n"]
        result_parts.append(f"Cypher 쿼리: {graph_results.get('query', 'N/A')}\n")
        result_parts.append(f"결과 개수: {result_count}\n")
        
        if not graph_results.get("results"):
            result_parts.append("\n아직 검색 결과가 확인되지 않았습니다.")
        else:
            results = graph_results["results"]
            if len(results) > 20:
                result_parts.append(f"\n## 요약: 총 {len(results)}개 결과 중 처음 10개만 표시\n")
                results = results[:10]
            
            for i, record in enumerate(results, 1):
                result_parts.append(f"\n## 결과 {i}")
                for key, value in record.items():
                    value_str = str(value)
                    if len(value_str) > 200:
                        value_str = value_str[:200] + "..."
                    result_parts.append(f"- {key}: {value_str}")
        
        text = "\n".join(result_parts)
        if len(text) > max_length:
            text = text[:max_length] + "\n\n[이하 생략 - 결과가 너무 많습니다]"
        
        return text
    
    def _format_vector_results(self, vector_results: Dict, max_length: int = 3000) -> str:
        """Vector RAG 결과 포맷팅 (노트북 구조)"""
        if vector_results.get("error"):
            return f"오류: {vector_results['error']}"
        
        if not vector_results.get("results"):
            return "아직 검색 결과가 확인되지 않았습니다."
        
        result_parts = ["# Vector RAG 검색 결과\n"]
        result_parts.append(f"결과 개수: {vector_results.get('count', 0)}\n")
        
        for i, doc in enumerate(vector_results["results"], 1):
            result_parts.append(f"\n## 문서 {i} (거리: {doc.get('distance', 'N/A')})")
            doc_text = doc.get('text', '')
            if len(doc_text) > 800:
                doc_text = doc_text[:800] + "..."
            result_parts.append(doc_text)
        
        text = "\n".join(result_parts)
        if len(text) > max_length:
            text = text[:max_length] + "\n\n[이하 생략]"
        
        return text
    
    def _extract_places_reference(self, graph_results: Dict, location_info: Optional[Dict] = None) -> Optional[Dict[str, Dict[str, Any]]]:
        """Graph RAG 결과에서 장소(대피소) 정보를 추출하여 레퍼런스로 구성
        
        Returns:
            장소 레퍼런스 딕셔너리
            {
                "장소_이름_1": {
                    "name": "대피소 이름",
                    "address": "주소",
                    "lat": 위도,
                    "lon": 경도,
                    "type": "대피소 유형",
                    "distance_km": 거리 (있는 경우),
                    "source": "Graph RAG"
                },
                ...
            }
        """
        places_ref = {}
        
        try:
            results = graph_results.get("results", [])
            if not results:
                return None
            
            # 거리 계산 함수 (있는 경우)
            def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
                """두 지점 간 거리 계산 (km)"""
                from math import radians, sin, cos, sqrt, atan2
                R = 6371  # 지구 반경 (km)
                lat1_rad = radians(lat1)
                lat2_rad = radians(lat2)
                delta_lat = radians(lat2 - lat1)
                delta_lon = radians(lon2 - lon1)
                a = sin(delta_lat/2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(delta_lon/2)**2
                c = 2 * atan2(sqrt(a), sqrt(1-a))
                return R * c
            
            user_lat = location_info.get("lat") if location_info else None
            user_lon = location_info.get("lon") if location_info else None
            
            for record in results:
                place_info = {}
                place_lat = None
                place_lon = None
                
                # Neo4j Node 객체 또는 딕셔너리에서 장소 정보 추출
                for key, value in record.items():
                    # Neo4j Node 객체인 경우
                    if hasattr(value, 'properties'):
                        props = value.properties
                        if isinstance(props, dict):
                            place_info['name'] = props.get('name', '')
                            place_info['address'] = props.get('address', '')
                            place_info['type'] = props.get('shelter_type', props.get('type', ''))
                            if 'lat' in props and 'lon' in props:
                                place_lat = float(props['lat'])
                                place_lon = float(props['lon'])
                                place_info['lat'] = place_lat
                                place_info['lon'] = place_lon
                    # 딕셔너리인 경우
                    elif isinstance(value, dict):
                        if 'name' in value or 'address' in value:
                            place_info['name'] = value.get('name', '')
                            place_info['address'] = value.get('address', '')
                            place_info['type'] = value.get('shelter_type', value.get('type', ''))
                            if 'lat' in value and 'lon' in value:
                                place_lat = float(value['lat'])
                                place_lon = float(value['lon'])
                                place_info['lat'] = place_lat
                                place_info['lon'] = place_lon
                    # 직접 속성인 경우
                    elif key in ['name', 's.name'] or key.endswith('.name'):
                        place_info['name'] = str(value) if value else ''
                    elif key in ['address', 's.address'] or key.endswith('.address'):
                        place_info['address'] = str(value) if value else ''
                    elif key in ['lat', 's.lat'] or key.endswith('.lat'):
                        try:
                            place_lat = float(value)
                            place_info['lat'] = place_lat
                        except:
                            pass
                    elif key in ['lon', 's.lon'] or key.endswith('.lon'):
                        try:
                            place_lon = float(value)
                            place_info['lon'] = place_lon
                        except:
                            pass
                    elif key in ['shelter_type', 's.shelter_type'] or key.endswith('.shelter_type'):
                        place_info['type'] = str(value) if value else ''
                
                # 장소 정보가 있는 경우 레퍼런스에 추가
                place_name = place_info.get('name', '')
                if place_name and place_name not in ['', '이름 없음', 'None']:
                    # 거리 계산 (사용자 위치와 장소 좌표가 모두 있는 경우)
                    if user_lat and user_lon and place_lat and place_lon:
                        distance = haversine_distance(user_lat, user_lon, place_lat, place_lon)
                        place_info['distance_km'] = round(distance, 2)
                    
                    place_info['source'] = 'Graph RAG'
                    
                    # 키는 이름으로 사용, 중복 방지를 위해 이름+주소 조합 사용
                    place_key = place_name
                    if place_info.get('address'):
                        place_key = f"{place_name}_{place_info['address'][:20]}"  # 주소 일부를 키에 포함
                    
                    # 중복 방지: 이미 같은 이름과 주소가 있으면 스킵
                    if place_key not in places_ref:
                        places_ref[place_key] = place_info
                    elif place_info.get('lat') and place_info.get('lon'):
                        # 좌표가 있는 것을 우선 (더 정확한 정보)
                        existing = places_ref[place_key]
                        if not (existing.get('lat') and existing.get('lon')):
                            places_ref[place_key] = place_info
            
            return places_ref if places_ref else None
            
        except Exception as e:
            logger.warning(f"[AdvisorAgent] 장소 레퍼런스 추출 오류: {e}")
            return None
    
    def _find_nearby_shelters(self, graph_results: Dict, lat: float, lon: float, radius_km: float) -> List[Dict[str, Any]]:
        """반경 내 대피소 찾기 (Graph RAG 결과 활용)"""
        shelters = []
        
        try:
            results = graph_results.get("results", [])
            if not results:
                return shelters
            
            # Haversine 거리 계산 함수
            from math import radians, sin, cos, sqrt, atan2
            
            def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
                """두 지점 간 거리 계산 (km)"""
                R = 6371  # 지구 반경 (km)
                lat1_rad = radians(lat1)
                lat2_rad = radians(lat2)
                delta_lat = radians(lat2 - lat1)
                delta_lon = radians(lon2 - lon1)
                a = sin(delta_lat/2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(delta_lon/2)**2
                c = 2 * atan2(sqrt(a), sqrt(1-a))
                return R * c
            
            for record in results:
                shelter_info = {}
                shelter_lat = None
                shelter_lon = None
                
                for key, value in record.items():
                    # Neo4j Node 객체인 경우
                    if hasattr(value, 'properties'):
                        props = value.properties
                        if isinstance(props, dict):
                            if 'lat' in props and 'lon' in props:
                                shelter_lat = float(props['lat'])
                                shelter_lon = float(props['lon'])
                                shelter_info['name'] = props.get('name', '')
                                shelter_info['address'] = props.get('address', '')
                                shelter_info['shelter_type'] = props.get('shelter_type', '')
                    # 딕셔너리인 경우
                    elif isinstance(value, dict):
                        if 'lat' in value and 'lon' in value:
                            shelter_lat = float(value['lat'])
                            shelter_lon = float(value['lon'])
                            shelter_info['name'] = value.get('name', '')
                            shelter_info['address'] = value.get('address', '')
                            shelter_info['shelter_type'] = value.get('shelter_type', '')
                    # 직접 속성인 경우
                    elif key == 'lat' or key == 's.lat' or key.endswith('.lat'):
                        try:
                            shelter_lat = float(value)
                        except:
                            pass
                    elif key == 'lon' or key == 's.lon' or key.endswith('.lon'):
                        try:
                            shelter_lon = float(value)
                        except:
                            pass
                    elif key == 'name' or key == 's.name' or key.endswith('.name'):
                        shelter_info['name'] = str(value)
                    elif key == 'address' or key == 's.address' or key.endswith('.address'):
                        shelter_info['address'] = str(value)
                    elif key == 'shelter_type' or key == 's.shelter_type' or key.endswith('.shelter_type'):
                        shelter_info['shelter_type'] = str(value)
                
                # 거리 계산 및 필터링
                if shelter_lat is not None and shelter_lon is not None:
                    distance = haversine_distance(lat, lon, shelter_lat, shelter_lon)
                    if distance <= radius_km:
                        shelter_info['distance_km'] = round(distance, 2)
                        shelters.append(shelter_info)
            
            # 거리순 정렬
            shelters.sort(key=lambda x: x.get('distance_km', float('inf')))
            
            # 최대 10개만 반환
            return shelters[:10]
            
        except Exception as e:
            logger.warning(f"[AdvisorAgent] 대피소 검색 오류: {e}")
            return shelters


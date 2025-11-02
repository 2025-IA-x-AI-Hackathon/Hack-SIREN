"""AdvisorAgent - 행동지침 생성 (3단계 + 위치 기반 안전 거점 + 근거)"""
from typing import Dict, List, Optional, Any
from google import genai
from config import GOOGLE_API_KEY, GEMINI_MODEL
from models import (
    AdvisoryResult,
    ProfileResult, PlanningResult, AnalysisResult
)


class AdvisorAgent:
    """행동지침 생성 에이전트"""
    
    def __init__(self):
        self.client = genai.Client(api_key=GOOGLE_API_KEY)
    
    def advise(
        self,
        input_text: str,
        profile: ProfileResult,
        planning: PlanningResult,
        analysis: AnalysisResult,
        location_info: Optional[Dict] = None
    ) -> AdvisoryResult:
        """행동지침 생성 (결론 + 증거)"""
        
        # 분석 결과 요약
        graph_summary = self._summarize_graph_results(analysis.graph_results)
        vector_summary = self._summarize_vector_results(analysis.vector_results)
        
        # 위치 정보 추가
        location_context = ""
        if location_info:
            location_context = f"""
위치 정보:
- 위도: {location_info.get('lat')}
- 경도: {location_info.get('lon')}
- 검색 반경: {location_info.get('radius_km', 5.0)}km
사용자 주변 반경 내 실제 이용 가능한 대피 지점을 제공해야 합니다.
"""
        
        prompt = f"""
당신은 재난대응 행동지침 전문가입니다.
검색 결과를 분석하여 추론을 통해 결정하고, 핵심 결론과 근거를 제공하세요.

사용자 입력:
{input_text}

{location_context}

ProfileAgent 분석:
- 메시지 유형: {profile.message_type.value}
- 추출 정보: {profile.extracted_info}

Graph RAG 검색 결과 요약:
{graph_summary}

Vector RAG 검색 결과 요약:
{vector_summary}

**검색 결과 분석 가이드:**
1. **위험성 평가 (Hazard)**: 
   - Hazard 노드와 TRIGGERS, CAUSES, INCREASES_RISK_OF 관계를 통해 위험성 평가
   - 현재 상황에서 발생 가능한 위험 요소 파악
   
2. **행동요령 (Policy)**:
   - Policy 노드와 GUIDES 관계를 통해 재난 유형별 행동요령 확인
   - 즉시 행동, 다음 단계, 주의사항으로 구분하여 적용
   
3. **대피소 정보 (Shelter)**:
   - Shelter 노드와 위치 정보를 통해 주변 안전 거점 파악
   - 위치 정보가 있으면 거리 기반으로 우선순위 제공

**작업 순서:**
1. 검색 결과에서 위험성 평가, 행동요령, 대피소 정보를 각각 추출
2. 위험성 평가를 바탕으로 주의·금지 사항 도출
3. 행동요령을 바탕으로 즉시 행동과 다음 단계 구분
4. 대피소 정보를 바탕으로 안전 거점 제시
5. 모든 근거를 공식 지침 기준으로 명시

다음 JSON 형식으로 응답하세요:
{{
    "conclusion": "검색 결과(위험성 평가, 행동요령, 대피소 정보)를 종합하여 3-5문장으로 핵심 결론을 정리. 다음 구조를 포함:\n- 즉시 해야 할 행동 (위험성 평가 + 행동요령 기반)\n- 다음 단계 행동 (행동요령 기반)\n- 주의·금지 사항 (위험성 평가 기반)\n- 안전 거점 (대피소 정보 기반)",
    "evidence": "검색 결과에서 실제로 찾은 구체적 근거를 다음 형식으로 제공:\n1. 위험성 평가: [Hazard 관계에서 발견한 위험 요소]\n2. 행동요령: [Policy GUIDES 관계에서 발견한 행동요령]\n3. 대피소 정보: [Shelter 노드에서 발견한 대피소 목록]\n각 근거는 Graph RAG 또는 Vector RAG 검색 결과에서 직접 확인한 정보만 포함"
}}

지침:
- conclusion은 위험성 평가, 행동요령, 대피소 정보를 모두 종합하여 3-5문장으로 작성
- evidence는 검색 결과에서 실제로 찾은 구체적 정보만 포함 (추론 불가, 실제 데이터만)
- 위험성 평가는 TRIGGERS, CAUSES, INCREASES_RISK_OF 관계에서 발견한 위험 요소 기반
- 행동요령은 GUIDES 관계에서 발견한 Policy 노드의 내용 기반
- 대피소 정보는 Shelter 노드와 IN 관계에서 발견한 정보 기반
- 모든 근거는 공식 지침(국민재난안전포털, 행정안전부 등) 기준으로 명시

JSON만 응답하고 설명은 제외하세요.
"""
        
        try:
            response = self.client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt.strip()
            )
            
            from utils import extract_text_from_response, parse_json_from_text
            
            text = extract_text_from_response(response).strip()
            result_dict = parse_json_from_text(text)
            
            if not result_dict:
                # 기본 지침
                result_dict = {
                    "conclusion": "검색 결과 분석 실패",
                    "evidence": ""
                }
            
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
            
            return AdvisoryResult(
                conclusion=conclusion,
                evidence=evidence
            )
        except Exception as e:
            # Fallback 지침
            return AdvisoryResult(
                conclusion=f"지침 생성 오류가 발생했습니다: {str(e)}",
                evidence=""
            )
    
    def _summarize_graph_results(self, graph_results: Dict) -> str:
        """Graph RAG 결과 요약"""
        if graph_results.get("error"):
            return f"오류: {graph_results['error']}"
        
        count = graph_results.get('count', 0)
        results = graph_results.get("results", [])
        
        if not results:
            return f"검색 결과 없음"
        
        summary = f"검색 결과: {count}개\n"
        
        # 대피소 정보 추출
        shelters = []
        for record in results[:10]:
            for key, value in record.items():
                if isinstance(value, dict) or hasattr(value, 'properties'):
                    props = value.properties if hasattr(value, 'properties') else value
                    if isinstance(props, dict):
                        if 'name' in props or 'address' in props:
                            shelters.append({
                                'name': props.get('name', ''),
                                'address': props.get('address', '')
                            })
                elif isinstance(value, str) and ('대피소' in value or 'Shelter' in key):
                    shelters.append({'name': value, 'address': ''})
        
        if shelters:
            summary += f"\n대피소 정보: {len(shelters)}개 발견\n"
            for i, s in enumerate(shelters[:3], 1):
                summary += f"  {i}. {s.get('name', '')} - {s.get('address', '')}\n"
        
        return summary
    
    def _summarize_vector_results(self, vector_results: Dict) -> str:
        """Vector RAG 결과 요약"""
        if vector_results.get("error"):
            return f"오류: {vector_results['error']}"
        
        results = vector_results.get("results", [])
        if not results:
            return "검색 결과 없음"
        
        summary = f"문서 검색 결과: {len(results)}개\n"
        
        for i, doc in enumerate(results[:3], 1):
            doc_text = doc.get('text', '')[:200]
            summary += f"\n문서 {i}: {doc_text}...\n"
        
        return summary
    
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
            print(f"대피소 검색 오류: {e}")
            return shelters


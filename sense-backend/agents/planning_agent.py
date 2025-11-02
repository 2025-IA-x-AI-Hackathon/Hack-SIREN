"""PlanningAgent - 검색 계획 수립 (서브 문제 추론 기반)"""
from typing import Dict, Any, Optional, List
import logging
import asyncio
from google import genai
from config import GOOGLE_API_KEY, GEMINI_MODEL
from models import PlanningResult

logger = logging.getLogger(__name__)


class PlanningAgent:
    """검색 계획 수립 에이전트 (질문을 서브 문제로 분해하여 검색 전략 수립)"""
    
    def __init__(self):
        self.client = genai.Client(api_key=GOOGLE_API_KEY)
    
    async def plan(self, input_text: str, user_info: Optional[dict] = None) -> PlanningResult:
        """검색 계획 수립 (질문을 서브 문제로 분해하고 구체적인 검색 전략 수립)"""
        
        logger.info(f"[PlanningAgent] 질문 분석 시작: {input_text[:100]}...")
        question = input_text
        
        # 사용자 위치 정보 추가
        location_context = ""
        if user_info:
            location_context = f"""
사용자 위치 정보 (매우 중요 - 이 정보를 활용하여 정확한 대피소 검색 수행):
- 위도: {user_info.get('lat', 'N/A')} (좌표 기반 거리 계산 가능)
- 경도: {user_info.get('lon', 'N/A')} (좌표 기반 거리 계산 가능)
- 층수: {user_info.get('floor', 'N/A')} (고층 건물 안전 고려 필요)
- 참고: 위도/경도가 제공되면 반드시 위치 기반 검색 전략 수립
"""
        
        # LLM을 사용하여 질문을 서브 문제로 분해
        prompt = f"""재난대응 검색 계획 전문가로서, 사용자 발화의도를 정확히 파악하여 구체적이고 명확한 서브 문제들로 분해하고 검색 전략을 수립하세요.

사용자 질문:
{question}

{location_context}

**1단계: 사용자 발화 의도 분석**
- 사용자가 구체적으로 언급한 정보를 정확히 추출하세요:
  * 지역명 (예: "서초구", "강남구", "강남역", "서울시" 등) - 대피소 검색에 필수
  * 재난 유형 (예: "지진", "산사태", "붕괴", "화재" 등) - 행동요령 검색에 필수
  * 구체적인 요구사항 (예: "가까운 대피소", "어디로 가야", "행동요령", "어떻게 해야" 등)
  * 시간적 요소 (예: "지금", "현재", "발생했을 때" 등)
  * 상황 정보:
    - 건물 층수 (예: "3층", "고층" 등) - 고층 대피 시 특별 주의 필요
    - 동반자 정보 (예: "할머니", "노약자", "어린이" 등) - 특수 상황 고려
    - 날씨/환경 (예: "비", "눈", "어둠" 등) - 대피 경로 선정 영향
  * 수량/범위 (예: "몇 개", "어디에", "어떻게" 등)
- 사용자가 명시적으로 언급한 키워드를 그대로 반영하세요
- 암묵적 의도도 파악하되, 명시적 정보를 우선적으로 반영하세요
- **위도/경도 정보가 제공되면 반드시 위치 기반 검색 우선 수행**

**2단계: 서브 문제 분해**
- 사용자 발화에서 구체적으로 언급된 정보를 각 서브 문제에 명확히 반영하세요
- 각 서브 문제는 사용자의 구체적 요구사항과 일대일 대응되도록 작성하세요
- **반드시 다음 두 가지를 분리하여 서브 문제로 작성:**
  1. **대피소 위치 검색** (Graph RAG 우선):
     - 사용자가 언급한 지역명 반영
     - 위도/경도가 있으면 위치 기반 거리 계산 검색
     - 실제 대피소 이름, 주소, 거리 정보 제공 목적
  2. **재난 행동요령 검색** (Vector RAG 우선):
     - 사용자가 언급한 재난 유형 반영
     - 상황 정보(고층, 노약자 동반, 날씨 등) 고려한 행동요령
     - 구체적이고 실행 가능한 행동 지침 제공 목적
- 추상적이거나 일반적인 서브 문제보다는 사용자가 요구한 구체적 정보를 중심으로 분해하세요

**3단계: 검색 전략 수립**
1. **대피소 검색 서브 문제**:
   - Graph RAG 우선: Shelter 노드에서 실제 대피소 이름, 주소, 위치(좌표) 검색
   - 지역명(gu) 필터링: 사용자가 언급한 구체적 지역명 반영 (예: "강남구", "서초구")
   - 위치 기반 검색: 위도/경도가 있으면 거리순 정렬 가능하도록 좌표 정보 포함
   - Vector RAG는 보조적: 대피소 관련 일반 문서 (우선순위 낮음)
   
2. **행동요령 검색 서브 문제**:
   - Vector RAG 우선: 재난 유형별 상세 행동요령 문서 검색
   - 상황 맞춤: 고층, 노약자 동반, 날씨 등 상황 정보를 키워드에 포함
   - Graph RAG 보조: Policy 노드에서 정책 정보 (우선순위 낮음)
   
3. 검색 우선순위: 대피소 위치 검색(1) > 행동요령 검색(2) > 불확실성 대응(3)

4. **위치 정보 활용**: 위도/경도가 제공되면 반드시 location_based=true로 설정하고 거리 계산 가능하도록 검색

**Graph RAG 검색 대상:**
- Shelter, TemporaryHousing: 대피소 및 임시주거시설 (위치, 유형, 수용인원 등)
- Admin: 행정구역 (gu, sigungu 속성)
- Hazard: 재난 유형 및 위험 요소 (지진, 산사태, 붕괴 등)
- Policy: 행동요령 정책 (GUIDES 관계를 통해 Hazard와 연결)
- Event: 재난 이벤트
- 관계: IN, GUIDES, TRIGGERS, CAUSES, INCREASES_RISK_OF, UPDATES

**Vector RAG 검색 대상:**
- 재난 행동요령 문서
- 재난 대응 가이드라인
- 상세한 행동 지침

다음 JSON 형식으로 응답하세요:
{{
    "sub_problems": [
        {{
            "id": 1,
            "question": "사용자가 구체적으로 언급한 요구사항을 정확히 반영한 서브 문제 (예: '서초구 근처 대피소 찾기' X, 사용자가 언급한 정확한 표현 사용)",
            "graph_search": {{
                "target_nodes": ["Shelter", "Admin"],
                "target_relations": ["IN"],
                "query_intent": "사용자가 언급한 구체적 정보를 정확히 검색하는 의도 (예: '강남구에 위치한 대피소 중 좌표 기반 거리 계산하여 이름, 주소, 좌표 반환')",
                "key_attributes": ["name", "address", "shelter_type", "lat", "lon"],
                "location_based": true/false,
                "specific_info": "사용자가 언급한 구체적 정보 (예: '강남구', '지진' 등) - 지역명은 반드시 포함",
                "region_filter": "사용자가 언급한 지역명 (예: '강남구', '서초구' 등) 또는 null"
            }},
            "vector_search": {{
                "keywords": ["사용자가 언급한 구체적 키워드"],
                "focus": "사용자 요구사항과 정확히 일치하는 검색 초점",
                "top_k": 5,
                "situation_context": "상황 정보 (예: '고층', '노약자', '우천' 등) 또는 null"
            }}
        }}
    ],
    "overall_strategy": {{
        "primary_focus": "사용자가 명시적으로 요구한 정보를 중심으로 한 검색 초점",
        "search_priority": ["서브 문제 ID 순서 (사용자가 명시적으로 요구한 정보 우선)"],
        "integration_approach": "사용자 발화의도에 맞춘 결과 통합 방식"
    }},
    "instructions": "사용자가 구체적으로 언급한 정보를 정확히 반영한 최종 답변 생성 지침"
}}

**중요 지침:**
- **서브 문제의 question 필드**: 사용자가 언급한 구체적 표현을 그대로 반영 (추상화 X)
  - 나쁜 예: "대피소 위치 및 정보 찾기"
  - 좋은 예: "강남역 근처 대피소 찾기" 또는 사용자가 언급한 정확한 표현

- **대피소 검색 서브 문제 (서브 문제 1, 최우선)**:
  - **region_filter**: 사용자가 언급한 지역명을 반드시 포함 (예: "강남구", "서초구")
  - **query_intent**: "강남구에 위치한 대피소 이름, 주소, 좌표 검색 (거리 계산 가능하도록)"
  - **location_based**: 위도/경도가 제공되면 반드시 true
  - **key_attributes**: name, address, lat, lon 필수 (거리 계산을 위해)
  - **specific_info**: 지역명 반드시 포함 (예: "강남구")

- **행동요령 검색 서브 문제 (서브 문제 2)**:
  - **keywords**: 재난 유형 필수 (예: "지진"), 상황 정보 포함 (예: "고층", "노약자", "우천")
  - **situation_context**: 건물 층수, 동반자, 날씨 등 상황 정보
  - **focus**: "지진 발생 시 행동요령 (고층 건물, 노약자 동반, 우천 상황 고려)"

- **검색 우선순위**: 
  1. 대피소 위치 검색 (Graph RAG, 사용자 지역명 + 좌표 기반)
  2. 행동요령 검색 (Vector RAG, 재난 유형 + 상황 정보)
  3. 불확실성 대응 (낮은 우선순위)

- **위치 정보 활용**: 위도/경도가 제공되면:
  - 반드시 location_based=true
  - 좌표 기반 거리 계산 가능하도록 lat, lon 속성 포함
  - 실제 대피소 이름, 주소, 거리를 정확히 제공할 수 있도록 검색

- **Graph RAG와 Vector RAG 역할**:
  - Graph RAG: 실제 대피소 데이터 (이름, 주소, 좌표) 제공
  - Vector RAG: 상세 행동요령 문서 제공
  
- **불확실성 대응**: 대피소 정보가 불확실하거나 찾지 못한 경우, 일반적인 재난 대응 행동 요령 검색 서브 문제 추가 (우선순위 3)

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
            plan_dict = parse_json_from_text(text)
            
            if not plan_dict:
                # Fallback: 기본 계획
                plan_dict = self._create_fallback_plan(question)
            
            # PlanningResult 생성
            sub_problems = plan_dict.get("sub_problems", [])
            logger.info(f"[PlanningAgent] 추론 완료: {len(sub_problems)}개 서브 문제 분해")
            for sp in sub_problems:
                logger.info(f"  - 서브 문제 {sp.get('id')}: {sp.get('question', '')[:50]}...")
            
            return PlanningResult(
                search_plan={
                    "sub_problems": sub_problems,
                    "overall_strategy": plan_dict.get("overall_strategy", {}),
                    "instructions": plan_dict.get("instructions", "")
                },
                reasoning=f"질문을 {len(sub_problems)}개의 서브 문제로 분해하여 검색 전략 수립"
            )
            
        except Exception as e:
            # Fallback: 기본 계획
            logger.warning(f"[PlanningAgent] 추론 오류: {str(e)}, 기본 계획 사용")
            plan_dict = self._create_fallback_plan(question)
            return PlanningResult(
                search_plan={
                    "sub_problems": plan_dict.get("sub_problems", []),
                    "overall_strategy": plan_dict.get("overall_strategy", {}),
                    "instructions": plan_dict.get("instructions", "")
                },
                reasoning=f"계획 수립 오류: {str(e)}, 기본 계획 사용"
            )
    
    def _create_fallback_plan(self, question: str) -> dict:
        """Fallback: 기본 검색 계획 생성"""
        # 노트북의 hybrid_rag 함수의 질문 유형 분류 로직
        if '알려주세요' in question or '찾고 싶어요' in question or '어디' in question:
            sub_problems = [{
                "id": 1,
                "question": "대피소/시설 위치 및 정보 찾기",
                "graph_search": {
                    "target_nodes": ["Shelter", "TemporaryHousing", "Admin"],
                    "target_relations": ["IN"],
                    "query_intent": "위치 기반 대피소 검색",
                    "key_attributes": ["name", "address", "shelter_type"],
                    "location_based": True
                },
                "vector_search": {
                    "keywords": ["대피소", "위치", "안전"],
                    "focus": "대피소 관련 문서",
                    "top_k": 3
                }
            }, {
                "id": 2,
                "question": "불확실성 대응: 확실한 행동 요령 찾기",
                "graph_search": {
                    "target_nodes": ["Policy", "Hazard"],
                    "target_relations": ["GUIDES"],
                    "query_intent": "일반적인 재난 대응 행동 요령 검색",
                    "key_attributes": ["name", "disaster_type", "category1", "category2", "category3"],
                    "location_based": False
                },
                "vector_search": {
                    "keywords": ["행동요령", "대응", "안전", "일반"],
                    "focus": "확실한 행동 요령 문서",
                    "top_k": 5
                }
            }]
            instructions = """- Graph RAG 결과에 실제 대피소/시설 목록이 있으면 구체적인 이름과 주소를 제시하세요
- 대피소가 많으면 주요 대피소 몇 개를 예시로 제시하고, 총 개수를 알려주세요
- 대피소 정보가 불확실하거나 찾지 못한 경우, 확실한 행동 요령을 참고하세요
- 간결하고 실행 가능한 답변 제공"""
            primary_focus = "대피소/시설 목록 검색"
        elif '행동' in question or '어떻게' in question or '요령' in question:
            sub_problems = [{
                "id": 1,
                "question": "행동요령 정책 정보 찾기",
                "graph_search": {
                    "target_nodes": ["Policy", "Hazard"],
                    "target_relations": ["GUIDES"],
                    "query_intent": "재난 유형별 행동요령 검색",
                    "key_attributes": ["name", "disaster_type", "category1", "category2", "category3"],
                    "location_based": False
                },
                "vector_search": {
                    "keywords": ["행동요령", "대응", "안전"],
                    "focus": "상세 행동요령 문서",
                    "top_k": 5
                }
            }, {
                "id": 2,
                "question": "불확실성 대응: 일반 행동 요령 찾기",
                "graph_search": {
                    "target_nodes": ["Policy"],
                    "target_relations": ["GUIDES"],
                    "query_intent": "일반적인 재난 대응 행동 요령 검색",
                    "key_attributes": ["name", "disaster_type"],
                    "location_based": False
                },
                "vector_search": {
                    "keywords": ["일반", "기본", "행동요령", "대응"],
                    "focus": "확실한 기본 행동 요령 문서",
                    "top_k": 3
                }
            }]
            instructions = """- Graph RAG 결과에 Policy(행동요령) 정보가 있으면 구체적으로 제시하세요
- Vector RAG 결과의 행동요령 문서를 참고하여 구체적인 행동 지침을 제공하세요
- 구체적인 행동요령이 불확실하거나 찾지 못한 경우, 일반적인 기본 행동 요령을 참고하세요
- 간결하고 실행 가능한 답변 제공"""
            primary_focus = "행동요령 검색"
        elif '재난' in question or '위험' in question or 'Hazard' in question or '지진' in question or '산사태' in question:
            sub_problems = [{
                "id": 1,
                "question": "재난/위험 요소 및 연쇄 관계 파악",
                "graph_search": {
                    "target_nodes": ["Hazard", "Event"],
                    "target_relations": ["TRIGGERS", "CAUSES", "INCREASES_RISK_OF"],
                    "query_intent": "재난 간 연쇄 관계 탐색",
                    "key_attributes": ["name", "hazard_type", "severity"],
                    "location_based": False
                },
                "vector_search": {
                    "keywords": ["재난", "위험", "대응"],
                    "focus": "재난 관련 문서",
                    "top_k": 5
                }
            }, {
                "id": 2,
                "question": "불확실성 대응: 확실한 재난 대응 행동 요령 찾기",
                "graph_search": {
                    "target_nodes": ["Policy", "Hazard"],
                    "target_relations": ["GUIDES"],
                    "query_intent": "재난 유형별 확실한 행동 요령 검색",
                    "key_attributes": ["name", "disaster_type", "category1", "category2", "category3"],
                    "location_based": False
                },
                "vector_search": {
                    "keywords": ["행동요령", "대응", "안전", "확실"],
                    "focus": "확실한 재난 대응 행동 요령 문서",
                    "top_k": 5
                }
            }]
            instructions = """- Graph RAG 결과에서 Hazard 노드와 관련 관계(TRIGGERS, CAUSES, INCREASES_RISK_OF)를 활용하세요
- 재난 간의 연쇄 관계를 명확히 설명하세요
- 구체적인 데이터와 근거를 제시하세요
- 재난 정보가 불확실하거나 불완전한 경우, 확실한 재난 대응 행동 요령을 참고하세요"""
            primary_focus = "재난/위험 평가 검색"
        else:
            sub_problems = [{
                "id": 1,
                "question": "일반 정보 검색",
                "graph_search": {
                    "target_nodes": ["Shelter", "Hazard", "Policy"],
                    "target_relations": ["IN", "GUIDES"],
                    "query_intent": "관련 정보 검색",
                    "key_attributes": ["name", "description"],
                    "location_based": False
                },
                "vector_search": {
                    "keywords": ["재난", "대응"],
                    "focus": "관련 문서",
                    "top_k": 5
                }
            }]
            instructions = """- 구체적인 데이터(개수, 위치 등)를 명확히 제시
- Graph RAG와 Vector RAG 결과를 모두 활용하세요
- 간결하고 실행 가능한 답변 제공
- 근거를 간단히 명시"""
            primary_focus = "일반 검색"
        
        # search_priority 설정 (불확실성 대응은 우선순위 낮게)
        search_priority = [1]
        if len(sub_problems) > 1:
            search_priority.append(2)
        
        return {
            "sub_problems": sub_problems,
            "overall_strategy": {
                "primary_focus": primary_focus,
                "search_priority": search_priority,
                "integration_approach": "Graph RAG와 Vector RAG 결과를 통합하여 답변 생성. 불확실한 정보가 있을 경우 확실한 행동 요령을 참고"
            },
            "instructions": instructions
        }

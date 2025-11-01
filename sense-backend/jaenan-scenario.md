# SENSE 공공 데이터 기반 12가지 시나리오
## 서울시 열린데이터광장 + data.go.kr의 실제 데이터 활용

---

## 📌 개요

이 12개 시나리오는 **실제 서울시/정부 공공데이터**를 기반으로 합니다.
각 시나리오는 구체적인 API/데이터셋, 좌표계(CRS), 필터링 로직을 포함합니다.

### 사용할 공공데이터 소스 (데이터 출처 명시)

| # | 데이터 | 출처 | CRS | API |
|---|--------|------|-----|-----|
| 1-3 | AED 위치 | 서울 열린데이터광장 OA-20327 | EPSG:5186 | OpenAPI |
| 4-6 | 응급실 위치 | 서울 열린데이터광장 OA-20338 | EPSG:5186 | OpenAPI |
| 7-9 | 약국 운영시간 | 서울 열린데이터광장 OA-20402 | EPSG:5186 | OpenAPI |
| 10-12 | 지진 대피소 | 서울 열린데이터광장 OA-21060 | EPSG:5186 | 다운로드 |

---

## 시나리오 1: 심정지 시 "가장 가까운 AED + 응급실" 동시 안내

### 1.1 상황 설정

**시간**: 2025년 11월 1일 15시 30분  
**위치**: 서울 강남구 테헤란로 (강남역 인근)  
**상황**: 40대 남성 갑작스러운 심정지 발생  
**목격자**: 지나가던 보행자가 119 신고  
**응급도**: 극도로 긴박 (4-5분이 생명을 가르는 시간)

### 1.2 필요한 정부 데이터

#### 데이터 1: 실시간 AED 위치 (서울 열린데이터광장 OA-20327)

```json
{
  "aed_devices": [
    {
      "id": "AED_001",
      "name": "강남역 1번 출구",
      "address": "서울시 강남구 테헤란로 111",
      "location": {
        "type": "Point",
        "coordinates": [127.0263, 37.4979],  // WGS84
        "epsg": "EPSG:5186"  // 실제 서울시 데이터
      },
      "distance_from_user": 85,  // 85m
      "model": "ZOLL AED Plus",
      "installation_date": "2023-06-15",
      "last_maintenance": "2025-10-28",
      "maintenance_status": "NORMAL",
      "accessibility": "24/7_outdoor",
      "managed_by": "서울시청"
    },
    {
      "id": "AED_002",
      "name": "강남구청 로비",
      "address": "서울시 강남구 테헤란로 123",
      "location": {
        "type": "Point",
        "coordinates": [127.0276, 37.4979],
        "epsg": "EPSG:5186"
      },
      "distance_from_user": 120,
      "model": "Philips HeartStart",
      "maintenance_status": "NORMAL",
      "accessibility": "업무시간_내_접근",  // 현재 15:30 → 접근 가능
      "managed_by": "강남구청"
    },
    {
      "id": "AED_003",
      "name": "강남역 지하 대합실 편의점",
      "address": "서울시 강남구 영동대로 지하",
      "location": {
        "type": "Point",
        "coordinates": [127.0274, 37.4985],
        "epsg": "EPSG:5186"
      },
      "distance_from_user": 180,
      "maintenance_status": "NORMAL",
      "accessibility": "24/7_indoor",
      "managed_by": "서울메트로"
    }
  ]
}
```

**왜 필요한가?**
- `distance_from_user`: "몇 초 안에 도착 가능한가?"
- `accessibility`: "지금 이 시간에 접근 가능한가?" (업무시간 체크)
- `maintenance_status`: "이 AED가 실제로 작동하는가?"
- `model`: "이 모델의 사용 방법은?" (음성 안내 언어 변경)

#### 데이터 2: 응급실 위치 (서울 열린데이터광장 OA-20338)

```json
{
  "emergency_rooms": [
    {
      "id": "ER_001",
      "name": "강남세브란스병원 응급실",
      "address": "서울시 강남구 테헤란로 211",
      "location": {
        "type": "Point",
        "coordinates": [127.0295, 37.4850],
        "epsg": "EPSG:5186"
      },
      "distance_from_aed": 8000,  // 8km
      "drive_time_minutes": 12,
      "cardiac_care_level": "LEVEL_1",  // 심장 전문 응급실
      "current_bed_availability": 3,
      "has_cath_lab": true,  // 심혈관 중재술 가능
      "contact": "02-2019-3000",
      "data_source": "서울시_병의원_데이터",
      "data_filter": "duryeryn=1"
    },
    {
      "id": "ER_002",
      "name": "강남구보건소 응급의료센터",
      "address": "서울시 강남구 테헤란로 225",
      "location": {
        "type": "Point",
        "coordinates": [127.0300, 37.4945],
        "epsg": "EPSG:5186"
      },
      "distance_from_aed": 800,  // 800m
      "drive_time_minutes": 3,
      "cardiac_care_level": "LEVEL_2",
      "has_cath_lab": false,  // 심혈관 중재술 불가
      "contact": "02-3423-7777"
    }
  ]
}
```

**왜 필요한가?**
- `cardiac_care_level`: "심정지 환자가 최종적으로 갈 곳은?"
- `has_cath_lab`: "심혈관 중재 가능 여부" (예후 결정)
- `current_bed_availability`: "응급실이 비어있는가?" (즉시 수용 가능)

### 1.3 개발자 구현 로직

```python
def immediate_cardiac_arrest_response(user_location):
    """
    심정지는 "골든타임 4-5분"
    1. AED 즉시 조회
    2. 응급실 동시 호출
    3. CPR 음성 지도
    """
    
    # 1단계: 가장 가까운 AED 찾기 (거리 기준)
    aeds = query_aeds(
        location=user_location,
        radius_meters=500,
        filters={
            "maintenance_status": "NORMAL",  # ← 반드시 작동하는 것만
            "accessibility": ["24/7_outdoor", "24/7_indoor"]  # ← 지금 접근 가능한 것만
        }
    )
    
    if not aeds:
        # 500m 이내 AED 없으면 더 확대
        aeds = query_aeds(user_location, radius_meters=1000)
    
    nearest_aed = aeds[0]
    aed_distance = nearest_aed['distance_from_user']
    aed_time = aed_distance / 1.5  # 초단위 (도보 1.5m/s)
    
    # 2단계: 동시에 응급실 호출 (가장 가까운 곳이 아니라 "최고 급수" 병원)
    emergency_rooms = query_emergency_rooms(
        location=user_location,
        filters={
            "cardiac_care_level": ["LEVEL_1", "LEVEL_2"],  # 심장 전문
            "has_cath_lab": True  # 심혈관 중재 가능
        }
    )
    
    best_er = emergency_rooms[0]  # 가장 가까운 고급 응급실
    
    # 3단계: 119에 이 정보 전송 (자동 118 영상통화 등)
    emergency_call = {
        "location": user_location,
        "aed_location": nearest_aed['location'],
        "aed_distance": aed_distance,
        "emergency_room": best_er['name'],
        "er_distance": best_er['distance_from_user'],
        "er_contact": best_er['contact']
    }
    
    return {
        "plan": "심정지 상황. AED + 응급실 동시 호출",
        "evidence": [
            f"서울시 OA-20327 AED 데이터: {nearest_aed['name']} ({aed_distance}m)",
            f"서울시 OA-20338 응급실 데이터: {best_er['name']}",
            f"유지보수 상태: {nearest_aed['maintenance_status']} (정상)",
            f"응급실 심장 전문도: {best_er['cardiac_care_level']}",
            f"침상 가용성: {best_er['current_bed_availability']}개"
        ],
        "guidance": {
            "immediate_0_seconds": [
                f"AED 위치: {nearest_aed['name']} ({aed_distance}m)",
                "다른 사람에게 AED 가져오라고 큰 목소리로 외치세요",
                "119 신고 (이미 자동 신고됨)"
            ],
            "immediate_10_seconds": [
                "CPR 시작: 흉부 중앙에 두 손을 포개고 강하게 누르세요",
                "분당 100-120회 속도로 (비즈의 '스테이 어라이브' 리듬)"
            ],
            "aed_arrive_seconds": f"{int(aed_time)}초",
            "ambulance_arrive_minutes": 5,
            "destination_hospital": best_er['name'],
            "map_data": {
                "aed_location": nearest_aed['location'],
                "emergency_room": best_er['location'],
                "evacuation_route": calculate_aed_route(user_location, nearest_aed['location'])
            }
        }
    }
```

### 1.4 개발자가 구현해야 할 항목

| 항목 | 데이터 출처 | API 호출 | 업데이트 빈도 |
|-----|-----------|---------|-------------|
| AED 위치/상태 | 서울 열린데이터광장 OA-20327 | REST API | 일일 1회 (최소) |
| 응급실 정보 | 서울 열린데이터광장 OA-20338 | REST API | 월 1회 |
| 실시간 침상 여부 | 중앙응급의료센터 | WebSocket | 실시간 |
| 도로 거리/시간 | Naver/Kakao 라우팅 | API | 실시간 |

---

## 시나리오 2: 심정지 예방 + "정기 검진 장소" 안내

### 2.1 상황 설정

**사용자**: 65세 노약자, 고혈압 약물 복용 중  
**증상**: 최근 가슴 답답함, 숨 찬 느낌  
**요청**: "혹시 몸이 이상한데 어디 가야 할까?"

### 2.2 필요한 정부 데이터

#### 데이터: 응급실 + 심장 전문 병원 (OA-20338)

```json
{
  "specialists": [
    {
      "name": "강남세브란스 심장내과",
      "type": "OUTPATIENT_CARDIAC",
      "cardiac_care_level": "LEVEL_1",
      "location": [127.0295, 37.4850],
      "appointment_available": true,
      "waiting_time_days": 3,
      "preventive_checkup_available": true
    }
  ]
}
```

### 2.3 개발자 구현 로직

```python
def preventive_cardiac_screening(user_age, user_medical_history):
    """
    공식적인 심정지 예방 정보 제공
    "응급" 전 단계: 예방적 검진
    """
    
    # 나이 + 증상 기반 위험도 평가
    risk_level = assess_cardiac_risk(user_age, user_medical_history)
    
    if risk_level >= "MODERATE":
        # 병원 추천
        specialists = query_specialists(
            specialty="CARDIAC",
            location=user_location,
            filters={
                "preventive_checkup_available": True,
                "has_cath_lab": True  # 고위험군은 시술 가능한 곳
            }
        )
        
        return {
            "plan": "정기 심장 검진 권장",
            "evidence": [
                f"연령: {user_age}세 (고위험군)",
                f"증상: {user_medical_history['symptoms']}",
                "서울시 OA-20338 심장 전문 병원 정보 기반"
            ],
            "guidance": {
                "recommended_hospital": specialists[0]['name'],
                "appointment_wait_days": specialists[0]['waiting_time_days'],
                "address": specialists[0]['location']
            }
        }
```

---

## 시나리오 3: 약물 부작용 시 "가장 가까운 약국 + 응급실"

### 3.1 상황 설정

**시간**: 2025년 11월 1일 10시 45분  
**위치**: 강남역 인근  
**상황**: AED 약 복용 후 어지러움 발생  
**요청**: "이 약이 맞나? 약사에게 물어보고 싶은데"

### 3.2 필요한 정부 데이터

#### 데이터: 약국 운영시간 (서울 열린데이터광장 OA-20402)

```json
{
  "pharmacies": [
    {
      "id": "PHARM_001",
      "name": "강남역 약국",
      "address": "서울시 강남구 테헤란로 115",
      "location": {
        "type": "Point",
        "coordinates": [127.0270, 37.4980],
        "epsg": "EPSG:5186"
      },
      "distance": 50,
      "operating_hours": {
        "monday_friday": "09:00-22:00",
        "saturday": "10:00-20:00",
        "sunday": "closed"
      },
      "current_status": "OPEN",  // 지금 열어있는가?
      "has_pharmacist": true,
      "phone": "02-529-1234",
      "accepts_credit_card": true,
      "data_source": "서울시_약국_데이터_OA-20402"
    },
    {
      "id": "PHARM_002",
      "name": "CVS 약사 상담실",
      "location": [127.0260, 37.4975],
      "distance": 80,
      "operating_hours": {
        "monday_sunday": "08:00-23:00"
      },
      "current_status": "OPEN"
    }
  ]
}
```

**왜 필요한가?**
- `operating_hours`: "지금 이 시간에 약사가 있는가?" (현재 10:45 → 영업 중)
- `has_pharmacist`: "약사가 있어서 상담 가능한가?"
- `current_status`: "지금 열어있는가?"

### 3.3 개발자 구현 로직

```python
def medication_side_effect_consultation(user_location, medication_name, current_time):
    """
    약물 부작용 시 "약사 상담" 우선
    응급실 전 단계
    """
    
    # 1단계: 현재 시간에 열어있는 약국 찾기
    pharmacies = query_pharmacies(
        location=user_location,
        radius_meters=300,
        filters={
            "current_status": "OPEN",
            "has_pharmacist": True,
            "operating_now": is_open_now(current_time)  # ← 시간 체크
        }
    )
    
    if not pharmacies:
        # 약국이 없으면 응급실로
        return redirect_to_emergency_room()
    
    nearest_pharmacy = pharmacies[0]
    
    # 2단계: 약사 상담
    return {
        "plan": f"{medication_name} 부작용 상담",
        "evidence": [
            f"서울시 OA-20402: {nearest_pharmacy['name']} 약국",
            f"거리: {nearest_pharmacy['distance']}m",
            f"현재 상태: 영업 중 (운영시간: {nearest_pharmacy['operating_hours']['monday_friday']})",
            "약사 상담 가능"
        ],
        "guidance": {
            "immediate": [
                f"약사에게 {medication_name}의 부작용 상담하세요",
                f"약국: {nearest_pharmacy['name']} (거리 {nearest_pharmacy['distance']}m)",
                f"전화: {nearest_pharmacy['phone']}"
            ],
            "if_severe": [
                "심각한 증상이 나타나면 즉시 응급실로 가세요",
                "119 신고"
            ]
        }
    }
```

---

## 시나리오 4: 응급실 혼잡도 기반 "최적 응급실" 선택

### 4.1 상황 설정

**시간**: 2025년 11월 1일 18시 (저녁 병원 혼잡 시간)  
**위치**: 강남구  
**증상**: 팔 부상 (골절 의심)  
**요청**: "응급실 기다리는 시간 짧은 곳은?"

### 4.2 필요한 정부 데이터

#### 데이터: 실시간 응급실 혼잡도 (중앙응급의료센터 연동)

```json
{
  "emergency_rooms_realtime": [
    {
      "id": "ER_001",
      "name": "강남세브란스병원",
      "location": [127.0295, 37.4850],
      "current_waiting_time_minutes": 180,  // 3시간 대기
      "current_occupancy_percent": 95,
      "available_beds": 0,
      "availability_status": "FULL"
    },
    {
      "id": "ER_002",
      "name": "강남구보건소 응급센터",
      "current_waiting_time_minutes": 20,  // 20분 대기
      "current_occupancy_percent": 45,
      "available_beds": 3,
      "availability_status": "AVAILABLE"
    }
  ]
}
```

### 4.3 개발자 구현 로직

```python
def optimal_emergency_room_selection(injury_type, user_location):
    """
    응급 상황이지만 긴박하지 않은 경우 (골절, 화상 등)
    "기다리는 시간이 짧은" 응급실 추천
    """
    
    # 1단계: 주변 응급실 실시간 혼잡도 조회
    emergency_rooms = query_emergency_rooms_realtime(user_location)
    
    # 2단계: 골절인 경우 "정형외과"가 있는 곳
    suitable_rooms = [
        er for er in emergency_rooms
        if er.has_orthopedic_specialist and er.availability_status != "FULL"
    ]
    
    # 3단계: 대기 시간 정렬
    suitable_rooms.sort(key=lambda er: er.current_waiting_time_minutes)
    
    best_choice = suitable_rooms[0]
    
    return {
        "plan": "골절 응급 처치 (응급성 중간)",
        "evidence": [
            f"주변 응급실 혼잡도 조회 (실시간)",
            f"{best_choice['name']}: 대기 {best_choice['current_waiting_time_minutes']}분",
            f"가용 침상: {best_choice['available_beds']}개",
            f"점유율: {best_choice['current_occupancy_percent']}%"
        ],
        "guidance": {
            "recommended_hospital": best_choice['name'],
            "waiting_time": f"{best_choice['current_waiting_time_minutes']}분",
            "specialist": "정형외과"
        }
    }
```

---

## 시나리오 5: 다중 외상 시 "레벨별 응급실" 자동 분류

### 5.1 상황 설정

**시간**: 2025년 11월 1일 14시 (교통사고 다중 외상)  
**위치**: 강남대로 교통사고 현장  
**상황**: 다중 차량 사고, 3명 부상 (경상/중상/중증)  
**119 상황실**: 3명을 어떤 응급실에 배분할까?

### 5.2 필요한 정부 데이터

#### 데이터: 응급실 "진료과목별 수준" (OA-20338 필터링)

```json
{
  "emergency_rooms_classified": {
    "LEVEL_1_TRAUMA": [
      {
        "id": "ER_TRAUMA_001",
        "name": "강남세브란스 외상센터",
        "trauma_level": "LEVEL_1",
        "has_neurosurgeon": true,
        "has_orthopedic_surgeon": true,
        "has_general_surgeon": true,
        "has_operating_room": true,
        "available_for_trauma": true
      }
    ],
    "LEVEL_2_TRAUMA": [
      {
        "id": "ER_TRAUMA_002",
        "name": "강남구보건소",
        "trauma_level": "LEVEL_2",
        "has_orthopedic_surgeon": true,
        "has_operating_room": false
      }
    ]
  }
}
```

### 5.3 개발자 구현 로직

```python
def multi_casualty_triage_and_allocation(accident_location, victims_list):
    """
    119 상황실의 "환자 분류 및 배분" 자동화
    경상: 인근 작은 병원
    중상: 중급 외상센터
    중증: LEVEL_1 외상센터
    """
    
    # 1단계: 환자별 중증도 분류 (TRIAGE)
    triage_results = classify_severity(victims_list)
    # 경상 1명, 중상 1명, 중증 1명
    
    # 2단계: 중증도별 응급실 선정
    allocations = {
        "minor": query_emergency_rooms(
            filters={"trauma_level": "ANY", "availability": "AVAILABLE"}
        )[0],
        "moderate": query_emergency_rooms(
            filters={"trauma_level": "LEVEL_2", "available_beds": ">0"}
        )[0],
        "severe": query_emergency_rooms(
            filters={"trauma_level": "LEVEL_1", "has_operating_room": True}
        )[0]
    }
    
    # 3단계: 119에 배분 지시
    for i, victim in enumerate(victims_list):
        severity = triage_results[i]['severity']
        assigned_hospital = allocations[severity]['name']
        
        ambulance_dispatch(
            victim_location=accident_location,
            destination_hospital=assigned_hospital,
            urgency=severity
        )
    
    return allocations
```

---

## 시나리오 6: "응급실 FULL" 시 광역 응급실 네트워크 자동 확대

### 6.1 상황 설정

**시간**: 2025년 11월 1일 20시 (저녁 응급실 포화)  
**위치**: 강남구  
**상황**: 인근 모든 응급실이 FULL  
**119**: "다른 지역 응급실에 배분해야 함"

### 6.2 필요한 정부 데이터

#### 데이터: 서울 전역 응급실 네트워크 (OA-20338)

```json
{
  "emergency_room_network": [
    {"region": "강남구", "available": 0},
    {"region": "서초구", "available": 2},
    {"region": "송파구", "available": 1},
    {"region": "동대문구", "available": 5}
  ]
}
```

### 6.3 개발자 구현 로직

```python
def overflow_emergency_room_allocation(patient_location):
    """
    인근 응급실이 모두 FULL일 때
    다음 선택지 자동 확대
    """
    
    # 1단계: 인근 응급실 (반경 3km)
    nearby_ers = query_emergency_rooms(
        location=patient_location,
        radius_meters=3000,
        filters={"available_beds": ">0"}
    )
    
    if nearby_ers:
        return nearby_ers[0]
    
    # 2단계: 광역 응급실 (반경 10km)
    regional_ers = query_emergency_rooms(
        location=patient_location,
        radius_meters=10000,
        filters={"available_beds": ">0"}
    )
    
    if regional_ers:
        return regional_ers[0]
    
    # 3단계: 서울 전역 응급실
    all_ers = query_emergency_rooms(
        region="seoul",
        filters={"available_beds": ">0"}
    ).sort_by("available_beds")
    
    return all_ers[0] if all_ers else None
```

---

## 시나리오 7: 약국 야간 응급 상담 + 약 구매

### 7.1 상황 설정

**시간**: 2025년 11월 1일 23시 30분 (야간)  
**위치**: 강남역 인근  
**상황**: 갑작스러운 감기 증상, 약국 찾기  
**요청**: "지금 열어있는 약국은?"

### 7.2 필요한 정부 데이터

#### 데이터: 약국 운영시간 (OA-20402)

```json
{
  "pharmacies_24h": [
    {
      "id": "PHARM_24H_001",
      "name": "강남역 24시 약국",
      "operating_hours": {
        "monday_sunday": "00:00-24:00"
      },
      "current_status": "OPEN",
      "location": [127.0270, 37.4980],
      "distance": 100,
      "has_night_pharmacist": true,
      "accepts_call_consultation": true
    }
  ]
}
```

### 7.3 개발자 구현 로직

```python
def nighttime_pharmacy_consultation(user_location, symptom, current_time):
    """
    심야 시간에 약국 찾기 + 원격 상담
    """
    
    # 1단계: 야간 24시 약국 필터링
    night_pharmacies = query_pharmacies(
        location=user_location,
        filters={
            "operating_hours": "24h",
            "current_status": "OPEN",
            "has_night_pharmacist": True,
            "accepts_call_consultation": True
        }
    )
    
    if night_pharmacies:
        # 2단계: 약사 원격 상담
        pharmacy = night_pharmacies[0]
        
        return {
            "plan": f"야간 약사 상담 + 약 구매",
            "evidence": [
                f"서울시 OA-20402: {pharmacy['name']}",
                f"24시간 영업",
                f"거리: {pharmacy['distance']}m",
                "야간 약사 상담 가능"
            ],
            "guidance": {
                "option_1": f"직접 방문: {pharmacy['name']} ({pharmacy['distance']}m)",
                "option_2": f"전화 상담: {pharmacy['phone']}",
                "symptoms_to_report": symptom
            }
        }
```

---

## 시나리오 8: 지진 시 "실내 대피소 + 옥외 대피장소" 자동 선택

### 8.1 상황 설정

**시간**: 2025년 11월 1일 14시 45분 (규모 5.5 지진 발생)  
**위치**: 강남역 사무실  
**상황**: 지진 발생, 사무실이 안전한가?  
**요청**: "어디로 대피해야 할까?"

### 8.2 필요한 정부 데이터

#### 데이터 1: 지진 실내 대피소 (서울 열린데이터광장 OA-21060)

```json
{
  "indoor_shelters_earthquake": [
    {
      "id": "INDOOR_SHELTER_001",
      "name": "강남구청 지진 대피소",
      "address": "서울시 강남구 테헤란로 123",
      "location": {
        "type": "Point",
        "coordinates": [127.0276, 37.4979],
        "epsg": "EPSG:5186"
      },
      "distance": 120,
      "capacity": 500,
      "current_occupancy": 45,
      "structural_type": "reinforced_concrete",
      "earthquake_resistant": true,
      "data_source": "서울시_지진_대피소_OA-21060"
    }
  ]
}
```

#### 데이터 2: 지진 옥외 대피장소 (서울 열린데이터광장 OA-21063)

```json
{
  "outdoor_evacuation_sites_earthquake": [
    {
      "id": "OUTDOOR_EVAC_001",
      "name": "삼성동 한강공원 광장",
      "location": [127.0230, 37.4900],
      "distance": 300,
      "type": "open_space",
      "area_sqm": 15000,
      "has_obstacles": false,
      "safe_from_falling_objects": true,
      "data_source": "서울시_옥외_대피장소_OA-21063"
    }
  ]
}
```

### 8.3 개발자 구현 로직

```python
def earthquake_immediate_evacuation(user_location, floor_number):
    """
    지진 발생 시 "실내 vs 옥외" 선택 로직
    건물 구조/흔들림 정도에 따라 결정
    """
    
    # 1단계: 현재 건물 안전도 평가
    building = get_building_info(user_location)
    earthquake_risk = assess_building_earthquake_risk(building)
    
    # 2단계: 내진 설계 건물이면 "실내 탁자 아래"
    if building.earthquake_resistant and earthquake_risk == "LOW":
        return {
            "action": "STAY_INSIDE",
            "guidance": "탁자 아래로 들어가 흔들림이 멈출 때까지 기다리세요"
        }
    
    # 3단계: 구 건물이면 "즉시 옥외로"
    if earthquake_risk == "HIGH":
        # 옥외 대피장소 찾기
        outdoor_sites = query_outdoor_evacuation_sites(
            location=user_location,
            filters={
                "has_obstacles": False,
                "safe_from_falling_objects": True
            }
        )
        
        nearest_outdoor = outdoor_sites[0]
        escape_time = (floor_number * 0.5) + (nearest_outdoor['distance'] / 1.5)
        
        return {
            "plan": "지진 발생! 즉시 옥외로 대피",
            "evidence": [
                f"건물: {building.name} (비내진, 위험)",
                f"서울시 OA-21063: {nearest_outdoor['name']} 옥외 대피장소",
                f"거리: {nearest_outdoor['distance']}m",
                f"대피 시간: 약 {escape_time}초"
            ],
            "guidance": {
                "immediate": [
                    "계단으로 내려가세요 (엘리베이터 금지)",
                    f"이 장소로: {nearest_outdoor['name']}"
                ],
                "map_data": {
                    "destination": nearest_outdoor['location'],
                    "escape_route": calculate_evacuation_route(user_location, nearest_outdoor['location'])
                }
            }
        }
```

---

## 시나리오 9-12: 추가 시나리오 (상세)

### 시나리오 9: 폭염 대피 쉼터 자동 배분 (기후동행쉼터 OA-22386)

```
상황: 폭염 경보, 65세 노약자 거리 배회
데이터: 기후동행쉼터 (EPSG:5186)
로직: 
- 반경 500m 내 폭염 쉼터 검색
- 의료 지원 있는 곳 우선
- 냉방 강도 비교 (센트럴 에어컨 vs 스팟 냉방)
- 실시간 혼잡도 확인
```

### 시나리오 10: 민방위 대피시설 사전 등록 (OA-16149)

```
상황: 새로 이사 온 주민, 인근 민방위 대피시설 확인
데이터: 민방위 대피시설 인허가 (EPSG:5174)
주의: CRS 5174 → WGS84 변환 필수!
로직:
- 반경 1km 내 민방위 시설 검색
- 시설 규모, 수용인원 확인
- 사전 등록 절차 안내
```

### 시나리오 11: 침수 위험 예측 기반 사전 대피 (OA-21172)

```
상황: 호우 경보 48시간 전, 한강변 주민
데이터: 풍수해 침수예상도 (EPSG:5186)
로직:
- 사용자 주소의 침수 위험도 검색
- 고위험: "48시간 내 대피 권고"
- 중위험: "짐 꾸리기 준비"
- 폴리곤 시각화 (침수 범위 표시)
```

### 시나리오 12: 화학 물질 누출 시 "유해물질 취급시설 확인 + 응급실"

```
상황: 불명의 화학 냄새 감지
데이터: 유해화학 취급시설 (LX 융합데이터, EPSG:5186)
로직:
- 반경 2km 내 화학 취급시설 검색
- 해당 시설에서 누출 가능성 확인
- 즉시 응급실로 안내 (화학 전문)
- 119 상황실에 시설 정보 전송 (대응 신속화)
```

---

## 개발자 체크리스트: 각 시나리오 구현 시

```
☐ 데이터 출처 명시 (서울 열린데이터광장 OA-XXXXX)
☐ CRS 확인 (EPSG:5186 vs EPSG:5174 vs WGS84)
☐ API 호출 빈도 (실시간 vs 일일 갱신)
☐ 필터링 로직 (현재 상태, 운영시간, 혼잡도)
☐ 거리/시간 계산 (도보 vs 차량)
☐ 실시간 데이터 연동 (침상 수, 대기 시간)
☐ 최악의 시나리오 (데이터 없을 때)
☐ 지도상 시각화 (위치, 경로, 폴리곤)
☐ 음성/문자 알림
☐ 근거 제시 (Plan → Evidence → Guidance)
```

---

## 핵심: "데이터 → 사람의 행동"

| 정부 데이터 | SENSE 의사결정 | 사용자 행동 |
|-----------|-------------|----------|
| AED 위치 (OA-20327) | 가장 가까운 AED 제시 | 85m 이내로 달려가기 |
| 응급실 혼잡도 | 가장 빠른 응급실 추천 | 20분 대기 vs 180분 대기 선택 |
| 약국 운영시간 (OA-20402) | "지금 열어있는가?" 확인 | 밤 11시 30분에 약국 방문 가능 |
| 지진 대피소 (OA-21060) | "건물 vs 옥외" 판단 | 계단으로 내려가기 vs 탁자 아래 |

**결론**: 공공 데이터가 정확하고 실시간이면, 생명을 구하는 시스템이 됩니다.


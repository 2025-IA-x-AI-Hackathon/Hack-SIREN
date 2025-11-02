# -*- coding: utf-8 -*-
"""
완전한 그래프 스키마 생성 스크립트
preprocessing01.ipynb의 결과를 사용하여 이미지의 모든 노드와 관계를 생성
"""

import pandas as pd
import numpy as np
from math import radians, sin, cos, sqrt, atan2
import glob
from pathlib import Path
import os

# 설정
DATA_DIR = 'data'
PROCESSED_DIR = 'data/processed'
OUTPUT_DIR = 'data/processed'
DOCS_DIR = 'docs'

print("=" * 80)
print("완전한 그래프 스키마 생성")
print("=" * 80)


print("\n[1] 전처리된 데이터 로드...")

data = {}
files = {
    'outdoor_shelter': 'outdoor_shelter_clean.csv',
    'indoor_shelter': 'indoor_shelter_clean.csv',
    'temporary_housing': 'temporary_housing_clean.csv',
    'water_facility': 'water_facility_clean.csv',
    'risk_zone': 'risk_zone_clean.csv',
    'casualty_risk': 'casualty_risk_clean.csv',
    'landslide_risk': 'landslide_risk_clean.csv',
    'collapse_risk': 'collapse_risk_clean.csv',
    'old_facility': 'old_facility_clean.csv'
}

for key, filename in files.items():
    filepath = f'{PROCESSED_DIR}/{filename}'
    if os.path.exists(filepath):
        data[key] = pd.read_csv(filepath, encoding='utf-8-sig')
        print(f"  - {key}: {len(data[key])} rows")


print("\n[2] Hazard 노드 생성...")

hazard_nodes = [
    {
        'id': 'hazard_earthquake',
        'type': 'Hazard',
        'hazard_type': '지진',
        'hazard_code': 'EQ',
        'name': '지진',
        'description': '지진으로 인한 재난',
        'severity': 'HIGH'
    },
    {
        'id': 'hazard_aging',
        'type': 'Hazard',
        'hazard_type': '노화',
        'hazard_code': 'AGING',
        'name': '노화',
        'description': '시설물 노화로 인한 위험',
        'severity': 'MEDIUM'
    },
    {
        'id': 'hazard_landslide',
        'type': 'Hazard',
        'hazard_type': '산사태',
        'hazard_code': 'LS',
        'name': '산사태',
        'description': '산사태로 인한 재난',
        'severity': 'HIGH'
    },
    {
        'id': 'hazard_collapse',
        'type': 'Hazard',
        'hazard_type': '붕괴',
        'hazard_code': 'COLLAPSE',
        'name': '붕괴',
        'description': '구조물 붕괴 재난',
        'severity': 'CRITICAL'
    }
]

print(f"  Hazard 노드: {len(hazard_nodes)} 개")


print("\n[3] Object 노드 준비...")

# preprocessing01의 neo4j_nodes.csv 로드
nodes_file = f'{PROCESSED_DIR}/neo4j_nodes.csv'
if os.path.exists(nodes_file):
    existing_nodes_df = pd.read_csv(nodes_file, encoding='utf-8-sig')
    print(f"  기존 노드 로드: {len(existing_nodes_df)} 개")
    
    # 노드를 딕셔너리 리스트로 변환
    object_nodes = existing_nodes_df.to_dict('records')
else:
    print("  경고: neo4j_nodes.csv 파일이 없습니다!")
    object_nodes = []


print("\n[4] Policy 노드 생성 (CSV 파일 기반)...")

policy_nodes = []

# CSV 파일에서 행동요령 데이터 읽기
policy_files = {
    'social_disaster': f'{DATA_DIR}/행정안전부_사회재난국민행동요령.csv',
    'life_safety': f'{DATA_DIR}/행정안전부_생활안전국민행동요령.csv'
}

for policy_type, csv_path in policy_files.items():
    try:
        # 인코딩 감지하여 읽기
        try:
            df_policy = pd.read_csv(csv_path, encoding='cp949')
        except:
            df_policy = pd.read_csv(csv_path, encoding='utf-8')
        
        print(f"  {policy_type} 로드: {len(df_policy)} 개")
        
        for idx, row in df_policy.iterrows():
            # 재난 유형 매핑
            disaster_type = row.get('카테고리2명칭', '기타')
            related_hazard = None
            
            # 카테고리에 따라 관련 Hazard 매핑
            if "지진" in str(disaster_type):
                related_hazard = "hazard_earthquake"
            elif "산사태" in str(disaster_type) or "산행" in str(disaster_type):
                related_hazard = "hazard_landslide"
            elif "붕괴" in str(disaster_type) or "폭발" in str(disaster_type) or "건물" in str(disaster_type):
                related_hazard = "hazard_collapse"
            elif "노후" in str(disaster_type) or "시설" in str(disaster_type):
                related_hazard = "hazard_aging"
            
            # Policy ID 생성
            cat1 = str(row.get('카테고리1코드', '')).replace('.0', '')
            cat2 = str(row.get('카테고리2코드', '')).replace('.0', '')
            cat3 = str(row.get('카테고리3코드', '')).replace('.0', '')
            policy_id = f"{policy_type}_{cat1}_{cat2}_{cat3}"
            
            # 행동요령 내용
            content = str(row.get('콘텐츠 내용', ''))
            url = str(row.get('콘텐츠 URL', ''))
            
            # Policy 명칭 구성
            cat1_name = str(row.get('카테고리1명칭', ''))
            cat2_name = str(row.get('카테고리2명칭', ''))
            cat3_name = str(row.get('카테고리3명칭', ''))
            policy_name = f"{cat1_name} > {cat2_name} > {cat3_name}"
            
            policy_nodes.append({
                'id': policy_id,
                'type': 'Policy',
                'policy_id': policy_id,
                'name': policy_name,
                'disaster_type': disaster_type,
                'category1': cat1_name,
                'category2': cat2_name,
                'category3': cat3_name,
                'related_hazard': related_hazard,
                'content': content[:500] if len(content) > 500 else content,
                'url': url,
                'content_length': len(content),
                'source': policy_type
            })
    except Exception as e:
        print(f"  Policy 로드 실패 {policy_type}: {e}")

print(f"  Policy 노드: {len(policy_nodes)} 개")


print("\n[5] Event 노드 생성...")

event_nodes = [
    {
        'id': 'event_earthquake_2024',
        'type': 'Event',
        'event_type': '지진',
        'name': '2024년 서울 지진 시나리오',
        'date': '2024-01-01',
        'magnitude': 5.5,
        'pga': 0.15,
        'description': '가상의 지진 시나리오'
    },
    {
        'id': 'event_heavy_rain_2024',
        'type': 'Event',
        'event_type': '강우',
        'name': '2024년 집중호우',
        'date': '2024-07-15',
        'rainfall': 300,
        'duration': 6,
        'description': '집중호우로 인한 산사태 위험'
    }
]

print(f"  Event 노드: {len(event_nodes)} 개")


print("\n[6] 관계 생성...")

relationships = []

# 6.1 TRIGGERS 관계 (Hazard → Hazard)
relationships.extend([
    {
        'from_id': 'hazard_earthquake',
        'from_type': 'Hazard',
        'to_id': 'hazard_landslide',
        'to_type': 'Hazard',
        'relationship_type': 'TRIGGERS',
        'probability': 0.3,
        'description': '지진이 산사태를 유발'
    },
])
print(f"  TRIGGERS: {1} 개")

# 6.2 CAUSES 관계 (Hazard → Hazard)
relationships.extend([
    {
        'from_id': 'hazard_earthquake',
        'from_type': 'Hazard',
        'to_id': 'hazard_collapse',
        'to_type': 'Hazard',
        'relationship_type': 'CAUSES',
        'probability': 0.4,
        'description': '지진이 붕괴를 유발'
    },
    {
        'from_id': 'hazard_landslide',
        'from_type': 'Hazard',
        'to_id': 'hazard_collapse',
        'to_type': 'Hazard',
        'relationship_type': 'CAUSES',
        'probability': 0.5,
        'description': '산사태가 붕괴를 유발'
    },
])
print(f"  CAUSES: {2} 개")

# 6.3 INCREASES_RISK_OF 관계
relationships.extend([
    {
        'from_id': 'hazard_aging',
        'from_type': 'Hazard',
        'to_id': 'hazard_collapse',
        'to_type': 'Hazard',
        'relationship_type': 'INCREASES_RISK_OF',
        'risk_increase': 0.6,
        'description': '노화가 붕괴 위험을 증가'
    },
])
print(f"  INCREASES_RISK_OF: {1} 개")

# 6.4 GUIDES 관계 (Policy → Hazard)
# 모든 행동요령은 여러 재난 유형에 적용 가능
guides_count = 0
hazard_list = [h['id'] for h in hazard_nodes]

for policy in policy_nodes:
    # 각 Policy를 모든 Hazard와 연결
    for hazard_id in hazard_list:
        relationships.append({
            'from_id': policy['id'],
            'from_type': 'Policy',
            'to_id': hazard_id,
            'to_type': 'Hazard',
            'relationship_type': 'GUIDES',
            'relevance': 0.5,  # 기본 관련도
            'description': f"{policy['name']} 행동요령"
        })
        guides_count += 1

print(f"  GUIDES (Policy→Hazard): {guides_count} 개")

# 6.5 UPDATES/TRIGGERS 관계 (Event → Hazard)
relationships.extend([
    {
        'from_id': 'event_earthquake_2024',
        'from_type': 'Event',
        'to_id': 'hazard_earthquake',
        'to_type': 'Hazard',
        'relationship_type': 'UPDATES',
        'pga': 0.15,
        'magnitude': 5.5,
        'description': '지진 발생 시 PGA 업데이트'
    },
    {
        'from_id': 'event_heavy_rain_2024',
        'from_type': 'Event',
        'to_id': 'hazard_landslide',
        'to_type': 'Hazard',
        'relationship_type': 'TRIGGERS',
        'rainfall': 300,
        'description': '집중호우가 산사태를 유발'
    },
])
print(f"  UPDATES/TRIGGERS(Event): {2} 개")

# 6.6 기존 관계 로드 (LOCATED_IN 등)
rels_file = f'{PROCESSED_DIR}/neo4j_relationships.csv'
if os.path.exists(rels_file):
    existing_rels_df = pd.read_csv(rels_file, encoding='utf-8-sig')
    existing_rels = existing_rels_df.to_dict('records')
    relationships.extend(existing_rels)
    print(f"  기존 관계 로드: {len(existing_rels)} 개")

# 6.7 공간 기반 관계 생성 (NEAR_BY, EXPOSED_TO, SAFETY_SCORE)
def haversine_distance(lat1, lon1, lat2, lon2):
    """두 지점 간 거리 계산 (km)"""
    R = 6371
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    return R * c

# 공간 관계 계산 (Shelter/Facility ↔ Zone)
spatial_rels_count = 0
if 'outdoor_shelter' in data and 'casualty_risk' in data:
    shelters = data['outdoor_shelter']
    zones = data['casualty_risk']
    
    for _, shelter in shelters.head(100).iterrows():  # 샘플만
        if pd.notna(shelter.get('lat')) and pd.notna(shelter.get('lon')):
            for _, zone in zones.iterrows():
                if pd.notna(zone.get('lat')) and pd.notna(zone.get('lon')):
                    distance = haversine_distance(
                        shelter['lat'], shelter['lon'],
                        zone['lat'], zone['lon']
                    )
                    
                    if distance <= 1.0:  # 1km 이내
                        relationships.append({
                            'from_id': f"shelter_{shelter['shelter_id']}",
                            'from_type': 'Shelter',
                            'to_id': f"zone_casualty_{zone['risk_id']}",
                            'to_type': 'Zone',
                            'relationship_type': 'NEAR_BY',
                            'distance': round(distance, 3)
                        })
                        spatial_rels_count += 1

print(f"  NEAR_BY: {spatial_rels_count} 개")


print("\n[7] 파일 저장...")

# 모든 노드 통합
all_nodes = hazard_nodes + object_nodes + policy_nodes + event_nodes

# DataFrame으로 변환
nodes_df = pd.DataFrame(all_nodes)
relationships_df = pd.DataFrame(relationships)

# 저장
nodes_df.to_csv(
    f'{OUTPUT_DIR}/neo4j_nodes_complete.csv',
    index=False,
    encoding='utf-8-sig'
)

relationships_df.to_csv(
    f'{OUTPUT_DIR}/neo4j_relationships_complete.csv',
    index=False,
    encoding='utf-8-sig'
)

print(f"  노드 저장: neo4j_nodes_complete.csv ({len(nodes_df)} 개)")
print(f"  관계 저장: neo4j_relationships_complete.csv ({len(relationships_df)} 개)")


print("\n" + "=" * 80)
print("완전한 그래프 스키마 생성 완료!")
print("=" * 80)

print(f"\n[노드 통계]")
if len(nodes_df) > 0 and 'type' in nodes_df.columns:
    print(nodes_df['type'].value_counts())

print(f"\n[관계 통계]")
if len(relationships_df) > 0 and 'relationship_type' in relationships_df.columns:
    print(relationships_df['relationship_type'].value_counts())

print(f"\n총 노드: {len(nodes_df)} 개")
print(f"총 관계: {len(relationships_df)} 개")
print("=" * 80)


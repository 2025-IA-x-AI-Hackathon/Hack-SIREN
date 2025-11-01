


<div align="center">

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![Flutter](https://img.shields.io/badge/Flutter-3.9.2-blue.svg)
![Platform](https://img.shields.io/badge/platform-Android-lightgrey.svg)

**실시간 재난 알림 및 대응 지원 시스템**

</div>

## 개요

**SENSE**는 재난 상황에서 실시간으로 알림을 받고, 상황에 맞는 행동 지침을 제공하며, 위치 정보와 층수 정보를 서버로 전송하여 효율적인 대피 및 구조 활동을 지원하는 모바일 애플리케이션입니다.

### 핵심 가치
- **실시간 재난 알림**: 수신된 재난 문자를 자동으로 감지 및 파싱
- **상황 인식 대화**: 재난 유형별 맞춤형 대화방 생성
- **위치 기반 서비스**: 현재 위치 및 층수 정보 제공
- **대피 경로 안내**: 지도 기반 대피소 위치 표시
- **데이터 전송**: 재난 상황 데이터를 서버로 실시간 전송

## 주요 기능

### 1. 재난 문자 자동 감지 및 파싱 (Android/Kotlin)

Android 기기에서 수신된 재난 문자(SMS)를 자동으로 감지하고, Flutter 앱으로 전달하는 네이티브 모듈입니다.

**기능:**
- `BroadcastReceiver`를 통한 실시간 SMS 수신 감지
- 키워드 기반 재난 문자 필터링
- `EventChannel`을 통한 Flutter-Native 통신

**지원하는 재난 유형:**
- 지진
- 화재
- 민방위 경보
- 기타 재난 상황

**위험 수준 분류:**
- 🟢 주의 (Advisory)
- 🟠 경보 (Warning)
- 🔴 위기 (Critical)

### 2. 지능형 대화 시스템 (Flutter)

#### 재난 문자 → 자동 대화 생성
수신된 재난 문자가 자동으로 파싱되어 새로운 대화방이 생성되고, 서버로 즉시 전송됩니다.

#### 새 대화 시작
사용자가 재난 관련 문의를 직접 시작할 수 있는 기능입니다. 입력한 메시지는 서버로 전송됩니다.

#### 테스트 시작
재난 상황 시뮬레이션을 위한 테스트 모드입니다. 실제 재난 문자가 수신된 이후의 상황을 가정하여 전체 워크플로우를 테스트할 수 있습니다.

### 3. 채팅방 기능

각 채팅방은 다음과 같은 정보를 제공합니다:

#### 현재 위치
- GPS 기반 실시간 위치 정보
- 주소 변환 (Geocoding)

#### 비상 연락
- **지인 연락**: 등록된 비상 연락처로 전화
- **119 긴급 신고**: 원터치 119 신고

#### 재난 정보 제공
- **재난 상세 내용**: 파싱된 재난 정보의 상세 설명
- **행동 지침**: 재난 유형별 맞춤형 행동 요령
- **지도 데이터**: 위험 지역 및 대피소 위치 표시

### 4. 서버 API 통신

모든 메시지와 재난 데이터는 서버로 실시간 전송됩니다.

**전송 데이터:**
- 재난 문자 원문 및 파싱 결과
- 사용자 입력 메시지
- 위치 정보
- 층수 예측 데이터
- 타임스탬프 및 메타데이터

### 5. 기압 기반 층수 예측

바로미터 센서를 활용하여 현재 층수를 예측하고 서버로 전송합니다.

**기능:**
- 실시간 기압 센서 데이터 수집
- 캘리브레이션된 기준층(1층) 대비 상대 고도 계산
- 건물 프로필(층고, 지하층 고도) 기반 층수 추정
- EMA(Exponential Moving Average) 필터를 통한 노이즈 제거

**계산 공식:**
ΔH = 29.27 × T × ln(P₀/P)
예상 층수 = 기준층 + (ΔH / 층고)

---

## 시작하기

### 필수 요구사항

- Flutter SDK 3.9.2 이상
- Android Studio 또는 VS Code
- Android SDK (Android 21 이상)
- Kotlin 지원

### 설치 및 실행

1. **저장소 클론**
```bash
git clone <repository-url>
cd temp_sense
```

2. **의존성 설치**
```bash
flutter pub get
```

3. **Android 권한 설정**
앱에서 다음 권한이 필요합니다:
- `RECEIVE_SMS`: 재난 문자 수신
- `READ_SMS`: SMS 읽기
- `ACCESS_FINE_LOCATION`: 정확한 위치 정보
- `CALL_PHONE`: 비상 통화

4. **실행**
```bash
flutter run
```

### 환경 변수 설정

기본값: `http://10.0.2.2:8080`

## 프로젝트 구조

### 핵심 모듈 설명

#### 1. Alert Module (`features/alert/`)
재난 문자 수신 및 파싱을 담당합니다.

- **SmsReceiver.kt**: Android BroadcastReceiver로 SMS 수신
- **DisasterAlertNotifier**: Flutter에서 재난 알림 상태 관리
- **disaster_alert_provider.dart**: 재난 유형 파싱 및 메시지 변환

#### 2. Message Module (`features/message/`)
메시지 데이터 모델 및 서버 통신을 담당합니다.

- **Message Entity**: 도메인 모델 (id, roomId, kind, text, payload, ts, mine)
- **MessageDto**: 서버 통신용 DTO
- **room_messages_provider.dart**: 채팅방별 메시지 관리

#### 3. Incident Module (`features/incident/`)
재난 대응 화면을 제공합니다.

- **incident_screen.dart**: 탭 기반 메인 화면
- **chat.dart**: 채팅 및 재난 정보 표시 UI
- **feed_tab.dart**: 상세 브리핑 화면

#### 4. Room List Module (`features/room_list/`)
대화방 목록 관리 및 필터링을 담당합니다.

- **room_list_page.dart**: 대화방 목록 UI
- **room_list_provider.dart**: 대화방 상태 관리 및 CRUD

#### 5. Estimator Module (`features/estimator/`)
기압 센서 기반 층수 예측을 담당합니다.

- **FloorEstimator**: 층수 계산 알고리즘
- **BuildingProfile**: 건물 정보 (층고, 기준층 등)
- **SensorController**: 센서 데이터 수집 및 필터링

## 주요 기능 상세

### 재난 문자 자동 처리 플로우

```
1. Android SMS 수신
   ↓
2. SmsReceiver.onReceive()
   ↓
3. 키워드 기반 필터링 (isDisasterAlert)
   ↓
4. EventChannel으로 Flutter 전달
   ↓
5. DisasterAlertStream에서 수신
   ↓
6. DisasterAlertNotifier에서 파싱
   ↓
7. Message 객체 생성 및 roomListProvider에 추가
   ↓
8. 서버로 전송 (MessageApi.send)
   ↓
9. UI 자동 업데이트
```
import 'package:flutter_riverpod/legacy.dart';
import 'package:sense/src/features/message/domain/entities/message.dart';

class RoomMessagesNotifier extends StateNotifier<List<Message>> {
  RoomMessagesNotifier(this.roomId, List<Message> initialMessages)
    : super(_getRoomMessages(initialMessages, roomId));
  final String roomId;

  static List<Message> _getRoomMessages(
    List<Message> allMessages,
    String roomId,
  ) {
    final roomMessages = allMessages
        .where((msg) => msg.roomId == roomId)
        .toList();
    if (roomMessages.isNotEmpty) {
      roomMessages.sort((a, b) => a.ts.compareTo(b.ts));
      return roomMessages;
    }
    if (roomId.startsWith('chat-')) {
      return [];
    }
    return _mock(roomId);
  }

  static String _formatDateTime(DateTime dateTime) {
    final year = dateTime.year;
    final month = dateTime.month.toString().padLeft(2, '0');
    final day = dateTime.day.toString().padLeft(2, '0');
    final hour = dateTime.hour.toString().padLeft(2, '0');
    final minute = dateTime.minute.toString().padLeft(2, '0');
    return '$year년 $month월 $day일 $hour:$minute';
  }

  static List<Message> _mock(String roomId) {
    final now = DateTime.now();
    switch (roomId) {
      case 'alert-fire-001':
        return [
          Message(
            id: 'm-fire-1',
            roomId: roomId,
            kind: MsgKind.hazard,
            text: '대규모 산불 발생',
            payload: {
              'title': '대규모 산불',
              'type': 'fire',
              'riskLevel': '위기',
              'level': 'severe',
              'detailText':
                  '''대규모 산불이 ${_formatDateTime(now.subtract(const Duration(minutes: 45)))} 강원도 지역에서 발생했습니다.

산불은 강한 바람을 타고 빠르게 확산되고 있으며, 현재 여러 주거 지역으로 번져가고 있습니다.

강원도 지역 주민 대피 명령이 발령되었습니다. 화재 구역으로부터 최소 5km 이상 떨어진 안전한 대피소로 즉시 이동하시기 바랍니다.

현재 산불 진압 작업이 진행 중이며, 소방헬기와 지상 진압대가 총동원되어 화재를 억제하기 위해 노력하고 있습니다.

안전 선언이 있을 때까지는 절대 귀가하지 마시고, 지정된 대피소에서 대기하시기 바랍니다. 호흡기 질환이 있으신 분은 특히 주의하시기 바랍니다.''',
            },
            ts: now.subtract(const Duration(minutes: 45)),
            mine: false,
          ),
          Message(
            id: 'm-fire-2',
            roomId: roomId,
            kind: MsgKind.map,
            text: '화재 구역 지도 업데이트',
            payload: {
              'bbox': [128.0, 37.5, 128.5, 38.0],
            },
            ts: now.subtract(const Duration(minutes: 42)),
            mine: false,
          ),
          Message(
            id: 'm-fire-3',
            roomId: roomId,
            kind: MsgKind.guideline,
            text: '즉시 대피하세요. 대피소 위치를 확인하고 화재 구역에 접근하지 마세요.',
            payload: {
              'bullets': ['지정된 대피소로 이동', '화재 구역 회피', '안전 선언 전까지 귀가 금지'],
            },
            ts: now.subtract(const Duration(minutes: 40)),
            mine: false,
          ),
          Message(
            id: 'm-fire-4',
            roomId: roomId,
            kind: MsgKind.hazard,
            text: '산불 확산 속도 증가',
            payload: {
              'level': 'critical',
              'detailText':
                  '''${_formatDateTime(now.subtract(const Duration(minutes: 35)))} 산불 확산 속도가 급격히 증가하고 있습니다.

바람 방향이 주거 지역 쪽으로 변경되면서 화재 위험 지역이 확대되었습니다.

추가 대피 명령이 발령되었으며, 인근 지역 주민들도 즉시 대피 준비를 하시기 바랍니다.

소방 당국은 헬기 및 지상 진압 작업을 강화하고 있으며, 주민 대피를 최우선으로 진행하고 있습니다.''',
            },
            ts: now.subtract(const Duration(minutes: 35)),
            mine: false,
          ),
          Message(
            id: 'm-fire-5',
            roomId: roomId,
            kind: MsgKind.map,
            text: '확대된 화재 구역 지도',
            payload: {
              'bbox': [127.8, 37.3, 128.7, 38.2],
            },
            ts: now.subtract(const Duration(minutes: 33)),
            mine: false,
          ),
          Message(
            id: 'm-fire-6',
            roomId: roomId,
            kind: MsgKind.guideline,
            text: '마스크 착용 필수. 통풍이 잘 되는 곳으로 대피하세요.',
            payload: {
              'bullets': [
                '마스크 또는 손수건으로 호흡기 보호',
                '통풍이 잘 되는 안전한 대피소로 이동',
                '화재 연기 기류 방향 확인',
                '긴급 연락처 확인',
              ],
            },
            ts: now.subtract(const Duration(minutes: 30)),
            mine: false,
          ),
          Message(
            id: 'm-fire-7',
            roomId: roomId,
            kind: MsgKind.map,
            text: '대피소 및 안전 통로 지도',
            payload: {
              'bbox': [127.9, 37.4, 128.6, 38.1],
            },
            ts: now.subtract(const Duration(minutes: 28)),
            mine: false,
          ),
          Message(
            id: 'm-fire-8',
            roomId: roomId,
            kind: MsgKind.chat,
            text: '가장 가까운 대피소가 어디인가요?',
            ts: now.subtract(const Duration(minutes: 25)),
            mine: true,
          ),
          Message(
            id: 'm-fire-9',
            roomId: roomId,
            kind: MsgKind.chat,
            text: '지도에서 초록색으로 표시된 대피소 위치를 확인해주세요.',
            ts: now.subtract(const Duration(minutes: 24)),
            mine: false,
          ),
          Message(
            id: 'm-fire-10',
            roomId: roomId,
            kind: MsgKind.guideline,
            text: '산불 진압 진행 상황 안내',
            payload: {
              'bullets': [
                '진압률 40% 달성',
                '헬기 15대 투입 중',
                '지상 진압대 200명 활동 중',
                '예상 진압 시간: 3-4시간',
              ],
            },
            ts: now.subtract(const Duration(minutes: 20)),
            mine: false,
          ),
        ]..sort((a, b) => a.ts.compareTo(b.ts));

      case 'alert-earthquake-001':
        return [
          Message(
            id: 'm-eq-1',
            roomId: roomId,
            kind: MsgKind.hazard,
            text: '규모 5.4 지진 발생',
            payload: {
              'title': '규모 5.4 지진',
              'type': 'earthquake',
              'riskLevel': '경보',
              'level': 'warning',
              'magnitude': '5.4',
              'location': '경북 포항시 북구 북쪽 9km',
              'depth': '10km',
              'detailText':
                  '''규모 5.4 지진이 ${_formatDateTime(now.subtract(const Duration(minutes: 50)))}에 발생했습니다.

진앙지는 경북 포항시 북구에서 북쪽으로 9km 떨어진 지점이며, 깊이는 10km입니다.

이번 지진은 전국 대부분의 지역에서 진동이 감지되었으며, 서울 지역에서도 미세한 진동이 감지되었습니다.

현재까지 인명 피해는 없으나, 일부 건물에 균열 등 재산 피해가 보고되고 있습니다. 정부는 중앙재난안전대책본부를 가동하고 '주의' 단계의 재난 경보를 발령했습니다.

여진 발생 가능성이 있으니 안전한 곳에서 대기하시기 바랍니다. 건물 내부에 계신 경우, 튼튼한 탁자나 책상 아래로 들어가 몸을 보호하세요. 전기와 가스는 차단하고, 문을 열어 출구를 확보하세요.

건물 밖으로 대피할 경우에는 반드시 계단을 이용하시고, 주변의 낙하물에 주의하시기 바랍니다.''',
            },
            ts: now.subtract(const Duration(minutes: 50)),
            mine: false,
          ),
          Message(
            id: 'm-eq-2',
            roomId: roomId,
            kind: MsgKind.guideline,
            text: '안전한 곳으로 대피하세요. 손상된 건물에서 멀리 떨어지고 여진에 대비하세요.',
            payload: {
              'bullets': ['넓은 공간으로 이동', '엘리베이터 사용 금지', '여진 주의', '건물 안전 점검'],
            },
            ts: now.subtract(const Duration(minutes: 48)),
            mine: false,
          ),
          Message(
            id: 'm-eq-3',
            roomId: roomId,
            kind: MsgKind.map,
            text: '지진 영향 지역 지도',
            payload: {
              'bbox': [129.3, 36.0, 129.4, 36.1],
            },
            ts: now.subtract(const Duration(minutes: 45)),
            mine: false,
          ),
          Message(
            id: 'm-eq-4',
            roomId: roomId,
            kind: MsgKind.hazard,
            text: '규모 3.2 여진 발생',
            payload: {
              'level': 'watch',
              'magnitude': '3.2',
              'location': '경북 포항시 북구',
              'depth': '8km',
              'detailText':
                  '''${_formatDateTime(now.subtract(const Duration(minutes: 40)))} 규모 3.2의 여진이 발생했습니다.

본진 발생 후 10분 만에 발생한 첫 번째 여진으로, 진앙지는 본진과 거의 동일한 위치입니다.

여진은 앞으로 며칠간 계속 발생할 수 있으니 안전한 장소에서 대기하시기 바랍니다.

건물 내부에 있으신 분들은 안전한 곳으로 이동하시고, 주변의 낙하물에 주의하시기 바랍니다.''',
            },
            ts: now.subtract(const Duration(minutes: 40)),
            mine: false,
          ),
          Message(
            id: 'm-eq-5',
            roomId: roomId,
            kind: MsgKind.guideline,
            text: '여진 대비 행동 요령',
            payload: {
              'bullets': [
                '넓은 공간에서 대기',
                '건물 내부 피하기',
                '전기 및 가스 차단 유지',
                '비상용품 준비',
              ],
            },
            ts: now.subtract(const Duration(minutes: 38)),
            mine: false,
          ),
          Message(
            id: 'm-eq-6',
            roomId: roomId,
            kind: MsgKind.map,
            text: '안전 대피소 위치 지도',
            payload: {
              'bbox': [129.25, 35.95, 129.45, 36.15],
            },
            ts: now.subtract(const Duration(minutes: 35)),
            mine: false,
          ),
          Message(
            id: 'm-eq-7',
            roomId: roomId,
            kind: MsgKind.hazard,
            text: '구조 안전 점검 완료',
            payload: {
              'level': 'advisory',
              'detailText':
                  '''${_formatDateTime(now.subtract(const Duration(minutes: 30)))} 긴급 구조 안전 점검이 완료되었습니다.

주요 건물들의 구조 안전이 확인되었으며, 일부 경미한 손상 건물에 대해서는 접근 금지 조치가 내려졌습니다.

안전이 확인된 건물로의 복귀는 허용되나, 여진 발생 가능성이 여전히 있으므로 주의가 필요합니다.

피해 복구 작업이 진행 중이며, 지속적인 여진 모니터링을 실시하고 있습니다.''',
            },
            ts: now.subtract(const Duration(minutes: 30)),
            mine: false,
          ),
          Message(
            id: 'm-eq-8',
            roomId: roomId,
            kind: MsgKind.chat,
            text: '안에 들어가도 안전한가요?',
            ts: now.subtract(const Duration(minutes: 25)),
            mine: true,
          ),
          Message(
            id: 'm-eq-9',
            roomId: roomId,
            kind: MsgKind.chat,
            text: '구조 안전이 확인될 때까지 대기하세요. 여진이 발생할 수 있습니다.',
            ts: now.subtract(const Duration(minutes: 24)),
            mine: false,
          ),
          Message(
            id: 'm-eq-10',
            roomId: roomId,
            kind: MsgKind.guideline,
            text: '피해 복구 및 지원 안내',
            payload: {
              'bullets': [
                '긴급 구조 지원 신고: 119',
                '재산 피해 신고: 지역 주민센터',
                '임시 거처 지원 문의',
                '심리 상담 서비스 이용',
              ],
            },
            ts: now.subtract(const Duration(minutes: 20)),
            mine: false,
          ),
        ]..sort((a, b) => a.ts.compareTo(b.ts));

      case 'alert-flood-001':
        return [
          Message(
            id: 'm-flood-1',
            roomId: roomId,
            kind: MsgKind.hazard,
            text: '호우로 인한 하천 범람',
            payload: {
              'title': '호우로 인한 하천 범람',
              'type': 'flood',
              'riskLevel': '주의',
              'level': 'advisory',
              'detailText':
                  '''호우로 인한 하천 범람이 ${_formatDateTime(now.subtract(const Duration(hours: 3, minutes: 30)))} 수도권 지역에서 발생했습니다.

강우량이 시간당 50mm를 초과하며 계속 증가하고 있어 하천 수위가 급상승하고 있습니다.

저지대 주민은 즉시 대피해야 합니다. 침수 지역을 통과하려고 하지 마시고, 반드시 고지대로 이동하시기 바랍니다.

하천과 계류 근처는 위험하니 접근하지 마시고, 침수된 도로에는 절대 진입하지 마세요.

기상청에 따르면 호우가 몇 시간 더 지속될 것으로 예상되므로, 안전한 장소에서 추가 안내를 기다리시기 바랍니다.''',
            },
            ts: now.subtract(const Duration(hours: 3, minutes: 30)),
            mine: false,
          ),
          Message(
            id: 'm-flood-2',
            roomId: roomId,
            kind: MsgKind.map,
            text: '범람 위험 지역 지도',
            payload: {
              'bbox': [126.9, 37.4, 127.1, 37.6],
            },
            ts: now.subtract(const Duration(hours: 3, minutes: 25)),
            mine: false,
          ),
          Message(
            id: 'm-flood-3',
            roomId: roomId,
            kind: MsgKind.guideline,
            text: '저지대 주민은 즉시 대피해야 합니다. 침수 지역을 통과하려고 하지 마세요.',
            payload: {
              'bullets': ['저지대 지역 대피', '하천 및 계류 회피', '침수 도로 주행 금지', '고지대로 이동'],
            },
            ts: now.subtract(const Duration(hours: 3, minutes: 20)),
            mine: false,
          ),
          Message(
            id: 'm-flood-4',
            roomId: roomId,
            kind: MsgKind.hazard,
            text: '하천 수위 급상승 경보',
            payload: {
              'level': 'warning',
              'detailText':
                  '''${_formatDateTime(now.subtract(const Duration(hours: 2, minutes: 45)))} 한강과 탄천 수위가 위험 수위를 초과했습니다.

계속되는 호우로 인해 하천 수위가 빠르게 상승하고 있으며, 일부 저지대 지역에 침수 피해가 발생하고 있습니다.

강변 도로 일부가 통제되었으며, 하천 주변 접근이 전면 금지되었습니다.

저지대 주민들의 즉시 대피가 필요하며, 비상 대피소가 운영되고 있습니다.''',
            },
            ts: now.subtract(const Duration(hours: 2, minutes: 45)),
            mine: false,
          ),
          Message(
            id: 'm-flood-5',
            roomId: roomId,
            kind: MsgKind.map,
            text: '침수 지역 및 대피 경로 지도',
            payload: {
              'bbox': [126.85, 37.35, 127.15, 37.65],
            },
            ts: now.subtract(const Duration(hours: 2, minutes: 40)),
            mine: false,
          ),
          Message(
            id: 'm-flood-6',
            roomId: roomId,
            kind: MsgKind.guideline,
            text: '비상 대피소 운영 안내',
            payload: {
              'bullets': [
                '주민센터 및 체육관 비상 대피소 개방',
                '대피소 위치: 앱 지도 참조',
                '필수품 지참: 신분증, 의약품, 휴대폰 충전기',
                '대피 시 동물 미반입 원칙',
              ],
            },
            ts: now.subtract(const Duration(hours: 2, minutes: 35)),
            mine: false,
          ),
          Message(
            id: 'm-flood-7',
            roomId: roomId,
            kind: MsgKind.hazard,
            text: '호우 예보 연장',
            payload: {
              'level': 'advisory',
              'detailText':
                  '''${_formatDateTime(now.subtract(const Duration(hours: 2, minutes: 15)))} 기상청이 호우 예보를 오후 6시까지 연장 발표했습니다.

시간당 30-50mm의 강우가 지속될 것으로 예상되며, 하천 수위는 오후까지 상승세를 유지할 전망입니다.

침수 위험 지역 주민들은 즉시 대피소로 이동하시기 바랍니다.

침수된 도로를 통과하려고 하지 마시고, 특히 지하차도나 저지대 도로는 절대 이용하지 마세요.''',
            },
            ts: now.subtract(const Duration(hours: 2, minutes: 15)),
            mine: false,
          ),
          Message(
            id: 'm-flood-8',
            roomId: roomId,
            kind: MsgKind.map,
            text: '현재 하천 수위 및 침수 지역 지도',
            payload: {
              'bbox': [126.88, 37.38, 127.12, 37.62],
            },
            ts: now.subtract(const Duration(hours: 2, minutes: 10)),
            mine: false,
          ),
          Message(
            id: 'm-flood-9',
            roomId: roomId,
            kind: MsgKind.chat,
            text: '언제까지 계속될까요?',
            ts: now.subtract(const Duration(hours: 1, minutes: 45)),
            mine: true,
          ),
          Message(
            id: 'm-flood-10',
            roomId: roomId,
            kind: MsgKind.chat,
            text: '호우가 몇 시간 더 지속될 것으로 예상됩니다. 추가 안내가 있을 때까지 안전한 장소에 머물러 주세요.',
            ts: now.subtract(const Duration(hours: 1, minutes: 44)),
            mine: false,
          ),
        ]..sort((a, b) => a.ts.compareTo(b.ts));

      case 'alert-power-001':
        final powerOutageTime = now.subtract(const Duration(hours: 2));
        return [
          Message(
            id: 'm-power-1',
            roomId: roomId,
            kind: MsgKind.hazard,
            text: '대규모 정전 발생',
            payload: {
              'title': '대규모 정전',
              'type': 'power_outage',
              'riskLevel': '주의',
              'level': 'watch',
              'detailText':
                  '''서울 및 경기 일부 지역에서 대규모 정전이 ${_formatDateTime(powerOutageTime)} 발생했습니다.

전력 공급 시설의 고장으로 인해 광역 정전이 발생했으며, 현재 한국전력공사가 긴급 복구 작업을 진행 중입니다.

예상 복구 시간은 3시간 내이며, 복구 작업이 완료되면 단계적으로 전력이 공급될 예정입니다.

전력이 돌아올 때 발생할 수 있는 서지(순간적인 고전압)로 인한 전자제품 손상을 방지하기 위해 민감한 전자제품의 플러그를 뽑아두시기 바랍니다.

양초 대신 손전등을 사용하고, 냉장고 문은 최소한으로만 여시며, 전력 절약에 협조해주시기 바랍니다.''',
            },
            ts: powerOutageTime,
            mine: false,
          ),
          Message(
            id: 'm-power-2',
            roomId: roomId,
            kind: MsgKind.map,
            text: '영향 지역 지도',
            payload: {
              'bbox': [126.8, 37.4, 127.2, 37.7],
            },
            ts: powerOutageTime.add(const Duration(minutes: 5)),
            mine: false,
          ),
          Message(
            id: 'm-power-3',
            roomId: roomId,
            kind: MsgKind.guideline,
            text: '3시간 내 복구 예상. 전력이 돌아오면 전력 절약에 협조해주세요.',
            payload: {
              'bullets': [
                '양초 대신 손전등 사용',
                '냉장고 문 최소한으로 열기',
                '민감한 전자제품 플러그 뽑기',
                '정전 신고',
              ],
            },
            ts: powerOutageTime.add(const Duration(minutes: 10)),
            mine: false,
          ),
          Message(
            id: 'm-power-4',
            roomId: roomId,
            kind: MsgKind.hazard,
            text: '복구 작업 진행 상황',
            payload: {
              'level': 'watch',
              'detailText':
                  '''${_formatDateTime(powerOutageTime.add(const Duration(minutes: 30)))} 복구 작업이 진행 중입니다.

한국전력공사가 고장 시설 수리를 위해 긴급 차단기를 교체하고 있으며, 일부 지역에 단계적 전력 공급을 시작했습니다.

예상 복구 시간은 약 2시간 30분 정도 남았으며, 복구 작업이 완료되는 대로 지역별로 전력이 공급될 예정입니다.

전력이 돌아올 때 발생할 수 있는 순간적인 고전압(서지)에 대비하여 민감한 전자제품은 플러그를 뽑아두시기 바랍니다.''',
            },
            ts: powerOutageTime.add(const Duration(minutes: 30)),
            mine: false,
          ),
          Message(
            id: 'm-power-5',
            roomId: roomId,
            kind: MsgKind.map,
            text: '복구 진행 지역 지도',
            payload: {
              'bbox': [126.85, 37.45, 127.15, 37.65],
            },
            ts: powerOutageTime.add(const Duration(minutes: 35)),
            mine: false,
          ),
          Message(
            id: 'm-power-6',
            roomId: roomId,
            kind: MsgKind.guideline,
            text: '정전 중 안전 수칙',
            payload: {
              'bullets': [
                '양초 사용 시 화재 주의',
                '냉장고 내 식품 관리',
                '휴대폰 배터리 절약 사용',
                '비상 연락망 확인',
              ],
            },
            ts: powerOutageTime.add(const Duration(minutes: 45)),
            mine: false,
          ),
          Message(
            id: 'm-power-7',
            roomId: roomId,
            kind: MsgKind.chat,
            text: '전력이 언제 복구되나요?',
            ts: powerOutageTime.add(const Duration(minutes: 60)),
            mine: true,
          ),
          Message(
            id: 'm-power-8',
            roomId: roomId,
            kind: MsgKind.chat,
            text: '예상 복구 시간은 3시간입니다. 복구 작업을 진행하고 있습니다.',
            ts: powerOutageTime.add(const Duration(minutes: 61)),
            mine: false,
          ),
          Message(
            id: 'm-power-9',
            roomId: roomId,
            kind: MsgKind.hazard,
            text: '일부 지역 전력 복구 완료',
            payload: {
              'level': 'advisory',
              'detailText':
                  '''${_formatDateTime(powerOutageTime.add(const Duration(minutes: 90)))} 일부 지역의 전력 공급이 복구되었습니다.

서울 강남구, 송파구 일대와 경기 성남시 일부 지역에 전력이 공급되었으며, 나머지 지역도 순차적으로 복구될 예정입니다.

전력이 돌아온 지역에서는 전력 사용량을 최소화하여 공급 안정성을 유지해주시기 바랍니다.

복구되지 않은 지역의 주민들께서는 조금만 더 기다려주시기 바랍니다. 복구 작업이 빠르게 진행되고 있습니다.''',
            },
            ts: powerOutageTime.add(const Duration(minutes: 90)),
            mine: false,
          ),
          Message(
            id: 'm-power-10',
            roomId: roomId,
            kind: MsgKind.map,
            text: '전력 복구 지역 지도',
            payload: {
              'bbox': [126.9, 37.48, 127.1, 37.55],
            },
            ts: powerOutageTime.add(const Duration(minutes: 95)),
            mine: false,
          ),
        ]..sort((a, b) => a.ts.compareTo(b.ts));

      default:
        // chat-로 시작하는 roomId는 빈 채팅방
        if (roomId.startsWith('chat-')) {
          return [];
        }
        // 기본 메시지 (기존 로직)
        return [
          Message(
            id: 'm-2',
            roomId: roomId,
            kind: MsgKind.hazard,
            text: '재난 경보 발령',
            payload: {
              'level': 'red',
              'detailText':
                  '''${_formatDateTime(now.subtract(const Duration(minutes: 18)))} 재난 경보가 발령되었습니다.

하천 접근을 금지하고, 지하 통로 이용을 자제하시기 바랍니다. 반드시 지정된 대피소로 이동하시고, 절대로 혼자 이동하지 말고 주변 사람들과 함께 대피하시기 바랍니다.

현재 상황에 대한 상세 정보는 중앙재난안전대책본부에서 지속적으로 업데이트하고 있습니다. 

안전한 장소에서 추가 안내를 기다리시고, 긴급한 상황이 발생할 경우 즉시 119 또는 112로 신고하시기 바랍니다.''',
            },
            ts: now.subtract(const Duration(minutes: 18)),
            mine: false,
          ),
          Message(
            id: 'm-3',
            roomId: roomId,
            kind: MsgKind.map,
            text: '위험구역 지도 업데이트',
            payload: {
              'bbox': [127.05, 37.47, 127.09, 37.49],
            },
            ts: now.subtract(const Duration(minutes: 12)),
            mine: false,
          ),
          Message(
            id: 'm-4',
            roomId: roomId,
            kind: MsgKind.guideline,
            text: '고지대 방향으로 이동하세요. 엘리베이터 사용 금지',
            payload: {
              'bullets': ['계단 이용', '지하 공간 대피 금지'],
            },
            ts: now.subtract(const Duration(minutes: 8)),
            mine: false,
          ),
          Message(
            id: 'm-6',
            roomId: roomId,
            kind: MsgKind.chat,
            text: '상황이 심각한가요?',
            ts: now.subtract(const Duration(minutes: 20)),
            mine: true,
          ),
        ]..sort((a, b) => a.ts.compareTo(b.ts));
    }
  }

  void add(Message message) {
    final list = [...state, message]..sort((a, b) => a.ts.compareTo(b.ts));
    state = list;
  }

  void updateMessages(List<Message> messages) {
    messages.sort((a, b) => a.ts.compareTo(b.ts));
    state = messages;
  }
}

List<Message> _getInitialMessages() {
  final allRoomIds = [
    'alert-fire-001',
    'alert-earthquake-001',
    'alert-flood-001',
    'alert-power-001',
  ];

  final List<Message> allMessages = [];
  for (final roomId in allRoomIds) {
    allMessages.addAll(RoomMessagesNotifier._mock(roomId));
  }
  return allMessages;
}

class AllMessagesNotifier extends StateNotifier<List<Message>> {
  AllMessagesNotifier() : super(_getInitialMessages());

  void addMessage(Message message) {
    state = [...state, message];
  }

  void removeMessagesByRoomId(String roomId) {
    state = state.where((msg) => msg.roomId != roomId).toList();
  }
}

final allMessagesProvider =
    StateNotifierProvider<AllMessagesNotifier, List<Message>>(
      (ref) => AllMessagesNotifier(),
    );

final roomMessagesProvider =
    StateNotifierProvider.family<RoomMessagesNotifier, List<Message>, String>((
      ref,
      roomId,
    ) {
      final allMessages = ref.watch(allMessagesProvider);
      final notifier = RoomMessagesNotifier(roomId, allMessages);
      ref.listen<List<Message>>(allMessagesProvider, (previous, next) {
        final roomMessages = next.where((msg) => msg.roomId == roomId).toList();
        if (roomMessages.isNotEmpty) {
          notifier.updateMessages(roomMessages);
        } else {
          if (roomId.startsWith('chat-')) {
            notifier.updateMessages([]);
          } else {
            notifier.updateMessages(RoomMessagesNotifier._mock(roomId));
          }
        }
      });
      return notifier;
    });

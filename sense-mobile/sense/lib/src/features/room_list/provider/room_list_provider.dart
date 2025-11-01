import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:sense/src/features/room_list/domain/room_summary.dart';

// 방 요약 리스트 Provider
// 정렬: active 우선(true 먼저), 그 다음 최근 lastTs 순
final roomListProvider = Provider<List<RoomSummary>>((ref) {
  List<RoomSummary> list = _mock();
  list.sort((a, b) {
    if (a.active != b.active) return a.active ? -1 : 1;
    return b.lastTs.compareTo(a.lastTs);
  });
  return list;
});

List<RoomSummary> _mock() {
  final now = DateTime.now();
  return [
    RoomSummary(
      roomId: 'alert-fire-001',
      title: '대규모 산불',
      type: 'fire',
      active: true,
      lastPreviewText: '주민 대피 명령 발령. 대피소 위치를 확인해주세요.',
      unreadCount: 3,
      lastTs: now.subtract(const Duration(minutes: 2)),
      startedAt: now.subtract(const Duration(hours: 1)),
    ),
    RoomSummary(
      roomId: 'alert-earthquake-001',
      title: '규모 4.5 지진',
      type: 'earthquake',
      active: true,
      lastPreviewText: '건물 붕괴 위험. 안전한 곳으로 대피하세요.',
      unreadCount: 2,
      lastTs: now.subtract(const Duration(minutes: 30)),
      startedAt: now.subtract(const Duration(hours: 1)),
    ),
    RoomSummary(
      roomId: 'alert-flood-001',
      title: '호우로 인한 하천 범람',
      type: 'flood',
      active: true,
      lastPreviewText: '저지대 주민 즉시 대피 필요.',
      unreadCount: 1,
      lastTs: now.subtract(const Duration(hours: 2)),
      startedAt: now.subtract(const Duration(hours: 3)),
    ),
    RoomSummary(
      roomId: 'alert-power-001',
      title: '대규모 정전',
      type: 'power_outage',
      active: false,
      lastPreviewText: '3시간 내 복구 예상. 전력 절약 부탁드립니다.',
      unreadCount: 0,
      lastTs: DateTime(2023, 10, 26),
      startedAt: DateTime(2023, 10, 26),
    ),
  ];
}

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:sense/src/core/palette/palette.dart';
import 'package:sense/src/features/alert/domain/disaster_alert.dart' as alert;
import 'package:sense/src/features/incident/provider/incident_providers.dart';
import 'package:sense/src/features/message/domain/entities/message.dart';
import 'package:sense/src/features/room_list/provider/room_list_provider.dart';
import 'package:uuid/uuid.dart';

enum FilterType { all, earthquake, fire, war, unspecified }

class RoomListPage extends ConsumerStatefulWidget {
  const RoomListPage({super.key});

  @override
  ConsumerState<RoomListPage> createState() => _RoomListPageState();
}

class _RoomListPageState extends ConsumerState<RoomListPage> {
  FilterType _selectedFilter = FilterType.all;

  void _handleNewChat(BuildContext context) {
    HapticFeedback.mediumImpact();
    final now = DateTime.now();
    final newRoomId = 'chat-${const Uuid().v4()}';

    // 상태 업데이트가 완료될 때까지 약간의 지연 후 네비게이션
    Future.microtask(() {
      if (context.mounted) {
        context.push('/rooms/$newRoomId');
      }
    });
  }

  void _handleTestStart(BuildContext context) {
    HapticFeedback.mediumImpact();

    final now = DateTime.now();
    final newRoomId = 'chat-${const Uuid().v4()}';

    // 테스트 메시지 텍스트 설정을 위한 Provider
    final testMessageText =
        '2025-11-02 15:00 서울특별시 동남쪽 2km 지역 M6.3 지진/낙하물,여진주의 국민재난안전포털 참고대응 Earthquake[기상청]';
    ref.read(initialChatMessageProvider(newRoomId).notifier).state =
        testMessageText;

    // 상태 업데이트가 완료될 때까지 약간의 지연 후 네비게이션
    Future.microtask(() {
      if (context.mounted) {
        context.push('/rooms/$newRoomId');
      }
    });
  }

  Map<String, dynamic>? _parseDisasterAlert(alert.DisasterAlert alertData) {
    final body = alertData.body;
    if (body.isEmpty) return null;

    // 재난 유형 파싱
    String type = 'unspecified';
    if (body.contains('지진') || body.contains('진도')) {
      type = 'earthquake';
    } else if (body.contains('화재') || body.contains('산불')) {
      type = 'fire';
    } else if (body.contains('전쟁') ||
        body.contains('민방위') ||
        body.contains('공습')) {
      type = 'war';
    } else if (body.contains('호우') ||
        body.contains('폭우') ||
        body.contains('범람')) {
      type = 'flood';
    } else if (body.contains('정전') || body.contains('전력')) {
      type = 'power_outage';
    }

    // 위험 수준 파싱
    String? riskLevel;
    if (body.contains('위기') || body.contains('긴급') || body.contains('즉시')) {
      riskLevel = '위기';
    } else if (body.contains('경보') || body.contains('주의보')) {
      riskLevel = '경보';
    } else if (body.contains('주의')) {
      riskLevel = '주의';
    } else {
      // 기본값은 경보
      riskLevel = '경보';
    }

    // 제목 추출
    String title = _extractTitle(body, type);

    return {
      'title': title,
      'type': type,
      'riskLevel': riskLevel,
      'sender': alertData.sender,
      'level': _riskLevelToLevel(riskLevel),
    };
  }

  String _extractTitle(String body, String type) {
    // 첫 줄 추출 시도
    final lines = body
        .split('\n')
        .where((line) => line.trim().isNotEmpty)
        .toList();
    if (lines.isNotEmpty) {
      final firstLine = lines.first.trim();
      if (firstLine.length <= 50) {
        return firstLine;
      }
      return firstLine.substring(0, 50);
    }

    // 타입별 기본 제목
    switch (type) {
      case 'earthquake':
        final magnitudeMatch = RegExp(r'규모\s*([0-9.]+)').firstMatch(body);
        if (magnitudeMatch != null) {
          return '규모 ${magnitudeMatch.group(1)} 지진';
        }
        return '지진 발생';
      case 'fire':
        return '화재 발생';
      case 'war':
        return '민방위 경보';
      case 'flood':
        return '호우 경보';
      case 'power_outage':
        return '정전 발생';
      default:
        return '재난 경보';
    }
  }

  String _riskLevelToLevel(String? riskLevel) {
    switch (riskLevel) {
      case '위기':
        return 'critical';
      case '경보':
        return 'warning';
      case '주의':
        return 'advisory';
      default:
        return 'warning';
    }
  }

  @override
  Widget build(BuildContext context) {
    final rooms = ref.watch(roomListProvider);
    final allAlerts = rooms.map((room) {
      DisasterType type;
      Color typeColor;
      IconData icon;

      switch (room.type) {
        case 'fire':
          type = DisasterType.fire;
          typeColor = Colors.red;
          icon = Icons.local_fire_department_outlined;
          break;
        case 'earthquake':
          type = DisasterType.earthquake;
          typeColor = Colors.orange;
          icon = Icons.vibration_outlined;
          break;
        case 'war':
          type = DisasterType.war;
          typeColor = Colors.purple;
          icon = Icons.warning_outlined;
          break;
        case 'unspecified':
          type = DisasterType.unspecified;
          typeColor = Palette.onGoing;
          icon = Icons.help_outline;
          break;
        case 'flood':
        case 'power_outage':
        case 'chat':
        default:
          type = DisasterType.unspecified;
          typeColor = Palette.onGoing;
          icon = Icons.help_outline;
          break;
      }

      final now = DateTime.now();
      final difference = now.difference(room.lastTs);
      String timestamp;
      if (difference.inMinutes < 1) {
        timestamp = '방금 전';
      } else if (difference.inMinutes < 60) {
        timestamp = '${difference.inMinutes}분 전';
      } else if (difference.inHours < 24) {
        timestamp = '${difference.inHours}시간 전';
      } else if (difference.inDays < 7) {
        timestamp = '${difference.inDays}일 전';
      } else {
        final year = room.lastTs.year;
        final month = room.lastTs.month.toString().padLeft(2, '0');
        final day = room.lastTs.day.toString().padLeft(2, '0');
        timestamp = '$year.$month.$day';
      }

      return DisasterAlert(
        roomId: room.roomId,
        type: type,
        typeColor: typeColor,
        icon: icon,
        title: room.title,
        location: room.type == 'unspecified' ? '대화방' : '위치 정보',
        timestamp: timestamp,
        message: room.lastPreviewText.isEmpty
            ? '메시지가 없습니다'
            : room.lastPreviewText,
        riskLevelLabel:
            room.riskLevel ?? (room.type == 'unspecified' ? '대화' : '경보'),
        status: room.active ? '진행중' : '종료',
        occurredAt:
            room.lastTs.hour.toString().padLeft(2, '0') +
            ':' +
            room.lastTs.minute.toString().padLeft(2, '0'),
      );
    }).toList();

    final filteredAlerts = _filterAlerts(allAlerts, _selectedFilter);

    return Scaffold(
      backgroundColor: const Color(0xFF171a21),
      body: SafeArea(
        child: Stack(
          children: [
            Center(
              child: ConstrainedBox(
                constraints: const BoxConstraints(maxWidth: 400),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Padding(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 16,
                        vertical: 12,
                      ),
                      child: SingleChildScrollView(
                        scrollDirection: Axis.horizontal,
                        child: Row(
                          children: [
                            _FilterChip(
                              label: '전체',
                              isActive: _selectedFilter == FilterType.all,
                              onTap: () {
                                setState(() {
                                  _selectedFilter = FilterType.all;
                                });
                              },
                            ),
                            const SizedBox(width: 8),
                            _FilterChip(
                              label: '지진',
                              isActive:
                                  _selectedFilter == FilterType.earthquake,
                              onTap: () {
                                setState(() {
                                  _selectedFilter = FilterType.earthquake;
                                });
                              },
                            ),
                            const SizedBox(width: 8),
                            _FilterChip(
                              label: '화재',
                              isActive: _selectedFilter == FilterType.fire,
                              onTap: () {
                                setState(() {
                                  _selectedFilter = FilterType.fire;
                                });
                              },
                            ),
                            const SizedBox(width: 8),
                            _FilterChip(
                              label: '전쟁',
                              isActive: _selectedFilter == FilterType.war,
                              onTap: () {
                                setState(() {
                                  _selectedFilter = FilterType.war;
                                });
                              },
                            ),
                            const SizedBox(width: 8),
                            _FilterChip(
                              label: '미지정',
                              isActive:
                                  _selectedFilter == FilterType.unspecified,
                              onTap: () {
                                setState(() {
                                  _selectedFilter = FilterType.unspecified;
                                });
                              },
                            ),
                          ],
                        ),
                      ),
                    ),
                    Expanded(
                      child: ListView.separated(
                        padding: const EdgeInsets.symmetric(
                          horizontal: 16,
                          vertical: 12,
                        ),
                        itemCount: filteredAlerts.length,
                        separatorBuilder: (context, index) =>
                            const SizedBox(height: 12),
                        itemBuilder: (context, index) {
                          return _DisasterAlertCard(
                            alert: filteredAlerts[index],
                          );
                        },
                      ),
                    ),
                    Container(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 16,
                        vertical: 12,
                      ),
                      decoration: BoxDecoration(
                        color: const Color(0xFF171a21),
                        border: Border(
                          top: BorderSide(color: Palette.border, width: 1),
                        ),
                      ),
                      child: SizedBox(
                        width: double.infinity,
                        child: ElevatedButton(
                          onPressed: () => _handleNewChat(context),
                          style: ElevatedButton.styleFrom(
                            backgroundColor: Palette.onGoing,
                            foregroundColor: Palette.textPrimary,
                            padding: const EdgeInsets.symmetric(vertical: 16),
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(12),
                            ),
                          ),
                          child: const Row(
                            mainAxisAlignment: MainAxisAlignment.center,
                            children: [
                              Icon(Icons.add_circle_outline, size: 20),
                              SizedBox(width: 8),
                              Text(
                                '새 대화 시작',
                                style: TextStyle(
                                  fontSize: 16,
                                  fontWeight: FontWeight.w600,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),
            Positioned(
              right: 16,
              bottom: 80,
              child: _TestStartButton(
                onPressed: () => _handleTestStart(context),
              ),
            ),
          ],
        ),
      ),
    );
  }

  List<DisasterAlert> _filterAlerts(
    List<DisasterAlert> alerts,
    FilterType filter,
  ) {
    if (filter == FilterType.all) {
      return alerts;
    }
    return alerts.where((alert) {
      switch (filter) {
        case FilterType.earthquake:
          return alert.type == DisasterType.earthquake;
        case FilterType.fire:
          return alert.type == DisasterType.fire;
        case FilterType.war:
          return alert.type == DisasterType.war;
        case FilterType.unspecified:
          return alert.type == DisasterType.unspecified;
        default:
          return true;
      }
    }).toList();
  }
}

enum DisasterType { fire, earthquake, war, unspecified }

class DisasterAlert {
  final String roomId;
  final DisasterType type;
  final Color typeColor;
  final IconData icon;
  final String title;
  final String location;
  final String timestamp;
  final String message;
  final String riskLevelLabel;
  final String status;
  final String occurredAt;

  DisasterAlert({
    required this.roomId,
    required this.type,
    required this.typeColor,
    required this.icon,
    required this.title,
    required this.location,
    required this.timestamp,
    required this.message,
    required this.riskLevelLabel,
    required this.status,
    required this.occurredAt,
  });
}

class _FilterChip extends StatelessWidget {
  const _FilterChip({
    required this.label,
    required this.isActive,
    required this.onTap,
  });

  final String label;
  final bool isActive;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final backgroundColor = isActive
        ? const Color(0xFFf59e0b)
        : const Color(0xFF374151);
    final textColor = isActive ? Colors.white : const Color(0xFFd1d5db);

    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        decoration: BoxDecoration(
          color: backgroundColor,
          borderRadius: BorderRadius.circular(12),
        ),
        child: Text(
          label,
          style: TextStyle(
            fontSize: 13,
            fontWeight: FontWeight.w600,
            color: textColor,
          ),
        ),
      ),
    );
  }
}

class _DisasterAlertCard extends StatelessWidget {
  const _DisasterAlertCard({required this.alert});
  final DisasterAlert alert;

  Color _getRiskLevelColor() {
    switch (alert.riskLevelLabel) {
      case '경보':
        return Colors.orange;
      case '위기':
        return Colors.red;
      case '주의':
        return Colors.green;
      case '대화':
      case '미지정':
      default:
        return Colors.grey;
    }
  }

  @override
  Widget build(BuildContext context) {
    final borderRadius = BorderRadius.circular(12);
    final riskLevelColor = _getRiskLevelColor();
    return InkWell(
      onTap: () {
        context.push('/rooms/${alert.roomId}');
      },
      borderRadius: borderRadius,
      child: ClipRRect(
        borderRadius: borderRadius,
        child: Container(
          color: Palette.listItemBackground,
          child: Stack(
            children: [
              Positioned(
                left: 0,
                top: 0,
                bottom: 0,
                child: Container(width: 6, color: riskLevelColor),
              ),
              Padding(
                padding: const EdgeInsets.all(16).copyWith(left: 16 + 6),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Container(
                          width: 40,
                          height: 40,
                          decoration: BoxDecoration(
                            color: riskLevelColor.withOpacity(0.2),
                            borderRadius: BorderRadius.circular(12),
                          ),
                          child: Icon(
                            alert.icon,
                            color: riskLevelColor,
                            size: 24,
                          ),
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                alert.title,
                                style: const TextStyle(
                                  fontSize: 16,
                                  fontWeight: FontWeight.bold,
                                  color: Color(0xFFf9fafb),
                                  fontFamily: 'Roboto',
                                ),
                              ),
                              const SizedBox(height: 2),
                              Text(
                                alert.location,
                                style: const TextStyle(
                                  fontSize: 12,
                                  color: Color(0xFF9ca3af),
                                  fontFamily: 'Roboto',
                                ),
                              ),
                            ],
                          ),
                        ),
                        Text(
                          alert.timestamp,
                          style: const TextStyle(
                            fontSize: 12,
                            color: Color(0xFF9ca3af),
                            fontFamily: 'Roboto',
                          ),
                        ),
                      ],
                    ),

                    const SizedBox(height: 12),
                    Text(
                      alert.message,
                      style: const TextStyle(
                        fontSize: 14,
                        color: Color(0xFFd1d5db),
                        fontFamily: 'Roboto',
                      ),
                    ),

                    const SizedBox(height: 12),
                    Container(height: 1, color: const Color(0xFF374151)),
                    const SizedBox(height: 12),
                    Row(
                      children: [
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              const Text(
                                '위험 수준',
                                style: TextStyle(
                                  fontSize: 12,
                                  color: Color(0xFF9ca3af),
                                  fontFamily: 'Roboto',
                                ),
                              ),
                              const SizedBox(height: 4),
                              Text(
                                alert.riskLevelLabel,
                                style: TextStyle(
                                  fontSize: 13,
                                  fontWeight: FontWeight.bold,
                                  color: riskLevelColor,
                                  fontFamily: 'Roboto',
                                ),
                              ),
                            ],
                          ),
                        ),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              const Text(
                                '상태',
                                style: TextStyle(
                                  fontSize: 12,
                                  color: Color(0xFF9ca3af),
                                  fontFamily: 'Roboto',
                                ),
                              ),
                              const SizedBox(height: 4),
                              Text(
                                alert.status,
                                style: const TextStyle(
                                  fontSize: 13,
                                  fontWeight: FontWeight.w500,
                                  color: Color(0xFFd1d5db),
                                  fontFamily: 'Roboto',
                                ),
                              ),
                            ],
                          ),
                        ),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              const Text(
                                '발생 시각',
                                style: TextStyle(
                                  fontSize: 12,
                                  color: Color(0xFF9ca3af),
                                  fontFamily: 'Roboto',
                                ),
                              ),
                              const SizedBox(height: 4),
                              Text(
                                alert.occurredAt,
                                style: const TextStyle(
                                  fontSize: 13,
                                  fontWeight: FontWeight.w500,
                                  color: Color(0xFFd1d5db),
                                  fontFamily: 'Roboto',
                                ),
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 12),
                    Center(
                      child: GestureDetector(
                        onTap: () {
                          context.push('/rooms/${alert.roomId}');
                        },
                        child: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: const [
                            Text(
                              '상세 보기',
                              style: TextStyle(
                                fontSize: 14,
                                fontWeight: FontWeight.w600,
                                color: Color(0xFFf59e0b),
                                fontFamily: 'Roboto',
                              ),
                            ),
                            SizedBox(width: 4),
                            Icon(
                              Icons.arrow_forward,
                              size: 16,
                              color: Color(0xFFf59e0b),
                            ),
                          ],
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _TestStartButton extends StatelessWidget {
  const _TestStartButton({required this.onPressed});
  final VoidCallback onPressed;
  @override
  Widget build(BuildContext context) {
    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: onPressed,
        borderRadius: BorderRadius.circular(28),
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
          decoration: BoxDecoration(
            color: Colors.blue,
            borderRadius: BorderRadius.circular(28),
            boxShadow: [
              BoxShadow(
                color: Colors.black.withOpacity(0.3),
                blurRadius: 8,
                offset: const Offset(0, 2),
              ),
            ],
          ),
          child: const Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(Icons.play_arrow, color: Colors.white, size: 20),
              SizedBox(width: 8),
              Text(
                '테스트 시작',
                style: TextStyle(
                  color: Colors.white,
                  fontSize: 14,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:sense/src/core/palette/palette.dart';

enum FilterType { all, earthquake, fire, powerOutage }

class RoomListPage extends ConsumerStatefulWidget {
  const RoomListPage({super.key});

  @override
  ConsumerState<RoomListPage> createState() => _RoomListPageState();
}

class _RoomListPageState extends ConsumerState<RoomListPage> {
  FilterType _selectedFilter = FilterType.all;

  @override
  Widget build(BuildContext context) {
    final allAlerts = _getSampleAlerts();
    final filteredAlerts = _filterAlerts(allAlerts, _selectedFilter);

    return Scaffold(
      backgroundColor: const Color(0xFF171a21),
      body: SafeArea(
        child: Center(
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
                          isActive: _selectedFilter == FilterType.earthquake,
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
                          label: '정전',
                          isActive: _selectedFilter == FilterType.powerOutage,
                          onTap: () {
                            setState(() {
                              _selectedFilter = FilterType.powerOutage;
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
                      return _DisasterAlertCard(alert: filteredAlerts[index]);
                    },
                  ),
                ),
              ],
            ),
          ),
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
        case FilterType.powerOutage:
          return alert.type == DisasterType.powerOutage;
        default:
          return true;
      }
    }).toList();
  }

  List<DisasterAlert> _getSampleAlerts() {
    return [
      DisasterAlert(
        roomId: 'alert-fire-001',
        type: DisasterType.fire,
        typeColor: Colors.red,
        icon: Icons.local_fire_department_outlined,
        title: '대규모 산불',
        location: '강원도 지역',
        timestamp: '2분 전',
        message: '주민 대피 명령 발령. 대피소 위치를 확인해주세요.',
        riskLevelLabel: '심각',
        status: '진압 중',
        occurredAt: '14:28',
      ),
      DisasterAlert(
        roomId: 'alert-earthquake-001',
        type: DisasterType.earthquake,
        typeColor: Colors.orange,
        icon: Icons.vibration_outlined,
        title: '규모 4.5 지진',
        location: '경북 포항',
        timestamp: '30분 전',
        message: '건물 붕괴 위험. 안전한 곳으로 대피하세요.',
        riskLevelLabel: '경보',
        status: '여진 관찰 중',
        occurredAt: '14:00',
      ),
      DisasterAlert(
        roomId: 'alert-flood-001',
        type: DisasterType.flood,
        typeColor: Colors.yellow,
        icon: Icons.flood_outlined,
        title: '호우로 인한 하천 범람',
        location: '수도권 지역',
        timestamp: '2시간 전',
        message: '저지대 주민 즉시 대피 필요.',
        riskLevelLabel: '주의',
        status: '대피 권고',
        occurredAt: '12:30',
      ),
      DisasterAlert(
        roomId: 'alert-power-001',
        type: DisasterType.powerOutage,
        typeColor: Colors.blue,
        icon: Icons.power_off_outlined,
        title: '대규모 정전',
        location: '서울 및 경기 일부',
        timestamp: '2023.10.26',
        message: '3시간 내 복구 예상. 전력 절약 부탁드립니다.',
        riskLevelLabel: '관찰',
        status: '복구 중',
        occurredAt: '2023.10.26',
      ),
    ];
  }
}

enum DisasterType { fire, earthquake, flood, powerOutage }

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

  @override
  Widget build(BuildContext context) {
    final borderRadius = BorderRadius.circular(12);

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
                child: Container(width: 6, color: alert.typeColor),
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
                            color: alert.typeColor.withOpacity(0.2),
                            borderRadius: BorderRadius.circular(12),
                          ),
                          child: Icon(
                            alert.icon,
                            color: alert.typeColor,
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
                                  color: alert.typeColor,
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

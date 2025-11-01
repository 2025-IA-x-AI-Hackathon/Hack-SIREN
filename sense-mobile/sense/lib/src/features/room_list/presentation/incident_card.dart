import 'package:flutter/material.dart';
import 'package:sense/src/core/palette/palette.dart';
import 'package:sense/src/features/room_list/domain/room_summary.dart';

class IncidentCard extends StatelessWidget {
  const IncidentCard({super.key, required this.data, required this.onTap});
  final RoomSummary data;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final severityInfo = _severityStyle(data);
    final rightTopLabel = _formatRelativeOrDate(data.lastTs);
    final timeLabel = _formatTimeOrDate(data.lastTs);
    final statusLabel = data.active ? '진행 중' : '복구 중';

    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      child: InkWell(
        borderRadius: BorderRadius.circular(8),
        onTap: onTap,
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Container(
              width: 4,
              decoration: BoxDecoration(
                color: severityInfo.color,
                borderRadius: BorderRadius.circular(4),
              ),
            ),
            Expanded(
              child: Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: const Color(0xFF1F2432),
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: Palette.border, width: 0.8),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Expanded(
                          child: Row(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Icon(
                                severityInfo.icon,
                                color: severityInfo.color,
                                size: 20,
                              ),
                              const SizedBox(width: 8),
                              Expanded(
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text(
                                      data.title,
                                      style: TextStyle(
                                        color: Palette.textPrimary,
                                        fontSize: 15,
                                        fontWeight: FontWeight.w700,
                                      ),
                                    ),
                                    Text(
                                      _typeToHuman(data.type),
                                      style: TextStyle(
                                        color: Palette.textPrimary.withOpacity(
                                          0.7,
                                        ),
                                        fontSize: 13,
                                        fontWeight: FontWeight.w500,
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                            ],
                          ),
                        ),
                        const SizedBox(width: 8),
                        Text(
                          rightTopLabel,
                          style: TextStyle(
                            color: Palette.textPrimary.withOpacity(0.6),
                            fontSize: 12,
                            fontWeight: FontWeight.w500,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 12),
                    Text(
                      data.lastPreviewText,
                      style: TextStyle(
                        color: Palette.textPrimary,
                        fontSize: 13,
                        height: 1.4,
                        fontWeight: FontWeight.w400,
                      ),
                    ),
                    const SizedBox(height: 16),
                    Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        _StatusColumn(
                          label: '위험수준',
                          value: severityInfo.label,
                          valueColor: severityInfo.color,
                        ),
                        const SizedBox(width: 16),
                        _StatusColumn(
                          label: '진행 상황',
                          value: statusLabel,
                          valueColor: Palette.textPrimary,
                        ),
                        const SizedBox(width: 16),
                        Expanded(
                          child: _StatusColumn(
                            label: data.active ? '안내 발생시' : '안내 발생/복구시',
                            value: timeLabel,
                            valueColor: Palette.textPrimary,
                            alignEnd: true,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 16),
                    Align(
                      alignment: Alignment.centerLeft,
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Text(
                            '자세히 보기',
                            style: TextStyle(
                              color: const Color(0xFFFFC857),
                              fontSize: 13,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                          const SizedBox(width: 4),
                          Icon(
                            Icons.chevron_right,
                            size: 18,
                            color: const Color(0xFFFFC857),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

_SeverityInfo _severityStyle(RoomSummary room) {
  switch (room.type) {
    case 'flood':
      return _SeverityInfo(
        label: '주의',
        color: const Color(0xFFFFC857),
        icon: Icons.water_damage_rounded,
      );
    case 'air_raid':
      return _SeverityInfo(
        label: '관심',
        color: Colors.blueGrey.shade400,
        icon: Icons.speaker,
      );
    default:
      return _SeverityInfo(
        label: room.active ? '심각' : '경계',
        color: Colors.redAccent,
        icon: Icons.warning_rounded,
      );
  }
}

class _StatusColumn extends StatelessWidget {
  const _StatusColumn({
    required this.label,
    required this.value,
    required this.valueColor,
    this.alignEnd = false,
  });

  final String label;
  final String value;
  final Color valueColor;
  final bool alignEnd;

  @override
  Widget build(BuildContext context) {
    final cross = alignEnd ? CrossAxisAlignment.end : CrossAxisAlignment.start;
    return Expanded(
      child: Column(
        crossAxisAlignment: cross,
        children: [
          Text(
            label,
            style: TextStyle(
              color: Palette.textPrimary.withOpacity(0.6),
              fontSize: 11,
              fontWeight: FontWeight.w500,
            ),
          ),
          const SizedBox(height: 4),
          Text(
            value,
            textAlign: alignEnd ? TextAlign.right : TextAlign.left,
            style: TextStyle(
              color: valueColor,
              fontSize: 13,
              fontWeight: FontWeight.w700,
            ),
          ),
        ],
      ),
    );
  }
}

class _SeverityInfo {
  final String label;
  final Color color;
  final IconData icon;
  const _SeverityInfo({
    required this.label,
    required this.color,
    required this.icon,
  });
}

String _typeToHuman(String t) {
  switch (t) {
    case 'flood':
      return '침수 / 홍수 경보';
    case 'air_raid':
      return '공습 / 경보 관련';
    default:
      return t;
  }
}

String _formatRelativeOrDate(DateTime ts) {
  final now = DateTime.now();
  final diff = now.difference(ts);
  if (diff.inMinutes < 1) {
    return '방금 전';
  } else if (diff.inMinutes < 60) {
    return '${diff.inMinutes}분 전';
  } else if (diff.inHours < 24) {
    return '${diff.inHours}시간 전';
  } else {
    final y = ts.year.toString();
    final m = ts.month.toString().padLeft(2, '0');
    final d = ts.day.toString().padLeft(2, '0');
    return '$y.$m.$d';
  }
}

String _formatTimeOrDate(DateTime ts) {
  final now = DateTime.now();
  final isSameDay =
      ts.year == now.year && ts.month == now.month && ts.day == now.day;
  if (isSameDay) {
    final hh = ts.hour.toString().padLeft(2, '0');
    final mm = ts.minute.toString().padLeft(2, '0');
    return '$hh:$mm';
  } else {
    final y = ts.year.toString();
    final m = ts.month.toString().padLeft(2, '0');
    final d = ts.day.toString().padLeft(2, '0');
    return '$y.$m.$d';
  }
}

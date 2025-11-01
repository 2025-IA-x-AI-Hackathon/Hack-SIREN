class RoomSummary {
  final String roomId;
  final String title;
  final String type;
  final bool active;
  final String lastPreviewText;
  final int unreadCount;
  final DateTime lastTs;
  final DateTime startedAt;

  const RoomSummary({
    required this.roomId,
    required this.title,
    required this.type,
    required this.active,
    required this.lastPreviewText,
    required this.unreadCount,
    required this.lastTs,
    required this.startedAt,
  });
}

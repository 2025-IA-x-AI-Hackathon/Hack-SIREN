enum MsgKind { chat, map, hazard, guideline }

class Message {
  final String id;
  final String roomId;
  final MsgKind kind;
  final String? text;
  final Map<String, dynamic>? payload;
  final DateTime ts;
  final bool mine;

  Message({
    required this.id,
    required this.roomId,
    required this.kind,
    required this.ts,
    this.text,
    this.payload,
    this.mine = false,
  });
}

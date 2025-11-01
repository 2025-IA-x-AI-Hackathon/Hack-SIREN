import 'package:sense/src/features/message/domain/entities/message.dart';

class MessageDto {
  final String id;
  final String roomId;
  final String kind;
  final String? text;
  final Map<String, dynamic>? payload;
  final String ts; // ISO8601 string
  final bool mine;

  const MessageDto({
    required this.id,
    required this.roomId,
    required this.kind,
    required this.ts,
    this.text,
    this.payload,
    this.mine = false,
  });

  factory MessageDto.fromJson(Map<String, dynamic> json) {
    return MessageDto(
      id: json['id'] as String,
      roomId: json['roomId'] as String,
      kind: json['kind'] as String,
      text: json['text'] as String?,
      payload: (json['payload'] as Map?)?.cast<String, dynamic>(),
      ts: json['ts'] as String,
      mine: (json['mine'] as bool?) ?? false,
    );
  }

  Map<String, dynamic> toJson() => {
    'id': id,
    'roomId': roomId,
    'kind': kind,
    'text': text,
    'payload': payload,
    'ts': ts,
    'mine': mine,
  };

  Message toDomain() {
    final msgKind = MsgKind.values.firstWhere(
      (msg) => msg.name == kind,
      orElse: () => MsgKind.chat,
    );
    final parsed = DateTime.tryParse(ts) ?? DateTime.now().toUtc();
    return Message(
      id: id,
      roomId: roomId,
      kind: msgKind,
      text: text,
      payload: payload,
      ts: parsed,
      mine: mine,
    );
  }

  static MessageDto fromDomain(Message msg) => MessageDto(
    id: msg.id,
    roomId: msg.roomId,
    kind: msg.kind.name,
    text: msg.text,
    payload: msg.payload,
    ts: msg.ts.toUtc().toIso8601String(),
    mine: msg.mine,
  );
}

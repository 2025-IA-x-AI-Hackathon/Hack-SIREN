import 'package:flutter/material.dart';
import 'package:sense/src/features/message/domain/entities/message.dart';

class MessageCard extends StatelessWidget {
  const MessageCard({
    super.key,
    required this.message,
    required this.expanded,
    required this.onToggleExpand,
  });

  final Message message;
  final bool expanded;
  final VoidCallback onToggleExpand;

  @override
  Widget build(BuildContext context) {
    switch (message.kind) {
      case MsgKind.chat:
        return ChatBubbleLayout(
          text: message.text ?? '',
          mine: message.mine,
          ts: message.ts,
        );
      case MsgKind.map:
        return MapMessageLayout(
          msg: message,
          expanded: expanded,
          onTap: onToggleExpand,
        );
      case MsgKind.hazard:
        return HazardMessageLayout(
          msg: message,
          expanded: expanded,
          onTap: onToggleExpand,
        );
      case MsgKind.guideline:
        return GuidelineMessageLayout(
          msg: message,
          expanded: expanded,
          onTap: onToggleExpand,
        );
    }
  }
}

class ChatBubbleLayout extends StatelessWidget {
  const ChatBubbleLayout({
    super.key,
    required this.text,
    required this.mine,
    required this.ts,
  });
  final String text;
  final bool mine;
  final DateTime ts;

  @override
  Widget build(BuildContext context) {
    final bg = mine ? Colors.blueGrey.shade700 : Colors.grey.shade800;
    final align = mine ? CrossAxisAlignment.end : CrossAxisAlignment.start;
    return Column(
      crossAxisAlignment: align,
      children: [
        Container(
          margin: const EdgeInsets.symmetric(vertical: 6),
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
          decoration: BoxDecoration(
            color: bg,
            borderRadius: BorderRadius.circular(12),
          ),
          child: Text(text),
        ),
      ],
    );
  }
}

class MapMessageLayout extends StatelessWidget {
  const MapMessageLayout({
    super.key,
    required this.msg,
    required this.expanded,
    required this.onTap,
  });
  final Message msg;
  final bool expanded;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      child: Container(
        margin: const EdgeInsets.symmetric(vertical: 8),
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          border: Border.all(color: Colors.grey.shade700),
          borderRadius: BorderRadius.circular(12),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              msg.text ?? '지도',
              style: const TextStyle(fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            Container(
              height: expanded ? 200 : 140,
              alignment: Alignment.center,
              child: const Text('지도 Placeholder'),
            ),
          ],
        ),
      ),
    );
  }
}

class HazardMessageLayout extends StatelessWidget {
  const HazardMessageLayout({
    super.key,
    required this.msg,
    required this.expanded,
    required this.onTap,
  });
  final Message msg;
  final bool expanded;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final level = (msg.payload?['level'] ?? 'N/A').toString();
    return InkWell(
      onTap: onTap,
      child: Container(
        margin: const EdgeInsets.symmetric(vertical: 8),
        decoration: BoxDecoration(
          border: Border.all(color: Colors.redAccent),
          borderRadius: BorderRadius.circular(12),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Container(
              height: 6,
              decoration: const BoxDecoration(
                color: Colors.redAccent,
                borderRadius: BorderRadius.vertical(top: Radius.circular(12)),
              ),
            ),
            Padding(
              padding: const EdgeInsets.fromLTRB(12, 10, 12, 8),
              child: Text(
                msg.text ?? '위험 경보',
                style: const TextStyle(fontWeight: FontWeight.bold),
              ),
            ),
            Padding(
              padding: const EdgeInsets.fromLTRB(12, 0, 12, 12),
              child: Text('위험 레벨: $level'),
            ),
          ],
        ),
      ),
    );
  }
}

class GuidelineMessageLayout extends StatelessWidget {
  const GuidelineMessageLayout({
    super.key,
    required this.msg,
    required this.expanded,
    required this.onTap,
  });
  final Message msg;
  final bool expanded;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final bullets =
        (msg.payload?['bullets'] as List?)?.cast<String>() ?? const <String>[];
    return InkWell(
      onTap: onTap,
      child: Container(
        margin: const EdgeInsets.symmetric(vertical: 8),
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          border: Border.all(color: Colors.grey.shade700),
          borderRadius: BorderRadius.circular(12),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              msg.text ?? '행동 지침',
              style: const TextStyle(fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 6),
            ...bullets.map(
              (b) => Padding(
                padding: const EdgeInsets.symmetric(vertical: 2),
                child: Text('• $b'),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

import 'package:flutter_riverpod/legacy.dart';
import 'package:sense/src/features/message/domain/entities/message.dart';
import 'package:sense/src/features/message/provider/room_messages_provider.dart';
import 'package:sense/src/features/room_list/domain/room_summary.dart';

class RoomListNotifier extends StateNotifier<List<RoomSummary>> {
  RoomListNotifier(this.allMessages) : super([]) {
    _updateFromMessages();
  }
  final List<Message> allMessages;

  void refreshFromProvider(List<Message> newMessages) {
    _updateFromMessages(newMessages);
  }

  void _updateFromMessages([List<Message>? messages]) {
    final messagesToUse = messages ?? allMessages;
    final Map<String, List<Message>> messagesByRoom = {};
    for (final message in messagesToUse) {
      messagesByRoom.putIfAbsent(message.roomId, () => []).add(message);
    }

    final List<RoomSummary> summaries = [];
    for (final entry in messagesByRoom.entries) {
      final roomId = entry.key;
      final messages = entry.value;
      if (messages.isEmpty) continue;
      messages.sort((a, b) => a.ts.compareTo(b.ts));
      final lastMessage = messages.last;
      final startedAt = messages.first.ts;
      final lastTs = lastMessage.ts;
      Message? latestHazard;
      for (int i = messages.length - 1; i >= 0; i--) {
        if (messages[i].kind == MsgKind.hazard) {
          latestHazard = messages[i];
          break;
        }
      }

      String title;
      String type;
      String? riskLevel;
      String? levelToRiskLevel(String? level) {
        if (level == null) return null;
        switch (level.toLowerCase()) {
          case 'severe':
          case 'critical':
          case 'red':
            return '위기';
          case 'warning':
            return '경보';
          case 'watch':
          case 'advisory':
            return '주의';
          default:
            return null;
        }
      }

      if (latestHazard != null && latestHazard.payload != null) {
        title =
            latestHazard.payload!['title'] as String? ??
            latestHazard.text ??
            '미지정';
        type = latestHazard.payload!['type'] as String? ?? 'unspecified';
        riskLevel =
            latestHazard.payload!['riskLevel'] as String? ??
            levelToRiskLevel(latestHazard.payload!['level'] as String?);
      } else {
        title = '미지정';
        type = 'unspecified';
        riskLevel = null;
      }

      String lastPreviewText = '';
      if (lastMessage.text != null) {
        lastPreviewText = lastMessage.text!;
      } else if (lastMessage.kind == MsgKind.guideline &&
          lastMessage.payload?['bullets'] != null) {
        final bullets = lastMessage.payload!['bullets'] as List?;
        if (bullets != null && bullets.isNotEmpty) {
          lastPreviewText = bullets[0].toString();
        }
      }

      final now = DateTime.now();
      final isActive = now.difference(lastTs).inHours < 24;
      final unreadCount = 0;
      summaries.add(
        RoomSummary(
          roomId: roomId,
          title: title,
          type: type,
          active: isActive,
          lastPreviewText: lastPreviewText,
          unreadCount: unreadCount,
          lastTs: lastTs,
          startedAt: startedAt,
          riskLevel: riskLevel,
        ),
      );
    }
    state = summaries;
    _sort();
  }

  void updateMessages(List<Message> newMessages) {
    _updateFromMessages(newMessages);
  }

  void addMessage(Message message, dynamic ref) {
    ref.read(allMessagesProvider.notifier).addMessage(message);
  }

  void _sort() {
    state = [...state];
    state.sort((a, b) {
      if (a.active != b.active) return a.active ? -1 : 1;
      return b.lastTs.compareTo(a.lastTs);
    });
  }

  void addRoom(RoomSummary room) {
    state = [...state, room];
    _sort();
  }

  void removeRoom(String roomId, dynamic ref) {
    ref.read(allMessagesProvider.notifier).removeMessagesByRoomId(roomId);
    allMessages.removeWhere((msg) => msg.roomId == roomId);
  }
}

final roomListProvider =
    StateNotifierProvider<RoomListNotifier, List<RoomSummary>>((ref) {
      final allMessages = ref.watch(allMessagesProvider);
      final notifier = RoomListNotifier(allMessages);
      ref.listen<List<Message>>(allMessagesProvider, (previous, next) {
        notifier.refreshFromProvider(next);
      });
      return notifier;
    });

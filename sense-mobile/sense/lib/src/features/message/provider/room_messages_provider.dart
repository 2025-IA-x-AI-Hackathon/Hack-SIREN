import 'package:flutter_riverpod/legacy.dart';
import 'package:sense/src/features/message/domain/entities/message.dart';

class RoomMessagesNotifier extends StateNotifier<List<Message>> {
  RoomMessagesNotifier(this.roomId) : super(_mock(roomId));
  final String roomId;

  static String _formatDateTime(DateTime dateTime) {
    final year = dateTime.year;
    final month = dateTime.month.toString().padLeft(2, '0');
    final day = dateTime.day.toString().padLeft(2, '0');
    final hour = dateTime.hour.toString().padLeft(2, '0');
    final minute = dateTime.minute.toString().padLeft(2, '0');
    return '$year년 $month월 $day일 $hour:$minute';
  }

  static List<Message> _mock(String roomId) {
    switch (roomId) {
      case 'fire':
        return []..sort((a, b) => a.ts.compareTo(b.ts));

      case 'earthquake':
        return []..sort((a, b) => a.ts.compareTo(b.ts));

      case 'flood':
        return []..sort((a, b) => a.ts.compareTo(b.ts));

      case 'power':
        return []..sort((a, b) => a.ts.compareTo(b.ts));

      default:
        return []..sort((a, b) => a.ts.compareTo(b.ts));
    }
  }

  void add(Message message) {
    final list = [...state, message]..sort((a, b) => a.ts.compareTo(b.ts));
    state = list;
  }
}

final roomMessagesProvider =
    StateNotifierProvider.family<RoomMessagesNotifier, List<Message>, String>(
      (ref, roomId) => RoomMessagesNotifier(roomId),
    );

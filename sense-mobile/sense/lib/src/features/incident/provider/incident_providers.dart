import 'package:flutter_riverpod/legacy.dart';

final jumpTargetMessageIdProvider = StateProvider.family<String?, String>(
  (ref, roomId) => null,
);
final initialChatMessageProvider = StateProvider.family<String?, String>(
  (ref, roomId) => null,
);

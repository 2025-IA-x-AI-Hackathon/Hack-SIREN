import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:sense/src/core/user/user_id_store.dart';

final anonUserIdProvider = FutureProvider<String>((ref) async {
  final store = UserIdStore();
  return store.getOrCreate();
});



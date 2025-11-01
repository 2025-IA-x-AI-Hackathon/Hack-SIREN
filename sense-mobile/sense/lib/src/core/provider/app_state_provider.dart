import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:dio/dio.dart';
import 'package:sense/src/core/provider/dio_provider.dart';
import 'package:sense/src/core/user/user_id_store.dart';

final userIdStoreProvider = Provider<UserIdStore>((_) => UserIdStore());

final dioProvider = Provider<Dio>((ref) {
  final dio = Dio(
    BaseOptions(
      baseUrl: const String.fromEnvironment(
        'API_BASE',
        defaultValue: 'http://10.0.2.2:8080',
      ),
      connectTimeout: const Duration(seconds: 2),
      receiveTimeout: const Duration(seconds: 2),
    ),
  );
  dio.interceptors.add(
    UserIdInterceptor(() => ref.read(userIdStoreProvider).getOrCreate()),
  );
  return dio;
});

class AppInitResult {
  final String userId;
  const AppInitResult({required this.userId});
}

final appInitProvider = FutureProvider<AppInitResult>((ref) async {
  final dio = ref.read(dioProvider);
  final userId = await ref.read(userIdStoreProvider).getOrCreate();
  Duration delay = const Duration(seconds: 2);
  await Future.delayed(delay);
  return AppInitResult(userId: userId);
});

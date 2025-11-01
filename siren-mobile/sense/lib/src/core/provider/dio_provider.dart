import 'package:dio/dio.dart';

class UserIdInterceptor extends Interceptor {
  final Future<String> Function() userIdProvider;
  UserIdInterceptor(this.userIdProvider);

  @override
  void onRequest(
    RequestOptions options,
    RequestInterceptorHandler handler,
  ) async {
    final userId = await userIdProvider();
    options.headers['X-Anon-Id'] = userId;
    handler.next(options);
  }
}

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:sense/src/features/room_list/presentation/room_list_page.dart';
import 'package:sense/src/features/splash/splash_screen.dart';

import 'route_name.dart';

class MyNavigatorObserver extends NavigatorObserver {
  @override
  void didPop(Route route, Route? previousRoute) {
    if (previousRoute == null) {}
    super.didPop(route, previousRoute);
  }
}

final routerNavigatorKey = GlobalKey<NavigatorState>();

final unauthorizedRoutes = [];

final routerProvider = Provider((ref) {
  return GoRouter(
    debugLogDiagnostics: true,
    initialLocation: '/rooms',
    navigatorKey: routerNavigatorKey,
    observers: [MyNavigatorObserver()],
    redirect: (context, state) {
      if (state.path == Routes.splash) {
        return '/rooms';
      }
      return null;
    },
    routes: [
      GoRoute(
        path: Routes.splash,
        builder: (context, state) {
          return const SplashScreen();
        },
      ),
      GoRoute(
        path: Routes.roomList,
        builder: (context, state) => const RoomListPage(),
        routes: [],
      ),
    ],
  );
});

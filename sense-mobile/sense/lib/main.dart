import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:sense/src/core/palette/palette.dart';
import 'package:sense/src/core/provider/app_state_provider.dart';
import 'package:sense/src/features/splash/splash_screen.dart';
import 'package:sense/src/router/router_provider.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(ProviderScope(child: const MyApp()));
}

class MyApp extends ConsumerWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final appInit = ref.watch(appInitProvider);
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      home: appInit.when(
        loading: () => const SplashScreen(),
        error: (e, _) =>
            Scaffold(body: Center(child: Text('Initialization failed: $e'))),
        data: (_) => const MainApp(),
      ),
    );
  }
}

class MainApp extends ConsumerWidget {
  const MainApp({super.key});
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final router = ref.watch(routerProvider);
    return MaterialApp.router(
      debugShowCheckedModeBanner: false,
      title: 'SENSE',
      routerConfig: router,
      theme: ThemeData(
        splashColor: Colors.transparent,
        highlightColor: Colors.transparent,
        appBarTheme: AppBarTheme(
          backgroundColor: Palette.background,
          elevation: 0,
          shadowColor: Colors.transparent,
          titleTextStyle: TextStyle(color: Colors.white),
        ),
      ),
    );
  }
}

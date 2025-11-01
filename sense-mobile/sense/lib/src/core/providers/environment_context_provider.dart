import 'package:flutter_riverpod/flutter_riverpod.dart';

class EnvironmentContext {
  final bool isUnderground;
  final bool hasStroller;
  const EnvironmentContext({
    required this.isUnderground,
    required this.hasStroller,
  });
}

final environmentContextProvider = FutureProvider<EnvironmentContext>((
  ref,
) async {
  return const EnvironmentContext(isUnderground: false, hasStroller: false);
});

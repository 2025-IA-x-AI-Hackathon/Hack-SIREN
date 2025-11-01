import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_riverpod/legacy.dart';
import 'package:sense/src/features/estimator/controller/profile_controller.dart';
import 'package:sense/src/features/estimator/controller/sensor_controller.dart';
import 'package:sense/src/features/estimator/data/pressure/pressure_source.dart';
import 'package:sense/src/features/estimator/data/pressure/sensors_plus_pressure_source.dart';
import 'package:sense/src/features/estimator/data/profile_repo.dart';

final profileRepoProvider = Provider<ProfileRepo>((ref) => ProfileRepo());

final pressureSourceProvider = Provider<PressureSource>((ref) {
  if (kDebugMode) {
    return SensorsPlusPressureSource();
  }
  return SensorsPlusPressureSource();
});

final sensorProvider = StateNotifierProvider<SensorController, SensorState>((
  ref,
) {
  final src = ref.watch(pressureSourceProvider);
  return SensorController(src);
});

final profileProvider = StateNotifierProvider<ProfileController, ProfileState>((
  ref,
) {
  final repo = ref.watch(profileRepoProvider);
  return ProfileController(repo);
});

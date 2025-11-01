import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:sense/src/features/estimator/domain/entities/estimation_result.dart';
import 'package:sense/src/features/estimator/domain/services/floor_estimator.dart';
import 'package:sense/src/features/estimator/provider/provider.dart';

final estimationProvider = Provider<EstimationResult?>((ref) {
  final sample = ref.watch(sensorProvider.select((s) => s.sample));
  final profile = ref.watch(profileProvider.select((p) => p.profile));
  final tempC = ref.watch(profileProvider.select((p) => p.tempC));
  if (sample == null || profile == null) return null;

  return FloorEstimator.estimate(
    profile: profile,
    pHpa: sample.emaHpa,
    tempC: tempC,
  );
});

String formatFloorLabel({
  required int baselineFloor,
  required int estimatedFloor,
}) {
  if (baselineFloor != 1) {
    return '${estimatedFloor}F';
  }
  if (estimatedFloor >= 1) {
    return '${estimatedFloor}F';
  }
  final b = 1 - estimatedFloor;
  return 'B$b';
}

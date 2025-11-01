import 'dart:math' as math;
import '../entities/building_profile.dart';
import '../entities/estimation_result.dart';

class FloorEstimator {
  static double deltaH({
    required double p0Hpa,
    required double pHpa,
    double tempC = 20,
  }) {
    final T = 273.15 + tempC;
    return 29.27 * T * math.log(p0Hpa / pHpa);
  }

  static int estimateFloorIndex({
    required double deltaMeters,
    required int baselineFloor,
    required double floorHeightM,
    required double basementFloorHeightM,
  }) {
    if (deltaMeters >= 0) {
      return (baselineFloor + (deltaMeters / floorHeightM)).round();
    } else {
      return (baselineFloor + (deltaMeters / basementFloorHeightM)).round();
    }
  }

  static EstimationResult estimate({
    required BuildingProfile profile,
    required double pHpa,
    double tempC = 20,
  }) {
    final dM = deltaH(p0Hpa: profile.p0Hpa, pHpa: pHpa, tempC: tempC);
    final fl = estimateFloorIndex(
      deltaMeters: dM,
      baselineFloor: profile.baselineFloor,
      floorHeightM: profile.floorHeightM,
      basementFloorHeightM: profile.basementFloorHeightM,
    );
    return EstimationResult(deltaMeters: dM, estimatedFloor: fl);
  }

  static double estimateFloorIndexContinuous({
    required double deltaMeters,
    required int baselineFloor,
    required double floorHeightM,
    required double basementFloorHeightM,
  }) {
    return deltaMeters >= 0
        ? baselineFloor + (deltaMeters / floorHeightM)
        : baselineFloor + (deltaMeters / basementFloorHeightM);
  }
}

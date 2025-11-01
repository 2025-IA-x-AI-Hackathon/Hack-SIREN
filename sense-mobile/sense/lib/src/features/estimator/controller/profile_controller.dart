import 'dart:math' as math;
import 'package:flutter_riverpod/legacy.dart';
import 'package:sense/src/features/estimator/data/profile_repo.dart';
import 'package:sense/src/features/estimator/domain/entities/building_profile.dart';

class ProfileState {
  final BuildingProfile? profile;
  final String buildingId;
  final double floorHeightM;
  final double basementFloorHeightM;
  final double tempC;
  final int? lastKnownFloor;

  const ProfileState({
    required this.profile,
    required this.buildingId,
    required this.floorHeightM,
    required this.basementFloorHeightM,
    required this.tempC,
    this.lastKnownFloor,
  });
  bool get baselineSet => profile != null;
  ProfileState copyWith({
    BuildingProfile? profile,
    String? buildingId,
    double? floorHeightM,
    double? basementFloorHeightM,
    double? tempC,
    int? lastKnownFloor,
    bool keepNullLastKnownFloor = false,
  }) => ProfileState(
    profile: profile ?? this.profile,
    buildingId: buildingId ?? this.buildingId,
    floorHeightM: floorHeightM ?? this.floorHeightM,
    basementFloorHeightM: basementFloorHeightM ?? this.basementFloorHeightM,
    tempC: tempC ?? this.tempC,
    lastKnownFloor: keepNullLastKnownFloor
        ? null
        : (lastKnownFloor ?? this.lastKnownFloor),
  );
}

class ProfileController extends StateNotifier<ProfileState> {
  final ProfileRepo repo;
  ProfileController(this.repo)
    : super(
        const ProfileState(
          profile: null,
          buildingId: 'MyBuilding',
          floorHeightM: 3.3,
          basementFloorHeightM: 3.2,
          tempC: 20,
          lastKnownFloor: null,
        ),
      );

  void setBuildingId(String v) => state = state.copyWith(buildingId: v);
  void setFloorHeight(double v) => state = state.copyWith(floorHeightM: v);
  void setBasementHeight(double v) =>
      state = state.copyWith(basementFloorHeightM: v);
  void setTemp(double v) => state = state.copyWith(tempC: v);
  void setLastKnownFloor(int? v) => state = state.copyWith(
    lastKnownFloor: v,
    keepNullLastKnownFloor: v == null,
  );

  Future<void> loadProfile(String buildingId) async {
    final p = await repo.load(buildingId);
    if (p != null) {
      state = state.copyWith(
        profile: p,
        buildingId: p.buildingId,
        floorHeightM: p.floorHeightM,
        basementFloorHeightM: p.basementFloorHeightM,
      );
    }
  }

  Future<void> loadLastProfile() async {
    final profile = await repo.loadLast();
    if (profile != null) {
      state = state.copyWith(
        profile: profile,
        buildingId: profile.buildingId,
        floorHeightM: profile.floorHeightM,
        basementFloorHeightM: profile.basementFloorHeightM,
      );
    }
  }

  Future<void> calibrateFromPressure(double p0Hpa) async {
    final prof = BuildingProfile(
      buildingId: state.buildingId,
      baselineFloor: 1,
      p0Hpa: p0Hpa,
      floorHeightM: state.floorHeightM,
      basementFloorHeightM: state.basementFloorHeightM,
      calibratedAt: DateTime.now(),
    );
    state = state.copyWith(profile: prof);
    await repo.save(prof);
  }

  Future<void> calibrateFromKnownFloor({
    required double currentHpa,
    required int currentFloor,
    double tempC = 20,
  }) async {
    final T = 273.15 + tempC;
    final int diff = currentFloor - 1;
    if (diff == 0) {
      return calibrateFromPressure(currentHpa);
    }

    final deltaMetersExpected = (diff >= 0)
        ? diff * state.floorHeightM
        : diff * state.basementFloorHeightM;
    final p0New = currentHpa * math.exp(deltaMetersExpected / (29.27 * T));

    final prof = BuildingProfile(
      buildingId: state.buildingId,
      baselineFloor: 1,
      p0Hpa: p0New,
      floorHeightM: state.floorHeightM,
      basementFloorHeightM: state.basementFloorHeightM,
      calibratedAt: DateTime.now(),
    );

    state = state.copyWith(profile: prof, lastKnownFloor: currentFloor);
    await repo.save(prof);
  }

  Future<void> learnFloorHeightFromMeasurement({
    required double currentHpa,
    required int currentFloor,
    double tempC = 20,
    double momentum = 0.5,
    double minM = 2.4,
    double maxM = 4.8,
  }) async {
    final prof = state.profile;
    if (prof == null) return;

    final int diff = currentFloor - 1;
    if (diff == 0) return;

    final T = 273.15 + tempC;
    final deltaMeters = 29.27 * T * math.log(prof.p0Hpa / currentHpa);
    final perFloorEst = (deltaMeters.abs() / diff.abs()).clamp(minM, maxM);

    if (diff > 0) {
      final updated =
          state.floorHeightM * (1 - momentum) + perFloorEst * momentum;
      state = state.copyWith(
        floorHeightM: updated,
        lastKnownFloor: currentFloor,
      );
      await repo.save(prof.copyWith(floorHeightM: updated));
    } else {
      final updated =
          state.basementFloorHeightM * (1 - momentum) + perFloorEst * momentum;
      state = state.copyWith(
        basementFloorHeightM: updated,
        lastKnownFloor: currentFloor,
      );
      await repo.save(prof.copyWith(basementFloorHeightM: updated));
    }
  }

  Future<void> calibrateFromKnownFloorAndLearn({
    required double currentHpa,
    required int currentFloor,
    double tempC = 20,
    double momentum = 0.5,
    double minM = 2.4,
    double maxM = 4.8,
    bool recomputeP0 = true,
  }) async {
    await calibrateFromKnownFloor(
      currentHpa: currentHpa,
      currentFloor: currentFloor,
      tempC: tempC,
    );

    await learnFloorHeightFromMeasurement(
      currentHpa: currentHpa,
      currentFloor: currentFloor,
      tempC: tempC,
      momentum: momentum,
      minM: minM,
      maxM: maxM,
    );

    if (recomputeP0) {
      final prof = state.profile!;
      final T = 273.15 + tempC;
      final int diff = currentFloor - 1;
      final deltaMetersExpected = (diff >= 0)
          ? diff * state.floorHeightM
          : diff * state.basementFloorHeightM;
      final p0New2 = currentHpa * math.exp(deltaMetersExpected / (29.27 * T));
      final refined = prof.copyWith(
        p0Hpa: p0New2,
        calibratedAt: DateTime.now(),
      );
      state = state.copyWith(profile: refined);
      await repo.save(refined);
    }
  }
}

extension on BuildingProfile {
  BuildingProfile copyWith({
    String? buildingId,
    int? baselineFloor,
    double? p0Hpa,
    double? floorHeightM,
    double? basementFloorHeightM,
    DateTime? calibratedAt,
  }) {
    return BuildingProfile(
      buildingId: buildingId ?? this.buildingId,
      baselineFloor: baselineFloor ?? this.baselineFloor,
      p0Hpa: p0Hpa ?? this.p0Hpa,
      floorHeightM: floorHeightM ?? this.floorHeightM,
      basementFloorHeightM: basementFloorHeightM ?? this.basementFloorHeightM,
      calibratedAt: calibratedAt ?? this.calibratedAt,
    );
  }
}

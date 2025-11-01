class BuildingProfile {
  final String buildingId;
  final int baselineFloor;
  final double p0Hpa;
  final double floorHeightM;
  final double basementFloorHeightM;
  final DateTime calibratedAt;

  const BuildingProfile({
    required this.buildingId,
    required this.baselineFloor,
    required this.p0Hpa,
    required this.floorHeightM,
    required this.basementFloorHeightM,
    required this.calibratedAt,
  });

  Map<String, dynamic> toJson() => {
    'buildingId': buildingId,
    'baselineFloor': baselineFloor,
    'p0Hpa': p0Hpa,
    'floorHeightM': floorHeightM,
    'basementFloorHeightM': basementFloorHeightM,
    'calibratedAt': calibratedAt.toIso8601String(),
  };

  factory BuildingProfile.fromJson(Map<String, dynamic> json) =>
      BuildingProfile(
        buildingId: json['buildingId'] as String,
        baselineFloor: (json['baselineFloor'] as num).toInt(),
        p0Hpa: (json['p0Hpa'] as num).toDouble(),
        floorHeightM: (json['floorHeightM'] as num).toDouble(),
        basementFloorHeightM: (json['basementFloorHeightM'] as num).toDouble(),
        calibratedAt: DateTime.parse(json['calibratedAt'] as String),
      );
}

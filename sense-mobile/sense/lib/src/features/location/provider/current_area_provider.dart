import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:geolocator/geolocator.dart';
import 'package:geocoding/geocoding.dart';

final currentAreaProvider = FutureProvider<String>((ref) async {
  String? gu;
  String? dong;

  LocationPermission permission = await Geolocator.checkPermission();
  if (permission == LocationPermission.denied ||
      permission == LocationPermission.deniedForever) {
    permission = await Geolocator.requestPermission();
  }
  if (permission == LocationPermission.denied ||
      permission == LocationPermission.deniedForever) {
    throw Exception('위치 권한 없음');
  }
  final pos = await Geolocator.getCurrentPosition(
    desiredAccuracy: LocationAccuracy.high,
  );
  final placeMarks = await placemarkFromCoordinates(
    pos.latitude,
    pos.longitude,
  );
  if (placeMarks.isEmpty) {
    throw Exception('주소를 찾을 수 없습니다');
  }
  final placeMark = placeMarks.first;
  final guCandidates = <String?>[
    placeMark.locality,
    placeMark.subAdministrativeArea,
    placeMark.subLocality,
  ];
  for (final guCandidate in guCandidates) {
    if (guCandidate != null && guCandidate.endsWith('구')) {
      gu = guCandidate;
      break;
    }
  }
  gu ??= placeMark.locality ?? placeMark.subAdministrativeArea ?? '';
  final dongCandidates = <String?>[
    placeMark.subLocality,
    placeMark.thoroughfare,
    placeMark.name,
  ];
  for (final dongCandidate in dongCandidates) {
    if (dongCandidate != null && dongCandidate.endsWith('동')) {
      dong = dongCandidate;
      break;
    }
  }
  dong ??= placeMark.subLocality ?? '';
  final pieces = [if (gu.isNotEmpty) gu, if (dong.isNotEmpty) dong];
  final areaLabel = pieces.join(' ').trim();
  if (areaLabel.isEmpty) {
    throw Exception('행정동 파싱 실패');
  }
  return areaLabel;
});

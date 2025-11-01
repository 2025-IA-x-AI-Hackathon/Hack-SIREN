import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:geolocator/geolocator.dart';
import 'package:geocoding/geocoding.dart';

final currentAreaProvider = FutureProvider<String>((ref) async {
  LocationPermission perm = await Geolocator.checkPermission();
  if (perm == LocationPermission.denied ||
      perm == LocationPermission.deniedForever) {
    perm = await Geolocator.requestPermission();
  }
  if (perm == LocationPermission.denied ||
      perm == LocationPermission.deniedForever) {
    throw Exception('위치 권한 없음');
  }
  final pos = await Geolocator.getCurrentPosition(
    desiredAccuracy: LocationAccuracy.high,
  );
  final placemarks = await placemarkFromCoordinates(
    pos.latitude,
    pos.longitude,
  );
  if (placemarks.isEmpty) {
    throw Exception('주소를 찾을 수 없습니다');
  }
  final placemark = placemarks.first;
  String? gu;
  String? dong;
  final guCandidates = <String?>[
    placemark.locality,
    placemark.subAdministrativeArea,
    placemark.subLocality,
  ];
  for (final candidate in guCandidates) {
    if (candidate != null && candidate.endsWith('구')) {
      gu = candidate;
      break;
    }
  }
  gu ??= placemark.locality ?? placemark.subAdministrativeArea ?? '';
  final dongCandidates = <String?>[
    placemark.subLocality,
    placemark.thoroughfare,
    placemark.name,
  ];
  for (final candidate in dongCandidates) {
    if (candidate != null && candidate.endsWith('동')) {
      dong = candidate;
      break;
    }
  }
  dong ??= placemark.subLocality ?? '';
  final pieces = [if (gu.isNotEmpty) gu, if (dong.isNotEmpty) dong];
  final areaLabel = pieces.join(' ').trim();
  if (areaLabel.isEmpty) {
    throw Exception('행정동 파싱 실패');
  }
  return areaLabel;
});

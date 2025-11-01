import 'dart:convert';
import 'package:sense/src/features/estimator/domain/entities/building_profile.dart';
import 'package:shared_preferences/shared_preferences.dart';

class ProfileRepo {
  static const _prefix = 'profile';
  static String _profileKey(String id) => '$_prefix:$id';
  static const _lastIdKey = '$_prefix:lastId';

  Future<void> save(BuildingProfile p) async {
    final sp = await SharedPreferences.getInstance();
    await sp.setString(_profileKey(p.buildingId), jsonEncode(p.toJson()));
    await sp.setString(_lastIdKey, p.buildingId);
  }

  Future<BuildingProfile?> load(String buildingId) async {
    final sp = await SharedPreferences.getInstance();
    final raw = sp.getString(_profileKey(buildingId));
    if (raw == null) return null;
    return BuildingProfile.fromJson(jsonDecode(raw));
  }

  Future<BuildingProfile?> loadLast() async {
    final sp = await SharedPreferences.getInstance();
    final lastId = sp.getString(_lastIdKey);
    if (lastId == null) return null;
    return load(lastId);
  }
}

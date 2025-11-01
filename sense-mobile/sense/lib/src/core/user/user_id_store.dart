import 'package:shared_preferences/shared_preferences.dart';
import 'package:uuid/uuid.dart';

class UserIdStore {
  static const _key = 'user_id';
  final _uuid = const Uuid();
  String? _cached;

  Future<String> getOrCreate() async {
    if (_cached != null && _cached!.isNotEmpty) return _cached!;

    final prefs = await SharedPreferences.getInstance();
    final existing = prefs.getString(_key);
    if (existing != null && existing.isNotEmpty) {
      _cached = existing;
      return existing;
    }

    final created = _uuid.v4();
    await prefs.setString(_key, created);
    _cached = created;
    return created;
  }

  Future<String?> getCachedOrNull() async {
    if (_cached != null) return _cached;
    final prefs = await SharedPreferences.getInstance();
    _cached = prefs.getString(_key);
    return _cached;
  }
}

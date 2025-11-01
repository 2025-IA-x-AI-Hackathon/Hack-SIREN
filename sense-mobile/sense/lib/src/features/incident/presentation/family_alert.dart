import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';

class EmergencyContact {
  final String phone;
  EmergencyContact({required this.phone});
  Map<String, dynamic> toJson() => {'phone': phone};

  factory EmergencyContact.fromJson(Map<String, dynamic> json) {
    return EmergencyContact(phone: json['phone'] as String);
  }
}

class EmergencyContactStore {
  static const _key = 'emergency_contact';
  static Future<void> save(EmergencyContact contact) async {
    final prefs = await SharedPreferences.getInstance();
    final jsonStr = jsonEncode(contact.toJson());
    await prefs.setString(_key, jsonStr);
  }

  static Future<EmergencyContact?> load() async {
    final prefs = await SharedPreferences.getInstance();
    final jsonStr = prefs.getString(_key);
    if (jsonStr == null) return null;
    final map = jsonDecode(jsonStr) as Map<String, dynamic>;
    return EmergencyContact.fromJson(map);
  }
}

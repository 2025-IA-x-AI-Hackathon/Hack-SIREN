import 'dart:convert';
import 'package:flutter/services.dart';
import 'package:sense/src/features/alert/domain/disaster_alert.dart';

class DisasterAlertStream {
  static const _channel = EventChannel('sense/disaster_alerts');
  static Stream<DisasterAlert> get stream {
    return _channel.receiveBroadcastStream().map((event) {
      final map = jsonDecode(event as String) as Map<String, dynamic>;
      return DisasterAlert.fromJson(map);
    });
  }
}

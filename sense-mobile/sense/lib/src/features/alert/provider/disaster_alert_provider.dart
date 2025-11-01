import 'dart:async';
import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/legacy.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:sense/src/features/alert/domain/disaster_alert.dart';
import 'package:sense/src/features/alert/data/disaster_alert_stream.dart';
import 'package:sense/src/features/message/domain/entities/message.dart';
import 'package:sense/src/features/message/data/dto/message_dto.dart';
import 'package:sense/src/features/room_list/provider/room_list_provider.dart';
import 'package:sense/src/core/network/message_api.dart';
import 'package:sense/src/core/provider/app_state_provider.dart';
import 'package:uuid/uuid.dart';

class DisasterAlertNotifier extends StateNotifier<List<DisasterAlert>> {
  StreamSubscription<DisasterAlert>? _sub;
  final Ref ref;

  DisasterAlertNotifier(this.ref) : super(const []) {
    _sub = DisasterAlertStream.stream.listen((alert) {
      state = [alert, ...state];
      _handleDisasterAlert(alert);
    });
  }

  void _handleDisasterAlert(DisasterAlert alert) {
    final parsed = _parseDisasterAlert(alert);
    if (parsed == null) return;
    final roomId = 'alert-${const Uuid().v4()}';
    final message = Message(
      id: 'msg-${const Uuid().v4()}',
      roomId: roomId,
      kind: MsgKind.hazard,
      text: alert.body,
      payload: parsed,
      ts: alert.timestamp,
      mine: false,
    );
    ref.read(roomListProvider.notifier).addMessage(message, ref);
    _sendToServer(message, ref);
  }

  Map<String, dynamic>? _parseDisasterAlert(DisasterAlert alert) {
    final body = alert.body;
    if (body.isEmpty) return null;
    String type = 'unspecified';
    if (body.contains('지진') || body.contains('진도')) {
      type = 'earthquake';
    } else if (body.contains('화재') || body.contains('산불')) {
      type = 'fire';
    } else if (body.contains('전쟁') ||
        body.contains('민방위') ||
        body.contains('공습')) {
      type = 'war';
    } else if (body.contains('호우') ||
        body.contains('폭우') ||
        body.contains('범람')) {
      type = 'flood';
    } else if (body.contains('정전') || body.contains('전력')) {
      type = 'power_outage';
    }

    String? riskLevel;
    if (body.contains('위기') || body.contains('긴급') || body.contains('즉시')) {
      riskLevel = '위기';
    } else if (body.contains('경보') || body.contains('주의보')) {
      riskLevel = '경보';
    } else if (body.contains('주의')) {
      riskLevel = '주의';
    } else {
      riskLevel = '경보';
    }
    String title = _extractTitle(body, type);
    return {
      'title': title,
      'type': type,
      'riskLevel': riskLevel,
      'sender': alert.sender,
      'level': _riskLevelToLevel(riskLevel),
    };
  }

  String _extractTitle(String body, String type) {
    final lines = body
        .split('\n')
        .where((line) => line.trim().isNotEmpty)
        .toList();
    if (lines.isNotEmpty) {
      final firstLine = lines.first.trim();
      if (firstLine.length <= 50) {
        return firstLine;
      }
      return firstLine.substring(0, 50);
    }
    switch (type) {
      case 'earthquake':
        final magnitudeMatch = RegExp(r'규모\s*([0-9.]+)').firstMatch(body);
        if (magnitudeMatch != null) {
          return '규모 ${magnitudeMatch.group(1)} 지진';
        }
        return '지진 발생';
      case 'fire':
        return '화재 발생';
      case 'war':
        return '민방위 경보';
      case 'flood':
        return '호우 경보';
      case 'power_outage':
        return '정전 발생';
      default:
        return '재난 경보';
    }
  }

  String _riskLevelToLevel(String? riskLevel) {
    switch (riskLevel) {
      case '위기':
        return 'critical';
      case '경보':
        return 'warning';
      case '주의':
        return 'advisory';
      default:
        return 'warning';
    }
  }

  Future<void> _sendToServer(Message message, Ref ref) async {
    try {
      final dio = ref.read(dioProvider);
      final messageApi = MessageApi(dio);
      final messageDto = MessageDto.fromDomain(message);
      await messageApi.send(messageDto);
    } catch (e) {
      debugPrint('Failed to send message to server: $e');
    }
  }

  @override
  void dispose() {
    _sub?.cancel();
    super.dispose();
  }
}

final disasterAlertProvider =
    StateNotifierProvider<DisasterAlertNotifier, List<DisasterAlert>>(
      (ref) => DisasterAlertNotifier(ref),
    );

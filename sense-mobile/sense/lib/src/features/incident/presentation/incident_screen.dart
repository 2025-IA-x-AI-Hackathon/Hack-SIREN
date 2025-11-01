import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:sense/src/core/palette/palette.dart';
import 'package:sense/src/features/incident/presentation/chat.dart';
import 'package:sense/src/features/incident/presentation/family_alert.dart';
import 'package:sense/src/features/location/provider/current_area_provider.dart';
import 'package:sense/src/features/room_list/provider/room_list_provider.dart';
import 'package:url_launcher/url_launcher_string.dart';

class IncidentScreen extends ConsumerStatefulWidget {
  const IncidentScreen({super.key, required this.roomId});
  final String roomId;

  @override
  ConsumerState<IncidentScreen> createState() => _IncidentScreenState();
}

class _IncidentScreenState extends ConsumerState<IncidentScreen>
    with SingleTickerProviderStateMixin {
  Future<EmergencyContact?> _showRegisterDialog(BuildContext context) async {
    final phoneController = TextEditingController();
    return showDialog<EmergencyContact>(
      context: context,
      barrierDismissible: false,
      builder: (context) {
        return AlertDialog(
          backgroundColor: const Color(0xFF2c2f3a),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(12),
          ),
          title: const Text(
            '비상 연락처 등록',
            style: TextStyle(color: Colors.white, fontWeight: FontWeight.w600),
          ),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(
                controller: phoneController,
                keyboardType: TextInputType.phone,
                style: const TextStyle(color: Colors.white),
                decoration: const InputDecoration(
                  labelText: '전화번호 (예: 01012345678)',
                  labelStyle: TextStyle(color: Colors.white70),
                  enabledBorder: UnderlineInputBorder(
                    borderSide: BorderSide(color: Colors.white30),
                  ),
                  focusedBorder: UnderlineInputBorder(
                    borderSide: BorderSide(color: Colors.white),
                  ),
                ),
              ),
            ],
          ),
          actions: [
            TextButton(
              onPressed: () {
                Navigator.of(context).pop(null);
              },
              child: const Text('취소', style: TextStyle(color: Colors.white70)),
            ),
            TextButton(
              onPressed: () {
                final phone = phoneController.text.trim();
                if (phone.isEmpty) {
                  return;
                }
                Navigator.of(context).pop(EmergencyContact(phone: phone));
              },
              child: const Text(
                '저장',
                style: TextStyle(
                  color: Colors.white,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ),
          ],
        );
      },
    );
  }

  Future<void> _handleFamilyTap(BuildContext context) async {
    HapticFeedback.mediumImpact();
    var contact = await EmergencyContactStore.load();
    if (contact == null) {
      contact = await _showRegisterDialog(context);
      if (contact == null) {
        return;
      }
      await EmergencyContactStore.save(contact);
      return;
    }
    final telUri = 'tel:${contact.phone}';
    if (await canLaunchUrlString(telUri)) {
      await launchUrlString(telUri);
    } else {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('전화 앱을 열 수 없어요 (${contact.phone})')),
      );
    }
  }

  Future<void> _handleDeleteRoom(BuildContext context) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: const Color(0xFF2c2f3a),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        title: const Text(
          '채팅방 삭제',
          style: TextStyle(color: Colors.white, fontWeight: FontWeight.w600),
        ),
        content: const Text(
          '이 채팅방을 삭제하시겠어요?',
          style: TextStyle(color: Colors.white70),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(false),
            child: const Text('취소', style: TextStyle(color: Colors.white70)),
          ),
          TextButton(
            onPressed: () {
              Navigator.of(context).pop(true);
            },
            child: const Text(
              '삭제',
              style: TextStyle(color: Colors.red, fontWeight: FontWeight.w600),
            ),
          ),
        ],
      ),
    );
    if (confirmed == true && context.mounted) {
      final roomId = widget.roomId;
      ref.read(roomListProvider.notifier).removeRoom(roomId, ref);
      if (context.mounted) {
        context.go('/rooms');
      }
    }
  }

  Widget _buildBottomActions(BuildContext context) {
    return Container(
      padding: const EdgeInsets.only(left: 16, right: 16, top: 12, bottom: 12),
      decoration: BoxDecoration(
        color: Palette.background,
        border: Border(bottom: BorderSide(color: Palette.border, width: 1)),
      ),
      child: Row(
        children: [
          Expanded(
            child: Material(
              color: Palette.system,
              borderRadius: BorderRadius.circular(12),
              child: InkWell(
                onTap: () {
                  _handleFamilyTap(context);
                },
                borderRadius: BorderRadius.circular(12),
                child: Container(
                  padding: const EdgeInsets.symmetric(vertical: 10),
                  child: const Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(
                        Icons.people_outline,
                        color: Palette.textPrimary,
                        size: 20,
                      ),
                      SizedBox(width: 8),
                      Text(
                        '긴급 연락',
                        style: TextStyle(
                          color: Palette.textPrimary,
                          fontSize: 16,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            flex: 2,
            child: Material(
              color: Palette.sosColor,
              borderRadius: BorderRadius.circular(12),
              child: InkWell(
                onTap: () async {
                  const tel = 'tel:119';
                  if (await canLaunchUrlString(tel)) {
                    await launchUrlString(tel);
                  }
                },
                borderRadius: BorderRadius.circular(12),
                child: Container(
                  padding: const EdgeInsets.symmetric(vertical: 10),
                  child: const Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(
                        Icons.emergency,
                        color: Palette.textPrimary,
                        size: 20,
                      ),
                      SizedBox(width: 8),
                      Text(
                        'SOS 긴급 신고',
                        style: TextStyle(
                          color: Palette.textPrimary,
                          fontSize: 16,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final rooms = ref.watch(roomListProvider);
    final match = rooms.where((e) => e.roomId == widget.roomId);
    final summary = match.isNotEmpty
        ? match.first
        : (rooms.isNotEmpty ? rooms.first : null);
    final areaAsync = ref.watch(currentAreaProvider);
    return Scaffold(
      appBar: AppBar(
        title: Text(summary?.title ?? '사건'),
        titleTextStyle: TextStyle(
          color: Palette.textPrimary,
          fontWeight: FontWeight.w700,
          fontSize: 16,
        ),
        iconTheme: IconThemeData(color: Palette.textPrimary),
        actions: [
          PopupMenuButton<String>(
            icon: Icon(Icons.more_vert, color: Palette.textPrimary),
            color: const Color(0xFF2c2f3a),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(12),
            ),
            onSelected: (value) async {
              if (value == 'delete') {
                await _handleDeleteRoom(context);
              }
            },
            itemBuilder: (context) => [
              PopupMenuItem<String>(
                value: 'delete',
                child: Row(
                  children: [
                    Icon(Icons.delete_outline, color: Colors.red, size: 20),
                    const SizedBox(width: 8),
                    const Text('채팅방 삭제', style: TextStyle(color: Colors.red)),
                  ],
                ),
              ),
            ],
          ),
        ],
      ),
      backgroundColor: Palette.background,
      body: SafeArea(
        child: Column(
          children: [
            const SizedBox(height: 12),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 12),
              child: Row(
                children: [
                  Container(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 12,
                      vertical: 6,
                    ),
                    decoration: BoxDecoration(
                      color: (summary?.active ?? false)
                          ? Palette.onGoing
                          : Palette.onGoing,
                      borderRadius: BorderRadius.circular(24),
                    ),
                    child: Text(
                      (summary?.active ?? false) ? '진행중' : '종료',
                      style: TextStyle(
                        color: Palette.textPrimary,
                        fontWeight: FontWeight.w700,
                        fontSize: 14,
                      ),
                    ),
                  ),
                  const SizedBox(width: 8),
                  Container(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 12,
                      vertical: 6,
                    ),
                    decoration: BoxDecoration(
                      color: Palette.chatBackground,
                      borderRadius: BorderRadius.circular(24),
                    ),
                    child: areaAsync.when(
                      data: (areaLabel) => Text(
                        '현재 위치: $areaLabel',
                        style: TextStyle(
                          color: Palette.textSecondary,
                          fontWeight: FontWeight.w700,
                          fontSize: 14,
                        ),
                      ),
                      loading: () => Text(
                        '위치 확인중',
                        style: TextStyle(
                          color: Palette.textPrimary,
                          fontWeight: FontWeight.w700,
                          fontSize: 14,
                        ),
                      ),
                      error: (err, st) => Text(
                        '위치 확인 실패',
                        style: TextStyle(
                          color: Palette.textPrimary,
                          fontWeight: FontWeight.w700,
                          fontSize: 14,
                        ),
                      ),
                    ),
                  ),
                ],
              ),
            ),
            _buildBottomActions(context),
            Expanded(child: Chat(roomId: widget.roomId)),
          ],
        ),
      ),
    );
  }
}

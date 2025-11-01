import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:webview_flutter/webview_flutter.dart';

import 'package:sense/src/core/palette/palette.dart';
import 'package:sense/src/core/provider/app_state_provider.dart';
import 'package:sense/src/core/network/message_api.dart';
import 'package:sense/src/features/incident/provider/incident_providers.dart';
import 'package:sense/src/features/message/data/dto/message_dto.dart';
import 'package:sense/src/features/message/domain/entities/message.dart';
import 'package:sense/src/features/message/provider/room_messages_provider.dart';
import 'package:sense/src/features/room_list/provider/room_list_provider.dart';

class Chat extends ConsumerStatefulWidget {
  const Chat({super.key, required this.roomId});
  final String roomId;

  @override
  ConsumerState<Chat> createState() => _ChatState();
}

class _ChatState extends ConsumerState<Chat> {
  final _scrollController = ScrollController();
  final _textController = TextEditingController();
  int _previousMessageCount = 0;
  bool _hasAutoSent = false;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _scrollToBottom();
    });
  }

  @override
  void dispose() {
    _scrollController.dispose();
    _textController.dispose();
    super.dispose();
  }

  void _handleInitialMessage() {
    if (_hasAutoSent) return;

    final initialMessage = ref.read(initialChatMessageProvider(widget.roomId));
    if (initialMessage != null && initialMessage.isNotEmpty) {
      _hasAutoSent = true;
      _textController.text = initialMessage;

      Future.delayed(const Duration(milliseconds: 300), () {
        if (mounted && _textController.text.trim().isNotEmpty) {
          _sendMessage();
        }
        if (mounted) {
          ref.read(initialChatMessageProvider(widget.roomId).notifier).state =
              null;
        }
      });
    }
  }

  Future<void> _sendMessage() async {
    final text = _textController.text.trim();
    if (text.isEmpty) return;

    final now = DateTime.now();
    final message = Message(
      id: 'msg-${now.millisecondsSinceEpoch}',
      roomId: widget.roomId,
      kind: MsgKind.chat,
      text: text,
      payload: null,
      ts: now,
      mine: true,
    );
    ref.read(roomListProvider.notifier).addMessage(message, ref);
    try {
      final dio = ref.read(dioProvider);
      final messageApi = MessageApi(dio);
      final messageDto = MessageDto.fromDomain(message);
      await messageApi.send(messageDto);
    } catch (e) {
      debugPrint('Failed to send message to server: $e');
    }

    _textController.clear();
  }

  void _scrollToBottom() {
    if (_scrollController.hasClients) {
      WidgetsBinding.instance.addPostFrameCallback((_) {
        if (_scrollController.hasClients) {
          _scrollController.animateTo(
            _scrollController.position.maxScrollExtent,
            duration: const Duration(milliseconds: 300),
            curve: Curves.easeOut,
          );
        }
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final allMessages = ref.watch(roomMessagesProvider(widget.roomId));
    final initialMessage = ref.watch(initialChatMessageProvider(widget.roomId));
    final messages = allMessages..sort((a, b) => a.ts.compareTo(b.ts));
    if (initialMessage != null && initialMessage.isNotEmpty && !_hasAutoSent) {
      WidgetsBinding.instance.addPostFrameCallback((_) {
        _handleInitialMessage();
      });
    }

    if (messages.isEmpty) {
      return Column(
        children: [
          const Expanded(
            child: Center(
              child: Text(
                '메시지가 없습니다',
                style: TextStyle(color: Palette.textSecondary),
              ),
            ),
          ),
          _InputBar(textController: _textController, onSend: _sendMessage),
        ],
      );
    }

    if (messages.length != _previousMessageCount) {
      _previousMessageCount = messages.length;
      _scrollToBottom();
    }

    // 나중에 사용할 항목, 처리 필요
    final hazardMessages =
        messages.where((m) => m.kind == MsgKind.hazard).toList()
          ..sort((a, b) => b.ts.compareTo(a.ts));
    final mainMessage = hazardMessages.isNotEmpty
        ? hazardMessages.first
        : messages.first;

    return Column(
      children: [
        Expanded(
          child: SingleChildScrollView(
            controller: _scrollController,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const SizedBox(height: 16),
                ...messages.asMap().entries.map((entry) {
                  final index = entry.key;
                  final message = entry.value;
                  return Column(
                    children: [
                      if (index > 0)
                        Padding(
                          padding: const EdgeInsets.symmetric(vertical: 8),
                        ),
                      Padding(
                        padding: const EdgeInsets.symmetric(horizontal: 16),
                        child: SizedBox(
                          width: double.infinity,
                          child: _buildMessageWidget(message),
                        ),
                      ),
                      const SizedBox(height: 16),
                    ],
                  );
                }),
              ],
            ),
          ),
        ),
        _InputBar(textController: _textController, onSend: _sendMessage),
      ],
    );
  }

  Widget _buildMessageWidget(Message message) {
    switch (message.kind) {
      case MsgKind.hazard:
        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _buildAlertHeader(message),
            const SizedBox(height: 24),
            _buildDetailContentSection(message),
          ],
        );
      case MsgKind.guideline:
        return _buildActionGuidelinesSection(message);
      case MsgKind.map:
        return _buildShelterSection(message);
      case MsgKind.chat:
        return _ChatBubble(
          text: message.text ?? '',
          mine: message.mine,
          timestamp: message.ts,
        );
    }
  }

  Widget _buildAlertHeader(Message message) {
    return Container(
      decoration: BoxDecoration(
        color: Colors.transparent,
        borderRadius: BorderRadius.circular(8),
      ),
      padding: EdgeInsets.zero,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
            decoration: BoxDecoration(
              color: Palette.onGoing,
              borderRadius: BorderRadius.circular(6),
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                const Icon(
                  Icons.warning_amber_rounded,
                  color: Palette.textPrimary,
                  size: 14,
                ),
                const SizedBox(width: 6),
                Text(
                  '수장 필요',
                  style: const TextStyle(
                    color: Palette.textPrimary,
                    fontWeight: FontWeight.w700,
                    fontSize: 13,
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),
          Text(
            message.text ?? '재난 발생',
            style: const TextStyle(
              color: Palette.textPrimary,
              fontSize: 24,
              fontWeight: FontWeight.w700,
              height: 1.3,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            '발생 시각: ${_formatDateTime(message.ts)}',
            style: TextStyle(
              color: Palette.textSecondary,
              fontSize: 14,
              fontWeight: FontWeight.w500,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildActionGuidelinesSection(Message message) {
    final bullets =
        (message.payload?['bullets'] as List?)?.cast<String>() ?? [];
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          crossAxisAlignment: CrossAxisAlignment.center,
          children: [
            const Text(
              '핵심 행동 요령',
              style: TextStyle(
                color: Palette.textPrimary,
                fontSize: 18,
                fontWeight: FontWeight.w700,
              ),
            ),
            Text(
              _formatTime(message.ts),
              style: TextStyle(
                color: Palette.textSecondary,
                fontSize: 12,
                fontWeight: FontWeight.w500,
              ),
            ),
          ],
        ),
        const SizedBox(height: 16),
        Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: Palette.background,
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: Palette.border, width: 1),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: bullets
                .map(
                  (bullet) => Padding(
                    padding: const EdgeInsets.only(bottom: 12),
                    child: Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Container(
                          margin: const EdgeInsets.only(top: 6, right: 12),
                          width: 6,
                          height: 6,
                          decoration: const BoxDecoration(
                            color: Palette.onGoing,
                            shape: BoxShape.circle,
                          ),
                        ),
                        Expanded(
                          child: Text(
                            bullet,
                            style: const TextStyle(
                              color: Palette.textPrimary,
                              fontSize: 15,
                              height: 1.5,
                              fontWeight: FontWeight.w500,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                )
                .toList(),
          ),
        ),
      ],
    );
  }

  Widget _buildDetailContentSection(Message message) {
    final detailText = _buildDetailText(message);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          crossAxisAlignment: CrossAxisAlignment.center,
          children: [
            const Text(
              '재난 상세 내용',
              style: TextStyle(
                color: Palette.textPrimary,
                fontSize: 18,
                fontWeight: FontWeight.w700,
              ),
            ),
            Text(
              _formatTime(message.ts),
              style: TextStyle(
                color: Palette.textSecondary,
                fontSize: 12,
                fontWeight: FontWeight.w500,
              ),
            ),
          ],
        ),
        const SizedBox(height: 16),
        Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: Palette.background,
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: Palette.border, width: 1),
          ),
          child: Text(
            detailText,
            style: TextStyle(
              color: Palette.textPrimary,
              fontSize: 15,
              height: 1.6,
              fontWeight: FontWeight.w400,
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildShelterSection(Message message) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          crossAxisAlignment: CrossAxisAlignment.center,
          children: [
            const Text(
              '주변 대피소 안내',
              style: TextStyle(
                color: Palette.textPrimary,
                fontSize: 18,
                fontWeight: FontWeight.w700,
              ),
            ),
            Text(
              _formatTime(message.ts),
              style: TextStyle(
                color: Palette.textSecondary,
                fontSize: 12,
                fontWeight: FontWeight.w500,
              ),
            ),
          ],
        ),
        const SizedBox(height: 16),
        Container(
          height: 200,
          decoration: BoxDecoration(
            color: Palette.background,
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: Palette.border, width: 1),
          ),
          clipBehavior: Clip.hardEdge,
          child: Stack(
            children: [
              AbsorbPointer(child: _ShelterMapView(payload: message.payload)),
              GestureDetector(
                onTap: () {
                  HapticFeedback.mediumImpact();
                  _showFullScreenMap(context, message.payload);
                },
                child: Container(color: Colors.transparent),
              ),
              Positioned(
                top: 8,
                right: 8,
                child: Material(
                  color: Colors.transparent,
                  child: InkWell(
                    onTap: () {
                      HapticFeedback.mediumImpact();
                      _showFullScreenMap(context, message.payload);
                    },
                    borderRadius: BorderRadius.circular(20),
                    child: Container(
                      padding: const EdgeInsets.all(10),
                      decoration: BoxDecoration(
                        color: Colors.black.withOpacity(0.7),
                        shape: BoxShape.circle,
                      ),
                      child: const Icon(
                        Icons.fullscreen,
                        color: Palette.textPrimary,
                        size: 20,
                      ),
                    ),
                  ),
                ),
              ),
              Positioned(
                bottom: 8,
                right: 8,
                child: Material(
                  color: Colors.transparent,
                  child: InkWell(
                    onTap: () {
                      HapticFeedback.mediumImpact();
                    },
                    borderRadius: BorderRadius.circular(20),
                    child: Container(
                      padding: const EdgeInsets.all(10),
                      decoration: BoxDecoration(
                        color: Colors.black.withOpacity(0.7),
                        shape: BoxShape.circle,
                      ),
                      child: const Icon(
                        Icons.my_location,
                        color: Palette.textPrimary,
                        size: 20,
                      ),
                    ),
                  ),
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }

  void _showFullScreenMap(BuildContext context, Map<String, dynamic>? payload) {
    showDialog(
      context: context,
      barrierColor: Colors.black.withOpacity(0.9),
      builder: (context) => Dialog(
        backgroundColor: Colors.transparent,
        insetPadding: EdgeInsets.zero,
        child: Container(
          width: MediaQuery.of(context).size.width,
          height: MediaQuery.of(context).size.height,
          decoration: const BoxDecoration(color: Palette.background),
          child: Stack(
            children: [
              _ShelterMapView(payload: payload),
              Positioned(
                top: MediaQuery.of(context).padding.top + 16,
                right: 16,
                child: Material(
                  color: Colors.transparent,
                  child: InkWell(
                    onTap: () {
                      Navigator.of(context).pop();
                    },
                    borderRadius: BorderRadius.circular(20),
                    child: Container(
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: Colors.black.withOpacity(0.7),
                        shape: BoxShape.circle,
                      ),
                      child: const Icon(
                        Icons.close,
                        color: Palette.textPrimary,
                        size: 24,
                      ),
                    ),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  String _formatDateTime(DateTime dateTime) {
    final year = dateTime.year;
    final month = dateTime.month.toString().padLeft(2, '0');
    final day = dateTime.day.toString().padLeft(2, '0');
    final hour = dateTime.hour.toString().padLeft(2, '0');
    final minute = dateTime.minute.toString().padLeft(2, '0');
    return '$year년 $month월 $day일 $hour:$minute';
  }

  String _formatTime(DateTime dateTime) {
    final hour = dateTime.hour.toString().padLeft(2, '0');
    final minute = dateTime.minute.toString().padLeft(2, '0');
    return '$hour:$minute';
  }

  String _buildDetailText(Message message) {
    final detailText = message.payload?['detailText'] as String?;
    if (detailText != null && detailText.isNotEmpty) {
      return detailText;
    }
    return message.text ?? '상세 정보 없음';
  }
}

class _ShelterMapView extends StatefulWidget {
  const _ShelterMapView({required this.payload});

  final Map<String, dynamic>? payload;

  @override
  State<_ShelterMapView> createState() => _ShelterMapViewState();
}

class _ShelterMapViewState extends State<_ShelterMapView>
    with AutomaticKeepAliveClientMixin<_ShelterMapView> {
  WebViewController? _controller;
  bool _isLoading = true;

  @override
  bool get wantKeepAlive => true;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _initWebView();
    });
  }

  void _initWebView() {
    if (!mounted) return;
    final html = _buildMapHtml();
    final controller = WebViewController()
      ..setJavaScriptMode(JavaScriptMode.unrestricted)
      ..setBackgroundColor(const Color(0xFF1a1a1a))
      ..addJavaScriptChannel(
        'MapLoaded',
        onMessageReceived: (JavaScriptMessage message) {
          if (mounted) {
            setState(() {
              _isLoading = false;
            });
          }
        },
      )
      ..setNavigationDelegate(
        NavigationDelegate(
          onPageFinished: (String _) {
            if (mounted && _isLoading) {
              setState(() {
                _isLoading = false;
              });
            }
          },
        ),
      )
      ..loadRequest(
        Uri.dataFromString(
          html,
          mimeType: 'text/html',
          encoding: Encoding.getByName('utf-8'),
        ),
      );

    setState(() {
      _controller = controller;
    });
  }

  String _buildMapHtml() {
    final bbox = widget.payload?['bbox'] as List?;
    final bboxJson = bbox != null ? jsonEncode(bbox) : 'null';

    const focusLat = 37.48;
    const focusLon = 127.06;
    const focusZoom = 15.0;

    final shelters = [
      [37.485, 127.065, '대피소 1'],
      [37.475, 127.055, '대피소 2'],
      [37.48, 127.07, '대피소 3'],
    ];

    return '''
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1.0,maximum-scale=1.0" />
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
  <style>
    * { margin:0; padding:0; box-sizing:border-box; }
    html, body {
      width:100%;
      height:100%;
      background:#1a1a1a;
      overflow:hidden;
    }
    #map {
      width:100%;
      height:100%;
    }
  </style>
</head>
<body>
  <div id="map"></div>
  <script>
    window._senseFocusLat = $focusLat;
    window._senseFocusLon = $focusLon;
    window._senseFocusZoom = $focusZoom;
    window._senseHazardBbox = $bboxJson;
    window._senseShelters = ${jsonEncode(shelters)};

    function initMap() {
      if (typeof L === 'undefined') {
        console.error('Leaflet not loaded');
        try {
          if (window.MapLoaded && window.MapLoaded.postMessage) {
            window.MapLoaded.postMessage('error');
          }
        } catch (_) {}
        return;
      }

      window._senseMap = L.map('map', {
        center: [window._senseFocusLat, window._senseFocusLon],
        zoom: window._senseFocusZoom,
        zoomControl: false,
      });

      L.tileLayer(
        'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
        {
          attribution: '© OpenStreetMap contributors',
          maxZoom: 19,
        }
      ).addTo(window._senseMap);

      // 현재 위치 마커
      L.circleMarker(
        [window._senseFocusLat, window._senseFocusLon],
        {
          radius: 10,
          color: '#ff4444',
          fillColor: '#ff4444',
          fillOpacity: 0.9,
          weight: 3
        }
      ).addTo(window._senseMap);

      // 대피소 마커
      if (window._senseShelters && Array.isArray(window._senseShelters)) {
        window._senseShelters.forEach(function(shelter) {
          L.marker([shelter[0], shelter[1]], {
            icon: L.icon({
              iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-blue.png',
              iconSize: [25, 41],
              iconAnchor: [12, 41],
              popupAnchor: [1, -34],
            })
          }).addTo(window._senseMap);
        });
      }

      // 위험구역 bbox (있는 경우)
      if (window._senseHazardBbox && window._senseHazardBbox.length === 4) {
        var b = window._senseHazardBbox;
        var rectBounds = [[b[1], b[0]], [b[3], b[2]]];
        L.rectangle(rectBounds, {
          color: '#ff6b6b',
          fillColor: '#ff6b6b',
          fillOpacity: 0.2,
          weight: 2
        }).addTo(window._senseMap);
      }

      try {
        if (window.MapLoaded && window.MapLoaded.postMessage) {
          window.MapLoaded.postMessage('loaded');
        }
      } catch (e) {
        console.log('Cannot send message to Flutter:', e);
      }
    }

    if (typeof L !== 'undefined') {
      initMap();
    } else {
      window.addEventListener('load', initMap);
    }
  </script>
</body>
</html>
''';
  }

  @override
  Widget build(BuildContext context) {
    super.build(context);

    if (_controller == null || _isLoading) {
      return Container(
        color: const Color(0xFF1a1a1a),
        alignment: Alignment.center,
        child: const SizedBox(
          width: 20,
          height: 20,
          child: CircularProgressIndicator(
            strokeWidth: 2,
            valueColor: AlwaysStoppedAnimation<Color>(Colors.grey),
          ),
        ),
      );
    }

    return WebViewWidget(controller: _controller!);
  }
}

class _InputBar extends StatelessWidget {
  const _InputBar({required this.textController, required this.onSend});

  final TextEditingController textController;
  final VoidCallback onSend;

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      top: false,
      child: Padding(
        padding: const EdgeInsets.fromLTRB(12, 8, 12, 12),
        child: Row(
          children: [
            Expanded(
              child: TextField(
                controller: textController,
                style: const TextStyle(color: Color(0xFFf9fafb)),
                keyboardType: TextInputType.multiline,
                minLines: 1,
                maxLines: 5,
                decoration: const InputDecoration(
                  hintText: '메시지 입력...',
                  hintStyle: TextStyle(color: Color(0xFF6b7280)),
                  isDense: true,
                  border: OutlineInputBorder(
                    borderSide: BorderSide(color: Color(0xFF4b5563)),
                  ),
                  enabledBorder: OutlineInputBorder(
                    borderSide: BorderSide(color: Color(0xFF4b5563)),
                  ),
                  focusedBorder: OutlineInputBorder(
                    borderSide: BorderSide(color: Color(0xFFf59e0b)),
                  ),
                ),
                onSubmitted: (_) => onSend(),
              ),
            ),
            const SizedBox(width: 8),
            IconButton(
              onPressed: onSend,
              icon: const Icon(Icons.send, color: Palette.white),
            ),
          ],
        ),
      ),
    );
  }
}

class _ChatBubble extends StatelessWidget {
  const _ChatBubble({
    required this.text,
    required this.mine,
    required this.timestamp,
  });

  final String text;
  final bool mine;
  final DateTime timestamp;

  String _formatTime(DateTime dateTime) {
    final hour = dateTime.hour.toString().padLeft(2, '0');
    final minute = dateTime.minute.toString().padLeft(2, '0');
    return '$hour:$minute';
  }

  @override
  Widget build(BuildContext context) {
    final bg = mine ? Palette.chatBackground : Palette.system;
    final maxBubbleWidth = MediaQuery.of(context).size.width * 0.8 - 20;
    return Align(
      alignment: mine ? Alignment.centerRight : Alignment.centerLeft,
      child: Column(
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              if (mine) ...[
                Spacer(),
                Text(
                  _formatTime(timestamp),
                  style: TextStyle(
                    color: Palette.textSecondary,
                    fontSize: 11,
                    fontWeight: FontWeight.w400,
                  ),
                ),
                SizedBox(width: 10),
              ],
              ConstrainedBox(
                constraints: BoxConstraints(maxWidth: maxBubbleWidth),
                child: Container(
                  margin: const EdgeInsets.only(top: 16),
                  padding: EdgeInsets.only(
                    top: 10,
                    bottom: 10,
                    left: 12,
                    right: mine ? 12 : 6,
                  ),
                  decoration: BoxDecoration(
                    border: Border.all(color: Palette.border, width: 0.8),
                    color: bg,
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Row(
                        mainAxisSize: MainAxisSize.min,
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Flexible(
                            child: Text(
                              text,
                              style: TextStyle(color: Palette.textPrimary),
                              softWrap: true,
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 6),
                    ],
                  ),
                ),
              ),
              if (!mine) ...[
                SizedBox(width: 10),
                Text(
                  _formatTime(timestamp),
                  style: TextStyle(
                    color: Palette.textSecondary,
                    fontSize: 11,
                    fontWeight: FontWeight.w400,
                  ),
                ),
              ],
            ],
          ),
        ],
      ),
    );
  }
}

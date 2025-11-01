import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_riverpod/legacy.dart';
import 'package:sense/src/features/estimator/provider/estimation_provider.dart';
import 'package:sense/src/features/estimator/provider/provider.dart';

final _baselineSheetOpenProvider = StateProvider<bool>((_) => false);

class LiveFloorBadge extends ConsumerWidget {
  const LiveFloorBadge({super.key, this.compact = false});
  final bool compact;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final sheetOpen = ref.watch(_baselineSheetOpenProvider);
    final est = sheetOpen
        ? ref.read(estimationProvider)
        : ref.watch(estimationProvider);
    final state = sheetOpen
        ? ref.read(profileProvider)
        : ref.watch(profileProvider);
    final hasProfile = est != null && state.profile != null;
    final label = hasProfile
        ? formatFloorLabel(baselineFloor: 1, estimatedFloor: est.estimatedFloor)
        : '—';

    final subtitle = hasProfile
        ? '${est!.deltaMeters.toStringAsFixed(1)} m'
        : '미설정';

    Future<void> openSheet() async {
      if (ref.read(_baselineSheetOpenProvider)) return;
      ref.read(_baselineSheetOpenProvider.notifier).state = true;
      try {
        final rootCtx = Navigator.of(context, rootNavigator: true).context;
        await showModalBottomSheet(
          context: rootCtx,
          useRootNavigator: true,
          isScrollControlled: true,
          showDragHandle: true,
          builder: (_) => const _BaselineSheet(),
        );
      } finally {
        ref.read(_baselineSheetOpenProvider.notifier).state = false;
      }
    }

    if (compact) {
      return GestureDetector(
        onTap: openSheet,
        child: Chip(
          labelPadding: const EdgeInsets.symmetric(horizontal: 8),
          avatar: const Icon(Icons.stairs_outlined, size: 18),
          label: sheetOpen
              ? Text(label, style: const TextStyle(fontWeight: FontWeight.w700))
              : AnimatedSwitcher(
                  duration: const Duration(milliseconds: 150),
                  child: Text(
                    label,
                    key: ValueKey(label),
                    style: const TextStyle(fontWeight: FontWeight.w700),
                  ),
                ),
        ),
      );
    }

    return Card(
      elevation: 0,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: BorderSide(color: Theme.of(context).colorScheme.outlineVariant),
      ),
      child: InkWell(
        onTap: openSheet,
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(Icons.stairs_outlined),
              const SizedBox(width: 8),
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('현재 층', style: Theme.of(context).textTheme.labelMedium),
                  Row(
                    children: [
                      sheetOpen
                          ? Text(
                              label,
                              style: Theme.of(context).textTheme.titleLarge
                                  ?.copyWith(fontWeight: FontWeight.w800),
                            )
                          : AnimatedSwitcher(
                              duration: const Duration(milliseconds: 150),
                              child: Text(
                                label,
                                key: ValueKey(label),
                                style: Theme.of(context).textTheme.titleLarge
                                    ?.copyWith(fontWeight: FontWeight.w800),
                              ),
                            ),
                      const SizedBox(width: 6),
                      Text(
                        subtitle,
                        style: Theme.of(context).textTheme.labelSmall?.copyWith(
                          color: Theme.of(context).hintColor,
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _BaselineSheet extends ConsumerStatefulWidget {
  const _BaselineSheet({super.key});
  @override
  ConsumerState<_BaselineSheet> createState() => _BaselineSheetState();
}

class _BaselineSheetState extends ConsumerState<_BaselineSheet> {
  bool _busy = false;

  Future<void> _calibrateP0Only() async {
    if (_busy) return;
    final sensor = ref.read(sensorProvider).sample;
    if (sensor == null) return;
    setState(() => _busy = true);
    try {
      await ref
          .read(profileProvider.notifier)
          .calibrateFromPressure(sensor.emaHpa);
      if (mounted) Navigator.of(context, rootNavigator: true).pop();
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final sensor = ref.watch(sensorProvider).sample;
    final bottomInset = MediaQuery.of(context).viewInsets.bottom;

    return SafeArea(
      top: false,
      child: Padding(
        padding: EdgeInsets.only(
          left: 16,
          right: 16,
          top: 16,
          bottom: bottomInset + 16,
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(
              '기준점 보정',
              style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w700),
            ),
            const SizedBox(height: 12),
            ListTile(
              contentPadding: EdgeInsets.zero,
              leading: const Icon(Icons.speed_outlined),
              title: const Text('현재 층을 기준층(1층)으로 저장'),
              subtitle: Text(
                sensor == null
                    ? '센서값 없음'
                    : '현재 압력: ${sensor.emaHpa.toStringAsFixed(2)} hPa',
                style: Theme.of(context).textTheme.labelSmall,
              ),
              trailing: FilledButton.tonal(
                onPressed: (sensor == null || _busy) ? null : _calibrateP0Only,
                child: _busy
                    ? const SizedBox(
                        width: 16,
                        height: 16,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : const Text('저장'),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _FloorInputDialog extends StatefulWidget {
  const _FloorInputDialog({required this.initial, super.key});
  final int initial;

  @override
  State<_FloorInputDialog> createState() => _FloorInputDialogState();
}

class _FloorInputDialogState extends State<_FloorInputDialog> {
  late final TextEditingController _c;
  bool _okBusy = false;

  @override
  void initState() {
    super.initState();
    _c = TextEditingController(text: widget.initial.toString());
  }

  @override
  void dispose() {
    _c.dispose();
    super.dispose();
  }

  void _submit() {
    if (_okBusy) return;
    setState(() => _okBusy = true);
    final v = int.tryParse(_c.text.trim());
    Navigator.of(context).pop(v);
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: const Text('현재 층 입력'),
      content: TextField(
        controller: _c,
        autofocus: true,
        keyboardType: const TextInputType.numberWithOptions(signed: true),
        decoration: const InputDecoration(hintText: '예: 1(1F), 0(B1), -1(B2)'),
      ),
      actions: [
        TextButton(
          onPressed: _okBusy ? null : () => Navigator.of(context).pop(null),
          child: const Text('취소'),
        ),
        FilledButton(
          onPressed: _okBusy ? null : _submit,
          child: _okBusy
              ? const SizedBox(
                  width: 16,
                  height: 16,
                  child: CircularProgressIndicator(strokeWidth: 2),
                )
              : const Text('확인'),
        ),
      ],
    );
  }
}

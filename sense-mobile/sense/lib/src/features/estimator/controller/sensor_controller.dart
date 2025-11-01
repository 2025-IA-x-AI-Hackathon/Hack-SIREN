import 'dart:async';
import 'package:flutter_riverpod/legacy.dart';
import 'package:sense/src/features/estimator/data/pressure/pressure_source.dart';
import 'package:sense/src/features/estimator/domain/entities/sensor.dart';
import 'package:sense/src/features/estimator/domain/services/pressure_ema.dart';

class SensorState {
  final Sensor? sample;
  const SensorState({this.sample});
  SensorState copyWith({Sensor? sample}) =>
      SensorState(sample: sample ?? this.sample);
}

class SensorController extends StateNotifier<SensorState> {
  final PressureSource source;
  final PressureEma _ema = PressureEma(0.35);
  StreamSubscription<double>? _sub;

  SensorController(this.source) : super(const SensorState()) {
    _sub = source.pressureHpa().listen((p) {
      final smoothed = _ema.update(p);
      state = state.copyWith(
        sample: Sensor(rawHpa: p, emaHpa: smoothed, ts: DateTime.now()),
      );
    });
  }

  @override
  void dispose() {
    _sub?.cancel();
    super.dispose();
  }
}

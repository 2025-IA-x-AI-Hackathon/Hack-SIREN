import 'package:sensors_plus/sensors_plus.dart';
import 'pressure_source.dart';

class SensorsPlusPressureSource implements PressureSource {
  @override
  Stream<double> pressureHpa() {
    return barometerEventStream(
      samplingPeriod: SensorInterval.gameInterval,
    ).map((e) => e.pressure);
  }
}

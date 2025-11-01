class PressureEma {
  final double alpha;
  double? _ema;
  PressureEma(this.alpha);
  double update(double x) {
    _ema = (_ema == null) ? x : alpha * x + (1 - alpha) * _ema!;
    return _ema!;
  }
}

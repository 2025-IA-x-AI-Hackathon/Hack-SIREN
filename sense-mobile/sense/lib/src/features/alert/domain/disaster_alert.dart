class DisasterAlert {
  final String sender;
  final String body;
  final DateTime timestamp;

  DisasterAlert({
    required this.sender,
    required this.body,
    required this.timestamp,
  });

  factory DisasterAlert.fromJson(Map<String, dynamic> json) {
    return DisasterAlert(
      sender: json['sender'] as String? ?? '',
      body: json['body'] as String? ?? '',
      timestamp: DateTime.fromMillisecondsSinceEpoch(
        json['timestamp'] as int? ?? DateTime.now().millisecondsSinceEpoch,
      ),
    );
  }
}

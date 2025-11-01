import 'package:dio/dio.dart';
import 'package:sense/src/features/message/data/dto/message_dto.dart';

class MessageApi {
  final Dio dio;
  MessageApi(this.dio);

  Future<List<MessageDto>> fetchSince(DateTime since) async {
    final iso = since.toUtc().toIso8601String();
    final _ = await Future.value(iso);
    return [];
  }

  Future<void> send(MessageDto dto) async {
    final _ = await Future.value(dto.toJson());
  }
}

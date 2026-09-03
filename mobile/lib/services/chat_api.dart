import 'package:dio/dio.dart';
import '../core/api_client.dart';
import '../core/api_exception.dart';
import '../models/chat.dart';

/// Wraps the REST half of chat (app/api/conversations/router.py). The
/// live/real-time half is ChatSocket (chat_socket.dart) — this class only
/// covers history + the "start a conversation" handshake + a REST
/// send fallback for when the socket isn't connected.
class ChatApi {
  final Dio _dio = ApiClient.instance.dio;

  Future<List<ConversationInfo>> listConversations() async {
    try {
      final res = await _dio.get('/conversations');
      return (res.data as List).map((j) => ConversationInfo.fromJson(j as Map<String, dynamic>)).toList();
    } on DioException catch (e) {
      throw ApiException.fromDioError(e);
    }
  }

  /// PATIENT-only per the backend — starts or resumes a conversation with
  /// a nurse (mirrors the "Message" button on a nurse's profile).
  Future<ConversationInfo> startConversation({required String nurseId}) async {
    try {
      final res = await _dio.post('/conversations', data: {'nurse_id': nurseId});
      return ConversationInfo.fromJson(res.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw ApiException.fromDioError(e);
    }
  }

  Future<List<ChatMessage>> listMessages(String conversationId, {int limit = 50, int offset = 0}) async {
    try {
      final res = await _dio.get('/conversations/$conversationId/messages',
          queryParameters: {'limit': limit, 'offset': offset});
      return (res.data as List).map((j) => ChatMessage.fromJson(j as Map<String, dynamic>)).toList();
    } on DioException catch (e) {
      throw ApiException.fromDioError(e);
    }
  }

  /// REST fallback send — used only if the WebSocket isn't connected
  /// (matches the backend's own documented fallback semantics).
  Future<ChatMessage> sendMessageRest(
    String conversationId, {
    required MessageType type,
    String? content,
    String? attachmentUrl,
  }) async {
    try {
      final res = await _dio.post('/conversations/$conversationId/messages', data: {
        'message_type': messageTypeToApi(type),
        if (content != null) 'content': content,
        if (attachmentUrl != null) 'attachment_url': attachmentUrl,
      });
      return ChatMessage.fromJson(res.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw ApiException.fromDioError(e);
    }
  }
}

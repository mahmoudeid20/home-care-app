import 'dart:async';
import 'dart:convert';
import 'package:web_socket_channel/web_socket_channel.dart';
import '../core/env.dart';
import '../core/token_storage.dart';
import '../models/chat.dart';

/// One socket per open conversation screen. Matches
/// app/websocket/chat_ws.py exactly:
///   - connect to  ws(s)://<host>/ws/conversations/{id}?token=<access_token>
///     (no /api/v1 prefix — see Env.wsBaseUrl; access token as a query
///     param because browsers/WS clients can't set a handshake header)
///   - send:    {"message_type": "TEXT", "content": "..."}
///              {"message_type": "IMAGE", "attachment_url": "...", "content": "optional caption"}
///   - receive: the persisted MessageResponse JSON, broadcast to every
///     participant connected to this conversation right now
///   - receive: {"error": "..."} if a sent frame failed validation —
///     the connection stays open, only that frame was rejected
///
/// Close codes the server uses: 4401 (bad/missing token), 4403 (not a
/// participant in this conversation) — surfaced via [onAuthError].
class ChatSocket {
  WebSocketChannel? _channel;
  StreamSubscription? _sub;

  final _messagesController = StreamController<ChatMessage>.broadcast();
  final _errorsController = StreamController<String>.broadcast();

  Stream<ChatMessage> get messages => _messagesController.stream;
  Stream<String> get errors => _errorsController.stream;

  /// Called when the server closes the socket with 4401/4403 — the caller
  /// (ChatThreadScreen) should show "you can't access this conversation"
  /// rather than a generic connection-error retry loop.
  void Function()? onAuthError;

  /// Called on any other disconnect (network drop, server restart) so the
  /// UI can show a "reconnecting..." indicator and offer manual retry.
  void Function()? onDisconnected;

  bool get isConnected => _channel != null;

  Future<void> connect(String conversationId) async {
    final token = await TokenStorage.instance.accessToken;
    if (token == null) {
      onAuthError?.call();
      return;
    }

    final uri = Uri.parse('${Env.wsBaseUrl}/ws/conversations/$conversationId?token=$token');
    final channel = WebSocketChannel.connect(uri);
    _channel = channel;

    _sub = channel.stream.listen(
      (raw) {
        final Map<String, dynamic> data = jsonDecode(raw as String) as Map<String, dynamic>;
        if (data.containsKey('error')) {
          _errorsController.add(data['error'] as String);
          return;
        }
        _messagesController.add(ChatMessage.fromJson(data));
      },
      onError: (_) {
        _channel = null;
        onDisconnected?.call();
      },
      onDone: () {
        final code = channel.closeCode;
        _channel = null;
        if (code == 4401 || code == 4403) {
          onAuthError?.call();
        } else {
          onDisconnected?.call();
        }
      },
      cancelOnError: true,
    );
  }

  void sendText(String content) {
    _channel?.sink.add(jsonEncode({'message_type': 'TEXT', 'content': content}));
  }

  void sendImage(String attachmentUrl, {String? caption}) {
    _channel?.sink.add(jsonEncode({
      'message_type': 'IMAGE',
      'attachment_url': attachmentUrl,
      if (caption != null) 'content': caption,
    }));
  }

  Future<void> dispose() async {
    await _sub?.cancel();
    await _channel?.sink.close();
    await _messagesController.close();
    await _errorsController.close();
  }
}

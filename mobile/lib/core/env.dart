/// Central runtime config. Override at build/run time with:
///   flutter run --dart-define=API_BASE_URL=https://api.sanad.app/api/v1
class Env {
  Env._();

  static const apiBaseUrl = String.fromEnvironment(
    'API_BASE_URL',
    // Connected to the 24/7 cloud backend on Hugging Face
    defaultValue: 'https://mahmoudeid205-homecare-api.hf.space/api/v1',
  );

  /// The WebSocket chat route (app/websocket/chat_ws.py) is mounted at the
  /// app root, not under /api/v1 (see app/main.py's chat_ws_router include),
  /// so it needs its own base derived from apiBaseUrl rather than reusing it.
  static String get wsBaseUrl {
    final uri = Uri.parse(apiBaseUrl);
    final scheme = uri.scheme == 'https' ? 'wss' : 'ws';
    return '$scheme://${uri.authority}';
  }
}

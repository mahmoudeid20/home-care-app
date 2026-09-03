/// Central runtime config. Override at build/run time with:
///   flutter run --dart-define=API_BASE_URL=https://api.sanad.app/api/v1
class Env {
  Env._();

  static const apiBaseUrl = String.fromEnvironment(
    'API_BASE_URL',
    // Uses the machine's local Wi-Fi IP so the app works seamlessly on physical
    // Android mobile devices as well as emulators and desktop.
    defaultValue: 'http://192.168.1.10:8000/api/v1',
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

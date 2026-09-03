import 'dart:async';
import 'package:dio/dio.dart';
import 'env.dart';
import 'token_storage.dart';
import 'api_exception.dart';

/// One Dio instance for the whole app.
///
/// - Attaches `Authorization: Bearer <access_token>` to every request.
/// - On a 401, tries exactly one silent refresh (POST /auth/refresh) and
///   replays the original request; if the refresh itself fails, calls
///   [onSessionExpired] so the UI can drop back to the login screen.
/// - Refreshes are single-flight: concurrent 401s while a refresh is
///   already in progress await the same Future instead of each firing
///   their own POST /auth/refresh (the backend rotates refresh tokens,
///   so a second concurrent refresh would invalidate the first).
class ApiClient {
  ApiClient._internal() {
    _dio = Dio(BaseOptions(
      baseUrl: Env.apiBaseUrl,
      connectTimeout: const Duration(seconds: 4),
      receiveTimeout: const Duration(seconds: 6),
      headers: {'Content-Type': 'application/json'},
    ));

    _dio.interceptors.add(InterceptorsWrapper(
      onRequest: (options, handler) async {
        final token = await TokenStorage.instance.accessToken;
        if (token != null) {
          options.headers['Authorization'] = 'Bearer $token';
        }
        handler.next(options);
      },
      onError: (error, handler) async {
        final isAuthEndpoint = error.requestOptions.path.contains('/auth/');
        if (error.response?.statusCode == 401 && !isAuthEndpoint) {
          try {
            await _refreshAccessToken();
            final retried = await _retry(error.requestOptions);
            return handler.resolve(retried);
          } catch (_) {
            await TokenStorage.instance.clear();
            onSessionExpired?.call();
          }
        }
        handler.next(error);
      },
    ));
  }

  static final ApiClient instance = ApiClient._internal();
  late final Dio _dio;
  Dio get dio => _dio;

  /// Set by AuthController at app start; invoked when a refresh attempt
  /// itself fails, meaning the refresh token is dead too — the user must
  /// log in again.
  void Function()? onSessionExpired;

  Future<Response<dynamic>> _retry(RequestOptions requestOptions) {
    final options = Options(method: requestOptions.method, headers: requestOptions.headers);
    return _dio.request<dynamic>(
      requestOptions.path,
      data: requestOptions.data,
      queryParameters: requestOptions.queryParameters,
      options: options,
    );
  }

  Completer<void>? _refreshCompleter;

  Future<void> _refreshAccessToken() async {
    if (_refreshCompleter != null) return _refreshCompleter!.future;

    final completer = Completer<void>();
    _refreshCompleter = completer;
    try {
      final refreshToken = await TokenStorage.instance.refreshToken;
      if (refreshToken == null) throw const ApiException(code: 'NO_REFRESH_TOKEN', message: 'Not logged in');

      // Bare Dio call (not this._dio) so the request interceptor above
      // doesn't attach a now-expired access token to the refresh call.
      final response = await Dio(BaseOptions(baseUrl: Env.apiBaseUrl)).post(
        '/auth/refresh',
        data: {'refresh_token': refreshToken},
      );
      final newAccess = response.data['access_token'] as String;
      final newRefresh = response.data['refresh_token'] as String;
      await TokenStorage.instance.save(accessToken: newAccess, refreshToken: newRefresh);
      completer.complete();
    } catch (e) {
      completer.completeError(e);
      rethrow;
    } finally {
      _refreshCompleter = null;
    }
  }
}

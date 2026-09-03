import 'package:dio/dio.dart';

/// Mirrors the error envelope every endpoint returns:
///   { "error": { "code": "...", "message": "...", "details": [...] } }
/// (see backend/app/main.py app_error_handler / validation_error_handler).
class ApiException implements Exception {
  final int? statusCode;
  final String code;
  final String message;

  const ApiException({this.statusCode, required this.code, required this.message});

  factory ApiException.fromDioError(DioException e) {
    final data = e.response?.data;
    if (data is Map && data['error'] is Map) {
      final err = data['error'] as Map;
      return ApiException(
        statusCode: e.response?.statusCode,
        code: (err['code'] as String?) ?? 'UNKNOWN_ERROR',
        message: (err['message'] as String?) ?? 'Something went wrong.',
      );
    }
    // Network-level failure (no response at all): timeout, no connectivity,
    // server unreachable — distinguish from a real API error above.
    return ApiException(
      statusCode: e.response?.statusCode,
      code: 'NETWORK_ERROR',
      message: switch (e.type) {
        DioExceptionType.connectionTimeout ||
        DioExceptionType.sendTimeout ||
        DioExceptionType.receiveTimeout =>
          'connection_timeout',
        DioExceptionType.connectionError => 'connection_error',
        _ => e.message ?? 'unknown_network_error',
      },
    );
  }

  @override
  String toString() => 'ApiException($code): $message';
}

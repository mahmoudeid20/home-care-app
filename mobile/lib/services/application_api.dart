import 'package:dio/dio.dart';
import '../core/api_client.dart';
import '../core/api_exception.dart';
import '../models/application.dart';
import '../models/booking.dart';

/// Wraps /applications (app/api/applications/router.py). PATIENT sends and
/// withdraws; NURSE lists received, accepts, and rejects.
class ApplicationApi {
  final Dio _dio = ApiClient.instance.dio;

  /// PATIENT-only — "send this care request to this specific nurse".
  Future<ApplicationInfo> send({
    required String careRequestId,
    required String nurseId,
    String? message,
  }) async {
    try {
      final res = await _dio.post('/applications', data: {
        'care_request_id': careRequestId,
        'nurse_id': nurseId,
        if (message != null && message.isNotEmpty) 'message': message,
      });
      return ApplicationInfo.fromJson(res.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw ApiException.fromDioError(e);
    }
  }

  /// NURSE-only — Section 18 "New Requests".
  Future<List<ApplicationInfo>> listReceived({int limit = 20, int offset = 0}) async {
    try {
      final res = await _dio.get('/applications/received', queryParameters: {'limit': limit, 'offset': offset});
      return (res.data as List).map((j) => ApplicationInfo.fromJson(j as Map<String, dynamic>)).toList();
    } on DioException catch (e) {
      throw ApiException.fromDioError(e);
    }
  }

  /// PATIENT-only.
  Future<List<ApplicationInfo>> listSent({int limit = 20, int offset = 0}) async {
    try {
      final res = await _dio.get('/applications/sent', queryParameters: {'limit': limit, 'offset': offset});
      return (res.data as List).map((j) => ApplicationInfo.fromJson(j as Map<String, dynamic>)).toList();
    } on DioException catch (e) {
      throw ApiException.fromDioError(e);
    }
  }

  /// NURSE-only. Accepting creates a Booking server-side — this is the
  /// one action in this API that returns a different resource type than
  /// what it operates on.
  Future<BookingInfo> accept(String applicationId) async {
    try {
      final res = await _dio.post('/applications/$applicationId/accept');
      return BookingInfo.fromJson(res.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw ApiException.fromDioError(e);
    }
  }

  /// NURSE-only.
  Future<ApplicationInfo> reject(String applicationId, {String? reason}) async {
    try {
      final res = await _dio.post('/applications/$applicationId/reject', data: {
        if (reason != null && reason.isNotEmpty) 'reason': reason,
      });
      return ApplicationInfo.fromJson(res.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw ApiException.fromDioError(e);
    }
  }

  /// PATIENT-only — withdraw before the nurse responds.
  Future<ApplicationInfo> withdraw(String applicationId) async {
    try {
      final res = await _dio.post('/applications/$applicationId/withdraw');
      return ApplicationInfo.fromJson(res.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw ApiException.fromDioError(e);
    }
  }
}

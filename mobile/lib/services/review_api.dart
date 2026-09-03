import 'package:dio/dio.dart';
import '../core/api_client.dart';
import '../core/api_exception.dart';
import '../models/review.dart';

/// Wraps app/api/reviews/router.py. PATIENT-only create, scoped to a
/// COMPLETED booking they own; public (any authed role) read per nurse.
class ReviewApi {
  final Dio _dio = ApiClient.instance.dio;

  Future<ReviewInfo> create({
    required String bookingId,
    required int overallRating,
    required int professionalism,
    required int communication,
    required int careQuality,
    String? comment,
  }) async {
    try {
      final res = await _dio.post('/reviews', data: {
        'booking_id': bookingId,
        'overall_rating': overallRating,
        'professionalism': professionalism,
        'communication': communication,
        'care_quality': careQuality,
        if (comment != null && comment.isNotEmpty) 'comment': comment,
      });
      return ReviewInfo.fromJson(res.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw ApiException.fromDioError(e);
    }
  }

  Future<List<ReviewInfo>> listForNurse(String nurseId, {int limit = 20, int offset = 0}) async {
    try {
      final res = await _dio.get('/nurses/$nurseId/reviews', queryParameters: {'limit': limit, 'offset': offset});
      return (res.data as List).map((j) => ReviewInfo.fromJson(j as Map<String, dynamic>)).toList();
    } on DioException catch (e) {
      throw ApiException.fromDioError(e);
    }
  }
}

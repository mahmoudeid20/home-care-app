import 'package:dio/dio.dart';
import '../core/api_client.dart';
import '../core/api_exception.dart';
import '../models/nurse_detail.dart';
import '../widgets/nurse_summary.dart';

/// Wraps GET /nurses (backend/app/api/nurses/router.py search_nurses).
/// Requires auth (PATIENT/NURSE/ADMIN) — the Authorization header is
/// attached automatically by ApiClient's interceptor.
class NurseApi {
  final Dio _dio = ApiClient.instance.dio;

  Future<List<NurseSummary>> search({
    String? specialtyId,
    double? minRating,
    bool verifiedOnly = false,
    int limit = 20,
    int offset = 0,
  }) async {
    try {
      final res = await _dio.get('/nurses', queryParameters: {
        if (specialtyId != null) 'specialty_id': specialtyId,
        if (minRating != null) 'min_rating': minRating,
        if (verifiedOnly) 'verified_only': true,
        'limit': limit,
        'offset': offset,
      });
      final list = res.data as List;
      return list.map((j) => NurseSummary.fromJson(j as Map<String, dynamic>)).toList();
    } on DioException catch (e) {
      throw ApiException.fromDioError(e);
    }
  }

  /// GET /nurses/{id} — full public profile (bio, services, availability).
  Future<NurseDetail> getById(String nurseId) async {
    try {
      final res = await _dio.get('/nurses/$nurseId');
      return NurseDetail.fromJson(res.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw ApiException.fromDioError(e);
    }
  }

  /// PATCH /nurses/me — used by the "change photo" flow on the Profile
  /// tab once ObjectStorageUploader has returned a real URL.
  Future<void> updateMyPhoto(String photoUrl) async {
    try {
      await _dio.patch('/nurses/me', data: {'photo_url': photoUrl});
    } on DioException catch (e) {
      throw ApiException.fromDioError(e);
    }
  }
}


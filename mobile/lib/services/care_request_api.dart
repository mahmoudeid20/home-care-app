import 'package:dio/dio.dart';
import '../core/api_client.dart';
import '../core/api_exception.dart';
import '../models/care_request.dart';

/// Wraps POST /care-requests and GET /care-requests
/// (app/api/care_requests/router.py). PATIENT role only.
class CareRequestApi {
  final Dio _dio = ApiClient.instance.dio;

  /// Returns the new care request's id.
  Future<String> create(CareRequestDraft draft) async {
    try {
      final res = await _dio.post('/care-requests', data: draft.toJson());
      return res.data['id'] as String;
    } on DioException catch (e) {
      throw ApiException.fromDioError(e);
    }
  }

  Future<List<CareRequestSummary>> listMine() async {
    try {
      final res = await _dio.get('/care-requests');
      return (res.data as List)
          .map((j) => CareRequestSummary.fromJson(j as Map<String, dynamic>))
          .toList();
    } on DioException catch (e) {
      throw ApiException.fromDioError(e);
    }
  }

  /// GET /care-requests/{id} — owning patient, or (since the backend
  /// change in this slice) a nurse who has applied to it.
  Future<CareRequestDetail> getById(String careRequestId) async {
    try {
      final res = await _dio.get('/care-requests/$careRequestId');
      return CareRequestDetail.fromJson(res.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw ApiException.fromDioError(e);
    }
  }
}

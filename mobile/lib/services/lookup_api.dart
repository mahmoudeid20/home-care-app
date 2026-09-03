import 'package:dio/dio.dart';
import '../core/api_client.dart';
import '../core/api_exception.dart';
import '../models/lookup.dart';

/// Wraps GET /specialties and GET /services (app/api/lookup/router.py).
/// Public catalog data — same endpoints regardless of role.
class LookupApi {
  final Dio _dio = ApiClient.instance.dio;

  Future<List<Specialty>> specialties() async {
    try {
      final res = await _dio.get('/specialties');
      return (res.data as List).map((j) => Specialty.fromJson(j as Map<String, dynamic>)).toList();
    } on DioException catch (e) {
      throw ApiException.fromDioError(e);
    }
  }

  Future<List<ServiceItem>> services() async {
    try {
      final res = await _dio.get('/services');
      return (res.data as List).map((j) => ServiceItem.fromJson(j as Map<String, dynamic>)).toList();
    } on DioException catch (e) {
      throw ApiException.fromDioError(e);
    }
  }
}

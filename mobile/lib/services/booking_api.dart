import 'package:dio/dio.dart';
import '../core/api_client.dart';
import '../core/api_exception.dart';
import '../models/booking.dart';

/// Wraps GET /bookings (app/api/bookings/router.py list_my_bookings).
/// Scoped server-side to whichever party (patient or nurse) is calling.
class BookingApi {
  final Dio _dio = ApiClient.instance.dio;

  Future<List<BookingInfo>> listMine() async {
    try {
      final res = await _dio.get('/bookings');
      return (res.data as List).map((j) => BookingInfo.fromJson(j as Map<String, dynamic>)).toList();
    } on DioException catch (e) {
      throw ApiException.fromDioError(e);
    }
  }
}

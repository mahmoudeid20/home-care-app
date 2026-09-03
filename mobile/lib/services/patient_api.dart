import 'package:dio/dio.dart';
import '../core/api_client.dart';
import '../core/api_exception.dart';

class PatientProfile {
  final String id;
  final String userId;
  final String fullName;
  final String? photoUrl;
  final String? governorate;
  final String? city;

  const PatientProfile({
    required this.id,
    required this.userId,
    required this.fullName,
    this.photoUrl,
    this.governorate,
    this.city,
  });

  factory PatientProfile.fromJson(Map<String, dynamic> j) {
    final loc = j['location'] as Map<String, dynamic>?;
    return PatientProfile(
      id: j['id'] as String,
      userId: j['user_id'] as String,
      fullName: j['full_name'] as String,
      photoUrl: j['photo_url'] as String?,
      governorate: loc?['governorate'] as String?,
      city: loc?['city'] as String?,
    );
  }
}

/// Wraps /patients endpoints
class PatientApi {
  final Dio _dio = ApiClient.instance.dio;

  Future<PatientProfile?> getMyProfile() async {
    try {
      final res = await _dio.get('/patients/me');
      return PatientProfile.fromJson(res.data as Map<String, dynamic>);
    } on DioException catch (e) {
      if (e.response?.statusCode == 404) return null;
      throw ApiException.fromDioError(e);
    }
  }

  Future<PatientProfile> createProfile({
    required String fullName,
    String? governorate,
    String? city,
    String? photoUrl,
  }) async {
    try {
      final res = await _dio.post('/patients/me', data: {
        'full_name': fullName,
        'preferred_language': 'ar',
        if (photoUrl != null && photoUrl.isNotEmpty) 'photo_url': photoUrl,
        if (governorate != null && city != null)
          'location': {
            'governorate': governorate,
            'city': city,
          },
      });
      return PatientProfile.fromJson(res.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw ApiException.fromDioError(e);
    }
  }

  Future<PatientProfile> updateProfile({
    String? fullName,
    String? governorate,
    String? city,
    String? photoUrl,
  }) async {
    try {
      final res = await _dio.patch('/patients/me', data: {
        if (fullName != null) 'full_name': fullName,
        if (photoUrl != null) 'photo_url': photoUrl,
        if (governorate != null && city != null)
          'location': {
            'governorate': governorate,
            'city': city,
          },
      });
      return PatientProfile.fromJson(res.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw ApiException.fromDioError(e);
    }
  }

  Future<void> updateMyPhoto(String photoUrl) async {
    try {
      await _dio.patch('/patients/me', data: {'photo_url': photoUrl});
    } on DioException catch (e) {
      throw ApiException.fromDioError(e);
    }
  }
}

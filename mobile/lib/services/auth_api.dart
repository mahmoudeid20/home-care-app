import 'package:dio/dio.dart';
import '../core/api_client.dart';
import '../core/api_exception.dart';
import '../core/token_storage.dart';
import '../models/user.dart';

/// Wraps backend/app/api/auth/router.py exactly — one method per endpoint,
/// same request/response field names as app/schemas/auth.py.
class AuthApi {
  final Dio _dio = ApiClient.instance.dio;

  Future<AppUser> register({
    required String email,
    required String password,
    required UserRole role,
    String? phone,
    String? username,
  }) async {
    try {
      final res = await _dio.post('/auth/register', data: {
        'email': email,
        'password': password,
        'role': userRoleToApi(role),
        if (phone != null && phone.isNotEmpty) 'phone': phone,
        if (username != null && username.isNotEmpty) 'username': username,
      });
      return await _handleAuthResponse(res.data);
    } on DioException catch (e) {
      throw ApiException.fromDioError(e);
    }
  }

  Future<AppUser> login({required String email, required String password}) async {
    try {
      final res = await _dio.post('/auth/login', data: {'email': email, 'password': password});
      return await _handleAuthResponse(res.data);
    } on DioException catch (e) {
      throw ApiException.fromDioError(e);
    }
  }

  Future<AppUser> fetchCurrentUser() async {
    try {
      final res = await _dio.get('/auth/me');
      return AppUser.fromJson(res.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw ApiException.fromDioError(e);
    }
  }

  Future<void> logout() async {
    final refreshToken = await TokenStorage.instance.refreshToken;
    if (refreshToken != null) {
      try {
        await _dio.post('/auth/logout', data: {'refresh_token': refreshToken});
      } on DioException {
        // Best-effort: even if server-side revocation fails (e.g. offline),
        // we still clear local tokens below so the device is logged out.
      }
    }
    await TokenStorage.instance.clear();
  }

  Future<AppUser> _handleAuthResponse(Map<String, dynamic> data) async {
    final tokens = data['tokens'] as Map<String, dynamic>;
    await TokenStorage.instance.save(
      accessToken: tokens['access_token'] as String,
      refreshToken: tokens['refresh_token'] as String,
    );
    return AppUser.fromJson(data['user'] as Map<String, dynamic>);
  }
}

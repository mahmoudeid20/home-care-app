import 'package:dio/dio.dart';
import '../core/api_client.dart';
import '../core/api_exception.dart';

class OtpApi {
  final ApiClient _client;

  OtpApi({ApiClient? client}) : _client = client ?? ApiClient.instance;

  Future<Map<String, dynamic>> sendOtp({
    required String recipient,
    String channel = 'EMAIL',
    String purpose = 'REGISTRATION',
  }) async {
    try {
      final response = await _client.dio.post(
        '/auth/send-otp',
        data: {
          'recipient': recipient.trim(),
          'channel': channel,
          'purpose': purpose,
        },
      );
      return response.data as Map<String, dynamic>;
    } on DioException catch (e) {
      throw ApiException.fromDioError(e);
    }
  }

  Future<bool> verifyOtp({
    required String recipient,
    required String code,
    String purpose = 'REGISTRATION',
  }) async {
    try {
      final response = await _client.dio.post(
        '/auth/verify-otp',
        data: {
          'recipient': recipient.trim(),
          'code': code.trim(),
          'purpose': purpose,
        },
      );
      return response.data['verified'] == true;
    } on DioException catch (e) {
      throw ApiException.fromDioError(e);
    }
  }

  Future<Map<String, dynamic>> validateNationalId(String nationalId) async {
    try {
      final response = await _client.dio.post(
        '/auth/validate-national-id',
        data: {'national_id': nationalId.trim()},
      );
      return response.data as Map<String, dynamic>;
    } on DioException catch (e) {
      throw ApiException.fromDioError(e);
    }
  }

  Future<void> acceptTerms() async {
    try {
      await _client.dio.post('/auth/accept-terms');
    } on DioException catch (e) {
      throw ApiException.fromDioError(e);
    }
  }
}

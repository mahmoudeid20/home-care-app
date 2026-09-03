import 'dart:io';
import 'package:dio/dio.dart';
import '../core/api_client.dart';
import '../core/api_exception.dart';
import 'object_storage_uploader.dart';

/// Uploads files directly to the backend's /uploads endpoint.
/// This is the simplest storage solution — no external service needed.
/// Files are stored on the backend server and served as static files.
///
/// To migrate to S3/Supabase later, just swap this class — the
/// ObjectStorageUploader interface stays the same.
class BackendUploadUploader implements ObjectStorageUploader {
  final Dio _dio = ApiClient.instance.dio;

  @override
  Future<String> upload(File file) async {
    final fileName = file.path.split(Platform.pathSeparator).last;
    final formData = FormData.fromMap({
      'file': await MultipartFile.fromFile(file.path, filename: fileName),
    });

    try {
      final res = await _dio.post('/uploads', data: formData);
      return res.data['url'] as String;
    } on DioException catch (e) {
      throw ApiException.fromDioError(e);
    }
  }
}

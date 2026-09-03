import 'package:flutter_secure_storage/flutter_secure_storage.dart';

/// Wraps flutter_secure_storage (Keychain on iOS, EncryptedSharedPreferences
/// on Android) so access/refresh tokens never sit in plain SharedPreferences.
class TokenStorage {
  TokenStorage._();
  static final instance = TokenStorage._();

  final _storage = const FlutterSecureStorage();

  static const _kAccess = 'sanad_access_token';
  static const _kRefresh = 'sanad_refresh_token';

  Future<void> save({required String accessToken, required String refreshToken}) async {
    await _storage.write(key: _kAccess, value: accessToken);
    await _storage.write(key: _kRefresh, value: refreshToken);
  }

  Future<String?> get accessToken => _storage.read(key: _kAccess);
  Future<String?> get refreshToken => _storage.read(key: _kRefresh);

  Future<void> updateAccessToken(String token) => _storage.write(key: _kAccess, value: token);

  Future<void> clear() async {
    await _storage.delete(key: _kAccess);
    await _storage.delete(key: _kRefresh);
  }
}

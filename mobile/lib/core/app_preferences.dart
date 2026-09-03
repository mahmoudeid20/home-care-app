import 'package:flutter/material.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class AppPreferences {
  AppPreferences._();
  static final instance = AppPreferences._();

  final _storage = const FlutterSecureStorage();

  static const _kLocale = 'sanad_app_locale';
  static const _kThemeMode = 'sanad_app_theme_mode';

  Future<void> saveLocale(String languageCode) async {
    await _storage.write(key: _kLocale, value: languageCode);
  }

  Future<String?> get savedLocale async => _storage.read(key: _kLocale);

  Future<void> saveThemeMode(ThemeMode mode) async {
    await _storage.write(key: _kThemeMode, value: mode.name);
  }

  Future<ThemeMode?> get savedThemeMode async {
    final val = await _storage.read(key: _kThemeMode);
    if (val == 'dark') return ThemeMode.dark;
    if (val == 'light') return ThemeMode.light;
    if (val == 'system') return ThemeMode.system;
    return null;
  }
}

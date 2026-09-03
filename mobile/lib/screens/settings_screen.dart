import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:image_picker/image_picker.dart';
import '../core/app_preferences.dart';
import '../l10n/app_localizations.dart';
import '../main.dart';
import '../state/auth_controller.dart';
import '../theme/app_theme.dart';
import '../models/user.dart';
import '../services/backend_upload_uploader.dart';
import '../services/patient_api.dart';
import '../services/nurse_api.dart';
import 'support_screen.dart';

class SettingsScreen extends ConsumerStatefulWidget {
  const SettingsScreen({super.key});

  @override
  ConsumerState<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends ConsumerState<SettingsScreen> {
  final _uploader = BackendUploadUploader();
  final _picker = ImagePicker();
  bool _uploadingPhoto = false;

  Future<void> _pickAndUploadPhoto() async {
    final file = await _picker.pickImage(source: ImageSource.gallery, imageQuality: 85);
    if (file == null) return;

    setState(() => _uploadingPhoto = true);
    try {
      final url = await _uploader.upload(File(file.path));

      final role = ref.read(authControllerProvider).user?.role;
      if (role == UserRole.nurse) {
        await NurseApi().updateMyPhoto(url);
      } else {
        await PatientApi().updateMyPhoto(url);
      }

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('تم تحديث الصورة الشخصية بنجاح')),
        );
      }
    } catch (_) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('فشل رفع الصورة، تأكد من الاتصال')),
        );
      }
    } finally {
      if (mounted) setState(() => _uploadingPhoto = false);
    }
  }

  void _confirmLogout() {
    final isArabic = ref.read(localeProvider).languageCode == 'ar';
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text(isArabic ? 'تسجيل الخروج' : 'Log out'),
        content: Text(
          isArabic
              ? 'هل أنت متأكد من رغبتك في تسجيل الخروج من التطبيق؟'
              : 'Are you sure you want to log out?',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(),
            child: Text(isArabic ? 'إلغاء' : 'Cancel'),
          ),
          ElevatedButton(
            style: ElevatedButton.styleFrom(backgroundColor: AppColors.danger),
            onPressed: () {
              Navigator.of(ctx).pop();
              ref.read(authControllerProvider.notifier).logout();
            },
            child: Text(isArabic ? 'خروج' : 'Log out'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final t = AppLocalizations.of(context);
    final auth = ref.watch(authControllerProvider);
    final user = auth.user;
    final profile = auth.patientProfile;
    final locale = ref.watch(localeProvider);
    final themeMode = ref.watch(themeModeProvider);
    final isArabic = locale.languageCode == 'ar';
    final isDark = themeMode == ThemeMode.dark;

    final fullName = profile?.fullName.isNotEmpty == true
        ? profile!.fullName
        : (user?.username ?? user?.email.split('@').first ?? (isArabic ? 'مستخدم سَنَد' : 'Sanad User'));
    final userRole = user?.role == UserRole.nurse
        ? (isArabic ? 'ممرض/ة معتمد' : 'Verified Nurse')
        : (isArabic ? 'مريض / صاحب حساب' : 'Patient / Account holder');
    final location = profile?.governorate != null
        ? '${profile!.governorate} • ${profile.city ?? ""}'
        : (isArabic ? 'جمهورية مصر العربية' : 'Egypt');

    return Scaffold(
      backgroundColor: AppColors.bgOf(context),
      appBar: AppBar(
        title: Text(t.settings),
        elevation: 0,
        backgroundColor: AppColors.surfaceOf(context),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
        child: Column(
          children: [
            // User Card Header
            Container(
              padding: const EdgeInsets.all(18),
              decoration: BoxDecoration(
                color: AppColors.surfaceOf(context),
                borderRadius: BorderRadius.circular(AppRadius.lg),
                border: Border.all(color: AppColors.lineOf(context)),
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withOpacity(isDark ? 0.2 : 0.03),
                    blurRadius: 10,
                    offset: const Offset(0, 3),
                  ),
                ],
              ),
              child: Row(
                children: [
                  Stack(
                    children: [
                      CircleAvatar(
                        radius: 34,
                        backgroundColor: AppColors.primary.withOpacity(0.12),
                        backgroundImage: profile?.photoUrl != null
                            ? NetworkImage(profile!.photoUrl!)
                            : null,
                        child: profile?.photoUrl == null
                            ? const Icon(Icons.person, size: 38, color: AppColors.primary)
                            : null,
                      ),
                      PositionTileCamera(
                        isLoading: _uploadingPhoto,
                        onTap: _pickAndUploadPhoto,
                      ),
                    ],
                  ),
                  const SizedBox(width: 16),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          fullName,
                          style: TextStyle(
                            fontSize: 16,
                            fontWeight: FontWeight.bold,
                            color: AppColors.inkOf(context),
                          ),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                        const SizedBox(height: 4),
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                          decoration: BoxDecoration(
                            color: AppColors.primary.withOpacity(0.1),
                            borderRadius: BorderRadius.circular(6),
                          ),
                          child: Text(
                            userRole,
                            style: const TextStyle(
                              fontSize: 11.5,
                              color: AppColors.primary,
                              fontWeight: FontWeight.w700,
                            ),
                          ),
                        ),
                        const SizedBox(height: 6),
                        Row(
                          children: [
                            const Icon(Icons.location_on_outlined, size: 14, color: AppColors.primary),
                            const SizedBox(width: 4),
                            Expanded(
                              child: Text(
                                location,
                                style: TextStyle(
                                  fontSize: 11,
                                  color: AppColors.inkSoftOf(context),
                                ),
                                overflow: TextOverflow.ellipsis,
                              ),
                            ),
                          ],
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 24),

            // App Preferences Section
            _SettingsSection(
              title: t.appPreferences,
              items: [
                _SettingsTile(
                  icon: Icons.language_rounded,
                  title: t.language,
                  subtitle: isArabic ? 'العربية' : 'English',
                  trailing: DropdownButton<String>(
                    value: locale.languageCode,
                    underline: const SizedBox.shrink(),
                    dropdownColor: AppColors.surfaceOf(context),
                    items: const [
                      DropdownMenuItem(value: 'ar', child: Text('العربية')),
                      DropdownMenuItem(value: 'en', child: Text('English')),
                    ],
                    onChanged: (lang) async {
                      if (lang != null) {
                        ref.read(localeProvider.notifier).state = Locale(lang);
                        await AppPreferences.instance.saveLocale(lang);
                      }
                    },
                  ),
                ),
                _SettingsTile(
                  icon: Icons.dark_mode_outlined,
                  title: t.darkMode,
                  subtitle: isDark
                      ? (isArabic ? 'مفعل' : 'On')
                      : (isArabic ? 'معطل' : 'Off'),
                  trailing: Switch(
                    value: isDark,
                    activeColor: AppColors.primary,
                    onChanged: (enabled) async {
                      final newMode = enabled ? ThemeMode.dark : ThemeMode.light;
                      ref.read(themeModeProvider.notifier).state = newMode;
                      await AppPreferences.instance.saveThemeMode(newMode);
                    },
                  ),
                ),
              ],
            ),
            const SizedBox(height: 18),

            // Support & About Section
            _SettingsSection(
              title: t.supportAndHelp,
              items: [
                _SettingsTile(
                  icon: Icons.support_agent_rounded,
                  title: t.contactSupport,
                  subtitle: isArabic ? 'الأسئلة الشائعة وخدمة العملاء' : 'FAQ & Customer Service',
                  onTap: () {
                    Navigator.of(context).push(
                      MaterialPageRoute(builder: (_) => const SupportScreen()),
                    );
                  },
                ),
                _SettingsTile(
                  icon: Icons.shield_outlined,
                  title: t.termsAndPrivacy,
                  onTap: () {
                    showDialog(
                      context: context,
                      builder: (ctx) => AlertDialog(
                        title: Text(t.termsAndPrivacy),
                        content: SingleChildScrollView(
                          child: Text(
                            isArabic
                                ? 'تطبيق سَنَد يلتزم بأعلى معايير حماية البيانات الطبية والشخصية وفقاً لقوانين جمهورية مصر العربية لعام 2026.'
                                : 'Sanad is committed to high medical data protection and privacy standards in accordance with Egyptian regulations.',
                            style: const TextStyle(fontSize: 13.5, height: 1.5),
                          ),
                        ),
                        actions: [
                          TextButton(
                            onPressed: () => Navigator.of(ctx).pop(),
                            child: Text(isArabic ? 'إغلاق' : 'Close'),
                          ),
                        ],
                      ),
                    );
                  },
                ),
              ],
            ),
            const SizedBox(height: 24),

            // Logout Button
            OutlinedButton.icon(
              onPressed: _confirmLogout,
              style: OutlinedButton.styleFrom(
                foregroundColor: AppColors.danger,
                side: const BorderSide(color: AppColors.danger, width: 1.2),
                minimumSize: const Size.fromHeight(50),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(AppRadius.md)),
              ),
              icon: const Icon(Icons.logout_rounded, size: 20),
              label: Text(t.logout, style: const TextStyle(fontWeight: FontWeight.bold)),
            ),
            const SizedBox(height: 32),
          ],
        ),
      ),
    );
  }
}

class PositionTileCamera extends StatelessWidget {
  final bool isLoading;
  final VoidCallback onTap;

  const PositionTileCamera({super.key, required this.isLoading, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return Positioned(
      bottom: 0,
      right: 0,
      child: InkWell(
        onTap: isLoading ? null : onTap,
        child: Container(
          padding: const EdgeInsets.all(6),
          decoration: BoxDecoration(
            color: AppColors.primary,
            shape: BoxShape.circle,
            border: Border.all(color: Colors.white, width: 2),
          ),
          child: isLoading
              ? const SizedBox(
                  width: 14,
                  height: 14,
                  child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                )
              : const Icon(Icons.camera_alt, color: Colors.white, size: 14),
        ),
      ),
    );
  }
}

class _SettingsSection extends StatelessWidget {
  final String title;
  final List<Widget> items;

  const _SettingsSection({required this.title, required this.items});

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 6),
          child: Text(
            title,
            style: TextStyle(
              fontSize: 14,
              fontWeight: FontWeight.w800,
              color: AppColors.inkSoftOf(context),
            ),
          ),
        ),
        Container(
          decoration: BoxDecoration(
            color: AppColors.surfaceOf(context),
            borderRadius: BorderRadius.circular(AppRadius.md),
            border: Border.all(color: AppColors.lineOf(context)),
          ),
          child: Column(
            children: [
              for (int i = 0; i < items.length; i++) ...[
                if (i > 0) Divider(height: 1, color: AppColors.lineOf(context)),
                items[i],
              ],
            ],
          ),
        ),
      ],
    );
  }
}

class _SettingsTile extends StatelessWidget {
  final IconData icon;
  final String title;
  final String? subtitle;
  final Widget? trailing;
  final VoidCallback? onTap;

  const _SettingsTile({
    super.key,
    required this.icon,
    required this.title,
    this.subtitle,
    this.trailing,
    this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return ListTile(
      leading: Container(
        padding: const EdgeInsets.all(8),
        decoration: BoxDecoration(
          color: AppColors.primary.withOpacity(0.1),
          borderRadius: BorderRadius.circular(8),
        ),
        child: Icon(icon, color: AppColors.primary, size: 20),
      ),
      title: Text(
        title,
        style: TextStyle(
          fontSize: 14,
          fontWeight: FontWeight.w700,
          color: AppColors.inkOf(context),
        ),
      ),
      subtitle: subtitle != null
          ? Text(
              subtitle!,
              style: TextStyle(fontSize: 12, color: AppColors.inkSoftOf(context)),
            )
          : null,
      trailing: trailing ?? (onTap != null ? Icon(Icons.arrow_forward_ios_rounded, size: 14, color: AppColors.inkSoftOf(context)) : null),
      onTap: onTap,
    );
  }
}

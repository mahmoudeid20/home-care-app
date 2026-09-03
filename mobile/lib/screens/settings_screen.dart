import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:image_picker/image_picker.dart';
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
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('تسجيل الخروج'),
        content: const Text('هل أنت متأكد من رغبتك في تسجيل الخروج من التطبيق؟'),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(),
            child: const Text('إلغاء'),
          ),
          ElevatedButton(
            style: ElevatedButton.styleFrom(backgroundColor: AppColors.danger),
            onPressed: () {
              Navigator.of(ctx).pop();
              ref.read(authControllerProvider.notifier).logout();
            },
            child: const Text('خروج'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final auth = ref.watch(authControllerProvider);
    final user = auth.user;
    final profile = auth.patientProfile;
    final locale = ref.watch(localeProvider);
    final themeMode = ref.watch(themeModeProvider);

    final fullName = profile?.fullName ?? user?.username ?? user?.email.split('@').first ?? 'مستخدم سَنَد';
    final userRole = user?.role == UserRole.nurse ? 'ممرض/ة معتمد' : 'مريض / صاحب حساب';
    final location = profile?.governorate != null ? '${profile!.governorate} • ${profile.city ?? ""}' : 'جمهورية مصر العربية';

    return Scaffold(
      backgroundColor: AppColors.bg,
      appBar: AppBar(
        title: const Text('الإعدادات'),
        elevation: 0,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
        child: Column(
          children: [
            // User Card Header
            Container(
              padding: const EdgeInsets.all(18),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(AppRadius.lg),
                border: Border.all(color: AppColors.line),
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withOpacity(0.02),
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
                        backgroundColor: AppColors.primarySurface,
                        child: Text(
                          fullName.isNotEmpty ? fullName[0] : 'س',
                          style: const TextStyle(
                            fontSize: 26,
                            fontWeight: FontWeight.bold,
                            color: AppColors.primary,
                          ),
                        ),
                      ),
                      Positioned(
                        bottom: 0,
                        right: 0,
                        child: InkWell(
                          onTap: _uploadingPhoto ? null : _pickAndUploadPhoto,
                          child: Container(
                            padding: const EdgeInsets.all(6),
                            decoration: const BoxDecoration(
                              color: AppColors.primary,
                              shape: BoxShape.circle,
                            ),
                            child: _uploadingPhoto
                                ? const SizedBox(
                                    width: 14,
                                    height: 14,
                                    child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2),
                                  )
                                : const Icon(Icons.camera_alt, color: Colors.white, size: 14),
                          ),
                        ),
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
                          style: const TextStyle(
                            fontWeight: FontWeight.w800,
                            fontSize: 16.5,
                            color: AppColors.ink,
                          ),
                        ),
                        const SizedBox(height: 2),
                        Text(
                          user?.email ?? '',
                          style: const TextStyle(fontSize: 12, color: AppColors.inkSoft),
                        ),
                        const SizedBox(height: 6),
                        Row(
                          children: [
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                              decoration: BoxDecoration(
                                color: AppColors.primarySurface,
                                borderRadius: BorderRadius.circular(6),
                              ),
                              child: Text(
                                userRole,
                                style: const TextStyle(
                                  fontSize: 11,
                                  fontWeight: FontWeight.bold,
                                  color: AppColors.primaryDark,
                                ),
                              ),
                            ),
                            const SizedBox(width: 8),
                            Expanded(
                              child: Text(
                                location,
                                style: const TextStyle(fontSize: 11, color: AppColors.inkSoft),
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
              title: 'تفضيلات التطبيق',
              items: [
                _SettingsTile(
                  icon: Icons.language_rounded,
                  title: 'اللغة',
                  subtitle: locale.languageCode == 'ar' ? 'العربية' : 'English',
                  trailing: DropdownButton<String>(
                    value: locale.languageCode,
                    underline: const SizedBox.shrink(),
                    items: const [
                      DropdownMenuItem(value: 'ar', child: Text('العربية')),
                      DropdownMenuItem(value: 'en', child: Text('English')),
                    ],
                    onChanged: (lang) {
                      if (lang != null) {
                        ref.read(localeProvider.notifier).state = Locale(lang);
                      }
                    },
                  ),
                ),
                _SettingsTile(
                  icon: Icons.dark_mode_outlined,
                  title: 'الوضع الليلي',
                  trailing: Switch(
                    value: themeMode == ThemeMode.dark,
                    activeColor: AppColors.primary,
                    onChanged: (enabled) {
                      ref.read(themeModeProvider.notifier).state =
                          enabled ? ThemeMode.dark : ThemeMode.light;
                    },
                  ),
                ),
              ],
            ),
            const SizedBox(height: 18),

            // Support & About Section
            _SettingsSection(
              title: 'الدعم والمساعدة',
              items: [
                _SettingsTile(
                  icon: Icons.support_agent_rounded,
                  title: 'مركز المساعدة والدعم الفني',
                  subtitle: 'الأسئلة الشائعة وخدمة العملاء',
                  onTap: () {
                    Navigator.of(context).push(
                      MaterialPageRoute(builder: (_) => const SupportScreen()),
                    );
                  },
                ),
                _SettingsTile(
                  icon: Icons.shield_outlined,
                  title: 'الشروط والأحكام وسياسة الخصوصية',
                  onTap: () {
                    showDialog(
                      context: context,
                      builder: (ctx) => AlertDialog(
                        title: const Text('الشروط وسياسة الخصوصية'),
                        content: const SingleChildScrollView(
                          child: Text(
                            'تطبيق سَنَد يلتزم بحماية البيانات الطبية والشخصية لكافة المستخدمين وفقاً لمعايير الخصوصية والأمان الطبي المعمول بها في جمهورية مصر العربية.\n\nتقتصر الخدمات على ربط المرضى بالممرضين المعتمدين والموثقين.',
                            style: TextStyle(fontSize: 13.5, height: 1.5),
                          ),
                        ),
                        actions: [
                          TextButton(
                            onPressed: () => Navigator.of(ctx).pop(),
                            child: const Text('إغلاق'),
                          ),
                        ],
                      ),
                    );
                  },
                ),
                _SettingsTile(
                  icon: Icons.info_outline_rounded,
                  title: 'عن تطبيق سَنَد',
                  subtitle: 'الإصدار 1.0.0 (حصري لمصر)',
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
              ),
              icon: const Icon(Icons.logout_rounded, size: 20),
              label: const Text('تسجيل الخروج', style: TextStyle(fontWeight: FontWeight.bold)),
            ),
            const SizedBox(height: 32),
          ],
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
            style: const TextStyle(
              fontSize: 14,
              fontWeight: FontWeight.w800,
              color: AppColors.inkSoft,
            ),
          ),
        ),
        Container(
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(AppRadius.md),
            border: Border.all(color: AppColors.line),
          ),
          child: Column(
            children: [
              for (int i = 0; i < items.length; i++) ...[
                if (i > 0) const Divider(height: 1, color: AppColors.line),
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
          color: AppColors.primarySurface,
          borderRadius: BorderRadius.circular(8),
        ),
        child: Icon(icon, color: AppColors.primary, size: 20),
      ),
      title: Text(
        title,
        style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w700, color: AppColors.ink),
      ),
      subtitle: subtitle != null
          ? Text(subtitle!, style: const TextStyle(fontSize: 12, color: AppColors.inkSoft))
          : null,
      trailing: trailing ?? (onTap != null ? const Icon(Icons.arrow_forward_ios_rounded, size: 14, color: AppColors.inkSoft) : null),
      onTap: onTap,
    );
  }
}

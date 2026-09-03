import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:image_picker/image_picker.dart';
import '../theme/app_theme.dart';
import '../l10n/app_localizations.dart';
import '../main.dart' show localeProvider, themeModeProvider;
import '../models/user.dart';
import '../services/nurse_api.dart';
import '../services/patient_api.dart';
import '../services/object_storage_uploader.dart';
import '../services/backend_upload_uploader.dart';
import '../state/auth_controller.dart';

class ProfileScreen extends ConsumerStatefulWidget {
  const ProfileScreen({super.key});

  @override
  ConsumerState<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends ConsumerState<ProfileScreen> {
  // Swap for a real provider once one is chosen — see
  // lib/services/object_storage_uploader.dart for exactly what to change.
  final ObjectStorageUploader _uploader = BackendUploadUploader();

  File? _localPreview;
  bool _uploading = false;

  Future<void> _pickAndUpload(UserRole role) async {
    final t = AppLocalizations.of(context)!;
    final source = await showModalBottomSheet<ImageSource>(
      context: context,
      builder: (ctx) => SafeArea(
        child: Wrap(children: [
          ListTile(
            leading: const Icon(Icons.photo_camera_outlined),
            title: Text(t.takePhoto),
            onTap: () => Navigator.of(ctx).pop(ImageSource.camera),
          ),
          ListTile(
            leading: const Icon(Icons.photo_library_outlined),
            title: Text(t.chooseFromGallery),
            onTap: () => Navigator.of(ctx).pop(ImageSource.gallery),
          ),
        ]),
      ),
    );
    if (source == null) return;

    final picked = await ImagePicker().pickImage(source: source, maxWidth: 1200, imageQuality: 85);
    if (picked == null || !mounted) return;

    final file = File(picked.path);
    setState(() {
      _localPreview = file; // instant feedback while the real upload runs
      _uploading = true;
    });

    try {
      final url = await _uploader.upload(file);
      if (role == UserRole.nurse) {
        await NurseApi().updateMyPhoto(url);
      } else {
        await PatientApi().updateMyPhoto(url);
      }
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(t.photoUpdated)));
    } on StorageNotConfiguredException {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(t.storageNotConfigured)));
    } catch (_) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(t.somethingWentWrong)));
    } finally {
      if (mounted) setState(() => _uploading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final t = AppLocalizations.of(context)!;
    final locale = ref.watch(localeProvider);
    final auth = ref.watch(authControllerProvider);
    final email = auth.user?.email ?? '';
    final initial = email.isNotEmpty ? email[0].toUpperCase() : '?';
    final role = auth.user?.role;

    return ListView(
      padding: const EdgeInsets.fromLTRB(20, 24, 20, 24),
      children: [
        Center(
          child: Column(children: [
            Stack(
              clipBehavior: Clip.none,
              children: [
                InkWell(
                  borderRadius: BorderRadius.circular(39),
                  onTap: role == null ? null : () => _pickAndUpload(role),
                  child: Container(
                    width: 78, height: 78,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      gradient: const LinearGradient(colors: [AppColors.amber, AppColors.amberDark]),
                      image: _localPreview != null
                          ? DecorationImage(image: FileImage(_localPreview!), fit: BoxFit.cover)
                          : null,
                    ),
                    alignment: Alignment.center,
                    child: _uploading
                        ? const CircularProgressIndicator(color: Colors.white, strokeWidth: 2)
                        : _localPreview == null
                            ? Text(initial, style: const TextStyle(color: Colors.white, fontSize: 26, fontWeight: FontWeight.w800))
                            : null,
                    // TODO(api): once a "my profile" fetch (GET /nurses/me
                    // or /patients/me) is wired in, prefer the server's
                    // photo_url over _localPreview once loaded — this only
                    // shows what was picked *this session*.
                  ),
                ),
                Positioned(
                  bottom: -2, right: -2,
                  child: Container(
                    width: 26, height: 26,
                    decoration: BoxDecoration(
                      color: AppColors.teal700,
                      shape: BoxShape.circle,
                      border: Border.all(color: AppColors.bg, width: 2),
                    ),
                    child: const Icon(Icons.camera_alt_rounded, size: 13, color: Colors.white),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 10),
            Text(email, style: Theme.of(context).textTheme.titleMedium),
            if (role != null)
              Text(
                switch (role) {
                  UserRole.patient => t.iAmPatient,
                  UserRole.nurse => t.iAmNurse,
                  UserRole.admin => 'Admin',
                },
                style: Theme.of(context).textTheme.bodySmall,
              ),
          ]),
        ),
        const SizedBox(height: 24),
        Text(t.language, style: Theme.of(context).textTheme.bodySmall),
        const SizedBox(height: 8),
        SegmentedButton<Locale>(
          segments: const [
            ButtonSegment(value: Locale('ar'), label: Text('العربية')),
            ButtonSegment(value: Locale('en'), label: Text('English')),
          ],
          selected: {locale},
          onSelectionChanged: (s) => ref.read(localeProvider.notifier).state = s.first,
        ),
        const SizedBox(height: 20),
        Text(t.darkMode, style: Theme.of(context).textTheme.bodySmall),
        const SizedBox(height: 8),
        SwitchListTile(
          title: Text(
            ref.watch(themeModeProvider) == ThemeMode.dark ? t.darkMode : t.lightMode,
            style: Theme.of(context).textTheme.bodyMedium,
          ),
          value: ref.watch(themeModeProvider) == ThemeMode.dark,
          onChanged: (dark) => ref.read(themeModeProvider.notifier).state =
              dark ? ThemeMode.dark : ThemeMode.light,
          activeColor: AppColors.teal700,
          contentPadding: EdgeInsets.zero,
        ),
        const SizedBox(height: 24),
        OutlinedButton.icon(
          onPressed: () => ref.read(authControllerProvider.notifier).logout(),
          icon: const Icon(Icons.logout_rounded, size: 18, color: AppColors.danger),
          label: Text(t.logout, style: const TextStyle(color: AppColors.danger, fontWeight: FontWeight.w700)),
          style: OutlinedButton.styleFrom(side: const BorderSide(color: AppColors.danger)),
        ),
      ],
    );
  }
}

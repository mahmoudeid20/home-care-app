import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:google_fonts/google_fonts.dart';

import '../core/app_preferences.dart';
import '../main.dart';
import '../theme/app_theme.dart';

class LanguageToggleButton extends ConsumerWidget {
  final bool isCompact;

  const LanguageToggleButton({super.key, this.isCompact = false});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final currentLocale = ref.watch(localeProvider);
    final isArabic = currentLocale.languageCode == 'ar';
    final targetLangText = isArabic ? 'English' : 'العربية';
    final targetLangCode = isArabic ? 'en' : 'ar';
    final isDark = AppColors.isDark(context);

    return InkWell(
      onTap: () async {
        ref.read(localeProvider.notifier).state = Locale(targetLangCode);
        await AppPreferences.instance.saveLocale(targetLangCode);
      },
      borderRadius: BorderRadius.circular(20),
      child: Container(
        padding: EdgeInsets.symmetric(
          horizontal: isCompact ? 10 : 14,
          vertical: isCompact ? 6 : 8,
        ),
        decoration: BoxDecoration(
          color: isDark ? AppColors.surfaceOf(context) : Colors.white.withOpacity(0.9),
          borderRadius: BorderRadius.circular(20),
          border: Border.all(
            color: isDark ? AppColors.lineOf(context) : AppColors.primary.withOpacity(0.3),
            width: 1.2,
          ),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withOpacity(0.04),
              blurRadius: 6,
              offset: const Offset(0, 2),
            ),
          ],
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              Icons.language_rounded,
              size: isCompact ? 16 : 18,
              color: AppColors.primary,
            ),
            const SizedBox(width: 6),
            Text(
              targetLangText,
              style: GoogleFonts.cairo(
                fontSize: isCompact ? 12 : 13,
                fontWeight: FontWeight.bold,
                color: isDark ? AppColors.inkOf(context) : AppColors.primary,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

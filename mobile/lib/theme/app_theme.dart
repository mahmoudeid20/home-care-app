import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

/// Design tokens for the Sanad home-care app.
/// Premium healthcare palette: Medical Blue, Teal accents, Amber highlights.
class AppColors {
  AppColors._();

  // Primary Medical Blues
  static const primaryDark = Color(0xFF0D47A1); // Deep Navy Blue
  static const primary = Color(0xFF1565C0); // Royal Medical Blue
  static const primaryLight = Color(0xFF1E88E5); // Bright Blue
  static const primarySurface = Color(0xFFEBF3FC); // Very Soft Blue Tint

  // Teal / Mint Accents
  static const accent = Color(0xFF00897B); // Medical Teal
  static const accentLight = Color(0xFFE0F2F1); // Soft Teal Tint
  static const cyan = Color(0xFF0288D1);

  // Backward-compatibility aliases for existing widgets
  static const teal900 = Color(0xFF0D47A1);
  static const teal700 = Color(0xFF1565C0);
  static const teal500 = Color(0xFF1E88E5);
  static const teal100 = Color(0xFFEBF3FC);

  // Warm Amber / Ratings
  static const amber = Color(0xFFFFA000);
  static const amberDark = Color(0xFFF57C00);

  // Neutrals
  static const bg = Color(0xFFF8FAFC); // Clean Modern Slate Background
  static const surface = Color(0xFFFFFFFF);
  static const cardBg = Color(0xFFFFFFFF);
  static const ink = Color(0xFF0F172A); // Dark Slate
  static const inkSoft = Color(0xFF64748B); // Slate Muted
  static const line = Color(0xFFE2E8F0); // Very Subtle Border
  static const lineDark = Color(0xFFCBD5E1);

  // Status
  static const success = Color(0xFF10B981);
  static const successLight = Color(0xFFD1FAE5);
  static const danger = Color(0xFFEF4444);
  static const dangerLight = Color(0xFFFEE2E2);
  static const warning = Color(0xFFF59E0B);
  static const warningLight = Color(0xFFFEF3C7);
}

class AppRadius {
  AppRadius._();
  static const sm = 10.0;
  static const md = 16.0;
  static const lg = 24.0;
  static const xl = 32.0;
}

class AppTheme {
  AppTheme._();

  /// [locale] selects the correct display typeface per script:
  /// Cairo for Arabic, Manrope/Inter for Latin scripts.
  static ThemeData light(Locale locale) {
    final isArabic = locale.languageCode == 'ar';
    final displayFont = isArabic ? GoogleFonts.cairo : GoogleFonts.manrope;
    final bodyFont = isArabic ? GoogleFonts.cairo : GoogleFonts.inter;

    final base = ThemeData(
      useMaterial3: true,
      scaffoldBackgroundColor: AppColors.bg,
      colorScheme: ColorScheme.fromSeed(
        seedColor: AppColors.primary,
        primary: AppColors.primary,
        secondary: AppColors.accent,
        surface: AppColors.surface,
        error: AppColors.danger,
        brightness: Brightness.light,
      ),
      textTheme: GoogleFonts.cairoTextTheme().copyWith(
        headlineMedium: displayFont(fontWeight: FontWeight.w800, fontSize: 24, color: AppColors.ink),
        headlineSmall: displayFont(fontWeight: FontWeight.w800, fontSize: 20, color: AppColors.primaryDark),
        titleLarge: displayFont(fontWeight: FontWeight.w700, fontSize: 18, color: AppColors.ink),
        titleMedium: displayFont(fontWeight: FontWeight.w700, fontSize: 15, color: AppColors.ink),
        titleSmall: displayFont(fontWeight: FontWeight.w600, fontSize: 14, color: AppColors.inkSoft),
        bodyLarge: bodyFont(fontSize: 15, color: AppColors.ink, height: 1.5),
        bodyMedium: bodyFont(fontSize: 13.5, color: AppColors.ink, height: 1.4),
        bodySmall: bodyFont(fontSize: 12, color: AppColors.inkSoft),
        labelLarge: displayFont(fontWeight: FontWeight.w700, fontSize: 14, color: Colors.white),
      ),
    );

    return base.copyWith(
      appBarTheme: AppBarTheme(
        backgroundColor: AppColors.surface,
        elevation: 0,
        scrolledUnderElevation: 1,
        centerTitle: true,
        foregroundColor: AppColors.primaryDark,
        titleTextStyle: displayFont(fontWeight: FontWeight.w800, fontSize: 18, color: AppColors.primaryDark),
        iconTheme: const IconThemeData(color: AppColors.primaryDark),
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: AppColors.primary,
          foregroundColor: Colors.white,
          elevation: 2,
          shadowColor: AppColors.primary.withOpacity(0.3),
          padding: const EdgeInsets.symmetric(vertical: 15, horizontal: 24),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(AppRadius.md)),
          textStyle: displayFont(fontWeight: FontWeight.w700, fontSize: 15),
        ),
      ),
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          foregroundColor: AppColors.primary,
          side: const BorderSide(color: AppColors.primary, width: 1.5),
          padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 20),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(AppRadius.md)),
          textStyle: displayFont(fontWeight: FontWeight.w700, fontSize: 14),
        ),
      ),
      cardTheme: CardThemeData(
        color: AppColors.surface,
        elevation: 1.5,
        shadowColor: Colors.black.withOpacity(0.04),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(AppRadius.md),
          side: const BorderSide(color: AppColors.line, width: 1),
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: Colors.white,
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 15),
        hintStyle: TextStyle(color: AppColors.inkSoft.withOpacity(0.7), fontSize: 13.5),
        labelStyle: const TextStyle(color: AppColors.inkSoft, fontSize: 14),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(AppRadius.md),
          borderSide: const BorderSide(color: AppColors.line),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(AppRadius.md),
          borderSide: const BorderSide(color: AppColors.line),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(AppRadius.md),
          borderSide: const BorderSide(color: AppColors.primary, width: 1.8),
        ),
        errorBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(AppRadius.md),
          borderSide: const BorderSide(color: AppColors.danger, width: 1.2),
        ),
      ),
      bottomNavigationBarTheme: const BottomNavigationBarThemeData(
        backgroundColor: AppColors.surface,
        selectedItemColor: AppColors.primary,
        unselectedItemColor: AppColors.inkSoft,
        type: BottomNavigationBarType.fixed,
        elevation: 8,
        selectedLabelStyle: TextStyle(fontWeight: FontWeight.bold, fontSize: 12),
        unselectedLabelStyle: TextStyle(fontSize: 11),
        showUnselectedLabels: true,
      ),
    );
  }

  /// Dark theme — refined slate dark mode.
  static ThemeData dark(Locale locale) {
    final isArabic = locale.languageCode == 'ar';
    final displayFont = isArabic ? GoogleFonts.cairo : GoogleFonts.manrope;
    final bodyFont = isArabic ? GoogleFonts.cairo : GoogleFonts.inter;

    const darkBg = Color(0xFF0F172A);
    const darkSurface = Color(0xFF1E293B);
    const darkLine = Color(0xFF334155);
    const darkInk = Color(0xFFF1F5F9);
    const darkInkSoft = Color(0xFF94A3B8);

    final base = ThemeData(
      useMaterial3: true,
      brightness: Brightness.dark,
      scaffoldBackgroundColor: darkBg,
      colorScheme: ColorScheme.fromSeed(
        seedColor: AppColors.primaryLight,
        brightness: Brightness.dark,
        primary: AppColors.primaryLight,
        secondary: AppColors.accent,
        surface: darkSurface,
        error: AppColors.danger,
      ),
      textTheme: GoogleFonts.cairoTextTheme(ThemeData.dark().textTheme).copyWith(
        headlineMedium: displayFont(fontWeight: FontWeight.w800, fontSize: 24, color: darkInk),
        headlineSmall: displayFont(fontWeight: FontWeight.w800, fontSize: 20, color: darkInk),
        titleLarge: displayFont(fontWeight: FontWeight.w700, fontSize: 18, color: darkInk),
        titleMedium: displayFont(fontWeight: FontWeight.w700, fontSize: 15, color: darkInk),
        titleSmall: displayFont(fontWeight: FontWeight.w600, fontSize: 14, color: darkInkSoft),
        bodyLarge: bodyFont(fontSize: 15, color: darkInk, height: 1.5),
        bodyMedium: bodyFont(fontSize: 13.5, color: darkInk, height: 1.4),
        bodySmall: bodyFont(fontSize: 12, color: darkInkSoft),
      ),
    );

    return base.copyWith(
      appBarTheme: AppBarTheme(
        backgroundColor: darkSurface,
        elevation: 0,
        foregroundColor: darkInk,
        titleTextStyle: displayFont(fontWeight: FontWeight.w800, fontSize: 18, color: darkInk),
        iconTheme: const IconThemeData(color: darkInk),
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: AppColors.primaryLight,
          foregroundColor: Colors.white,
          padding: const EdgeInsets.symmetric(vertical: 15, horizontal: 24),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(AppRadius.md)),
          textStyle: displayFont(fontWeight: FontWeight.w700, fontSize: 15),
        ),
      ),
      cardTheme: CardThemeData(
        color: darkSurface,
        elevation: 1,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(AppRadius.md),
          side: const BorderSide(color: darkLine),
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: const Color(0xFF1E293B),
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 15),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(AppRadius.md),
          borderSide: const BorderSide(color: darkLine),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(AppRadius.md),
          borderSide: const BorderSide(color: AppColors.primaryLight, width: 1.8),
        ),
      ),
      bottomNavigationBarTheme: const BottomNavigationBarThemeData(
        backgroundColor: darkSurface,
        selectedItemColor: AppColors.primaryLight,
        unselectedItemColor: darkInkSoft,
        type: BottomNavigationBarType.fixed,
        elevation: 8,
        showUnselectedLabels: true,
      ),
    );
  }
}

import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'l10n/app_localizations.dart';
import 'theme/app_theme.dart';
import 'screens/root_shell.dart';
import 'screens/splash_screen.dart';
import 'screens/auth/login_screen.dart';
import 'screens/onboarding_screen.dart';
import 'screens/profile_setup_wizard.dart';
import 'state/auth_controller.dart';

import 'core/app_preferences.dart';

/// Holds the current locale; toggled from the Settings or Registration screens.
/// Defaults to Arabic — the app's primary market.
final localeProvider = StateProvider<Locale>((ref) => const Locale('ar'));

/// Controls light/dark/system theme. Toggled from the Settings screen.
final themeModeProvider = StateProvider<ThemeMode>((ref) => ThemeMode.light);

/// Cached onboarding state for instant first-frame transition
final hasSeenOnboardingProvider = StateProvider<bool>((ref) => false);

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Global error handler — catch uncaught Flutter framework errors
  FlutterError.onError = (details) {
    FlutterError.presentError(details);
  };

  // Run all storage reads in parallel for instant cold-start launch
  final results = await Future.wait([
    AppPreferences.instance.savedLocale,
    AppPreferences.instance.savedThemeMode,
    OnboardingScreen.hasSeenOnboarding(),
  ]);

  final savedLang = results[0] as String?;
  final savedTheme = results[1] as ThemeMode?;
  final hasSeen = (results[2] as bool?) ?? false;

  final initialLocale = (savedLang == 'en') ? const Locale('en') : const Locale('ar');
  final initialTheme = savedTheme ?? ThemeMode.light;

  runApp(
    ProviderScope(
      overrides: [
        localeProvider.overrideWith((ref) => initialLocale),
        themeModeProvider.overrideWith((ref) => initialTheme),
        hasSeenOnboardingProvider.overrideWith((ref) => hasSeen),
      ],
      child: const SanadApp(),
    ),
  );
}

class SanadApp extends ConsumerWidget {
  const SanadApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final locale = ref.watch(localeProvider);

    return MaterialApp(
      title: 'Home Care',
      debugShowCheckedModeBanner: false,
      locale: locale,
      supportedLocales: const [Locale('ar'), Locale('en')],
      localizationsDelegates: const [
        AppLocalizations.delegate,
        GlobalMaterialLocalizations.delegate,
        GlobalWidgetsLocalizations.delegate,
        GlobalCupertinoLocalizations.delegate,
      ],
      theme: AppTheme.light(locale),
      darkTheme: AppTheme.dark(locale),
      themeMode: ref.watch(themeModeProvider),
      home: const _AuthGate(),
    );
  }
}

/// Root-level reactive switch driven by AuthController's state:
/// - bootstrapping -> SplashScreen
/// - unauthenticated -> Onboarding (first time) or LoginScreen
/// - needsProfileSetup -> ProfileSetupWizard
/// - authenticated -> RootShell
class _AuthGate extends ConsumerWidget {
  const _AuthGate();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final auth = ref.watch(authControllerProvider);
    return switch (auth.status) {
      AuthStatus.bootstrapping => const SplashScreen(),
      AuthStatus.unauthenticated => const _UnauthenticatedGate(),
      AuthStatus.needsProfileSetup => const ProfileSetupWizard(),
      AuthStatus.authenticated => const RootShell(),
    };
  }
}

class _UnauthenticatedGate extends ConsumerWidget {
  const _UnauthenticatedGate();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final hasSeen = ref.watch(hasSeenOnboardingProvider);
    return hasSeen ? const LoginScreen() : const OnboardingScreen();
  }
}

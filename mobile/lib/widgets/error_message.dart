import 'package:flutter/material.dart';
import '../core/api_exception.dart';
import '../l10n/app_localizations.dart';
import '../theme/app_theme.dart';

/// Translates an ApiException's machine code into a message the person can
/// actually act on. Backend validation messages (e.g. "Password must
/// contain at least one digit") are already human-readable English from
/// FastAPI/Pydantic, so those pass through as-is; only our own network-level
/// codes get a localized string, since those never come with English text
/// from the server (there's no response body to read a message from).
String friendlyErrorMessage(ApiException e, AppLocalizations t) {
  return switch (e.code) {
    'NETWORK_ERROR' => switch (e.message) {
        'connection_timeout' => t.connectionTimeout,
        'connection_error' => t.connectionError,
        _ => t.connectionError,
      },
    'VALIDATION_ERROR' => e.message,
    _ => e.message.isNotEmpty ? e.message : t.somethingWentWrong,
  };
}

class ErrorMessage extends StatelessWidget {
  final String message;
  const ErrorMessage({super.key, required this.message});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 11),
      decoration: BoxDecoration(
        color: const Color(0xFFFDEDED),
        borderRadius: BorderRadius.circular(AppRadius.sm),
        border: Border.all(color: AppColors.danger.withOpacity(0.25)),
      ),
      child: Row(
        children: [
          const Icon(Icons.error_outline_rounded, size: 18, color: AppColors.danger),
          const SizedBox(width: 8),
          Expanded(
            child: Text(message, style: const TextStyle(color: AppColors.danger, fontSize: 12.5, fontWeight: FontWeight.w600)),
          ),
        ],
      ),
    );
  }
}

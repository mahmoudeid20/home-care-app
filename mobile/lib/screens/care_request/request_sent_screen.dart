import 'package:flutter/material.dart';
import '../../l10n/app_localizations.dart';
import '../../theme/app_theme.dart';
import '../root_shell.dart';

class RequestSentScreen extends StatelessWidget {
  final String? nurseName;
  const RequestSentScreen({super.key, this.nurseName});

  @override
  Widget build(BuildContext context) {
    final t = AppLocalizations.of(context)!;
    return Scaffold(
      body: SafeArea(
        child: Center(
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 32),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Container(
                  width: 76,
                  height: 76,
                  decoration: const BoxDecoration(shape: BoxShape.circle, color: Color(0xFFE9F8EF)),
                  child: const Icon(Icons.check_rounded, color: AppColors.success, size: 38),
                ),
                const SizedBox(height: 20),
                Text(t.requestSentTitle,
                    textAlign: TextAlign.center, style: Theme.of(context).textTheme.headlineSmall),
                const SizedBox(height: 8),
                Text(t.requestSentBody, textAlign: TextAlign.center, style: Theme.of(context).textTheme.bodyMedium),
                const SizedBox(height: 28),
                ElevatedButton(
                  onPressed: () => Navigator.of(context).pushAndRemoveUntil(
                    MaterialPageRoute(builder: (_) => const RootShell()),
                    (route) => false,
                  ),
                  child: Text(t.backToHome),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

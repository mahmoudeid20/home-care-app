import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/api_exception.dart';
import '../../l10n/app_localizations.dart';
import '../../models/application.dart';
import '../../models/enums.dart';
import '../../services/application_api.dart';
import '../../state/nurse_providers.dart';
import '../../theme/app_theme.dart';
import '../../widgets/error_message.dart';

final sentApplicationsProvider = FutureProvider.autoDispose((ref) => ApplicationApi().listSent());

class SentRequestsScreen extends ConsumerWidget {
  const SentRequestsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final t = AppLocalizations.of(context)!;
    final async = ref.watch(sentApplicationsProvider);

    return Scaffold(
      appBar: AppBar(title: Text(t.mySentRequests)),
      body: RefreshIndicator(
        onRefresh: () async => ref.invalidate(sentApplicationsProvider),
        child: async.when(
          loading: () => const Center(child: CircularProgressIndicator()),
          error: (err, _) => Center(
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 24),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  ErrorMessage(message: err is ApiException ? friendlyErrorMessage(err, t) : t.somethingWentWrong),
                  const SizedBox(height: 12),
                  OutlinedButton(onPressed: () => ref.invalidate(sentApplicationsProvider), child: Text(t.retry)),
                ],
              ),
            ),
          ),
          data: (applications) {
            if (applications.isEmpty) {
              return ListView(children: [
                const SizedBox(height: 80),
                Center(child: Text(t.noSentRequestsYet, style: Theme.of(context).textTheme.bodySmall)),
              ]);
            }
            return ListView.separated(
              padding: const EdgeInsets.all(20),
              itemCount: applications.length,
              separatorBuilder: (_, __) => const SizedBox(height: 10),
              itemBuilder: (_, i) => _SentRequestCard(application: applications[i]),
            );
          },
        ),
      ),
    );
  }
}

class _SentRequestCard extends ConsumerStatefulWidget {
  final ApplicationInfo application;
  const _SentRequestCard({required this.application});

  @override
  ConsumerState<_SentRequestCard> createState() => _SentRequestCardState();
}

class _SentRequestCardState extends ConsumerState<_SentRequestCard> {
  bool _withdrawing = false;

  (Color, Color) _pillColors(ApplicationStatus s) => switch (s) {
        ApplicationStatus.pending => (const Color(0xFFFFF4E0), AppColors.amberDark),
        ApplicationStatus.accepted => (const Color(0xFFE9F8EF), AppColors.success),
        ApplicationStatus.rejected || ApplicationStatus.withdrawn => (AppColors.line, AppColors.inkSoft),
      };

  String _label(AppLocalizations t, ApplicationStatus s) => switch (s) {
        ApplicationStatus.pending => t.appPending,
        ApplicationStatus.accepted => t.appAccepted,
        ApplicationStatus.rejected => t.appRejected,
        ApplicationStatus.withdrawn => t.appWithdrawn,
      };

  Future<void> _withdraw() async {
    final t = AppLocalizations.of(context)!;
    setState(() => _withdrawing = true);
    try {
      await ApplicationApi().withdraw(widget.application.id);
      if (!mounted) return;
      ref.invalidate(sentApplicationsProvider);
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(t.requestWithdrawn)));
    } on ApiException catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(friendlyErrorMessage(e, t))));
    } finally {
      if (mounted) setState(() => _withdrawing = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final t = AppLocalizations.of(context)!;
    final (bg, fg) = _pillColors(widget.application.status);
    final nurseAsync = ref.watch(nurseDetailProvider(widget.application.nurseId));

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 3),
                  decoration: BoxDecoration(color: bg, borderRadius: BorderRadius.circular(7)),
                  child: Text(_label(t, widget.application.status),
                      style: TextStyle(fontSize: 10, fontWeight: FontWeight.w800, color: fg)),
                ),
                if (widget.application.status == ApplicationStatus.pending)
                  TextButton(
                    onPressed: _withdrawing ? null : _withdraw,
                    child: _withdrawing
                        ? const SizedBox(width: 14, height: 14, child: CircularProgressIndicator(strokeWidth: 2))
                        : Text(t.withdrawRequest, style: const TextStyle(color: AppColors.danger, fontSize: 11.5)),
                  ),
              ],
            ),
            const SizedBox(height: 6),
            nurseAsync.when(
              loading: () => const SizedBox(height: 16, width: 100, child: LinearProgressIndicator()),
              error: (_, __) => Text('#${widget.application.nurseId.substring(0, 8)}',
                  style: Theme.of(context).textTheme.titleMedium),
              data: (nurse) => Text(nurse.fullName, style: Theme.of(context).textTheme.titleMedium),
            ),
          ],
        ),
      ),
    );
  }
}

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/api_exception.dart';
import '../../l10n/app_localizations.dart';
import '../../models/application.dart';
import '../../models/enums.dart';
import '../../services/application_api.dart';
import '../../theme/app_theme.dart';
import '../../widgets/error_message.dart';
import 'application_detail_screen.dart';

final receivedApplicationsProvider = FutureProvider.autoDispose((ref) => ApplicationApi().listReceived());

class ReceivedRequestsScreen extends ConsumerWidget {
  const ReceivedRequestsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final t = AppLocalizations.of(context)!;
    final async = ref.watch(receivedApplicationsProvider);

    return RefreshIndicator(
      onRefresh: () async => ref.invalidate(receivedApplicationsProvider),
      child: CustomScrollView(slivers: [
        SliverToBoxAdapter(
          child: Padding(
            padding: const EdgeInsets.fromLTRB(20, 16, 20, 4),
            child: Text(t.newRequests, style: Theme.of(context).textTheme.headlineSmall),
          ),
        ),
        async.when(
          loading: () => const SliverFillRemaining(
            hasScrollBody: false,
            child: Center(child: CircularProgressIndicator()),
          ),
          error: (err, _) => SliverFillRemaining(
            hasScrollBody: false,
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 20),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  ErrorMessage(message: err is ApiException ? friendlyErrorMessage(err, t) : t.somethingWentWrong),
                  const SizedBox(height: 12),
                  OutlinedButton(onPressed: () => ref.invalidate(receivedApplicationsProvider), child: Text(t.retry)),
                ],
              ),
            ),
          ),
          data: (applications) {
            if (applications.isEmpty) {
              return SliverFillRemaining(
                hasScrollBody: false,
                child: Center(child: Text(t.noRequestsYet, style: Theme.of(context).textTheme.bodySmall)),
              );
            }
            return SliverPadding(
              padding: const EdgeInsets.all(20),
              sliver: SliverList.separated(
                itemCount: applications.length,
                separatorBuilder: (_, __) => const SizedBox(height: 10),
                itemBuilder: (_, i) => _ApplicationCard(application: applications[i]),
              ),
            );
          },
        ),
      ]),
    );
  }
}

class _ApplicationCard extends StatelessWidget {
  final ApplicationInfo application;
  const _ApplicationCard({required this.application});

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

  @override
  Widget build(BuildContext context) {
    final t = AppLocalizations.of(context)!;
    final (bg, fg) = _pillColors(application.status);

    return Card(
      child: InkWell(
        borderRadius: BorderRadius.circular(AppRadius.md),
        onTap: () => Navigator.of(context).push(
          MaterialPageRoute(builder: (_) => ApplicationDetailScreen(application: application)),
        ),
        child: Padding(
          padding: const EdgeInsets.all(14),
          child: Row(
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 3),
                      decoration: BoxDecoration(color: bg, borderRadius: BorderRadius.circular(7)),
                      child: Text(_label(t, application.status),
                          style: TextStyle(fontSize: 10, fontWeight: FontWeight.w800, color: fg)),
                    ),
                    const SizedBox(height: 8),
                    if (application.message != null && application.message!.isNotEmpty)
                      Text(application.message!,
                          maxLines: 2, overflow: TextOverflow.ellipsis, style: Theme.of(context).textTheme.bodySmall),
                  ],
                ),
              ),
              const Icon(Icons.chevron_right_rounded, color: AppColors.inkSoft),
            ],
          ),
        ),
      ),
    );
  }
}

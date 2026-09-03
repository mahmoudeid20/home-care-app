import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../core/api_exception.dart';
import '../l10n/app_localizations.dart';
import '../models/nurse_detail.dart';
import '../theme/app_theme.dart';
import '../widgets/error_message.dart';
import '../widgets/nurse_card.dart';
import '../widgets/nurse_summary.dart';
import 'care_request/care_request_form_screen.dart';
import '../state/nurse_providers.dart';
import '../services/chat_api.dart';
import '../services/review_api.dart';
import '../models/review.dart';
import 'chat_thread_screen.dart';

final _nurseReviewsProvider =
    FutureProvider.autoDispose.family<List<ReviewInfo>, String>((ref, nurseId) => ReviewApi().listForNurse(nurseId));

class NurseDetailScreen extends ConsumerWidget {
  final String nurseId;
  const NurseDetailScreen({super.key, required this.nurseId});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final t = AppLocalizations.of(context)!;
    final async = ref.watch(nurseDetailProvider(nurseId));

    return Scaffold(
      appBar: AppBar(),
      body: async.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (err, _) => Center(
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 24),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                ErrorMessage(message: err is ApiException ? friendlyErrorMessage(err, t) : t.somethingWentWrong),
                const SizedBox(height: 12),
                OutlinedButton(
                  onPressed: () => ref.invalidate(nurseDetailProvider(nurseId)),
                  child: Text(t.retry),
                ),
              ],
            ),
          ),
        ),
        data: (nurse) => _NurseDetailBody(nurse: nurse),
      ),
    );
  }
}

class _NurseDetailBody extends StatelessWidget {
  final NurseDetail nurse;
  const _NurseDetailBody({required this.nurse});

  @override
  Widget build(BuildContext context) {
    final t = AppLocalizations.of(context)!;
    final locale = Localizations.localeOf(context).languageCode;
    final asSummary = NurseSummary(
      id: nurse.id,
      fullName: nurse.fullName,
      professionalTitle: nurse.professionalTitle,
      experienceYears: nurse.experienceYears,
      averageRating: nurse.averageRating,
      reviewCount: nurse.reviewCount,
      isVerified: nurse.isFullyVerified,
      photoUrl: nurse.photoUrl,
    );

    return Stack(
      children: [
        ListView(
          padding: const EdgeInsets.fromLTRB(20, 8, 20, 100),
          children: [
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                NurseAvatar(nurse: asSummary, size: 68),
                const SizedBox(width: 14),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(nurse.fullName, style: Theme.of(context).textTheme.headlineSmall),
                      if (nurse.professionalTitle != null)
                        Text(nurse.professionalTitle!, style: Theme.of(context).textTheme.bodySmall),
                      const SizedBox(height: 6),
                      Row(
                        children: [
                          const Icon(Icons.star_rounded, size: 15, color: AppColors.amber),
                          const SizedBox(width: 3),
                          Flexible(
                            child: Text('${nurse.averageRating.toStringAsFixed(1)} (${nurse.reviewCount})',
                                style: Theme.of(context).textTheme.bodySmall, overflow: TextOverflow.ellipsis),
                          ),
                          const SizedBox(width: 10),
                          Flexible(
                            child: Text('${nurse.experienceYears} ${t.yearsExperience}',
                                style: Theme.of(context).textTheme.bodySmall, overflow: TextOverflow.ellipsis),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
              ],
            ),
            const SizedBox(height: 18),
            Row(
              children: [
                Expanded(
                  child: _StatCard(
                    label: t.verified,
                    value: nurse.isFullyVerified ? '✓' : '—',
                    positive: nurse.isFullyVerified,
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: _StatCard(label: t.yearsExperience, value: '${nurse.experienceYears}'),
                ),
              ],
            ),
            if (nurse.bio != null && nurse.bio!.isNotEmpty) ...[
              const SizedBox(height: 22),
              Text(t.about, style: Theme.of(context).textTheme.titleMedium),
              const SizedBox(height: 8),
              Text(nurse.bio!, style: Theme.of(context).textTheme.bodyMedium?.copyWith(height: 1.6)),
            ],
            if (nurse.services.isNotEmpty) ...[
              const SizedBox(height: 22),
              Text(t.servicesAndPrices, style: Theme.of(context).textTheme.titleMedium),
              const SizedBox(height: 8),
              ...nurse.services.map((s) => Card(
                    margin: const EdgeInsets.only(bottom: 8),
                    child: ListTile(
                      dense: true,
                      title: Text(s.service.nameFor(locale)),
                      trailing: Text(
                        '${s.price.toStringAsFixed(0)} ${t.egp} · ${_unitLabel(t, s.priceUnit.name)}',
                        style: const TextStyle(fontWeight: FontWeight.w800, color: AppColors.teal700),
                      ),
                    ),
                  )),
            ],
            if (nurse.specialties.isNotEmpty) ...[
              const SizedBox(height: 10),
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: nurse.specialties
                    .map((s) => Chip(
                          label: Text(s.nameFor(locale), style: const TextStyle(fontSize: 11.5)),
                          backgroundColor: AppColors.teal100,
                          side: BorderSide.none,
                        ))
                    .toList(),
              ),
            ],
            const SizedBox(height: 22),
            Text(t.reviews, style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 8),
            _ReviewsSection(nurseId: nurse.id),
          ],
        ),
        Positioned(
          left: 0, right: 0, bottom: 0,
          child: Container(
            padding: const EdgeInsets.fromLTRB(20, 14, 20, 22),
            decoration: BoxDecoration(
              color: AppColors.bg,
              boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.06), blurRadius: 16, offset: const Offset(0, -4))],
            ),
            child: Row(
              children: [
                Expanded(
                  flex: 2,
                  child: ElevatedButton(
                    onPressed: () => Navigator.of(context).push(
                      MaterialPageRoute(builder: (_) => CareRequestFormScreen(targetNurse: nurse)),
                    ),
                    child: Text(t.sendRequest),
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: _MessageButton(nurseId: nurse.id, nurseName: nurse.fullName),
                ),
              ],
            ),
          ),
        ),
      ],
    );
  }

  String _unitLabel(AppLocalizations t, String unitName) => switch (unitName) {
        'hourly' => t.hourly,
        'daily' => t.daily,
        'weekly' => t.weekly,
        'monthly' => t.monthly,
        _ => unitName,
      };
}

class _StatCard extends StatelessWidget {
  final String label;
  final String value;
  final bool positive;
  const _StatCard({required this.label, required this.value, this.positive = true});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(vertical: 12),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(AppRadius.md),
        border: Border.all(color: AppColors.line),
      ),
      alignment: Alignment.center,
      child: Column(
        children: [
          Text(value,
              style: TextStyle(
                  fontWeight: FontWeight.w800,
                  fontSize: 16,
                  color: positive ? AppColors.success : AppColors.inkSoft)),
          const SizedBox(height: 2),
          Text(label, style: Theme.of(context).textTheme.bodySmall),
        ],
      ),
    );
  }
}

/// Starts (or resumes — the backend is idempotent per patient+nurse pair)
/// a conversation, then navigates straight into the thread. PATIENT role
/// only server-side; a NURSE viewing another nurse's profile never happens
/// in this app's navigation, so no client-side role check is duplicated here.
class _MessageButton extends ConsumerStatefulWidget {
  final String nurseId;
  final String nurseName;
  const _MessageButton({required this.nurseId, required this.nurseName});

  @override
  ConsumerState<_MessageButton> createState() => _MessageButtonState();
}

class _MessageButtonState extends ConsumerState<_MessageButton> {
  bool _loading = false;

  Future<void> _start() async {
    setState(() => _loading = true);
    try {
      final conversation = await ChatApi().startConversation(nurseId: widget.nurseId);
      if (!mounted) return;
      Navigator.of(context).push(
        MaterialPageRoute(builder: (_) => ChatThreadScreen(conversation: conversation)),
      );
    } on ApiException catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.message)));
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return OutlinedButton(
      onPressed: _loading ? null : _start,
      style: OutlinedButton.styleFrom(
        padding: const EdgeInsets.symmetric(vertical: 14),
        side: const BorderSide(color: AppColors.teal700),
      ),
      child: _loading
          ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2))
          : const Icon(Icons.chat_bubble_outline_rounded, size: 18, color: AppColors.teal700),
    );
  }
}

/// GET /nurses/{id}/reviews, shown as the "Reviews" section on a nurse's
/// profile (Section 16). Kept as its own small ConsumerWidget rather than
/// converting _NurseDetailBody itself to a ConsumerWidget, since nothing
/// else on that screen needs Riverpod.
class _ReviewsSection extends ConsumerWidget {
  final String nurseId;
  const _ReviewsSection({required this.nurseId});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final t = AppLocalizations.of(context)!;
    final async = ref.watch(_nurseReviewsProvider(nurseId));

    return async.when(
      loading: () => const Padding(
        padding: EdgeInsets.symmetric(vertical: 8),
        child: LinearProgressIndicator(),
      ),
      error: (err, _) => ErrorMessage(
        message: err is ApiException ? friendlyErrorMessage(err, t) : t.somethingWentWrong,
      ),
      data: (reviews) {
        if (reviews.isEmpty) {
          return Text(t.noReviewsYet, style: Theme.of(context).textTheme.bodySmall);
        }
        return Column(
          children: reviews.map((r) => _ReviewCard(review: r)).toList(),
        );
      },
    );
  }
}

class _ReviewCard extends StatelessWidget {
  final ReviewInfo review;
  const _ReviewCard({required this.review});

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: List.generate(
                5,
                (i) => Icon(
                  i < review.overallRating ? Icons.star_rounded : Icons.star_border_rounded,
                  size: 14,
                  color: AppColors.amber,
                ),
              ),
            ),
            if (review.comment != null && review.comment!.isNotEmpty) ...[
              const SizedBox(height: 6),
              Text(review.comment!, style: Theme.of(context).textTheme.bodySmall),
            ],
          ],
        ),
      ),
    );
  }
}

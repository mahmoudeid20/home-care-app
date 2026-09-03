import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/api_exception.dart';
import '../../l10n/app_localizations.dart';
import '../../models/application.dart';
import '../../models/enums.dart';
import '../../services/application_api.dart';
import '../../services/care_request_api.dart';
import '../../theme/app_theme.dart';
import '../../widgets/error_message.dart';
import 'received_requests_screen.dart';

final _careRequestDetailProvider =
    FutureProvider.autoDispose.family((ref, String careRequestId) => CareRequestApi().getById(careRequestId));

class ApplicationDetailScreen extends ConsumerStatefulWidget {
  final ApplicationInfo application;
  const ApplicationDetailScreen({super.key, required this.application});

  @override
  ConsumerState<ApplicationDetailScreen> createState() => _ApplicationDetailScreenState();
}

class _ApplicationDetailScreenState extends ConsumerState<ApplicationDetailScreen> {
  bool _acting = false;

  Future<void> _accept() async {
    final t = AppLocalizations.of(context)!;
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        content: Text(t.acceptRequestConfirm),
        actions: [
          TextButton(onPressed: () => Navigator.of(ctx).pop(false), child: Text(t.back)),
          FilledButton(onPressed: () => Navigator.of(ctx).pop(true), child: Text(t.accept)),
        ],
      ),
    );
    if (confirmed != true) return;

    setState(() => _acting = true);
    try {
      await ApplicationApi().accept(widget.application.id);
      if (!mounted) return;
      ref.invalidate(receivedApplicationsProvider);
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(t.requestAccepted)));
      Navigator.of(context).pop();
    } on ApiException catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(friendlyErrorMessage(e, t))));
    } finally {
      if (mounted) setState(() => _acting = false);
    }
  }

  Future<void> _reject() async {
    final t = AppLocalizations.of(context)!;
    final reasonCtrl = TextEditingController();
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        content: TextField(
          controller: reasonCtrl,
          decoration: InputDecoration(labelText: t.rejectReasonHint),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.of(ctx).pop(false), child: Text(t.back)),
          FilledButton(
            style: FilledButton.styleFrom(backgroundColor: AppColors.danger),
            onPressed: () => Navigator.of(ctx).pop(true),
            child: Text(t.reject),
          ),
        ],
      ),
    );
    if (confirmed != true) return;

    setState(() => _acting = true);
    try {
      await ApplicationApi().reject(widget.application.id, reason: reasonCtrl.text.trim());
      if (!mounted) return;
      ref.invalidate(receivedApplicationsProvider);
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(t.requestRejected)));
      Navigator.of(context).pop();
    } on ApiException catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(friendlyErrorMessage(e, t))));
    } finally {
      if (mounted) setState(() => _acting = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final t = AppLocalizations.of(context)!;
    final async = ref.watch(_careRequestDetailProvider(widget.application.careRequestId));
    final isPending = widget.application.status == ApplicationStatus.pending;

    return Scaffold(
      appBar: AppBar(),
      body: async.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (err, _) => Center(
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 24),
            child: ErrorMessage(message: err is ApiException ? friendlyErrorMessage(err, t) : t.somethingWentWrong),
          ),
        ),
        data: (cr) => Stack(
          children: [
            ListView(
              padding: EdgeInsets.fromLTRB(20, 8, 20, isPending ? 100 : 24),
              children: [
                Text(cr.patientName, style: Theme.of(context).textTheme.headlineSmall),
                const SizedBox(height: 4),
                Text('${cr.patientAge} · ${cr.patientGender == Gender.female ? t.female : t.male}',
                    style: Theme.of(context).textTheme.bodySmall),
                const SizedBox(height: 18),
                _Field(label: t.medicalConditionLabel, value: cr.medicalCondition),
                if (cr.specialRequirements != null && cr.specialRequirements!.isNotEmpty)
                  _Field(label: t.specialRequirementsLabel, value: cr.specialRequirements!),
                if (cr.location != null)
                  _Field(label: t.locationSection, value: '${cr.location!.governorate}, ${cr.location!.city}'),
                _Field(
                  label: t.startDateLabel,
                  value: '${cr.startDate.year}-${cr.startDate.month.toString().padLeft(2, '0')}-${cr.startDate.day.toString().padLeft(2, '0')}',
                ),
                if (cr.budgetMin != null || cr.budgetMax != null)
                  _Field(
                    label: t.budgetLabel,
                    value: '${cr.budgetMin?.toStringAsFixed(0) ?? '?'} – ${cr.budgetMax?.toStringAsFixed(0) ?? '?'}',
                  ),
                if (widget.application.message != null && widget.application.message!.isNotEmpty)
                  _Field(label: t.messageHint, value: widget.application.message!),
              ],
            ),
            if (isPending)
              Positioned(
                left: 0, right: 0, bottom: 0,
                child: Container(
                  padding: const EdgeInsets.fromLTRB(20, 14, 20, 22),
                  decoration: BoxDecoration(
                    color: AppColors.bg,
                    boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.06), blurRadius: 16, offset: const Offset(0, -4))],
                  ),
                  child: Row(children: [
                    Expanded(
                      child: OutlinedButton(
                        onPressed: _acting ? null : _reject,
                        style: OutlinedButton.styleFrom(side: const BorderSide(color: AppColors.danger)),
                        child: Text(t.reject, style: const TextStyle(color: AppColors.danger)),
                      ),
                    ),
                    const SizedBox(width: 10),
                    Expanded(
                      child: ElevatedButton(
                        onPressed: _acting ? null : _accept,
                        child: _acting
                            ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                            : Text(t.accept),
                      ),
                    ),
                  ]),
                ),
              ),
          ],
        ),
      ),
    );
  }
}

class _Field extends StatelessWidget {
  final String label;
  final String value;
  const _Field({required this.label, required this.value});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(label, style: Theme.of(context).textTheme.bodySmall),
          const SizedBox(height: 3),
          Text(value, style: Theme.of(context).textTheme.bodyMedium?.copyWith(height: 1.5)),
        ],
      ),
    );
  }
}

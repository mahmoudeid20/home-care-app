import 'package:flutter/material.dart';
import '../core/api_exception.dart';
import '../l10n/app_localizations.dart';
import '../services/review_api.dart';
import '../theme/app_theme.dart';
import '../widgets/error_message.dart';

class LeaveReviewScreen extends StatefulWidget {
  final String bookingId;
  final String nurseName;
  const LeaveReviewScreen({super.key, required this.bookingId, required this.nurseName});

  @override
  State<LeaveReviewScreen> createState() => _LeaveReviewScreenState();
}

class _LeaveReviewScreenState extends State<LeaveReviewScreen> {
  int _overall = 5;
  int _professionalism = 5;
  int _communication = 5;
  int _careQuality = 5;
  final _commentCtrl = TextEditingController();

  bool _submitting = false;
  String? _errorMessage;

  @override
  void dispose() {
    _commentCtrl.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    final t = AppLocalizations.of(context)!;
    setState(() {
      _submitting = true;
      _errorMessage = null;
    });
    try {
      await ReviewApi().create(
        bookingId: widget.bookingId,
        overallRating: _overall,
        professionalism: _professionalism,
        communication: _communication,
        careQuality: _careQuality,
        comment: _commentCtrl.text.trim(),
      );
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(t.reviewSubmitted)));
      Navigator.of(context).pop(true);
    } on ApiException catch (e) {
      setState(() {
        // 409 means this booking already has a review — show the specific
        // message rather than a generic error, since retrying won't help.
        _errorMessage = e.statusCode == 409 ? t.alreadyReviewed : friendlyErrorMessage(e, t);
      });
    } catch (_) {
      setState(() => _errorMessage = t.somethingWentWrong);
    } finally {
      if (mounted) setState(() => _submitting = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final t = AppLocalizations.of(context)!;

    return Scaffold(
      appBar: AppBar(title: Text(t.leaveReview)),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.fromLTRB(20, 16, 20, 32),
          children: [
            Text(widget.nurseName, style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 20),
            if (_errorMessage != null) ...[
              ErrorMessage(message: _errorMessage!),
              const SizedBox(height: 16),
            ],
            _StarRow(label: t.overallRating, value: _overall, onChanged: (v) => setState(() => _overall = v)),
            _StarRow(
                label: t.professionalismRating,
                value: _professionalism,
                onChanged: (v) => setState(() => _professionalism = v)),
            _StarRow(
                label: t.communicationRating,
                value: _communication,
                onChanged: (v) => setState(() => _communication = v)),
            _StarRow(
                label: t.careQualityRating, value: _careQuality, onChanged: (v) => setState(() => _careQuality = v)),
            const SizedBox(height: 12),
            TextField(
              controller: _commentCtrl,
              maxLines: 4,
              decoration: InputDecoration(labelText: t.commentOptional, alignLabelWithHint: true),
            ),
            const SizedBox(height: 24),
            ElevatedButton(
              onPressed: _submitting ? null : _submit,
              child: _submitting
                  ? const SizedBox(
                      width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                  : Text(t.submitReview),
            ),
          ],
        ),
      ),
    );
  }
}

class _StarRow extends StatelessWidget {
  final String label;
  final int value;
  final ValueChanged<int> onChanged;
  const _StarRow({required this.label, required this.value, required this.onChanged});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(label, style: Theme.of(context).textTheme.bodySmall),
          const SizedBox(height: 4),
          Row(
            children: List.generate(5, (i) {
              final filled = i < value;
              return IconButton(
                padding: EdgeInsets.zero,
                constraints: const BoxConstraints(),
                onPressed: () => onChanged(i + 1),
                icon: Icon(
                  filled ? Icons.star_rounded : Icons.star_border_rounded,
                  color: AppColors.amber,
                  size: 28,
                ),
              );
            }),
          ),
        ],
      ),
    );
  }
}

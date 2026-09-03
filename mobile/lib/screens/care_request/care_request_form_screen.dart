import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/api_exception.dart';
import '../../l10n/app_localizations.dart';
import '../../models/care_request.dart';
import '../../models/enums.dart';
import '../../models/lookup.dart';
import '../../models/nurse_detail.dart';
import '../../services/application_api.dart';
import '../../services/care_request_api.dart';
import '../../services/lookup_api.dart';
import '../../theme/app_theme.dart';
import '../../widgets/error_message.dart';
import 'request_sent_screen.dart';

final _servicesProvider = FutureProvider.autoDispose((ref) => LookupApi().services());

/// Section 9's 6-step patient onboarding flow, implemented as one
/// scrollable form with clearly numbered sections instead of a literal
/// swipeable wizard — every field from CareRequestCreate is present and
/// required/optional exactly as the backend schema defines it; this is
/// a presentation choice, not a scope cut.
///
/// If [targetNurse] is provided (came from a nurse's profile page), the
/// newly created care request is immediately sent to that specific nurse
/// via POST /applications — matching the "Section 11: send to a specific
/// nurse" flow. Without a target nurse, this just creates an open request
/// (visible to the matching engine) with no next step wired here yet.
class CareRequestFormScreen extends ConsumerStatefulWidget {
  final NurseDetail? targetNurse;
  const CareRequestFormScreen({super.key, this.targetNurse});

  @override
  ConsumerState<CareRequestFormScreen> createState() => _CareRequestFormScreenState();
}

class _CareRequestFormScreenState extends ConsumerState<CareRequestFormScreen> {
  final _formKey = GlobalKey<FormState>();
  final _draft = CareRequestDraft();

  final _nameCtrl = TextEditingController();
  final _ageCtrl = TextEditingController();
  final _conditionCtrl = TextEditingController();
  final _specialReqCtrl = TextEditingController();
  final _governorateCtrl = TextEditingController();
  final _cityCtrl = TextEditingController();
  final _areaCtrl = TextEditingController();
  final _hoursCtrl = TextEditingController();
  final _budgetMinCtrl = TextEditingController();
  final _budgetMaxCtrl = TextEditingController();

  bool _submitting = false;
  String? _errorMessage;

  @override
  void dispose() {
    for (final c in [
      _nameCtrl, _ageCtrl, _conditionCtrl, _specialReqCtrl, _governorateCtrl,
      _cityCtrl, _areaCtrl, _hoursCtrl, _budgetMinCtrl, _budgetMaxCtrl,
    ]) {
      c.dispose();
    }
    super.dispose();
  }

  Future<void> _pickDate({required bool isStart}) async {
    final now = DateTime.now();
    final picked = await showDatePicker(
      context: context,
      initialDate: now,
      firstDate: now,
      lastDate: now.add(const Duration(days: 365)),
    );
    if (picked == null) return;
    setState(() {
      if (isStart) {
        _draft.startDate = picked;
      } else {
        _draft.endDate = picked;
      }
    });
  }

  Future<void> _submit() async {
    final t = AppLocalizations.of(context)!;
    if (!_formKey.currentState!.validate()) return;
    if (_draft.location == null) {
      _draft.location = LocationData(
        governorate: _governorateCtrl.text.trim(),
        city: _cityCtrl.text.trim(),
        area: _areaCtrl.text.trim().isEmpty ? null : _areaCtrl.text.trim(),
      );
    }
    if (!_draft.isSubmittable) return;

    setState(() {
      _submitting = true;
      _errorMessage = null;
    });
    try {
      final careRequestId = await CareRequestApi().create(_draft);
      if (widget.targetNurse != null) {
        await ApplicationApi().send(careRequestId: careRequestId, nurseId: widget.targetNurse!.id);
      }
      if (!mounted) return;
      Navigator.of(context).pushReplacement(
        MaterialPageRoute(builder: (_) => RequestSentScreen(nurseName: widget.targetNurse?.fullName)),
      );
    } on ApiException catch (e) {
      setState(() => _errorMessage = friendlyErrorMessage(e, t));
    } catch (_) {
      setState(() => _errorMessage = t.somethingWentWrong);
    } finally {
      if (mounted) setState(() => _submitting = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final t = AppLocalizations.of(context)!;
    final locale = Localizations.localeOf(context).languageCode;
    final servicesAsync = ref.watch(_servicesProvider);

    return Scaffold(
      appBar: AppBar(title: Text(t.newRequestTitle)),
      body: SafeArea(
        child: Form(
          key: _formKey,
          child: ListView(
            padding: const EdgeInsets.fromLTRB(20, 12, 20, 40),
            children: [
              if (_errorMessage != null) ...[
                ErrorMessage(message: _errorMessage!),
                const SizedBox(height: 14),
              ],

              _SectionHeader(t.patientInfoSection),
              TextFormField(
                controller: _nameCtrl,
                decoration: InputDecoration(labelText: t.patientNameLabel),
                onChanged: (v) => _draft.patientName = v,
                validator: (v) => (v == null || v.trim().length < 2) ? t.requiredField : null,
              ),
              const SizedBox(height: 12),
              Row(children: [
                Expanded(
                  child: TextFormField(
                    controller: _ageCtrl,
                    keyboardType: TextInputType.number,
                    decoration: InputDecoration(labelText: t.patientAgeLabel),
                    onChanged: (v) => _draft.patientAge = int.tryParse(v),
                    validator: (v) => (int.tryParse(v ?? '') == null) ? t.requiredField : null,
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: DropdownButtonFormField<Gender>(
                    value: _draft.patientGender,
                    decoration: InputDecoration(labelText: t.patientGenderLabel),
                    items: [
                      DropdownMenuItem(value: Gender.female, child: Text(t.female)),
                      DropdownMenuItem(value: Gender.male, child: Text(t.male)),
                    ],
                    onChanged: (v) => setState(() => _draft.patientGender = v ?? Gender.female),
                  ),
                ),
              ]),
              const SizedBox(height: 12),
              TextFormField(
                controller: _conditionCtrl,
                maxLines: 3,
                decoration: InputDecoration(labelText: t.medicalConditionLabel, alignLabelWithHint: true),
                onChanged: (v) => _draft.medicalCondition = v,
                validator: (v) => (v == null || v.trim().length < 3) ? t.requiredField : null,
              ),
              const SizedBox(height: 12),
              DropdownButtonFormField<MobilityStatus>(
                value: _draft.mobilityStatus,
                decoration: InputDecoration(labelText: t.mobilityStatusLabel),
                items: [
                  DropdownMenuItem(value: MobilityStatus.independent, child: Text(t.mobilityIndependent)),
                  DropdownMenuItem(value: MobilityStatus.needsAssistance, child: Text(t.mobilityAssistance)),
                  DropdownMenuItem(value: MobilityStatus.wheelchair, child: Text(t.mobilityWheelchair)),
                  DropdownMenuItem(value: MobilityStatus.bedridden, child: Text(t.mobilityBedridden)),
                ],
                onChanged: (v) => setState(() => _draft.mobilityStatus = v ?? MobilityStatus.independent),
              ),
              const SizedBox(height: 12),
              TextFormField(
                controller: _specialReqCtrl,
                decoration: InputDecoration(labelText: t.specialRequirementsLabel),
                onChanged: (v) => _draft.specialRequirements = v,
              ),

              _SectionHeader(t.careNeededSection),
              servicesAsync.when(
                loading: () => const Padding(
                  padding: EdgeInsets.symmetric(vertical: 12),
                  child: LinearProgressIndicator(),
                ),
                error: (err, _) => ErrorMessage(
                  message: err is ApiException ? friendlyErrorMessage(err, t) : t.somethingWentWrong,
                ),
                data: (services) => _ServiceMultiSelect(
                  services: services,
                  locale: locale,
                  selectedIds: _draft.serviceIds,
                  label: t.selectServices,
                  onChanged: (ids) => setState(() => _draft.serviceIds = ids),
                ),
              ),

              _SectionHeader(t.locationSection),
              TextFormField(
                controller: _governorateCtrl,
                decoration: InputDecoration(labelText: t.governorateLabel),
                validator: (v) => (v == null || v.trim().isEmpty) ? t.requiredField : null,
              ),
              const SizedBox(height: 12),
              TextFormField(
                controller: _cityCtrl,
                decoration: InputDecoration(labelText: t.cityLabel),
                validator: (v) => (v == null || v.trim().isEmpty) ? t.requiredField : null,
              ),
              const SizedBox(height: 12),
              TextFormField(
                controller: _areaCtrl,
                decoration: InputDecoration(labelText: t.areaLabel),
              ),

              _SectionHeader(t.scheduleSection),
              _DateField(
                label: t.startDateLabel,
                value: _draft.startDate,
                onTap: () => _pickDate(isStart: true),
              ),
              const SizedBox(height: 12),
              _DateField(
                label: t.endDateLabel,
                value: _draft.endDate,
                onTap: () => _pickDate(isStart: false),
              ),
              const SizedBox(height: 12),
              TextFormField(
                controller: _hoursCtrl,
                keyboardType: TextInputType.number,
                decoration: InputDecoration(labelText: t.hoursPerDayLabel),
                onChanged: (v) => _draft.hoursPerDay = double.tryParse(v),
              ),
              const SizedBox(height: 12),
              DropdownButtonFormField<PriceUnit>(
                value: _draft.paymentFrequency,
                decoration: InputDecoration(labelText: t.paymentFrequencyLabel),
                items: [
                  DropdownMenuItem(value: PriceUnit.hourly, child: Text(t.hourly)),
                  DropdownMenuItem(value: PriceUnit.daily, child: Text(t.daily)),
                  DropdownMenuItem(value: PriceUnit.weekly, child: Text(t.weekly)),
                  DropdownMenuItem(value: PriceUnit.monthly, child: Text(t.monthly)),
                ],
                onChanged: (v) => setState(() => _draft.paymentFrequency = v ?? PriceUnit.daily),
              ),

              _SectionHeader(t.budgetSection),
              Row(children: [
                Expanded(
                  child: TextFormField(
                    controller: _budgetMinCtrl,
                    keyboardType: TextInputType.number,
                    decoration: InputDecoration(labelText: t.budgetMinLabel),
                    onChanged: (v) => _draft.budgetMin = double.tryParse(v),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: TextFormField(
                    controller: _budgetMaxCtrl,
                    keyboardType: TextInputType.number,
                    decoration: InputDecoration(labelText: t.budgetMaxLabel),
                    onChanged: (v) => _draft.budgetMax = double.tryParse(v),
                  ),
                ),
              ]),

              const SizedBox(height: 28),
              ElevatedButton(
                onPressed: _submitting ? null : _submit,
                child: _submitting
                    ? const SizedBox(
                        width: 20, height: 20,
                        child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                    : Text(t.submitRequest),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _SectionHeader extends StatelessWidget {
  final String text;
  const _SectionHeader(this.text);

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(top: 22, bottom: 10),
      child: Text(text,
          style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 13.5, color: AppColors.teal900)),
    );
  }
}

class _DateField extends StatelessWidget {
  final String label;
  final DateTime? value;
  final VoidCallback onTap;
  const _DateField({required this.label, required this.value, required this.onTap});

  @override
  Widget build(BuildContext context) {
    final t = AppLocalizations.of(context)!;
    final text = value == null
        ? t.pickDate
        : '${value!.year}-${value!.month.toString().padLeft(2, '0')}-${value!.day.toString().padLeft(2, '0')}';
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(AppRadius.sm),
      child: InputDecorator(
        decoration: InputDecoration(labelText: label),
        child: Row(
          children: [
            Text(text, style: TextStyle(color: value == null ? AppColors.inkSoft : AppColors.ink)),
            const Spacer(),
            const Icon(Icons.calendar_today_rounded, size: 16, color: AppColors.inkSoft),
          ],
        ),
      ),
    );
  }
}

class _ServiceMultiSelect extends StatelessWidget {
  final List<ServiceItem> services;
  final String locale;
  final List<String> selectedIds;
  final String label;
  final ValueChanged<List<String>> onChanged;

  const _ServiceMultiSelect({
    required this.services,
    required this.locale,
    required this.selectedIds,
    required this.label,
    required this.onChanged,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(label, style: Theme.of(context).textTheme.bodySmall),
        const SizedBox(height: 8),
        Wrap(
          spacing: 8,
          runSpacing: 8,
          children: services.map((s) {
            final selected = selectedIds.contains(s.id);
            return FilterChip(
              label: Text(s.nameFor(locale), style: const TextStyle(fontSize: 12)),
              selected: selected,
              selectedColor: AppColors.teal700,
              checkmarkColor: Colors.white,
              labelStyle: TextStyle(color: selected ? Colors.white : AppColors.ink),
              backgroundColor: AppColors.surface,
              side: const BorderSide(color: AppColors.line),
              onSelected: (v) {
                final next = List<String>.from(selectedIds);
                if (v) {
                  next.add(s.id);
                } else {
                  next.remove(s.id);
                }
                onChanged(next);
              },
            );
          }).toList(),
        ),
      ],
    );
  }
}

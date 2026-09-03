import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../l10n/app_localizations.dart';
import '../core/api_exception.dart';
import '../core/egypt_locations.dart';
import '../models/lookup.dart';
import '../services/lookup_api.dart';
import '../services/patient_api.dart';
import '../state/auth_controller.dart';
import '../theme/app_theme.dart';
import '../widgets/error_message.dart';

class ProfileSetupWizard extends ConsumerStatefulWidget {
  const ProfileSetupWizard({super.key});

  @override
  ConsumerState<ProfileSetupWizard> createState() => _ProfileSetupWizardState();
}

class _ProfileSetupWizardState extends ConsumerState<ProfileSetupWizard> {
  int _currentStep = 0;
  final _formKey = GlobalKey<FormState>();

  final _fullNameCtrl = TextEditingController();
  final _usernameCtrl = TextEditingController();

  String? _selectedGovernorate;
  String? _selectedCity;
  final Set<String> _selectedSpecialtyIds = {};
  final Set<String> _selectedSpecialtyNames = {};

  List<Specialty> _specialties = [];
  List<ServiceItem> _services = [];
  bool _loadingLookups = true;
  bool _saving = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    final user = ref.read(authControllerProvider).user;
    if (user?.username != null && user!.username!.isNotEmpty) {
      _usernameCtrl.text = user.username!;
    }
    _loadLookups();
  }

  @override
  void dispose() {
    _fullNameCtrl.dispose();
    _usernameCtrl.dispose();
    super.dispose();
  }

  Future<void> _loadLookups() async {
    try {
      final lookupApi = LookupApi();
      final specs = await lookupApi.specialties();
      final servs = await lookupApi.services();
      if (mounted) {
        setState(() {
          _specialties = specs;
          _services = servs;
          _loadingLookups = false;
        });
      }
    } catch (_) {
      if (mounted) {
        setState(() => _loadingLookups = false);
      }
    }
  }

  bool _validateStep1() {
    final t = AppLocalizations.of(context);
    final name = _fullNameCtrl.text.trim();
    final parts = name.split(RegExp(r'\s+')).where((s) => s.isNotEmpty).toList();
    if (parts.length < 4) {
      setState(() => _error = t.fullNameQuadrupleValidation);
      return false;
    }
    setState(() => _error = null);
    return true;
  }

  bool _validateStep2() {
    if (_selectedGovernorate == null || _selectedCity == null) {
      setState(() => _error = 'من فضلك اختر المحافظة والمدينة');
      return false;
    }
    setState(() => _error = null);
    return true;
  }

  Future<void> _submit() async {
    final t = AppLocalizations.of(context);
    setState(() {
      _saving = true;
      _error = null;
    });

    try {
      final patientApi = PatientApi();
      final profile = await patientApi.createProfile(
        fullName: _fullNameCtrl.text.trim(),
        governorate: _selectedGovernorate,
        city: _selectedCity,
      );

      // Successfully saved profile
      ref.read(authControllerProvider.notifier).completeProfileSetup(profile);
      // Navigation is reactive through main.dart's _AuthGate!
    } on ApiException catch (e) {
      // If profile already exists, fetch or proceed
      if (e.statusCode == 409) {
        final profile = await PatientApi().getMyProfile();
        if (profile != null) {
          ref.read(authControllerProvider.notifier).completeProfileSetup(profile);
          return;
        }
      }
      setState(() => _error = friendlyErrorMessage(e, t));
    } catch (_) {
      setState(() => _error = t.somethingWentWrong);
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final t = AppLocalizations.of(context);

    return Scaffold(
      backgroundColor: AppColors.bg,
      appBar: AppBar(
        title: Text(t.profileSetupTitle),
        automaticallyImplyLeading: false,
      ),
      body: SafeArea(
        child: Column(
          children: [
            // Progress Indicator
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 14),
              color: Colors.white,
              child: Column(
                children: [
                  Row(
                    children: [
                      _StepBadge(number: 1, title: t.stepPersonal, isActive: _currentStep >= 0, isCurrent: _currentStep == 0),
                      Expanded(child: Container(height: 2, color: _currentStep >= 1 ? AppColors.primary : AppColors.line)),
                      _StepBadge(number: 2, title: t.stepLocation, isActive: _currentStep >= 1, isCurrent: _currentStep == 1),
                      Expanded(child: Container(height: 2, color: _currentStep >= 2 ? AppColors.primary : AppColors.line)),
                      _StepBadge(number: 3, title: t.stepNursingType, isActive: _currentStep >= 2, isCurrent: _currentStep == 2),
                    ],
                  ),
                ],
              ),
            ),

            if (_error != null) ...[
              Padding(
                padding: const EdgeInsets.fromLTRB(20, 16, 20, 0),
                child: ErrorMessage(message: _error!),
              ),
            ],

            // Step Content
            Expanded(
              child: SingleChildScrollView(
                padding: const EdgeInsets.all(24),
                child: Form(
                  key: _formKey,
                  child: _buildCurrentStep(t),
                ),
              ),
            ),

            // Bottom Navigation Controls
            Container(
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                color: Colors.white,
                border: Border(top: BorderSide(color: AppColors.line)),
              ),
              child: Row(
                children: [
                  if (_currentStep > 0) ...[
                    OutlinedButton(
                      onPressed: _saving ? null : () => setState(() {
                        _error = null;
                        _currentStep--;
                      }),
                      child: const Text('السابق'),
                    ),
                    const SizedBox(width: 14),
                  ],
                  Expanded(
                    child: ElevatedButton(
                      onPressed: _saving
                          ? null
                          : () {
                              if (_currentStep == 0) {
                                if (_validateStep1()) {
                                  setState(() => _currentStep = 1);
                                }
                              } else if (_currentStep == 1) {
                                if (_validateStep2()) {
                                  setState(() => _currentStep = 2);
                                }
                              } else {
                                _submit();
                              }
                            },
                      style: ElevatedButton.styleFrom(
                        backgroundColor: AppColors.primary,
                        minimumSize: const Size.fromHeight(50),
                      ),
                      child: _saving
                          ? const SizedBox(
                              width: 22,
                              height: 22,
                              child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2),
                            )
                          : Text(_currentStep == 2 ? t.saveAndContinue : t.next),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildCurrentStep(AppLocalizations t) {
    switch (_currentStep) {
      case 0:
        return _buildStep1Personal(t);
      case 1:
        return _buildStep2Location(t);
      case 2:
        return _buildStep3NursingType(t);
      default:
        return const SizedBox.shrink();
    }
  }

  Widget _buildStep1Personal(AppLocalizations t) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          t.stepPersonal,
          style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w800, color: AppColors.ink),
        ),
        const SizedBox(height: 6),
        Text(
          'أدخل اسمك بالكامل ليكون واضحاً لمقدمي الرعاية الصحية.',
          style: const TextStyle(fontSize: 13.5, color: AppColors.inkSoft),
        ),
        const SizedBox(height: 24),

        // Avatar Preview
        Center(
          child: Stack(
            children: [
              CircleAvatar(
                radius: 46,
                backgroundColor: AppColors.primarySurface,
                child: const Icon(Icons.person, size: 50, color: AppColors.primary),
              ),
            ],
          ),
        ),
        const SizedBox(height: 28),

        // Full Quadruple Name
        Text(t.fullName, style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 14)),
        const SizedBox(height: 8),
        TextFormField(
          controller: _fullNameCtrl,
          textInputAction: TextInputAction.next,
          decoration: InputDecoration(
            hintText: t.fullNameQuadrupleHint,
            prefixIcon: const Icon(Icons.badge_outlined, color: AppColors.primary),
          ),
          validator: (v) {
            if (v == null || v.trim().isEmpty) return t.requiredField;
            final parts = v.trim().split(RegExp(r'\s+')).where((s) => s.isNotEmpty).toList();
            if (parts.length < 4) return t.fullNameQuadrupleValidation;
            return null;
          },
        ),
        const SizedBox(height: 6),
        Text(
          'الاسم الرباعي إلزامي لضمان أمان وموثوقية التواصل الطبي.',
          style: TextStyle(fontSize: 12, color: AppColors.inkSoft.withOpacity(0.8)),
        ),
        const SizedBox(height: 20),

        // Username
        Text(t.username, style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 14)),
        const SizedBox(height: 8),
        TextFormField(
          controller: _usernameCtrl,
          textInputAction: TextInputAction.done,
          decoration: InputDecoration(
            hintText: t.usernameHint,
            prefixIcon: const Icon(Icons.alternate_email_rounded, color: AppColors.primary),
          ),
          validator: (v) {
            if (v != null && v.trim().isNotEmpty && v.trim().length < 3) {
              return t.usernameValidation;
            }
            return null;
          },
        ),
      ],
    );
  }

  Widget _buildStep2Location(AppLocalizations t) {
    final cities = _selectedGovernorate != null
        ? EgyptLocations.getCities(_selectedGovernorate!)
        : <String>[];

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          t.stepLocation,
          style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w800, color: AppColors.ink),
        ),
        const SizedBox(height: 6),
        Text(
          'حدد محافظتك ومدينتك داخل جمهورية مصر العربية لعرض أقرب الممرضين لك.',
          style: const TextStyle(fontSize: 13.5, color: AppColors.inkSoft),
        ),
        const SizedBox(height: 24),

        // Governorate Dropdown
        Text(t.governorate, style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 14)),
        const SizedBox(height: 8),
        DropdownButtonFormField<String>(
          value: _selectedGovernorate,
          hint: Text(t.selectGovernorate),
          isExpanded: true,
          decoration: const InputDecoration(
            prefixIcon: Icon(Icons.location_city_rounded, color: AppColors.primary),
          ),
          items: EgyptLocations.governorates.map((gov) {
            return DropdownMenuItem<String>(
              value: gov,
              child: Text(gov),
            );
          }).toList(),
          onChanged: (val) {
            setState(() {
              _selectedGovernorate = val;
              _selectedCity = null; // reset city
            });
          },
        ),
        const SizedBox(height: 20),

        // City Dropdown
        Text(t.city, style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 14)),
        const SizedBox(height: 8),
        DropdownButtonFormField<String>(
          value: _selectedCity,
          hint: Text(t.selectCity),
          isExpanded: true,
          decoration: const InputDecoration(
            prefixIcon: Icon(Icons.pin_drop_rounded, color: AppColors.primary),
          ),
          items: cities.map((city) {
            return DropdownMenuItem<String>(
              value: city,
              child: Text(city),
            );
          }).toList(),
          onChanged: _selectedGovernorate == null
              ? null
              : (val) => setState(() => _selectedCity = val),
        ),
      ],
    );
  }

  Widget _buildStep3NursingType(AppLocalizations t) {
    final isArabic = Localizations.localeOf(context).languageCode == 'ar';

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          t.whatNursingDoYouNeed,
          style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w800, color: AppColors.ink),
        ),
        const SizedBox(height: 6),
        Text(
          t.selectSpecialtiesOrServices,
          style: const TextStyle(fontSize: 13.5, color: AppColors.inkSoft),
        ),
        const SizedBox(height: 24),

        if (_loadingLookups)
          const Center(
            child: Padding(
              padding: EdgeInsets.all(32),
              child: CircularProgressIndicator(),
            ),
          )
        else ...[
          const Text(
            'التخصصات الطبية للتمريض',
            style: TextStyle(fontWeight: FontWeight.w800, fontSize: 15, color: AppColors.primaryDark),
          ),
          const SizedBox(height: 12),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: _specialties.map((spec) {
              final isSelected = _selectedSpecialtyIds.contains(spec.id);
              final name = isArabic ? spec.nameAr : spec.nameEn;
              return FilterChip(
                label: Text(name),
                selected: isSelected,
                selectedColor: AppColors.primarySurface,
                checkmarkColor: AppColors.primary,
                labelStyle: TextStyle(
                  color: isSelected ? AppColors.primaryDark : AppColors.ink,
                  fontWeight: isSelected ? FontWeight.w700 : FontWeight.normal,
                ),
                side: BorderSide(
                  color: isSelected ? AppColors.primary : AppColors.line,
                ),
                onSelected: (selected) {
                  setState(() {
                    if (selected) {
                      _selectedSpecialtyIds.add(spec.id);
                      _selectedSpecialtyNames.add(name);
                    } else {
                      _selectedSpecialtyIds.remove(spec.id);
                      _selectedSpecialtyNames.remove(name);
                    }
                  });
                },
              );
            }).toList(),
          ),
          const SizedBox(height: 24),

          const Text(
            'الخدمات المطلوبة',
            style: TextStyle(fontWeight: FontWeight.w800, fontSize: 15, color: AppColors.primaryDark),
          ),
          const SizedBox(height: 12),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: _services.map((srv) {
              final isSelected = _selectedSpecialtyIds.contains(srv.id);
              final name = isArabic ? srv.nameAr : srv.nameEn;
              return FilterChip(
                label: Text(name),
                selected: isSelected,
                selectedColor: AppColors.primarySurface,
                checkmarkColor: AppColors.primary,
                labelStyle: TextStyle(
                  color: isSelected ? AppColors.primaryDark : AppColors.ink,
                  fontWeight: isSelected ? FontWeight.w700 : FontWeight.normal,
                ),
                side: BorderSide(
                  color: isSelected ? AppColors.primary : AppColors.line,
                ),
                onSelected: (selected) {
                  setState(() {
                    if (selected) {
                      _selectedSpecialtyIds.add(srv.id);
                      _selectedSpecialtyNames.add(name);
                    } else {
                      _selectedSpecialtyIds.remove(srv.id);
                      _selectedSpecialtyNames.remove(name);
                    }
                  });
                },
              );
            }).toList(),
          ),
        ],
      ],
    );
  }
}

class _StepBadge extends StatelessWidget {
  final int number;
  final String title;
  final bool isActive;
  final bool isCurrent;

  const _StepBadge({
    required this.number,
    required this.title,
    required this.isActive,
    required this.isCurrent,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Container(
          width: 32,
          height: 32,
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            color: isActive ? AppColors.primary : AppColors.line,
            border: isCurrent ? Border.all(color: AppColors.primaryDark, width: 2) : null,
          ),
          child: Center(
            child: Text(
              '$number',
              style: TextStyle(
                color: isActive ? Colors.white : AppColors.inkSoft,
                fontWeight: FontWeight.bold,
                fontSize: 14,
              ),
            ),
          ),
        ),
        const SizedBox(height: 4),
        Text(
          title,
          style: TextStyle(
            fontSize: 11,
            fontWeight: isCurrent ? FontWeight.w800 : FontWeight.w500,
            color: isCurrent ? AppColors.primaryDark : AppColors.inkSoft,
          ),
        ),
      ],
    );
  }
}

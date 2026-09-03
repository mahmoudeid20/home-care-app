import 'enums.dart';
import 'lookup.dart';

/// Mirrors CareRequestCreate in app/schemas/care_request.py exactly —
/// every field the 6-step Section 9 flow collects, field-for-field, so
/// the backend never sees a shape it doesn't expect.
class CareRequestDraft {
  // Step 1 — patient info
  String patientName = '';
  int? patientAge;
  Gender patientGender = Gender.female;
  String medicalCondition = '';
  MobilityStatus mobilityStatus = MobilityStatus.independent;
  String? specialRequirements;

  // Step 2 — required care
  List<String> serviceIds = [];

  // Step 3 — nurse requirements
  Gender? preferredNurseGender;
  int? minExperienceYears;
  List<String> requiredSpecialtyIds = [];
  List<String> languages = [];
  bool verifiedNursesOnly = false;
  ShiftType preferredShift = ShiftType.custom;

  // Step 4 — location
  LocationData? location;

  // Step 5 — schedule
  DateTime? startDate;
  DateTime? endDate;
  double? hoursPerDay;
  int? numberOfDays;
  String? customScheduleNote;
  PriceUnit paymentFrequency = PriceUnit.daily;

  // Step 6 — budget
  double? budgetMin;
  double? budgetMax;

  bool get step1Valid =>
      patientName.trim().length >= 2 && patientAge != null && medicalCondition.trim().length >= 3;
  bool get step2Valid => serviceIds.isNotEmpty;
  bool get step4Valid => location != null;
  bool get step5Valid => startDate != null;
  bool get isSubmittable => step1Valid && step2Valid && step4Valid && step5Valid;

  Map<String, dynamic> toJson() {
    String dateStr(DateTime d) =>
        '${d.year.toString().padLeft(4, '0')}-${d.month.toString().padLeft(2, '0')}-${d.day.toString().padLeft(2, '0')}';

    return {
      'patient_name': patientName.trim(),
      'patient_age': patientAge,
      'patient_gender': genderToApi(patientGender),
      'medical_condition': medicalCondition.trim(),
      'mobility_status': mobilityStatusToApi(mobilityStatus),
      if (specialRequirements != null && specialRequirements!.isNotEmpty)
        'special_requirements': specialRequirements,
      'service_ids': serviceIds,
      if (preferredNurseGender != null) 'preferred_nurse_gender': genderToApi(preferredNurseGender!),
      if (minExperienceYears != null) 'min_experience_years': minExperienceYears,
      'required_specialty_ids': requiredSpecialtyIds,
      'languages': languages,
      'verified_nurses_only': verifiedNursesOnly,
      'preferred_shift': shiftTypeToApi(preferredShift),
      'location': location!.toJson(),
      'start_date': dateStr(startDate!),
      if (endDate != null) 'end_date': dateStr(endDate!),
      if (hoursPerDay != null) 'hours_per_day': hoursPerDay,
      if (numberOfDays != null) 'number_of_days': numberOfDays,
      if (customScheduleNote != null && customScheduleNote!.isNotEmpty)
        'custom_schedule_note': customScheduleNote,
      'payment_frequency': priceUnitToApi(paymentFrequency),
      if (budgetMin != null) 'budget_min': budgetMin,
      if (budgetMax != null) 'budget_max': budgetMax,
    };
  }
}

class CareRequestSummary {
  final String id;
  final CareRequestStatus status;
  final String patientName;
  final DateTime startDate;

  const CareRequestSummary({
    required this.id,
    required this.status,
    required this.patientName,
    required this.startDate,
  });

  factory CareRequestSummary.fromJson(Map<String, dynamic> j) => CareRequestSummary(
        id: j['id'] as String,
        status: careRequestStatusFromApi(j['status'] as String),
        patientName: j['patient_name'] as String,
        startDate: DateTime.parse(j['start_date'] as String),
      );
}

/// Full CareRequestResponse — what a nurse sees when reviewing a
/// received application (Section 18 "New Requests" detail view).
class CareRequestDetail {
  final String id;
  final CareRequestStatus status;
  final String patientName;
  final int patientAge;
  final Gender patientGender;
  final String medicalCondition;
  final MobilityStatus mobilityStatus;
  final String? specialRequirements;
  final LocationData? location;
  final DateTime startDate;
  final DateTime? endDate;
  final double? hoursPerDay;
  final PriceUnit paymentFrequency;
  final double? budgetMin;
  final double? budgetMax;

  const CareRequestDetail({
    required this.id,
    required this.status,
    required this.patientName,
    required this.patientAge,
    required this.patientGender,
    required this.medicalCondition,
    required this.mobilityStatus,
    this.specialRequirements,
    this.location,
    required this.startDate,
    this.endDate,
    this.hoursPerDay,
    required this.paymentFrequency,
    this.budgetMin,
    this.budgetMax,
  });

  factory CareRequestDetail.fromJson(Map<String, dynamic> j) => CareRequestDetail(
        id: j['id'] as String,
        status: careRequestStatusFromApi(j['status'] as String),
        patientName: j['patient_name'] as String,
        patientAge: (j['patient_age'] as num).toInt(),
        patientGender: genderFromApi(j['patient_gender'] as String),
        medicalCondition: j['medical_condition'] as String,
        mobilityStatus: mobilityStatusFromApi(j['mobility_status'] as String),
        specialRequirements: j['special_requirements'] as String?,
        location: j['location'] != null ? LocationData.fromJson(j['location'] as Map<String, dynamic>) : null,
        startDate: DateTime.parse(j['start_date'] as String),
        endDate: j['end_date'] != null ? DateTime.parse(j['end_date'] as String) : null,
        hoursPerDay: (j['hours_per_day'] as num?)?.toDouble(),
        paymentFrequency: priceUnitFromApi(j['payment_frequency'] as String),
        budgetMin: (j['budget_min'] as num?)?.toDouble(),
        budgetMax: (j['budget_max'] as num?)?.toDouble(),
      );
}

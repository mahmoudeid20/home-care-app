import 'enums.dart';

class ApplicationInfo {
  final String id;
  final String careRequestId;
  final String nurseId;
  final String patientId;
  final ApplicationStatus status;
  final String? message;
  final String? rejectionReason;

  const ApplicationInfo({
    required this.id,
    required this.careRequestId,
    required this.nurseId,
    required this.patientId,
    required this.status,
    this.message,
    this.rejectionReason,
  });

  factory ApplicationInfo.fromJson(Map<String, dynamic> j) => ApplicationInfo(
        id: j['id'] as String,
        careRequestId: j['care_request_id'] as String,
        nurseId: j['nurse_id'] as String,
        patientId: j['patient_id'] as String,
        status: applicationStatusFromApi(j['status'] as String),
        message: j['message'] as String?,
        rejectionReason: j['rejection_reason'] as String?,
      );
}

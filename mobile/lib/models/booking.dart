import 'enums.dart';

class BookingInfo {
  final String id;
  final String careRequestId;
  final String applicationId;
  final String patientId;
  final String nurseId;
  final BookingStatus status;

  final DateTime startDate;
  final DateTime? endDate;
  final double? hoursPerDay;
  final PriceUnit paymentFrequency;
  final double? agreedPrice;

  const BookingInfo({
    required this.id,
    required this.careRequestId,
    required this.applicationId,
    required this.patientId,
    required this.nurseId,
    required this.status,
    required this.startDate,
    this.endDate,
    this.hoursPerDay,
    required this.paymentFrequency,
    this.agreedPrice,
  });

  factory BookingInfo.fromJson(Map<String, dynamic> j) => BookingInfo(
        id: j['id'] as String,
        careRequestId: j['care_request_id'] as String,
        applicationId: j['application_id'] as String,
        patientId: j['patient_id'] as String,
        nurseId: j['nurse_id'] as String,
        status: bookingStatusFromApi(j['status'] as String),
        startDate: DateTime.parse(j['start_date'] as String),
        endDate: j['end_date'] != null ? DateTime.parse(j['end_date'] as String) : null,
        hoursPerDay: (j['hours_per_day'] as num?)?.toDouble(),
        paymentFrequency: priceUnitFromApi(j['payment_frequency'] as String),
        agreedPrice: (j['agreed_price'] as num?)?.toDouble(),
      );
}

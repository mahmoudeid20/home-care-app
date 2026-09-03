/// Every enum here mirrors a backend Python enum's `.value` strings
/// exactly (see app/models/nurse.py, app/models/care_request.py,
/// app/models/application.py, app/models/booking.py). Do not rename
/// the API-facing string constants — only the Dart identifiers are ours.

enum Gender { male, female }

String genderToApi(Gender g) => g == Gender.male ? 'MALE' : 'FEMALE';
Gender genderFromApi(String v) => v == 'MALE' ? Gender.male : Gender.female;

enum PriceUnit { hourly, daily, weekly, monthly }

const _priceUnitApi = {
  PriceUnit.hourly: 'HOURLY',
  PriceUnit.daily: 'DAILY',
  PriceUnit.weekly: 'WEEKLY',
  PriceUnit.monthly: 'MONTHLY',
};
String priceUnitToApi(PriceUnit u) => _priceUnitApi[u]!;
PriceUnit priceUnitFromApi(String v) =>
    _priceUnitApi.entries.firstWhere((e) => e.value == v, orElse: () => const MapEntry(PriceUnit.hourly, 'HOURLY')).key;

enum ShiftType { morning, evening, night, hours24, custom }

const _shiftTypeApi = {
  ShiftType.morning: 'MORNING',
  ShiftType.evening: 'EVENING',
  ShiftType.night: 'NIGHT',
  ShiftType.hours24: 'HOURS_24',
  ShiftType.custom: 'CUSTOM',
};
String shiftTypeToApi(ShiftType s) => _shiftTypeApi[s]!;
ShiftType shiftTypeFromApi(String v) =>
    _shiftTypeApi.entries.firstWhere((e) => e.value == v, orElse: () => const MapEntry(ShiftType.custom, 'CUSTOM')).key;

enum MobilityStatus { independent, needsAssistance, wheelchair, bedridden }

const _mobilityApi = {
  MobilityStatus.independent: 'INDEPENDENT',
  MobilityStatus.needsAssistance: 'NEEDS_ASSISTANCE',
  MobilityStatus.wheelchair: 'WHEELCHAIR',
  MobilityStatus.bedridden: 'BEDRIDDEN',
};
String mobilityStatusToApi(MobilityStatus m) => _mobilityApi[m]!;
MobilityStatus mobilityStatusFromApi(String v) =>
    _mobilityApi.entries.firstWhere((e) => e.value == v, orElse: () => const MapEntry(MobilityStatus.independent, 'INDEPENDENT')).key;

enum CareRequestStatus { open, matched, closed, expired, cancelled }

CareRequestStatus careRequestStatusFromApi(String v) => switch (v) {
      'OPEN' => CareRequestStatus.open,
      'MATCHED' => CareRequestStatus.matched,
      'CLOSED' => CareRequestStatus.closed,
      'EXPIRED' => CareRequestStatus.expired,
      'CANCELLED' => CareRequestStatus.cancelled,
      _ => CareRequestStatus.open,
    };

enum ApplicationStatus { pending, accepted, rejected, withdrawn }

ApplicationStatus applicationStatusFromApi(String v) => switch (v) {
      'PENDING' => ApplicationStatus.pending,
      'ACCEPTED' => ApplicationStatus.accepted,
      'REJECTED' => ApplicationStatus.rejected,
      'WITHDRAWN' => ApplicationStatus.withdrawn,
      _ => ApplicationStatus.pending,
    };

enum BookingStatus { accepted, confirmed, active, completed, reviewed, cancelled, expired }

BookingStatus bookingStatusFromApi(String v) => switch (v) {
      'ACCEPTED' => BookingStatus.accepted,
      'CONFIRMED' => BookingStatus.confirmed,
      'ACTIVE' => BookingStatus.active,
      'COMPLETED' => BookingStatus.completed,
      'REVIEWED' => BookingStatus.reviewed,
      'CANCELLED' => BookingStatus.cancelled,
      'EXPIRED' => BookingStatus.expired,
      _ => BookingStatus.accepted,
    };

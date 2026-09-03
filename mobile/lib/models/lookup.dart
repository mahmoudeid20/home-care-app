/// Both Specialty and Service carry name_en/name_ar from the backend
/// (app/schemas/lookup.py) — [nameFor] picks the right one for display
/// instead of the app needing a separate translation table for catalog data.
class Specialty {
  final String id;
  final String nameEn;
  final String nameAr;
  const Specialty({required this.id, required this.nameEn, required this.nameAr});

  factory Specialty.fromJson(Map<String, dynamic> j) =>
      Specialty(id: j['id'] as String, nameEn: j['name_en'] as String, nameAr: j['name_ar'] as String);

  String nameFor(String languageCode) => languageCode == 'ar' ? nameAr : nameEn;
}

class ServiceItem {
  final String id;
  final String nameEn;
  final String nameAr;
  const ServiceItem({required this.id, required this.nameEn, required this.nameAr});

  factory ServiceItem.fromJson(Map<String, dynamic> j) =>
      ServiceItem(id: j['id'] as String, nameEn: j['name_en'] as String, nameAr: j['name_ar'] as String);

  String nameFor(String languageCode) => languageCode == 'ar' ? nameAr : nameEn;
}

class LocationData {
  final String? id;
  final String governorate;
  final String city;
  final String? area;
  final String? addressLine;
  final double? latitude;
  final double? longitude;

  const LocationData({
    this.id,
    required this.governorate,
    required this.city,
    this.area,
    this.addressLine,
    this.latitude,
    this.longitude,
  });

  factory LocationData.fromJson(Map<String, dynamic> j) => LocationData(
        id: j['id'] as String?,
        governorate: j['governorate'] as String,
        city: j['city'] as String,
        area: j['area'] as String?,
        addressLine: j['address_line'] as String?,
        latitude: (j['latitude'] as num?)?.toDouble(),
        longitude: (j['longitude'] as num?)?.toDouble(),
      );

  Map<String, dynamic> toJson() => {
        'governorate': governorate,
        'city': city,
        if (area != null && area!.isNotEmpty) 'area': area,
        if (addressLine != null && addressLine!.isNotEmpty) 'address_line': addressLine,
        if (latitude != null) 'latitude': latitude,
        if (longitude != null) 'longitude': longitude,
      };
}

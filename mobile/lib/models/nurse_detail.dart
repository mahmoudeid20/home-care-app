import 'enums.dart';
import 'lookup.dart';

class NurseServiceOffering {
  final ServiceItem service;
  final double price;
  final PriceUnit priceUnit;
  const NurseServiceOffering({required this.service, required this.price, required this.priceUnit});

  factory NurseServiceOffering.fromJson(Map<String, dynamic> j) => NurseServiceOffering(
        service: ServiceItem.fromJson(j['service'] as Map<String, dynamic>),
        price: (j['price'] as num).toDouble(),
        priceUnit: priceUnitFromApi(j['price_unit'] as String),
      );
}

/// Full public profile — mirrors NurseResponse in app/schemas/nurse.py.
class NurseDetail {
  final String id;
  final String userId;
  final String fullName;
  final String? professionalTitle;
  final String? bio;
  final Gender gender;
  final int experienceYears;
  final String? education;
  final String? photoUrl;
  final LocationData? location;

  final bool identityVerified;
  final bool qualificationVerified;
  final bool experienceVerified;
  final bool isApproved;
  final bool isSuspended;

  final double averageRating;
  final int reviewCount;

  final List<Specialty> specialties;
  final List<NurseServiceOffering> services;

  const NurseDetail({
    required this.id,
    required this.userId,
    required this.fullName,
    this.professionalTitle,
    this.bio,
    required this.gender,
    required this.experienceYears,
    this.education,
    this.photoUrl,
    this.location,
    required this.identityVerified,
    required this.qualificationVerified,
    required this.experienceVerified,
    required this.isApproved,
    required this.isSuspended,
    required this.averageRating,
    required this.reviewCount,
    required this.specialties,
    required this.services,
  });

  bool get isFullyVerified => identityVerified && qualificationVerified && experienceVerified;

  factory NurseDetail.fromJson(Map<String, dynamic> j) => NurseDetail(
        id: j['id'] as String,
        userId: j['user_id'] as String,
        fullName: j['full_name'] as String,
        professionalTitle: j['professional_title'] as String?,
        bio: j['bio'] as String?,
        gender: genderFromApi(j['gender'] as String),
        experienceYears: (j['experience_years'] as num?)?.toInt() ?? 0,
        education: j['education'] as String?,
        photoUrl: j['photo_url'] as String?,
        location: j['location'] != null ? LocationData.fromJson(j['location'] as Map<String, dynamic>) : null,
        identityVerified: j['identity_verified'] as bool? ?? false,
        qualificationVerified: j['qualification_verified'] as bool? ?? false,
        experienceVerified: j['experience_verified'] as bool? ?? false,
        isApproved: j['is_approved'] as bool? ?? false,
        isSuspended: j['is_suspended'] as bool? ?? false,
        averageRating: (j['average_rating'] as num?)?.toDouble() ?? 0.0,
        reviewCount: (j['review_count'] as num?)?.toInt() ?? 0,
        specialties: ((j['specialties'] as List?) ?? [])
            .map((e) => Specialty.fromJson(e as Map<String, dynamic>))
            .toList(),
        services: ((j['services'] as List?) ?? [])
            .map((e) => NurseServiceOffering.fromJson(e as Map<String, dynamic>))
            .toList(),
      );
}

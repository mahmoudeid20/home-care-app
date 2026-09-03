/// Mirrors the fields returned by GET /nurses/search
/// (see backend/app/schemas/nurse.py, backend/app/services/nurse_search_service.py).
class NurseSummary {
  final String id;
  final String fullName;
  final String? professionalTitle;
  final int experienceYears;
  final double averageRating;
  final int reviewCount;
  final bool isVerified;
  final double? startingPrice;
  final String? photoUrl;

  const NurseSummary({
    required this.id,
    required this.fullName,
    this.professionalTitle,
    required this.experienceYears,
    required this.averageRating,
    required this.reviewCount,
    required this.isVerified,
    this.startingPrice,
    this.photoUrl,
  });

  factory NurseSummary.fromJson(Map<String, dynamic> j) => NurseSummary(
        id: j['id'] as String,
        fullName: j['full_name'] as String,
        professionalTitle: j['professional_title'] as String?,
        experienceYears: (j['experience_years'] as num?)?.toInt() ?? 0,
        averageRating: (j['average_rating'] as num?)?.toDouble() ?? 0.0,
        reviewCount: (j['review_count'] as num?)?.toInt() ?? 0,
        isVerified: j['is_verified'] as bool? ?? false,
        startingPrice: (j['starting_price'] as num?)?.toDouble(),
        // Matches NurseSearchResult.photo_url — nullable until the nurse
        // uploads a photo (see backend/app/schemas/nurse.py).
        photoUrl: j['photo_url'] as String?,
      );
}

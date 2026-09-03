class ReviewInfo {
  final String id;
  final String bookingId;
  final String nurseId;
  final int overallRating;
  final int professionalism;
  final int communication;
  final int careQuality;
  final String? comment;
  final DateTime createdAt;

  const ReviewInfo({
    required this.id,
    required this.bookingId,
    required this.nurseId,
    required this.overallRating,
    required this.professionalism,
    required this.communication,
    required this.careQuality,
    this.comment,
    required this.createdAt,
  });

  factory ReviewInfo.fromJson(Map<String, dynamic> j) => ReviewInfo(
        id: j['id'] as String,
        bookingId: j['booking_id'] as String,
        nurseId: j['nurse_id'] as String,
        overallRating: (j['overall_rating'] as num).toInt(),
        professionalism: (j['professionalism'] as num).toInt(),
        communication: (j['communication'] as num).toInt(),
        careQuality: (j['care_quality'] as num).toInt(),
        comment: j['comment'] as String?,
        createdAt: DateTime.parse(j['created_at'] as String),
      );
}

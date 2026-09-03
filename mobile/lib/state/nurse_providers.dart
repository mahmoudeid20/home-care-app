import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/nurse_detail.dart';
import '../services/nurse_api.dart';

/// Shared across NurseDetailScreen and BookingsScreen so opening a nurse's
/// profile after already seeing them in a booking card doesn't re-fetch —
/// Riverpod keys FutureProvider.family by the parameter, so the same
/// nurseId hits cache instead of firing a second GET /nurses/{id}.
final nurseDetailProvider =
    FutureProvider.autoDispose.family<NurseDetail, String>((ref, nurseId) => NurseApi().getById(nurseId));

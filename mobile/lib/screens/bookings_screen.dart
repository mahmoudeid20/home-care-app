import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../core/api_exception.dart';
import '../l10n/app_localizations.dart';
import '../models/booking.dart';
import '../models/enums.dart';
import '../services/booking_api.dart';
import '../state/auth_controller.dart';
import '../models/user.dart';
import '../state/nurse_providers.dart';
import '../theme/app_theme.dart';
import '../widgets/error_message.dart';
import 'nurse_detail_screen.dart';
import 'patient/sent_requests_screen.dart';
import 'leave_review_screen.dart';

final _bookingsProvider = FutureProvider.autoDispose((ref) => BookingApi().listMine());

class BookingsScreen extends ConsumerWidget {
  const BookingsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final t = AppLocalizations.of(context)!;
    final async = ref.watch(_bookingsProvider);
    final isPatient = ref.watch(authControllerProvider).user?.role == UserRole.patient;

    return RefreshIndicator(
      onRefresh: () async => ref.invalidate(_bookingsProvider),
      child: CustomScrollView(slivers: [
        SliverToBoxAdapter(
          child: Padding(
            padding: const EdgeInsets.fromLTRB(20, 16, 20, 4),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(t.myBookings, style: Theme.of(context).textTheme.headlineSmall),
                if (isPatient)
                  TextButton(
                    onPressed: () => Navigator.of(context).push(
                      MaterialPageRoute(builder: (_) => const SentRequestsScreen()),
                    ),
                    child: Text(t.mySentRequests, style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w700)),
                  ),
              ],
            ),
          ),
        ),
        async.when(
          loading: () => const SliverFillRemaining(
            hasScrollBody: false,
            child: Center(child: CircularProgressIndicator()),
          ),
          error: (err, _) => SliverFillRemaining(
            hasScrollBody: false,
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 20),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  ErrorMessage(message: err is ApiException ? friendlyErrorMessage(err, t) : t.somethingWentWrong),
                  const SizedBox(height: 12),
                  OutlinedButton(onPressed: () => ref.invalidate(_bookingsProvider), child: Text(t.retry)),
                ],
              ),
            ),
          ),
          data: (bookings) {
            if (bookings.isEmpty) {
              return SliverFillRemaining(
                hasScrollBody: false,
                child: Center(
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(Icons.event_note_outlined, size: 56, color: AppColors.inkSoft.withOpacity(0.4)),
                      const SizedBox(height: 12),
                      Text(t.noBookingsYet, textAlign: TextAlign.center, style: Theme.of(context).textTheme.bodySmall),
                    ],
                  ),
                ),
              );
            }
            return SliverPadding(
              padding: const EdgeInsets.all(20),
              sliver: SliverList.separated(
                itemCount: bookings.length,
                separatorBuilder: (_, __) => const SizedBox(height: 10),
                itemBuilder: (_, i) => _BookingCard(booking: bookings[i]),
              ),
            );
          },
        ),
      ]),
    );
  }
}

class _BookingCard extends ConsumerWidget {
  final BookingInfo booking;
  const _BookingCard({required this.booking});

  (Color, Color) _pillColors(BookingStatus s) => switch (s) {
        BookingStatus.active => (const Color(0xFFFFF4E0), AppColors.amberDark),
        BookingStatus.confirmed || BookingStatus.accepted => (AppColors.teal100, AppColors.teal900),
        BookingStatus.reviewed || BookingStatus.completed => (const Color(0xFFE9F8EF), AppColors.success),
        BookingStatus.cancelled || BookingStatus.expired => (AppColors.line, AppColors.inkSoft),
      };

  String _label(AppLocalizations t, BookingStatus s) => switch (s) {
        BookingStatus.accepted => t.statusAccepted,
        BookingStatus.confirmed => t.statusConfirmed,
        BookingStatus.active => t.statusActive,
        BookingStatus.completed => t.statusCompleted,
        BookingStatus.reviewed => t.statusReviewed,
        BookingStatus.cancelled => t.statusCancelled,
        BookingStatus.expired => t.statusExpired,
      };

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final t = AppLocalizations.of(context)!;
    final (bg, fg) = _pillColors(booking.status);
    final nurseAsync = ref.watch(nurseDetailProvider(booking.nurseId));
    final dateStr = '${booking.startDate.day}/${booking.startDate.month}/${booking.startDate.year}';

    return Card(
      child: InkWell(
        borderRadius: BorderRadius.circular(AppRadius.md),
        onTap: () => Navigator.of(context).push(
          MaterialPageRoute(builder: (_) => NurseDetailScreen(nurseId: booking.nurseId)),
        ),
        child: Padding(
          padding: const EdgeInsets.all(14),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 3),
                    decoration: BoxDecoration(color: bg, borderRadius: BorderRadius.circular(7)),
                    child: Text(_label(t, booking.status),
                        style: TextStyle(fontSize: 10, fontWeight: FontWeight.w800, color: fg)),
                  ),
                  Text(dateStr, style: Theme.of(context).textTheme.bodySmall),
                ],
              ),
              const SizedBox(height: 8),
              nurseAsync.when(
                loading: () => const SizedBox(
                  height: 16, width: 100,
                  child: LinearProgressIndicator(),
                ),
                error: (_, __) => Text('#${booking.nurseId.substring(0, 8)}', style: Theme.of(context).textTheme.titleMedium),
                data: (nurse) => Text(nurse.fullName, style: Theme.of(context).textTheme.titleMedium),
              ),
              if (booking.agreedPrice != null)
                Padding(
                  padding: const EdgeInsets.only(top: 4),
                  child: Text('${booking.agreedPrice!.toStringAsFixed(0)} ${t.egp}',
                      style: const TextStyle(fontWeight: FontWeight.w800, color: AppColors.teal700, fontSize: 12.5)),
                ),
              if (booking.status == BookingStatus.completed)
                Padding(
                  padding: const EdgeInsets.only(top: 10),
                  child: SizedBox(
                    width: double.infinity,
                    child: OutlinedButton(
                      onPressed: () async {
                        final nurseName = await ref.read(nurseDetailProvider(booking.nurseId).future).then(
                              (n) => n.fullName,
                              onError: (_) => '',
                            );
                        if (!context.mounted) return;
                        final done = await Navigator.of(context).push<bool>(
                          MaterialPageRoute(
                            builder: (_) => LeaveReviewScreen(bookingId: booking.id, nurseName: nurseName),
                          ),
                        );
                        if (done == true) ref.invalidate(_bookingsProvider);
                      },
                      child: Text(t.leaveReview),
                    ),
                  ),
                ),
            ],
          ),
        ),
      ),
    );
  }
}

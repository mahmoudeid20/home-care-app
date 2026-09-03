import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../core/api_exception.dart';
import '../theme/app_theme.dart';
import '../l10n/app_localizations.dart';
import '../widgets/nurse_card.dart';
import '../widgets/nurse_summary.dart';
import '../widgets/error_message.dart';
import '../services/nurse_api.dart';
import '../state/auth_controller.dart';
import 'nurse_detail_screen.dart';
import 'care_request/care_request_form_screen.dart';
import 'support_screen.dart';

final _searchQueryProvider = StateProvider<String>((ref) => '');
final _selectedSpecialtyFilterProvider = StateProvider<String>((ref) => '');

final _rawNursesProvider = FutureProvider<List<NurseSummary>>((ref) async {
  return NurseApi().search();
});

final _nurseSearchProvider = Provider<AsyncValue<List<NurseSummary>>>((ref) {
  final query = ref.watch(_searchQueryProvider).trim().toLowerCase();
  final specialtyFilter = ref.watch(_selectedSpecialtyFilterProvider);
  final rawAsync = ref.watch(_rawNursesProvider);

  return rawAsync.whenData((nurses) {
    return nurses.where((n) {
      // Search query filter
      final name = n.fullName.toLowerCase();
      final title = n.professionalTitle?.toLowerCase() ?? '';
      final matchesQuery = query.isEmpty || name.contains(query) || title.contains(query);

      // Specialty filter
      final matchesSpecialty = specialtyFilter.isEmpty ||
          specialtyFilter == 'الكل' ||
          (n.professionalTitle?.contains(specialtyFilter) ?? false) ||
          name.contains(specialtyFilter);

      return matchesQuery && matchesSpecialty;
    }).toList();
  });
});

class HomeScreen extends ConsumerStatefulWidget {
  const HomeScreen({super.key});

  @override
  ConsumerState<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends ConsumerState<HomeScreen> {
  final _searchCtrl = TextEditingController();

  final List<String> _specialties = [
    'الكل',
    'تمريض عام',
    'رعاية كبار السن',
    'رعاية ما بعد الجراحة',
    'رعاية الجروح',
    'رعاية الأمراض المزمنة',
  ];

  @override
  void dispose() {
    _searchCtrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final t = AppLocalizations.of(context)!;
    final auth = ref.watch(authControllerProvider);
    final nursesAsync = ref.watch(_nurseSearchProvider);
    final selectedSpecialty = ref.watch(_selectedSpecialtyFilterProvider);

    final displayName = auth.patientProfile?.fullName.isNotEmpty == true
        ? auth.patientProfile!.fullName.split(' ').first
        : (auth.user?.username ?? auth.user?.email.split('@').first ?? '');

    final userLocation = auth.patientProfile?.governorate != null
        ? '${auth.patientProfile!.governorate} • ${auth.patientProfile!.city ?? ""}'
        : 'مصر';

    return RefreshIndicator(
      color: AppColors.primary,
      onRefresh: () async => ref.invalidate(_rawNursesProvider),
      child: CustomScrollView(
        slivers: [
          // Top Bar & Welcome Header
          SliverToBoxAdapter(
            child: Container(
              padding: const EdgeInsets.fromLTRB(20, 16, 20, 20),
              decoration: BoxDecoration(
                color: AppColors.surfaceOf(context),
                borderRadius: const BorderRadius.only(
                  bottomLeft: Radius.circular(24),
                  bottomRight: Radius.circular(24),
                ),
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withOpacity(AppColors.isDark(context) ? 0.2 : 0.04),
                    blurRadius: 10,
                    offset: const Offset(0, 4),
                  ),
                ],
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // User greeting & Location pill
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            'أهلاً بك، $displayName 👋',
                            style: TextStyle(
                              fontSize: 20,
                              fontWeight: FontWeight.w900,
                              color: AppColors.inkOf(context),
                            ),
                          ),
                          const SizedBox(height: 3),
                          Row(
                            children: [
                              const Icon(Icons.location_on_rounded, size: 14, color: AppColors.primary),
                              const SizedBox(width: 4),
                              Text(
                                userLocation,
                                style: TextStyle(
                                  fontSize: 12.5,
                                  color: AppColors.inkSoftOf(context),
                                  fontWeight: FontWeight.w600,
                                ),
                              ),
                            ],
                          ),
                        ],
                      ),
                      // Support Quick Icon
                      IconButton(
                        onPressed: () {
                          Navigator.of(context).push(
                            MaterialPageRoute(builder: (_) => const SupportScreen()),
                          );
                        },
                        style: IconButton.styleFrom(
                          backgroundColor: AppColors.isDark(context)
                              ? AppColors.bgOf(context)
                              : AppColors.primarySurface,
                        ),
                        icon: const Icon(Icons.headset_mic_rounded, color: AppColors.primary, size: 22),
                      ),
                    ],
                  ),
                  const SizedBox(height: 16),

                  // Search Bar
                  Container(
                    decoration: BoxDecoration(
                      color: AppColors.bgOf(context),
                      borderRadius: BorderRadius.circular(AppRadius.md),
                      border: Border.all(color: AppColors.lineOf(context)),
                    ),
                    child: TextField(
                      controller: _searchCtrl,
                      style: TextStyle(color: AppColors.inkOf(context)),
                      decoration: InputDecoration(
                        hintText: 'ابحث باسم الممرض، التخصص، أو الخدمة…',
                        hintStyle: TextStyle(fontSize: 13.5, color: AppColors.inkSoftOf(context)),
                        prefixIcon: const Icon(Icons.search_rounded, color: AppColors.primary, size: 22),
                        suffixIcon: _searchCtrl.text.isNotEmpty
                            ? IconButton(
                                icon: const Icon(Icons.clear_rounded, size: 18, color: AppColors.inkSoft),
                                onPressed: () {
                                  _searchCtrl.clear();
                                  ref.read(_searchQueryProvider.notifier).state = '';
                                  setState(() {});
                                },
                              )
                            : null,
                        border: InputBorder.none,
                        enabledBorder: InputBorder.none,
                        focusedBorder: InputBorder.none,
                        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
                      ),
                      onChanged: (value) {
                        ref.read(_searchQueryProvider.notifier).state = value;
                        setState(() {});
                      },
                    ),
                  ),
                ],
              ),
            ),
          ),

          // Quick Action Cards
          SliverToBoxAdapter(
            child: Padding(
              padding: const EdgeInsets.fromLTRB(20, 20, 20, 10),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'الخدمات السريعة',
                    style: TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.w800,
                      color: AppColors.inkOf(context),
                    ),
                  ),
                  const SizedBox(height: 12),
                  Row(
                    children: [
                      Expanded(
                        child: _QuickActionCard(
                          title: 'طلب تمريض جديد',
                          subtitle: 'حدد موعدك والخدمة',
                          icon: Icons.add_circle_outline_rounded,
                          color: AppColors.primary,
                          onTap: () {
                            Navigator.of(context).push(
                              MaterialPageRoute(builder: (_) => const CareRequestFormScreen()),
                            );
                          },
                        ),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: _QuickActionCard(
                          title: 'الدعم والمساعدة',
                          subtitle: 'تواصل فوري 24/7',
                          icon: Icons.support_agent_rounded,
                          color: AppColors.accent,
                          onTap: () {
                            Navigator.of(context).push(
                              MaterialPageRoute(builder: (_) => const SupportScreen()),
                            );
                          },
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ),

          // Horizontal Specialties Filter
          SliverToBoxAdapter(
            child: Padding(
              padding: const EdgeInsets.fromLTRB(0, 14, 0, 10),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 20),
                    child: Text(
                      'التخصصات التمريضية',
                      style: TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.w800,
                        color: AppColors.inkOf(context),
                      ),
                    ),
                  ),
                  const SizedBox(height: 10),
                  SizedBox(
                    height: 42,
                    child: ListView.builder(
                      scrollDirection: Axis.horizontal,
                      padding: const EdgeInsets.symmetric(horizontal: 16),
                      itemCount: _specialties.length,
                      itemBuilder: (context, idx) {
                        final spec = _specialties[idx];
                        final isSelected = selectedSpecialty == spec ||
                            (selectedSpecialty.isEmpty && spec == 'الكل');
                        return Padding(
                          padding: const EdgeInsets.symmetric(horizontal: 4),
                          child: FilterChip(
                            label: Text(spec),
                            selected: isSelected,
                            selectedColor: AppColors.primary,
                            checkmarkColor: Colors.white,
                            backgroundColor: AppColors.surfaceOf(context),
                            side: BorderSide(
                              color: isSelected ? AppColors.primary : AppColors.lineOf(context),
                            ),
                            labelStyle: TextStyle(
                              color: isSelected ? Colors.white : AppColors.inkOf(context),
                              fontWeight: isSelected ? FontWeight.bold : FontWeight.w500,
                              fontSize: 12.5,
                            ),
                            onSelected: (selected) {
                              ref.read(_selectedSpecialtyFilterProvider.notifier).state =
                                  spec == 'الكل' ? '' : spec;
                            },
                          ),
                        );
                      },
                    ),
                  ),
                ],
              ),
            ),
          ),

          // Recommended Nurses Section Header
          SliverToBoxAdapter(
            child: Padding(
              padding: const EdgeInsets.fromLTRB(20, 16, 20, 12),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'ترشيحات مقترحة لك',
                        style: TextStyle(
                          fontSize: 16.5,
                          fontWeight: FontWeight.w800,
                          color: AppColors.inkOf(context),
                        ),
                      ),
                      SizedBox(height: 2),
                      Text(
                        'ممرضون معتمدون وموثقون بالقرب منك',
                        style: TextStyle(fontSize: 12, color: AppColors.inkSoft),
                      ),
                    ],
                  ),
                  TextButton(
                    onPressed: () {
                      _searchCtrl.clear();
                      ref.read(_searchQueryProvider.notifier).state = '';
                      ref.read(_selectedSpecialtyFilterProvider.notifier).state = '';
                    },
                    child: const Text(
                      'عرض الكل',
                      style: TextStyle(
                        color: AppColors.primary,
                        fontWeight: FontWeight.w700,
                        fontSize: 13,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),

          // Nurses List / State
          nursesAsync.when(
            loading: () => const SliverFillRemaining(
              hasScrollBody: false,
              child: Center(
                child: Padding(
                  padding: EdgeInsets.all(40),
                  child: CircularProgressIndicator(color: AppColors.primary),
                ),
              ),
            ),
            error: (err, _) => SliverFillRemaining(
              hasScrollBody: false,
              child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: 20),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    ErrorMessage(
                      message: err is ApiException ? friendlyErrorMessage(err, t) : t.somethingWentWrong,
                    ),
                    const SizedBox(height: 12),
                    OutlinedButton(
                      onPressed: () => ref.invalidate(_nurseSearchProvider),
                      child: Text(t.retry),
                    ),
                  ],
                ),
              ),
            ),
            data: (nurses) {
              if (nurses.isEmpty) {
                return SliverFillRemaining(
                  hasScrollBody: false,
                  child: Center(
                    child: Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 40),
                      child: Column(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Icon(
                            Icons.person_search_rounded,
                            size: 64,
                            color: AppColors.inkSoft.withOpacity(0.5),
                          ),
                          const SizedBox(height: 12),
                          Text(
                            t.noNursesFound,
                            textAlign: TextAlign.center,
                            style: const TextStyle(
                              fontSize: 14,
                              fontWeight: FontWeight.w600,
                              color: AppColors.inkSoft,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                );
              }
              return SliverPadding(
                padding: const EdgeInsets.symmetric(horizontal: 20),
                sliver: SliverList.builder(
                  itemCount: nurses.length,
                  itemBuilder: (_, i) => NurseCard(
                    nurse: nurses[i],
                    onTap: () {
                      Navigator.of(context).push(
                        MaterialPageRoute(
                          builder: (_) => NurseDetailScreen(nurseId: nurses[i].id),
                        ),
                      );
                    },
                  ),
                ),
              );
            },
          ),
          const SliverToBoxAdapter(child: SizedBox(height: 32)),
        ],
      ),
    );
  }
}

class _QuickActionCard extends StatelessWidget {
  final String title;
  final String subtitle;
  final IconData icon;
  final Color color;
  final VoidCallback onTap;

  const _QuickActionCard({
    required this.title,
    required this.subtitle,
    required this.icon,
    required this.color,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: AppColors.surfaceOf(context),
        borderRadius: BorderRadius.circular(AppRadius.md),
        border: Border.all(color: AppColors.lineOf(context)),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(AppColors.isDark(context) ? 0.2 : 0.02),
            blurRadius: 8,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Material(
        color: Colors.transparent,
        borderRadius: BorderRadius.circular(AppRadius.md),
        child: InkWell(
          borderRadius: BorderRadius.circular(AppRadius.md),
          onTap: onTap,
          child: Padding(
            padding: const EdgeInsets.all(14),
            child: Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(10),
                  decoration: BoxDecoration(
                    color: color.withOpacity(0.12),
                    borderRadius: BorderRadius.circular(AppRadius.sm),
                  ),
                  child: Icon(icon, color: color, size: 24),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        title,
                        style: TextStyle(
                          fontWeight: FontWeight.bold,
                          fontSize: 13.5,
                          color: AppColors.inkOf(context),
                        ),
                      ),
                      const SizedBox(height: 2),
                      Text(
                        subtitle,
                        style: TextStyle(fontSize: 11, color: AppColors.inkSoftOf(context)),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

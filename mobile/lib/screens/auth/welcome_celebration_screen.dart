import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

import '../../theme/app_theme.dart';

class WelcomeCelebrationScreen extends StatelessWidget {
  final String userName;
  final bool isNurse;
  final VoidCallback onStart;

  const WelcomeCelebrationScreen({
    super.key,
    required this.userName,
    required this.isNurse,
    required this.onStart,
  });

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.bgOf(context),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 28, vertical: 24),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Spacer(),

              // Animated celebration icon
              Container(
                width: 120,
                height: 120,
                decoration: BoxDecoration(
                  gradient: const LinearGradient(
                    colors: [AppColors.primary, AppColors.accent],
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                  ),
                  shape: BoxShape.circle,
                  boxShadow: [
                    BoxShadow(
                      color: AppColors.primary.withOpacity(0.35),
                      blurRadius: 24,
                      offset: const Offset(0, 10),
                    ),
                  ],
                ),
                child: const Center(
                  child: Icon(Icons.verified, color: Colors.white, size: 64),
                ),
              ),
              const SizedBox(height: 32),

              // Welcome header
              Text(
                'أهلاً بك يا دكتور / أستاذ',
                style: GoogleFonts.cairo(
                  fontSize: 16,
                  color: AppColors.inkSoftOf(context),
                ),
              ),
              const SizedBox(height: 4),
              Text(
                userName,
                textAlign: TextAlign.center,
                style: GoogleFonts.cairo(
                  fontSize: 24,
                  fontWeight: FontWeight.bold,
                  color: AppColors.primary,
                ),
              ),
              const SizedBox(height: 8),

              Container(
                padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 6),
                decoration: BoxDecoration(
                  color: AppColors.success.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(20),
                  border: Border.all(color: AppColors.success.withOpacity(0.3)),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    const Icon(Icons.check_circle, color: AppColors.success, size: 16),
                    const SizedBox(width: 6),
                    Text(
                      'تم اكتمال توثيق الهوية والبيانات بنجاح',
                      style: GoogleFonts.cairo(
                        fontSize: 12,
                        fontWeight: FontWeight.bold,
                        color: AppColors.success,
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 24),

              // Info card
              Container(
                padding: const EdgeInsets.all(18),
                decoration: BoxDecoration(
                  color: AppColors.surfaceOf(context),
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(color: AppColors.lineOf(context)),
                ),
                child: Text(
                  isNurse
                      ? 'تم حفظ مستنداتك وتراخيصك بنجاح. سيقوم الفريق الطبي بمراجعة التراخيص لمنحك شارة "ممرض معتمد". يمكنك الآن تصفح المنصة وإعداد مواعيدك وخدماتك.'
                      : 'أصبح حسابك جاهزاً وموثقاً بالكامل! يمكنك الآن استكشاف أمهر الممرضين والممرضات المعتمدين في منطقتك وحجز الرعاية الطبية المنزلية بكل أمان وسهولة.',
                  textAlign: TextAlign.center,
                  style: GoogleFonts.cairo(
                    fontSize: 13.5,
                    color: AppColors.inkOf(context),
                    height: 1.65,
                  ),
                ),
              ),

              const Spacer(),

              // Start button
              SizedBox(
                width: double.infinity,
                height: 54,
                child: ElevatedButton(
                  onPressed: onStart,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: AppColors.primary,
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(16),
                    ),
                    elevation: 4,
                  ),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Text(
                        'ابدأ استخدام سَنَد الآن',
                        style: GoogleFonts.cairo(
                          fontSize: 16,
                          fontWeight: FontWeight.bold,
                          color: Colors.white,
                        ),
                      ),
                      const SizedBox(width: 8),
                      const Icon(Icons.arrow_back, color: Colors.white, size: 20),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 16),
            ],
          ),
        ),
      ),
    );
  }
}

import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

import '../../services/otp_api.dart';
import '../../theme/app_theme.dart';

class TermsAgreementScreen extends StatefulWidget {
  final bool isNurse;
  final VoidCallback onAccepted;

  const TermsAgreementScreen({
    super.key,
    required this.isNurse,
    required this.onAccepted,
  });

  @override
  State<TermsAgreementScreen> createState() => _TermsAgreementScreenState();
}

class _TermsAgreementScreenState extends State<TermsAgreementScreen> {
  final OtpApi _otpApi = OtpApi();
  bool _agreedToTerms = false;
  bool _agreedToMedicalEthics = false;
  bool _isSubmitting = false;

  Future<void> _submit() async {
    if (!_agreedToTerms || !_agreedToMedicalEthics) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('يرجى الموافقة على جميع الشروط وسياسة الخصوصية للمتابعة'),
          backgroundColor: AppColors.danger,
        ),
      );
      return;
    }

    setState(() => _isSubmitting = true);
    try {
      await _otpApi.acceptTerms();
      widget.onAccepted();
    } catch (_) {
      // Continue even if local dev fails
      widget.onAccepted();
    } finally {
      if (mounted) setState(() => _isSubmitting = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.bgOf(context),
      appBar: AppBar(
        title: const Text('الشروط وسياسة الخصوصية / Terms'),
        elevation: 0,
        backgroundColor: AppColors.surfaceOf(context),
      ),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
                // Top header
                Row(
                  children: [
                    Container(
                      padding: const EdgeInsets.all(10),
                      decoration: BoxDecoration(
                        color: AppColors.primary.withOpacity(0.1),
                        shape: BoxShape.circle,
                      ),
                      child: const Icon(Icons.gavel_outlined, color: AppColors.primary, size: 28),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            'ميثاق Home Care الطبي المعتمد 2026',
                            style: GoogleFonts.cairo(
                              fontSize: 16,
                              fontWeight: FontWeight.bold,
                              color: AppColors.inkOf(context),
                            ),
                          ),
                          Text(
                            'معايير الحماية والسرية الطبية المعتمدة في جمهورية مصر العربية',
                            style: GoogleFonts.cairo(fontSize: 12, color: AppColors.inkSoftOf(context)),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 16),

                // Policy content container
                Expanded(
                  child: Container(
                    padding: const EdgeInsets.all(16),
                    decoration: BoxDecoration(
                      color: AppColors.surfaceOf(context),
                      borderRadius: BorderRadius.circular(16),
                      border: Border.all(color: AppColors.lineOf(context)),
                    ),
                    child: SingleChildScrollView(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          _buildSectionTitle('1. سرية وأمان البيانات الطبية'),
                          _buildSectionBody(
                            'يلتزم تطبيق "Home Care" بأعلى معايير التشفير والحماية لبيانات المرضى والممرضين وفقاً لقانون حماية البيانات الشخصية المصري. لا يتم مشاركة السجلات الطبية أو العناوين إلا مع أطراف الخدمة المصرح لهم أثناء الحجز فقط.',
                          ),
                          const SizedBox(height: 14),

                          _buildSectionTitle('2. إخلاء المسؤولية للحالات الطارئة'),
                          _buildSectionBody(
                            'تطبيق "Home Care" مخصص لخدمات الرعاية والتمريض المنزلي المجدولة وغير الطارئة. في حال وجود حالات حرجة أو طوارئ تستدعي التدخل الفوري، يجب الاتصال بالإسعاف المصري (123) مباشرة أو التوجه لأقرب مستشفى طوارئ.',
                          ),
                          const SizedBox(height: 14),

                          _buildSectionTitle(widget.isNurse ? '3. ميثاق شرف وأخلاقيات التمريض' : '3. حقوق والتزامات المستفيد'),
                          _buildSectionBody(
                            widget.isNurse
                                ? 'يلتزم الممرض/ة بتقديم الرعاية بأعلى درجات المهنية والأمانة وفق تراخيص وزارة الصحة ونقابة التمريض المصرية، والالتزام بالمواعيد والمحافظة على أسرار المريض ومقر إقامته.'
                                : 'يلتزم العميل بتوفير بيئة آمنة للممرض/ة أثناء تقديم الخدمة، وتوضيح التاريخ المرضي والدوائي بدقة لضمان سلامة تقديم الرعاية الطبية.',
                          ),
                          const SizedBox(height: 14),

                          _buildSectionTitle('4. سياسة الدفع والإلغاء'),
                          _buildSectionBody(
                            'تتم التسويات المالية وفق الأسعار المحددة في التطبيق بشفافية كاملة. يحق للطرفين الإلغاء قبل موعد الزيارة وفق سياسة الإلغاء المعتمدة المعلنة في المنصة.',
                          ),
                        ],
                      ),
                    ),
                  ),
                ),

                const SizedBox(height: 16),

                // Checkbox 1
                CheckboxListTile(
                  value: _agreedToTerms,
                  onChanged: (val) => setState(() => _agreedToTerms = val ?? false),
                  title: Text(
                    'أوافق على الشروط والأحكام وسياسة الخصوصية لمنصة Home Care',
                    style: GoogleFonts.cairo(fontSize: 13, fontWeight: FontWeight.bold),
                  ),
                  controlAffinity: ListTileControlAffinity.leading,
                  activeColor: AppColors.primary,
                  contentPadding: EdgeInsets.zero,
                ),

                // Checkbox 2
                CheckboxListTile(
                  value: _agreedToMedicalEthics,
                  onChanged: (val) => setState(() => _agreedToMedicalEthics = val ?? false),
                  title: Text(
                    'أقر بالالتزام بالميثاق الطبي وحماية سرية بيانات الرعاية الصحية 2026',
                    style: GoogleFonts.cairo(fontSize: 13, fontWeight: FontWeight.bold),
                  ),
                  controlAffinity: ListTileControlAffinity.leading,
                  activeColor: AppColors.primary,
                  contentPadding: EdgeInsets.zero,
                ),

                const SizedBox(height: 16),

                // Accept Button
                SizedBox(
                  width: double.infinity,
                  height: 52,
                  child: ElevatedButton(
                    onPressed: _isSubmitting ? null : _submit,
                    style: ElevatedButton.styleFrom(
                      backgroundColor: AppColors.primary,
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
                    ),
                    child: _isSubmitting
                        ? const SizedBox(width: 24, height: 24, child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2))
                        : Text(
                            'الموافقة والمتابعة',
                            style: GoogleFonts.cairo(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.white),
                          ),
                  ),
                ),
                const SizedBox(height: 10),
              ],
            ),
          ),
        ),
      );
  }

  Widget _buildSectionTitle(String title) {
    return Text(
      title,
      style: GoogleFonts.cairo(
        fontSize: 14,
        fontWeight: FontWeight.bold,
        color: AppColors.primary,
      ),
    );
  }

  Widget _buildSectionBody(String text) {
    return Padding(
      padding: const EdgeInsets.only(top: 4),
      child: Text(
        text,
        style: GoogleFonts.cairo(
          fontSize: 12.5,
          color: AppColors.inkOf(context),
          height: 1.6,
        ),
      ),
    );
  }
}

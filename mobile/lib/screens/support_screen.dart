import 'package:flutter/material.dart';
import 'package:dio/dio.dart';
import '../core/api_client.dart';
import '../theme/app_theme.dart';
import '../widgets/error_message.dart';

class SupportScreen extends StatefulWidget {
  const SupportScreen({super.key});

  @override
  State<SupportScreen> createState() => _SupportScreenState();
}

class _SupportScreenState extends State<SupportScreen> {
  final _complaintCtrl = TextEditingController();
  String _category = 'استفسار عام';
  bool _sending = false;
  bool _sentSuccess = false;
  String? _error;

  final List<String> _categories = [
    'استفسار عام',
    'شكوى بخصوص ممرض',
    'مشكلة في الحجز',
    'مشكلة فنية في التطبيق',
    'اقتراح لتطوير الخدمة',
  ];

  final List<Map<String, String>> _faqs = [
    {
      'q': 'كيف يتم التحقق من موثوقية الممرضين في Home Care؟',
      'a': 'يخضع جميع الممرضين والممرضات لمراجعة دقيقة لبطاقة الرقم القومي، شهادة التخرج، ترخيص مزاولة المهنة المعتمد من وزارة الصحة ونقابة التمريض المصرية، بالإضافة لشهادات الخبرة.',
    },
    {
      'q': 'ما هي المحافظات المتاحة حالياً للخدمة؟',
      'a': 'تطبيق Home Care مخصص لجمهورية مصر العربية ويوفر تغطية في كافة محافظات مصر وعلى رأسها القاهرة، الجيزة، الإسكندرية، ومحافظات الدلتا والصعيد.',
    },
    {
      'q': 'هل يمكن إلغاء الحجز أو تعديل موعده؟',
      'a': 'نعم، يمكنك إلغاء الحجز من شاشة الحجوزات قبل بدء تقديم الخدمة أو التواصل مباشرة مع الممرض عبر الدردشة لتنسيق المواعيد.',
    },
    {
      'q': 'ما هي طرق الدفع المتاحة؟',
      'a': 'تتيح منصة Home Care الدفع النقدي المباشر بعد انتهاء الخدمة، بالإضافة للمحافظ الإلكترونية (فودافون كاش وغيرها) والبطاقات البنكية.',
    },
    {
      'q': 'ماذا أفعل في الحالات الطارئة؟',
      'a': 'خدمات Home Care مخصصة للرعاية المنزلية والتمريضية غير الطارئة. في الحالات الحرجة أو الطوارئ الطبية العاجلة، يُرجى الاتصال فوراً بهيئة الإسعاف المصرية على الرقم 123.',
    },
  ];

  @override
  void dispose() {
    _complaintCtrl.dispose();
    super.dispose();
  }

  Future<void> _submitComplaint() async {
    final text = _complaintCtrl.text.trim();
    if (text.isEmpty) {
      setState(() => _error = 'من فضلك اكتب تفاصيل الرسالة أو الشكوى');
      return;
    }

    setState(() {
      _sending = true;
      _error = null;
    });

    try {
      final dio = ApiClient.instance.dio;
      await dio.post('/complaints', data: {
        'category': _category,
        'description': text,
        'attachments': [],
      });

      setState(() {
        _sentSuccess = true;
        _complaintCtrl.clear();
      });
    } on DioException catch (e) {
      setState(() => _error = e.response?.data?['error']?['message'] ?? 'تعذر إرسال الرسالة، حاول مرة أخرى');
    } catch (_) {
      setState(() => _error = 'حصل خطأ أثناء الإرسال');
    } finally {
      if (mounted) setState(() => _sending = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.bg,
      appBar: AppBar(
        title: const Text('الدعم والمساعدة'),
        elevation: 0,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Header Banner
            Container(
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                gradient: const LinearGradient(
                  colors: [AppColors.primaryDark, AppColors.primary],
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                ),
                borderRadius: BorderRadius.circular(AppRadius.lg),
                boxShadow: [
                  BoxShadow(
                    color: AppColors.primary.withOpacity(0.25),
                    blurRadius: 16,
                    offset: const Offset(0, 6),
                  ),
                ],
              ),
              child: Row(
                children: [
                  Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: Colors.white.withOpacity(0.18),
                      shape: BoxShape.circle,
                    ),
                    child: const Icon(Icons.headset_mic_rounded, color: Colors.white, size: 36),
                  ),
                  const SizedBox(width: 16),
                  const Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'فريق خدمة عملاء Home Care',
                          style: TextStyle(
                            color: Colors.white,
                            fontSize: 17,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        SizedBox(height: 4),
                        Text(
                          'نحن هنا لمساعدتك على مدار الساعة لضمان أفضل رعاية طبية لأحبائك.',
                          style: TextStyle(color: Colors.white70, fontSize: 12.5),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 20),

            // Contact Channels
            Row(
              children: [
                Expanded(
                  child: _ContactBox(
                    icon: Icons.chat_rounded,
                    label: 'واتساب',
                    sub: '01012345678',
                    color: const Color(0xFF25D366),
                    onTap: () {
                      ScaffoldMessenger.of(context).showSnackBar(
                        const SnackBar(content: Text('خدمة واتساب: 01012345678')),
                      );
                    },
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: _ContactBox(
                    icon: Icons.phone_in_talk_rounded,
                    label: 'اتصال هاتفي',
                    sub: '19000 (مصر)',
                    color: AppColors.primary,
                    onTap: () {
                      ScaffoldMessenger.of(context).showSnackBar(
                        const SnackBar(content: Text('الخط الساخن: 19000')),
                      );
                    },
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: _ContactBox(
                    icon: Icons.mail_outline_rounded,
                    label: 'البريد',
                    sub: 'support@sanad.care',
                    color: AppColors.accent,
                    onTap: () {
                      ScaffoldMessenger.of(context).showSnackBar(
                        const SnackBar(content: Text('البريد: support@sanad.care')),
                      );
                    },
                  ),
                ),
              ],
            ),
            const SizedBox(height: 28),

            // Submit Complaint Form
            Container(
              padding: const EdgeInsets.all(18),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(AppRadius.md),
                border: Border.all(color: AppColors.line),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    'تقديم شكوى أو استفسار',
                    style: TextStyle(fontWeight: FontWeight.w800, fontSize: 16, color: AppColors.ink),
                  ),
                  const SizedBox(height: 4),
                  const Text(
                    'سيتم مراجعة طلبك والرد عليك من قبل إدارة المنصة في أقرب وقت.',
                    style: TextStyle(fontSize: 12.5, color: AppColors.inkSoft),
                  ),
                  const SizedBox(height: 16),

                  if (_sentSuccess) ...[
                    Container(
                      padding: const EdgeInsets.all(14),
                      decoration: BoxDecoration(
                        color: AppColors.successLight,
                        borderRadius: BorderRadius.circular(AppRadius.sm),
                        border: Border.all(color: AppColors.success),
                      ),
                      child: const Row(
                        children: [
                          Icon(Icons.check_circle_rounded, color: AppColors.success, size: 22),
                          SizedBox(width: 10),
                          Expanded(
                            child: Text(
                              'تم إرسال رسالتك بنجاح وسيتواصل معك فريق الدعم قريباً.',
                              style: TextStyle(color: AppColors.success, fontWeight: FontWeight.bold, fontSize: 13),
                            ),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 14),
                  ],

                  if (_error != null) ...[
                    ErrorMessage(message: _error!),
                    const SizedBox(height: 12),
                  ],

                  // Category dropdown
                  DropdownButtonFormField<String>(
                    value: _category,
                    decoration: const InputDecoration(
                      labelText: 'نوع الطلب',
                      contentPadding: EdgeInsets.symmetric(horizontal: 14, vertical: 12),
                    ),
                    items: _categories.map((cat) {
                      return DropdownMenuItem(value: cat, child: Text(cat, style: const TextStyle(fontSize: 13.5)));
                    }).toList(),
                    onChanged: (val) => setState(() => _category = val!),
                  ),
                  const SizedBox(height: 14),

                  // Message text field
                  TextField(
                    controller: _complaintCtrl,
                    maxLines: 4,
                    decoration: const InputDecoration(
                      hintText: 'اكتب تفاصيل استفسارك أو شكواك هنا…',
                      alignLabelWithHint: true,
                    ),
                  ),
                  const SizedBox(height: 16),

                  ElevatedButton(
                    onPressed: _sending ? null : _submitComplaint,
                    style: ElevatedButton.styleFrom(
                      backgroundColor: AppColors.primary,
                      minimumSize: const Size.fromHeight(48),
                    ),
                    child: _sending
                        ? const SizedBox(
                            width: 20, height: 20,
                            child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2),
                          )
                        : const Text('إرسال الآن', style: TextStyle(fontWeight: FontWeight.bold)),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 28),

            // FAQ Section
            const Text(
              'الأسئلة الشائعة',
              style: TextStyle(fontWeight: FontWeight.w800, fontSize: 17, color: AppColors.ink),
            ),
            const SizedBox(height: 12),

            ..._faqs.map((faq) => Container(
                  margin: const EdgeInsets.only(bottom: 10),
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(AppRadius.md),
                    border: Border.all(color: AppColors.line),
                  ),
                  child: ExpansionTile(
                    shape: const Border(),
                    collapsedShape: const Border(),
                    title: Text(
                      faq['q']!,
                      style: const TextStyle(
                        fontWeight: FontWeight.w700,
                        fontSize: 14,
                        color: AppColors.ink,
                      ),
                    ),
                    children: [
                      Padding(
                        padding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
                        child: Text(
                          faq['a']!,
                          style: const TextStyle(fontSize: 13, color: AppColors.inkSoft, height: 1.5),
                        ),
                      ),
                    ],
                  ),
                )),
            const SizedBox(height: 24),
          ],
        ),
      ),
    );
  }
}

class _ContactBox extends StatelessWidget {
  final IconData icon;
  final String label;
  final String sub;
  final Color color;
  final VoidCallback onTap;

  const _ContactBox({
    required this.icon,
    required this.label,
    required this.sub,
    required this.color,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(AppRadius.md),
        border: Border.all(color: AppColors.line),
      ),
      child: Material(
        color: Colors.transparent,
        borderRadius: BorderRadius.circular(AppRadius.md),
        child: InkWell(
          borderRadius: BorderRadius.circular(AppRadius.md),
          onTap: onTap,
          child: Padding(
            padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 8),
            child: Column(
              children: [
                Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: color.withOpacity(0.12),
                    shape: BoxShape.circle,
                  ),
                  child: Icon(icon, color: color, size: 22),
                ),
                const SizedBox(height: 8),
                Text(
                  label,
                  style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: AppColors.ink),
                ),
                const SizedBox(height: 2),
                Text(
                  sub,
                  style: const TextStyle(fontSize: 10, color: AppColors.inkSoft),
                  overflow: TextOverflow.ellipsis,
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

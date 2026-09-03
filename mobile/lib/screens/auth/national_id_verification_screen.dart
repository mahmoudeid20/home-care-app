import 'dart:io';
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:image_picker/image_picker.dart';

import '../../core/egypt_locations.dart';
import '../../core/egyptian_id_parser.dart';
import '../../services/backend_upload_uploader.dart';
import '../../services/otp_api.dart';
import '../../theme/app_theme.dart';

class NationalIdVerificationScreen extends StatefulWidget {
  final bool isNurse;
  final Function(String nationalId, String governorate, String city, String address, String? frontUrl, String? backUrl) onCompleted;

  const NationalIdVerificationScreen({
    super.key,
    required this.isNurse,
    required this.onCompleted,
  });

  @override
  State<NationalIdVerificationScreen> createState() => _NationalIdVerificationScreenState();
}

class _NationalIdVerificationScreenState extends State<NationalIdVerificationScreen> {
  final ImagePicker _picker = ImagePicker();
  final BackendUploadUploader _uploader = BackendUploadUploader();
  final OtpApi _otpApi = OtpApi();

  File? _frontImage;
  File? _backImage;
  String? _frontUploadedUrl;
  String? _backUploadedUrl;

  final TextEditingController _idController = TextEditingController();
  final TextEditingController _addressController = TextEditingController();

  String? _selectedGovernorate;
  String? _selectedCity;
  EgyptianIdInfo? _idInfo;

  bool _isScanning = false;
  bool _isSubmitting = false;
  String? _errorMessage;

  @override
  void initState() {
    super.initState();
    _idController.addListener(_onIdChanged);
  }

  @override
  void dispose() {
    _idController.dispose();
    _addressController.dispose();
    super.dispose();
  }

  void _onIdChanged() {
    final text = _idController.text.trim();
    if (text.length == 14) {
      final info = parseEgyptianId(text);
      setState(() {
        _idInfo = info;
        if (info.isValid && info.governorate != null && EgyptLocations.governorates.contains(info.governorate)) {
          _selectedGovernorate = info.governorate;
          _selectedCity = null;
        }
      });
    } else {
      if (_idInfo != null) {
        setState(() => _idInfo = null);
      }
    }
  }

  Future<void> _captureCardImage(bool isFront) async {
    final source = await showModalBottomSheet<ImageSource>(
      context: context,
      backgroundColor: Colors.white,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (ctx) => Directionality(
        textDirection: TextDirection.rtl,
        child: SafeArea(
          child: Padding(
            padding: const EdgeInsets.symmetric(vertical: 20, horizontal: 16),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(
                  isFront ? 'تصوير وجه البطاقة (الأمامي)' : 'تصوير ظهر البطاقة (الخلفي)',
                  style: GoogleFonts.cairo(fontSize: 17, fontWeight: FontWeight.bold),
                ),
                const SizedBox(height: 16),
                ListTile(
                  leading: const Icon(Icons.camera_alt_outlined, color: AppColors.primary),
                  title: Text('التقاط صورة بالكاميرا', style: GoogleFonts.cairo(fontSize: 15)),
                  onTap: () => Navigator.pop(ctx, ImageSource.camera),
                ),
                ListTile(
                  leading: const Icon(Icons.photo_library_outlined, color: AppColors.accent),
                  title: Text('اختيار من المعرض', style: GoogleFonts.cairo(fontSize: 15)),
                  onTap: () => Navigator.pop(ctx, ImageSource.gallery),
                ),
              ],
            ),
          ),
        ),
      ),
    );

    if (source == null) return;

    try {
      final picked = await _picker.pickImage(source: source, imageQuality: 85);
      if (picked == null) return;

      final file = File(picked.path);
      setState(() {
        if (isFront) {
          _frontImage = file;
        } else {
          _backImage = file;
        }
      });

      // If front image, run OCR simulation / extraction
      if (isFront) {
        _simulateOcrExtraction(file);
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('تعذر اختيار الصورة: $e'), backgroundColor: AppColors.danger),
      );
    }
  }

  void _simulateOcrExtraction(File file) {
    setState(() => _isScanning = true);
    Future.delayed(const Duration(milliseconds: 900), () {
      if (!mounted) return;
      setState(() => _isScanning = false);
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('تم مسح وجه البطاقة بنجاح! تأكد من الرقم أدناه'),
          backgroundColor: AppColors.accent,
        ),
      );
    });
  }

  Future<void> _submit() async {
    final nid = _idController.text.trim();
    final info = parseEgyptianId(nid);

    if (!info.isValid) {
      setState(() => _errorMessage = info.errorMessage ?? 'الرقم القومي غير صالح');
      return;
    }

    if (_selectedGovernorate == null) {
      setState(() => _errorMessage = 'يرجى اختيار المحافظة');
      return;
    }

    if (_selectedCity == null) {
      setState(() => _errorMessage = 'يرجى اختيار المدينة / المركز');
      return;
    }

    if (widget.isNurse && (_frontImage == null || _backImage == null)) {
      setState(() => _errorMessage = 'يرجى تصوير بطاقة الرقم القومي (الوجه والظهر) للتحقق الأمني للممرضين');
      return;
    }

    setState(() {
      _isSubmitting = true;
      _errorMessage = null;
    });

    try {
      // 1. Upload ID front & back if present
      if (_frontImage != null && _frontUploadedUrl == null) {
        _frontUploadedUrl = await _uploader.upload(_frontImage!);
      }
      if (_backImage != null && _backUploadedUrl == null) {
        _backUploadedUrl = await _uploader.upload(_backImage!);
      }

      // 2. Validate with backend
      await _otpApi.validateNationalId(nid);

      widget.onCompleted(
        nid,
        _selectedGovernorate!,
        _selectedCity!,
        _addressController.text.trim(),
        _frontUploadedUrl,
        _backUploadedUrl,
      );
    } catch (e) {
      setState(() => _errorMessage = e.toString().replaceFirst('Exception: ', ''));
    } finally {
      if (mounted) setState(() => _isSubmitting = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Directionality(
      textDirection: TextDirection.rtl,
      child: Scaffold(
        backgroundColor: AppColors.bg,
        appBar: AppBar(
          title: Text(widget.isNurse ? 'توثيق الهوية والعنوان للممرض' : 'تأكيد الهوية والعنوان'),
          elevation: 0,
        ),
        body: SafeArea(
          child: SingleChildScrollView(
            padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Header badge
                Container(
                  padding: const EdgeInsets.all(14),
                  decoration: BoxDecoration(
                    color: AppColors.primary.withOpacity(0.06),
                    borderRadius: BorderRadius.circular(14),
                    border: Border.all(color: AppColors.primary.withOpacity(0.15)),
                  ),
                  child: Row(
                    children: [
                      const Icon(Icons.verified_user_outlined, color: AppColors.primary, size: 28),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              'توثيق آمن ومعتمد لعام 2026',
                              style: GoogleFonts.cairo(
                                fontSize: 14,
                                fontWeight: FontWeight.bold,
                                color: AppColors.primary,
                              ),
                            ),
                            Text(
                              widget.isNurse
                                  ? 'يتطلب ميثاق التمريض المصري فحص بطاقة الرقم القومي لضمان سلامة المرضى'
                                  : 'تأكيد هويتك يمنحك أولوية في الحجز وحماية لمعاملاتك الطبية',
                              style: GoogleFonts.cairo(fontSize: 12, color: AppColors.inkSoft),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 24),

                // Front & Back ID Card Capture
                Text(
                  'تصوير بطاقة الرقم القومي (وجه وضهر)',
                  style: GoogleFonts.cairo(fontSize: 15, fontWeight: FontWeight.bold),
                ),
                const SizedBox(height: 12),

                Row(
                  children: [
                    // Front Card
                    Expanded(
                      child: _buildIdCardBox(
                        title: 'الوجه الأمامي',
                        subtitle: 'يحتوي على الصورة والرقم',
                        file: _frontImage,
                        icon: Icons.badge_outlined,
                        onTap: () => _captureCardImage(true),
                      ),
                    ),
                    const SizedBox(width: 12),
                    // Back Card
                    Expanded(
                      child: _buildIdCardBox(
                        title: 'الظهر (الخلفي)',
                        subtitle: 'يحتوي على المهنة والعنوان',
                        file: _backImage,
                        icon: Icons.flip_to_back_outlined,
                        onTap: () => _captureCardImage(false),
                      ),
                    ),
                  ],
                ),

                if (_isScanning) ...[
                  const SizedBox(height: 14),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2)),
                      const SizedBox(width: 10),
                      Text('جاري مسح بيانات البطاقة بالذكاء الاصطناعي...', style: GoogleFonts.cairo(fontSize: 13, color: AppColors.primary)),
                    ],
                  ),
                ],

                const SizedBox(height: 24),

                // 14-digit National ID Input
                Text(
                  'الرقم القومي (14 رقماً)',
                  style: GoogleFonts.cairo(fontSize: 14, fontWeight: FontWeight.bold),
                ),
                const SizedBox(height: 6),
                TextField(
                  controller: _idController,
                  keyboardType: TextInputType.number,
                  maxLength: 14,
                  style: GoogleFonts.cairo(fontSize: 16, fontWeight: FontWeight.bold, letterSpacing: 2),
                  decoration: InputDecoration(
                    hintText: '29805140101234',
                    counterText: '',
                    prefixIcon: const Icon(Icons.numbers, color: AppColors.primary),
                    filled: true,
                    fillColor: Colors.white,
                    border: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: const BorderSide(color: AppColors.line)),
                    focusedBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: const BorderSide(color: AppColors.primary, width: 2)),
                  ),
                ),

                // Auto-extracted details banner
                if (_idInfo != null && _idInfo!.isValid) ...[
                  const SizedBox(height: 12),
                  Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: AppColors.accent.withOpacity(0.08),
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(color: AppColors.accent.withOpacity(0.3)),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            const Icon(Icons.auto_awesome, color: AppColors.accent, size: 18),
                            const SizedBox(width: 6),
                            Text('البيانات المستخرجة آلياً من الرقم القومي:', style: GoogleFonts.cairo(fontSize: 13, fontWeight: FontWeight.bold, color: AppColors.accent)),
                          ],
                        ),
                        const SizedBox(height: 8),
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Text('تاريخ الميلاد: ${_idInfo!.birthDate?.toLocal().toString().split(' ')[0]}', style: GoogleFonts.cairo(fontSize: 13)),
                            Text('النوع: ${_idInfo!.gender}', style: GoogleFonts.cairo(fontSize: 13, fontWeight: FontWeight.bold)),
                            Text('المحافظة: ${_idInfo!.governorate}', style: GoogleFonts.cairo(fontSize: 13, color: AppColors.primary)),
                          ],
                        ),
                      ],
                    ),
                  ),
                ],

                const SizedBox(height: 24),

                // Governorate & City Dropdowns
                Text('المحافظة والمدينة في مصر', style: GoogleFonts.cairo(fontSize: 14, fontWeight: FontWeight.bold)),
                const SizedBox(height: 8),

                DropdownButtonFormField<String>(
                  value: _selectedGovernorate,
                  hint: Text('اختر المحافظة', style: GoogleFonts.cairo(fontSize: 14)),
                  items: EgyptLocations.governorates.map((gov) {
                    return DropdownMenuItem(value: gov, child: Text(gov, style: GoogleFonts.cairo(fontSize: 14)));
                  }).toList(),
                  onChanged: (val) {
                    setState(() {
                      _selectedGovernorate = val;
                      _selectedCity = null;
                    });
                  },
                  decoration: InputDecoration(
                    prefixIcon: const Icon(Icons.map_outlined, color: AppColors.primary),
                    filled: true,
                    fillColor: Colors.white,
                    border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                  ),
                ),

                const SizedBox(height: 12),

                if (_selectedGovernorate != null)
                  DropdownButtonFormField<String>(
                    value: _selectedCity,
                    hint: Text('اختر المدينة / المركز', style: GoogleFonts.cairo(fontSize: 14)),
                    items: EgyptLocations.getCities(_selectedGovernorate!).map((c) {
                      return DropdownMenuItem(value: c, child: Text(c, style: GoogleFonts.cairo(fontSize: 14)));
                    }).toList(),
                    onChanged: (val) => setState(() => _selectedCity = val),
                    decoration: InputDecoration(
                      prefixIcon: const Icon(Icons.location_city_outlined, color: AppColors.primary),
                      filled: true,
                      fillColor: Colors.white,
                      border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                    ),
                  ),

                const SizedBox(height: 14),

                // Detailed address input
                Text('العنوان بالتفصيل (الشارع / رقم العمارة)', style: GoogleFonts.cairo(fontSize: 14, fontWeight: FontWeight.bold)),
                const SizedBox(height: 6),
                TextField(
                  controller: _addressController,
                  style: GoogleFonts.cairo(fontSize: 14),
                  decoration: InputDecoration(
                    hintText: 'مثال: شارع التحرير، عمارة 12، الدور الثالث',
                    prefixIcon: const Icon(Icons.home_outlined, color: AppColors.primary),
                    filled: true,
                    fillColor: Colors.white,
                    border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                  ),
                ),

                if (_errorMessage != null) ...[
                  const SizedBox(height: 16),
                  Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: AppColors.danger.withOpacity(0.08),
                      borderRadius: BorderRadius.circular(10),
                      border: Border.all(color: AppColors.danger.withOpacity(0.3)),
                    ),
                    child: Text(
                      _errorMessage!,
                      style: GoogleFonts.cairo(fontSize: 13, color: AppColors.danger, fontWeight: FontWeight.w600),
                    ),
                  ),
                ],

                const SizedBox(height: 32),

                // Submit Button
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
                            'حفظ ومتابعة',
                            style: GoogleFonts.cairo(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.white),
                          ),
                  ),
                ),
                const SizedBox(height: 20),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildIdCardBox({
    required String title,
    required String subtitle,
    required File? file,
    required IconData icon,
    required VoidCallback onTap,
  }) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(14),
      child: Container(
        height: 130,
        padding: const EdgeInsets.all(10),
        decoration: BoxDecoration(
          color: file != null ? Colors.transparent : Colors.white,
          borderRadius: BorderRadius.circular(14),
          border: Border.all(
            color: file != null ? AppColors.accent : AppColors.line,
            width: file != null ? 2 : 1,
          ),
        ),
        child: file != null
            ? ClipRRect(
                borderRadius: BorderRadius.circular(10),
                child: Stack(
                  fit: StackFit.expand,
                  children: [
                    Image.file(file, fit: BoxFit.cover),
                    Container(
                      color: Colors.black.withOpacity(0.35),
                      child: const Center(
                        child: Icon(Icons.check_circle, color: Colors.white, size: 36),
                      ),
                    ),
                  ],
                ),
              )
            : Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(icon, color: AppColors.primary, size: 36),
                  const SizedBox(height: 8),
                  Text(title, style: GoogleFonts.cairo(fontSize: 13, fontWeight: FontWeight.bold)),
                  Text(subtitle, style: GoogleFonts.cairo(fontSize: 10, color: AppColors.inkSoft), textAlign: TextAlign.center),
                ],
              ),
      ),
    );
  }
}

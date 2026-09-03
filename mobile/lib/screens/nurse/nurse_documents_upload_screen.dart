import 'dart:io';
import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

import '../../core/api_client.dart';
import '../../services/backend_upload_uploader.dart';
import '../../theme/app_theme.dart';

class UploadedDocItem {
  final String title;
  final String documentType; // GRADUATION_CERTIFICATE, NURSING_CERTIFICATE, etc.
  final bool isRequired;
  File? localFile;
  String? uploadedUrl;
  bool isUploading = false;
  String? error;

  UploadedDocItem({
    required this.title,
    required this.documentType,
    this.isRequired = true,
    this.localFile,
    this.uploadedUrl,
  });
}

class NurseDocumentsUploadScreen extends StatefulWidget {
  final VoidCallback onCompleted;

  const NurseDocumentsUploadScreen({super.key, required this.onCompleted});

  @override
  State<NurseDocumentsUploadScreen> createState() => _NurseDocumentsUploadScreenState();
}

class _NurseDocumentsUploadScreenState extends State<NurseDocumentsUploadScreen> {
  final BackendUploadUploader _uploader = BackendUploadUploader();
  final ApiClient _client = ApiClient.instance;

  final List<UploadedDocItem> _documents = [
    UploadedDocItem(
      title: 'شهادة التخرج (كلية أو معهد تمريض)',
      documentType: 'GRADUATION_CERTIFICATE',
      isRequired: true,
    ),
    UploadedDocItem(
      title: 'ترخيص مزاولة المهنة (كارنيه النقابة)',
      documentType: 'NURSING_CERTIFICATE',
      isRequired: true,
    ),
    UploadedDocItem(
      title: 'شهادات الخبرة أو الدورات الطبية (اختياري)',
      documentType: 'EXPERIENCE_CERTIFICATE',
      isRequired: false,
    ),
  ];

  bool _isSubmitting = false;

  Future<void> _pickAndUploadDocument(UploadedDocItem item) async {
    try {
      final result = await FilePicker.platform.pickFiles(
        type: FileType.custom,
        allowedExtensions: ['pdf', 'jpg', 'jpeg', 'png'],
      );

      if (result == null || result.files.single.path == null) return;

      final file = File(result.files.single.path!);
      setState(() {
        item.localFile = file;
        item.isUploading = true;
        item.error = null;
      });

      // Upload file to backend uploads directory
      final url = await _uploader.upload(file);

      // Register document with nurse profile
      await _client.dio.post(
        '/nurses/me/documents',
        data: {
          'document_type': item.documentType,
          'file_url': url,
        },
      );

      setState(() {
        item.uploadedUrl = url;
        item.isUploading = false;
      });

      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('تم رفع ${item.title} بنجاح!'),
          backgroundColor: AppColors.success,
        ),
      );
    } catch (e) {
      setState(() {
        item.isUploading = false;
        item.error = 'تعذر رفع الملف: $e';
      });
    }
  }

  void _finish() {
    final missingRequired = _documents.where((d) => d.isRequired && d.uploadedUrl == null).toList();
    if (missingRequired.isNotEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('يرجى رفع ${missingRequired.first.title} للمتابعة'),
          backgroundColor: AppColors.danger,
        ),
      );
      return;
    }

    widget.onCompleted();
  }

  @override
  Widget build(BuildContext context) {
    return Directionality(
      textDirection: TextDirection.rtl,
      child: Scaffold(
        backgroundColor: AppColors.bg,
        appBar: AppBar(
          title: const Text('رفع الشهادات والتراخيص'),
          elevation: 0,
        ),
        body: SafeArea(
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Container(
                  padding: const EdgeInsets.all(14),
                  decoration: BoxDecoration(
                    color: AppColors.accent.withOpacity(0.08),
                    borderRadius: BorderRadius.circular(14),
                    border: Border.all(color: AppColors.accent.withOpacity(0.2)),
                  ),
                  child: Row(
                    children: [
                      const Icon(Icons.school_outlined, color: AppColors.accent, size: 28),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Text(
                          'تساعد هذه المستندات إدارة "سَنَد" في التحقق من كفاءتك ومنحك شارة "ممرض معتمد" وفتح الحجوزات لحسابك.',
                          style: GoogleFonts.cairo(fontSize: 13, color: AppColors.ink),
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 20),

                Expanded(
                  child: ListView.separated(
                    itemCount: _documents.length,
                    separatorBuilder: (_, __) => const SizedBox(height: 14),
                    itemBuilder: (context, index) {
                      final item = _documents[index];
                      final isDone = item.uploadedUrl != null;

                      return Container(
                        padding: const EdgeInsets.all(16),
                        decoration: BoxDecoration(
                          color: Colors.white,
                          borderRadius: BorderRadius.circular(14),
                          border: Border.all(
                            color: isDone ? AppColors.success : AppColors.line,
                            width: isDone ? 1.5 : 1,
                          ),
                        ),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              children: [
                                Icon(
                                  isDone ? Icons.check_circle : Icons.upload_file_outlined,
                                  color: isDone ? AppColors.success : AppColors.primary,
                                  size: 24,
                                ),
                                const SizedBox(width: 10),
                                Expanded(
                                  child: Text(
                                    item.title,
                                    style: GoogleFonts.cairo(
                                      fontSize: 14,
                                      fontWeight: FontWeight.bold,
                                      color: AppColors.ink,
                                    ),
                                  ),
                                ),
                                if (item.isRequired)
                                  Container(
                                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                                    decoration: BoxDecoration(
                                      color: AppColors.danger.withOpacity(0.08),
                                      borderRadius: BorderRadius.circular(6),
                                    ),
                                    child: Text(
                                      'إلزامي',
                                      style: GoogleFonts.cairo(fontSize: 11, color: AppColors.danger, fontWeight: FontWeight.bold),
                                    ),
                                  ),
                              ],
                            ),
                            const SizedBox(height: 12),

                            if (item.isUploading)
                              const Padding(
                                padding: EdgeInsets.symmetric(vertical: 8),
                                child: Row(
                                  children: [
                                    SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2)),
                                    SizedBox(width: 10),
                                    Text('جاري رفع المستند ومعالجته...'),
                                  ],
                                ),
                              )
                            else if (isDone)
                              Row(
                                children: [
                                  const Icon(Icons.picture_as_pdf, color: AppColors.primary, size: 20),
                                  const SizedBox(width: 6),
                                  Expanded(
                                    child: Text(
                                      item.localFile?.path.split(Platform.pathSeparator).last ?? 'تم الرفع بنجاح',
                                      style: GoogleFonts.cairo(fontSize: 12, color: AppColors.inkSoft),
                                      overflow: TextOverflow.ellipsis,
                                    ),
                                  ),
                                  TextButton(
                                    onPressed: () => _pickAndUploadDocument(item),
                                    child: const Text('تغيير'),
                                  ),
                                ],
                              )
                            else
                              OutlinedButton.icon(
                                onPressed: () => _pickAndUploadDocument(item),
                                icon: const Icon(Icons.attach_file, size: 18),
                                label: Text('اختيار ملف (PDF أو صورة)', style: GoogleFonts.cairo(fontSize: 13)),
                                style: OutlinedButton.styleFrom(
                                  side: const BorderSide(color: AppColors.primary),
                                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                                ),
                              ),

                            if (item.error != null)
                              Padding(
                                padding: const EdgeInsets.only(top: 8),
                                child: Text(item.error!, style: GoogleFonts.cairo(fontSize: 12, color: AppColors.danger)),
                              ),
                          ],
                        ),
                      );
                    },
                  ),
                ),

                // Complete Button
                SizedBox(
                  width: double.infinity,
                  height: 52,
                  child: ElevatedButton(
                    onPressed: _isSubmitting ? null : _finish,
                    style: ElevatedButton.styleFrom(
                      backgroundColor: AppColors.primary,
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
                    ),
                    child: Text(
                      'متابعة الخطوة التالية',
                      style: GoogleFonts.cairo(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.white),
                    ),
                  ),
                ),
                const SizedBox(height: 12),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

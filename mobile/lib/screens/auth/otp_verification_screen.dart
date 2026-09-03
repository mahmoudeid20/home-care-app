import 'dart:async';
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

import '../../services/otp_api.dart';
import '../../theme/app_theme.dart';

class OtpVerificationScreen extends StatefulWidget {
  final String recipient;
  final String channel; // EMAIL or SMS
  final String purpose;
  final String? initialDebugCode;
  final VoidCallback onVerified;

  const OtpVerificationScreen({
    super.key,
    required this.recipient,
    this.channel = 'EMAIL',
    this.purpose = 'REGISTRATION',
    this.initialDebugCode,
    required this.onVerified,
  });

  @override
  State<OtpVerificationScreen> createState() => _OtpVerificationScreenState();
}

class _OtpVerificationScreenState extends State<OtpVerificationScreen> {
  final OtpApi _otpApi = OtpApi();
  final List<TextEditingController> _controllers = List.generate(6, (_) => TextEditingController());
  final List<FocusNode> _focusNodes = List.generate(6, (_) => FocusNode());

  bool _isLoading = false;
  String? _errorMessage;
  String? _debugCode;

  int _resendCountdown = 60;
  Timer? _timer;

  @override
  void initState() {
    super.initState();
    _debugCode = widget.initialDebugCode;
    _startCountdown();

    // If initialDebugCode was provided, autofill after build
    if (_debugCode != null && _debugCode!.length == 6) {
      WidgetsBinding.instance.addPostFrameCallback((_) {
        for (int i = 0; i < 6; i++) {
          _controllers[i].text = _debugCode![i];
        }
        setState(() {});
      });
    }
  }

  @override
  void dispose() {
    _timer?.cancel();
    for (final c in _controllers) {
      c.dispose();
    }
    for (final f in _focusNodes) {
      f.dispose();
    }
    super.dispose();
  }

  void _startCountdown() {
    _resendCountdown = 60;
    _timer?.cancel();
    _timer = Timer.periodic(const Duration(seconds: 1), (timer) {
      if (_resendCountdown > 0) {
        setState(() => _resendCountdown--);
      } else {
        timer.cancel();
      }
    });
  }

  String get _currentCode => _controllers.map((c) => c.text).join();

  Future<void> _verifyCode() async {
    final code = _currentCode;
    if (code.length != 6) {
      setState(() => _errorMessage = 'يرجى إدخال رمز التحقق كاملاً (6 أرقام)');
      return;
    }

    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    try {
      final success = await _otpApi.verifyOtp(
        recipient: widget.recipient,
        code: code,
        purpose: widget.purpose,
      );

      if (success) {
        if (!mounted) return;
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('تم التحقق بنجاح!'),
            backgroundColor: AppColors.success,
          ),
        );
        widget.onVerified();
      }
    } catch (e) {
      setState(() => _errorMessage = e.toString().replaceFirst('Exception: ', ''));
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  Future<void> _resendCode() async {
    if (_resendCountdown > 0) return;

    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    try {
      final res = await _otpApi.sendOtp(
        recipient: widget.recipient,
        channel: widget.channel,
        purpose: widget.purpose,
      );

      _startCountdown();
      setState(() {
        _debugCode = res['debug_code'] as String?;
      });

      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('تم إرسال رمز تحقق جديد بنجاح'),
          backgroundColor: AppColors.primary,
        ),
      );
    } catch (e) {
      setState(() => _errorMessage = e.toString().replaceFirst('Exception: ', ''));
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Directionality(
      textDirection: TextDirection.rtl,
      child: Scaffold(
        backgroundColor: AppColors.bg,
        appBar: AppBar(
          title: const Text('تأكيد الحساب'),
          elevation: 0,
        ),
        body: SafeArea(
          child: SingleChildScrollView(
            padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 20),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.center,
              children: [
                const SizedBox(height: 16),
                Container(
                  width: 90,
                  height: 90,
                  decoration: BoxDecoration(
                    color: AppColors.primary.withOpacity(0.08),
                    shape: BoxShape.circle,
                  ),
                  child: const Icon(
                    Icons.mark_email_read_outlined,
                    color: AppColors.primary,
                    size: 46,
                  ),
                ),
                const SizedBox(height: 24),
                Text(
                  'رمز التحقق السريع (OTP)',
                  style: GoogleFonts.cairo(
                    fontSize: 22,
                    fontWeight: FontWeight.bold,
                    color: AppColors.ink,
                  ),
                ),
                const SizedBox(height: 8),
                Text(
                  widget.channel == 'EMAIL'
                      ? 'تم إرسال رمز تأكيد مكون من 6 أرقام إلى بريدك الإلكتروني:'
                      : 'تم إرسال رمز تأكيد مكون من 6 أرقام إلى هاتفك:',
                  textAlign: TextAlign.center,
                  style: GoogleFonts.cairo(
                    fontSize: 14,
                    color: AppColors.inkSoft,
                  ),
                ),
                const SizedBox(height: 6),
                Text(
                  widget.recipient,
                  style: GoogleFonts.cairo(
                    fontSize: 15,
                    fontWeight: FontWeight.bold,
                    color: AppColors.primary,
                  ),
                ),
                const SizedBox(height: 32),

                // 6 Pin Boxes
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                  children: List.generate(6, (index) {
                    return SizedBox(
                      width: 48,
                      height: 56,
                      child: TextField(
                        controller: _controllers[index],
                        focusNode: _focusNodes[index],
                        keyboardType: TextInputType.number,
                        textAlign: TextAlign.center,
                        maxLength: 1,
                        style: GoogleFonts.cairo(
                          fontSize: 22,
                          fontWeight: FontWeight.bold,
                          color: AppColors.ink,
                        ),
                        decoration: InputDecoration(
                          counterText: '',
                          filled: true,
                          fillColor: Colors.white,
                          border: OutlineInputBorder(
                            borderRadius: BorderRadius.circular(12),
                            borderSide: const BorderSide(color: AppColors.line),
                          ),
                          focusedBorder: OutlineInputBorder(
                            borderRadius: BorderRadius.circular(12),
                            borderSide: const BorderSide(color: AppColors.primary, width: 2),
                          ),
                        ),
                        onChanged: (val) {
                          if (val.isNotEmpty && index < 5) {
                            _focusNodes[index + 1].requestFocus();
                          } else if (val.isEmpty && index > 0) {
                            _focusNodes[index - 1].requestFocus();
                          }
                          if (_currentCode.length == 6) {
                            _verifyCode();
                          }
                        },
                      ),
                    );
                  }),
                ),

                if (_debugCode != null) ...[
                  const SizedBox(height: 18),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
                    decoration: BoxDecoration(
                      color: AppColors.accent.withOpacity(0.12),
                      borderRadius: BorderRadius.circular(10),
                      border: Border.all(color: AppColors.accent),
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        const Icon(Icons.info_outline, color: AppColors.accent, size: 18),
                        const SizedBox(width: 8),
                        Text(
                          'رمز التجربة السريع: $_debugCode',
                          style: GoogleFonts.cairo(
                            fontSize: 13,
                            fontWeight: FontWeight.bold,
                            color: AppColors.accent,
                          ),
                        ),
                      ],
                    ),
                  ),
                ],

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
                      style: GoogleFonts.cairo(
                        fontSize: 13,
                        color: AppColors.danger,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ),
                ],

                const SizedBox(height: 36),

                // Submit button
                SizedBox(
                  width: double.infinity,
                  height: 52,
                  child: ElevatedButton(
                    onPressed: _isLoading ? null : _verifyCode,
                    style: ElevatedButton.styleFrom(
                      backgroundColor: AppColors.primary,
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(14),
                      ),
                    ),
                    child: _isLoading
                        ? const SizedBox(
                            width: 24,
                            height: 24,
                            child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2),
                          )
                        : Text(
                            'تأكيد ومتابعة',
                            style: GoogleFonts.cairo(
                              fontSize: 16,
                              fontWeight: FontWeight.bold,
                              color: Colors.white,
                            ),
                          ),
                  ),
                ),

                const SizedBox(height: 24),

                // Resend Timer
                Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Text(
                      'لم يصلك الرمز؟ ',
                      style: GoogleFonts.cairo(
                        fontSize: 14,
                        color: AppColors.inkSoft,
                      ),
                    ),
                    if (_resendCountdown > 0)
                      Text(
                        'إعادة الإرسال بعد $_resendCountdown ثانية',
                        style: GoogleFonts.cairo(
                          fontSize: 14,
                          fontWeight: FontWeight.bold,
                          color: AppColors.primary,
                        ),
                      )
                    else
                      TextButton(
                        onPressed: _isLoading ? null : _resendCode,
                        child: Text(
                          'إعادة إرسال الرمز الآن',
                          style: GoogleFonts.cairo(
                            fontSize: 14,
                            fontWeight: FontWeight.bold,
                            color: AppColors.primary,
                          ),
                        ),
                      ),
                  ],
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

// ignore: unused_import
import 'package:intl/intl.dart' as intl;
import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for Arabic (`ar`).
class AppLocalizationsAr extends AppLocalizations {
  AppLocalizationsAr([String locale = 'ar']) : super(locale);

  @override
  String get brandName => 'Home Care';

  @override
  String get brandSub => 'رعاية منزلية موثوقة';

  @override
  String homeGreeting(String name) {
    return 'أهلاً يا $name 👋';
  }

  @override
  String get homeSub => 'مين هنطلب النهاردة؟';

  @override
  String get searchPlaceholder => 'دوّر باسم التخصص أو المنطقة…';

  @override
  String get topRatedNearYou => 'الأعلى تقييماً بالقرب منك';

  @override
  String get seeAll => 'عرض الكل';

  @override
  String get verified => 'موثّقة';

  @override
  String get bookNow => 'احجز الآن';

  @override
  String get navHome => 'الرئيسية';

  @override
  String get navBookings => 'حجوزاتي';

  @override
  String get navChat => 'الدردشة';

  @override
  String get navProfile => 'حسابي';

  @override
  String get myBookings => 'حجوزاتي';

  @override
  String get statusPending => 'بانتظار الموافقة';

  @override
  String get statusAccepted => 'تم القبول';

  @override
  String get statusConfirmed => 'مؤكد';

  @override
  String get statusActive => 'جارية الآن';

  @override
  String get statusCompleted => 'مكتملة';

  @override
  String get statusReviewed => 'تم التقييم';

  @override
  String get statusCancelled => 'ملغي';

  @override
  String get statusExpired => 'منتهي';

  @override
  String get login => 'تسجيل الدخول';

  @override
  String get register => 'إنشاء حساب';

  @override
  String get email => 'البريد الإلكتروني';

  @override
  String get password => 'كلمة المرور';

  @override
  String get iAmPatient => 'أنا مريض';

  @override
  String get iAmNurse => 'أنا ممرض/ة';

  @override
  String get language => 'اللغة';

  @override
  String get welcomeBack => 'أهلاً بيك تاني';

  @override
  String get loginSubtitle => 'سجّل دخولك عشان تكمل';

  @override
  String get createAccountTitle => 'إنشاء حساب جديد';

  @override
  String get createAccountSubtitle => 'اختار نوع الحساب وابدأ';

  @override
  String get phoneOptional => 'رقم الموبايل (اختياري)';

  @override
  String get confirmPassword => 'تأكيد كلمة المرور';

  @override
  String get dontHaveAccount => 'معندكش حساب؟';

  @override
  String get alreadyHaveAccount => 'عندك حساب بالفعل؟';

  @override
  String get passwordsDontMatch => 'كلمتا المرور مش متطابقتين';

  @override
  String get passwordTooWeak =>
      'لازم تحتوي على حرف ورقم على الأقل، و8 حروف كحد أدنى';

  @override
  String get invalidEmail => 'بريد إلكتروني غير صحيح';

  @override
  String get requiredField => 'الحقل ده مطلوب';

  @override
  String get connectionError => 'مفيش اتصال بالإنترنت. جرّب تاني.';

  @override
  String get connectionTimeout => 'الاتصال بطيء أوي، جرّب تاني.';

  @override
  String get retry => 'إعادة المحاولة';

  @override
  String get logout => 'تسجيل الخروج';

  @override
  String get noNursesFound => 'مفيش ممرضين متاحين دلوقتي في المنطقة دي';

  @override
  String get somethingWentWrong => 'حصل خطأ، جرّب تاني';

  @override
  String get sendRequest => 'ابعت طلب لهذا الممرض/ة';

  @override
  String get about => 'نبذة';

  @override
  String get servicesAndPrices => 'الخدمات والأسعار';

  @override
  String get reviews => 'تقييمات';

  @override
  String get yearsExperience => 'سنوات خبرة';

  @override
  String get newRequestTitle => 'طلب رعاية جديد';

  @override
  String get patientInfoSection => '١. بيانات المريض';

  @override
  String get careNeededSection => '٢. الرعاية المطلوبة';

  @override
  String get nurseRequirementsSection => '٣. مواصفات الممرض/ة (اختياري)';

  @override
  String get locationSection => '٤. العنوان';

  @override
  String get scheduleSection => '٥. الموعد';

  @override
  String get budgetSection => '٦. الميزانية (اختياري)';

  @override
  String get patientNameLabel => 'اسم المريض';

  @override
  String get patientAgeLabel => 'السن';

  @override
  String get patientGenderLabel => 'النوع';

  @override
  String get male => 'ذكر';

  @override
  String get female => 'أنثى';

  @override
  String get medicalConditionLabel => 'الحالة الصحية (وصف مختصر)';

  @override
  String get mobilityStatusLabel => 'الحالة الحركية';

  @override
  String get mobilityIndependent => 'يتحرك بمفرده';

  @override
  String get mobilityAssistance => 'محتاج مساعدة';

  @override
  String get mobilityWheelchair => 'كرسي متحرك';

  @override
  String get mobilityBedridden => 'طريح الفراش';

  @override
  String get specialRequirementsLabel => 'متطلبات خاصة (اختياري)';

  @override
  String get selectServices => 'اختار الخدمة المطلوبة';

  @override
  String get governorateLabel => 'المحافظة';

  @override
  String get cityLabel => 'المدينة/الحي';

  @override
  String get areaLabel => 'المنطقة (اختياري)';

  @override
  String get startDateLabel => 'تاريخ البداية';

  @override
  String get endDateLabel => 'تاريخ النهاية (اختياري)';

  @override
  String get hoursPerDayLabel => 'عدد الساعات يوميًا (اختياري)';

  @override
  String get paymentFrequencyLabel => 'طريقة الدفع';

  @override
  String get hourly => 'بالساعة';

  @override
  String get daily => 'باليوم';

  @override
  String get weekly => 'بالأسبوع';

  @override
  String get monthly => 'بالشهر';

  @override
  String get budgetMinLabel => 'الحد الأدنى (اختياري)';

  @override
  String get budgetMaxLabel => 'الحد الأقصى (اختياري)';

  @override
  String get submitRequest => 'إرسال الطلب';

  @override
  String get requestSentTitle => 'تم إرسال الطلب';

  @override
  String get requestSentBody => 'طلبك اتبعت للممرض/ة. هيوصلك إشعار لما يردّ.';

  @override
  String get backToHome => 'رجوع للرئيسية';

  @override
  String get pickDate => 'اختار التاريخ';

  @override
  String stepOf(String current, String total) {
    return 'خطوة $current من $total';
  }

  @override
  String get next => 'التالي';

  @override
  String get back => 'السابق';

  @override
  String get noConversationsYet => 'لسه معندكش محادثات';

  @override
  String get messageHint => 'اكتب رسالة…';

  @override
  String get reconnecting => 'بيحاول يتصل تاني…';

  @override
  String get connectionLost => 'الاتصال انقطع';

  @override
  String get cantAccessConversation => 'معندكش صلاحية الوصول للمحادثة دي';

  @override
  String get send => 'إرسال';

  @override
  String get choosePhotoSource => 'اختار مصدر الصورة';

  @override
  String get takePhoto => 'التقاط صورة';

  @override
  String get chooseFromGallery => 'اختيار من المعرض';

  @override
  String get uploadingPhoto => 'جاري رفع الصورة…';

  @override
  String get photoUpdated => 'اتحدثت صورتك';

  @override
  String get storageNotConfigured =>
      'رفع الصور لسه مش متاح — محتاج ربط مساحة تخزين خارجية';

  @override
  String get newRequests => 'طلبات جديدة';

  @override
  String get noRequestsYet => 'لسه معندكش طلبات';

  @override
  String get appPending => 'بانتظار ردك';

  @override
  String get appAccepted => 'مقبول';

  @override
  String get appRejected => 'مرفوض';

  @override
  String get appWithdrawn => 'تم سحبه';

  @override
  String get accept => 'قبول';

  @override
  String get reject => 'رفض';

  @override
  String get acceptRequestConfirm => 'قبول الطلب ده هيحوّله لحجز مؤكد. تأكيد؟';

  @override
  String get rejectReasonHint => 'سبب الرفض (اختياري)';

  @override
  String get requestAccepted => 'تم قبول الطلب وإنشاء الحجز';

  @override
  String get requestRejected => 'تم رفض الطلب';

  @override
  String get patientLabel => 'المريض';

  @override
  String get budgetLabel => 'الميزانية المقترحة';

  @override
  String get notSpecified => 'غير محدد';

  @override
  String get mySentRequests => 'طلباتي المرسلة';

  @override
  String get noSentRequestsYet => 'لسه معملتش أي طلب';

  @override
  String get withdrawRequest => 'سحب الطلب';

  @override
  String get requestWithdrawn => 'تم سحب الطلب';

  @override
  String get leaveReview => 'قيّم التجربة';

  @override
  String get overallRating => 'التقييم العام';

  @override
  String get professionalismRating => 'الاحترافية';

  @override
  String get communicationRating => 'التواصل';

  @override
  String get careQualityRating => 'جودة الرعاية';

  @override
  String get commentOptional => 'تعليق (اختياري)';

  @override
  String get submitReview => 'إرسال التقييم';

  @override
  String get reviewSubmitted => 'شكرًا، اتسجل تقييمك';

  @override
  String get alreadyReviewed => 'قيّمت الحجز ده قبل كده';

  @override
  String get noReviewsYet => 'لسه معملهاش حد تقييم';

  @override
  String get noBookingsYet => 'مفيش حجوزات لسه — ابدأ بالبحث عن ممرض';

  @override
  String get startSearching => 'ابدأ البحث';

  @override
  String get searchNurses => 'البحث عن ممرض…';

  @override
  String get egp => 'ج.م';

  @override
  String get darkMode => 'الوضع الليلي';

  @override
  String get lightMode => 'الوضع النهاري';

  @override
  String get noChatsYet => 'لسه معندكش محادثات — ابدأ محادثة مع ممرض';

  @override
  String get browseNurses => 'تصفح الممرضين';

  @override
  String get filterBySpecialty => 'فلترة حسب التخصص';

  @override
  String get allSpecialties => 'كل التخصصات';

  @override
  String get clearSearch => 'مسح البحث';

  @override
  String get onboardingTitle1 => 'رعاية صحية موثوقة في بيتك';

  @override
  String get onboardingSub1 =>
      'احصل على أفضل الممرضين والممرضات المعتمدين لرعاية كبار السن والمرضى بكل أمانة واحترافية.';

  @override
  String get onboardingTitle2 => 'كوادر طبية معتمدة وموثقة';

  @override
  String get onboardingSub2 =>
      'جميع ممرضي Home Care تم التحقق من هوياتهم وشهاداتهم وتراخيص مزاولة المهنة بعناية تامة.';

  @override
  String get onboardingTitle3 => 'سهولة في الحجز والمتابعة';

  @override
  String get onboardingSub3 =>
      'حدد موقعك ونوع الرعاية المطلوبة، واحصل على ترشيحات فورية وتواصل مباشر مع الممرض.';

  @override
  String get skip => 'تخطي';

  @override
  String get startNow => 'ابدأ الآن';

  @override
  String get fullName => 'الاسم بالكامل (رباعي)';

  @override
  String get fullNameQuadrupleHint => 'مثال: محمود أحمد إبراهيم السيد';

  @override
  String get fullNameQuadrupleValidation =>
      'يجب إدخال الاسم بالكامل (٤ أسماء على الأقل)';

  @override
  String get username => 'اسم المستخدم (اليوزر نيم)';

  @override
  String get usernameHint => 'مثال: mahmoud_eid';

  @override
  String get usernameValidation => 'اسم المستخدم يجب ألا يقل عن ٣ أحرف';

  @override
  String get profileSetupTitle => 'إكمال بيانات حسابك';

  @override
  String get profileSetupSubtitle =>
      'خطوات بسيطة لتخصيص تجربتك وترشيح أفضل الممرضين لك';

  @override
  String get stepPersonal => 'البيانات الشخصية';

  @override
  String get stepLocation => 'الموقع والمحافظة';

  @override
  String get stepNursingType => 'نوع التمريض المطلوب';

  @override
  String get governorate => 'المحافظة';

  @override
  String get selectGovernorate => 'اختر المحافظة في مصر';

  @override
  String get city => 'المدينة / المركز';

  @override
  String get selectCity => 'اختر المدينة أو المركز';

  @override
  String get whatNursingDoYouNeed =>
      'ما هو نوع التمريض أو الخدمة التي تبحث عنها؟';

  @override
  String get selectSpecialtiesOrServices =>
      'يمكنك اختيار أكثر من تخصص أو خدمة للترشيح المباشر';

  @override
  String get saveAndContinue => 'حفظ ومتابعة';

  @override
  String get recommendedForYou => 'ترشيحات مقترحة لك';

  @override
  String get basedOnYourNeeds => 'بناءً على موقعك ونوع التمريض المطلوب';

  @override
  String get quickActions => 'خدمات سريعة';

  @override
  String get requestCareNow => 'طلب تمريض جديد';

  @override
  String get exploreSpecialties => 'تصفح التخصصات';

  @override
  String get navSettings => 'الإعدادات';

  @override
  String get settings => 'الإعدادات';

  @override
  String get accountSettings => 'إعدادات الحساب';

  @override
  String get appPreferences => 'تفضيلات التطبيق';

  @override
  String get supportAndHelp => 'الدعم والمساعدة';

  @override
  String get faq => 'الأسئلة الشائعة';

  @override
  String get contactSupport => 'تواصل مع خدمة العملاء';

  @override
  String get reportProblem => 'تقديم شكوى أو اقتراح';

  @override
  String get complaintSent => 'تم إرسال رسالتك بنجاح، وسنتواصل معك قريباً';

  @override
  String get problemDescription => 'تفاصيل المشكلة أو الشكوى';

  @override
  String get whatsappSupport => 'محادثة عبر واتساب';

  @override
  String get callSupport => 'اتصال بفريق الدعم';

  @override
  String get emailSupport => 'راسلنا عبر البريد';

  @override
  String get termsAndPrivacy => 'الشروط والأحكام وسياسة الخصوصية';

  @override
  String get appVersion => 'إصدار التطبيق';

  @override
  String get profileUpdated => 'تم تحديث الملف الشخصي بنجاح';
}

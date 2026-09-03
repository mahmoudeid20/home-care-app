import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:flutter/widgets.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:intl/intl.dart' as intl;

import 'app_localizations_ar.dart';
import 'app_localizations_en.dart';

// ignore_for_file: type=lint

/// Callers can lookup localized strings with an instance of AppLocalizations
/// returned by `AppLocalizations.of(context)`.
///
/// Applications need to include `AppLocalizations.delegate()` in their app's
/// `localizationDelegates` list, and the locales they support in the app's
/// `supportedLocales` list. For example:
///
/// ```dart
/// import 'l10n/app_localizations.dart';
///
/// return MaterialApp(
///   localizationsDelegates: AppLocalizations.localizationsDelegates,
///   supportedLocales: AppLocalizations.supportedLocales,
///   home: MyApplicationHome(),
/// );
/// ```
///
/// ## Update pubspec.yaml
///
/// Please make sure to update your pubspec.yaml to include the following
/// packages:
///
/// ```yaml
/// dependencies:
///   # Internationalization support.
///   flutter_localizations:
///     sdk: flutter
///   intl: any # Use the pinned version from flutter_localizations
///
///   # Rest of dependencies
/// ```
///
/// ## iOS Applications
///
/// iOS applications define key application metadata, including supported
/// locales, in an Info.plist file that is built into the application bundle.
/// To configure the locales supported by your app, you’ll need to edit this
/// file.
///
/// First, open your project’s ios/Runner.xcworkspace Xcode workspace file.
/// Then, in the Project Navigator, open the Info.plist file under the Runner
/// project’s Runner folder.
///
/// Next, select the Information Property List item, select Add Item from the
/// Editor menu, then select Localizations from the pop-up menu.
///
/// Select and expand the newly-created Localizations item then, for each
/// locale your application supports, add a new item and select the locale
/// you wish to add from the pop-up menu in the Value field. This list should
/// be consistent with the languages listed in the AppLocalizations.supportedLocales
/// property.
abstract class AppLocalizations {
  AppLocalizations(String locale)
      : localeName = intl.Intl.canonicalizedLocale(locale.toString());

  final String localeName;

  static AppLocalizations of(BuildContext context) {
    return Localizations.of<AppLocalizations>(context, AppLocalizations)!;
  }

  static const LocalizationsDelegate<AppLocalizations> delegate =
      _AppLocalizationsDelegate();

  /// A list of this localizations delegate along with the default localizations
  /// delegates.
  ///
  /// Returns a list of localizations delegates containing this delegate along with
  /// GlobalMaterialLocalizations.delegate, GlobalCupertinoLocalizations.delegate,
  /// and GlobalWidgetsLocalizations.delegate.
  ///
  /// Additional delegates can be added by appending to this list in
  /// MaterialApp. This list does not have to be used at all if a custom list
  /// of delegates is preferred or required.
  static const List<LocalizationsDelegate<dynamic>> localizationsDelegates =
      <LocalizationsDelegate<dynamic>>[
    delegate,
    GlobalMaterialLocalizations.delegate,
    GlobalCupertinoLocalizations.delegate,
    GlobalWidgetsLocalizations.delegate,
  ];

  /// A list of this localizations delegate's supported locales.
  static const List<Locale> supportedLocales = <Locale>[
    Locale('ar'),
    Locale('en')
  ];

  /// No description provided for @brandName.
  ///
  /// In ar, this message translates to:
  /// **'سَنَد'**
  String get brandName;

  /// No description provided for @brandSub.
  ///
  /// In ar, this message translates to:
  /// **'رعاية منزلية موثوقة'**
  String get brandSub;

  /// No description provided for @homeGreeting.
  ///
  /// In ar, this message translates to:
  /// **'أهلاً يا {name} 👋'**
  String homeGreeting(String name);

  /// No description provided for @homeSub.
  ///
  /// In ar, this message translates to:
  /// **'مين هنطلب النهاردة؟'**
  String get homeSub;

  /// No description provided for @searchPlaceholder.
  ///
  /// In ar, this message translates to:
  /// **'دوّر باسم التخصص أو المنطقة…'**
  String get searchPlaceholder;

  /// No description provided for @topRatedNearYou.
  ///
  /// In ar, this message translates to:
  /// **'الأعلى تقييماً بالقرب منك'**
  String get topRatedNearYou;

  /// No description provided for @seeAll.
  ///
  /// In ar, this message translates to:
  /// **'عرض الكل'**
  String get seeAll;

  /// No description provided for @verified.
  ///
  /// In ar, this message translates to:
  /// **'موثّقة'**
  String get verified;

  /// No description provided for @bookNow.
  ///
  /// In ar, this message translates to:
  /// **'احجز الآن'**
  String get bookNow;

  /// No description provided for @navHome.
  ///
  /// In ar, this message translates to:
  /// **'الرئيسية'**
  String get navHome;

  /// No description provided for @navBookings.
  ///
  /// In ar, this message translates to:
  /// **'حجوزاتي'**
  String get navBookings;

  /// No description provided for @navChat.
  ///
  /// In ar, this message translates to:
  /// **'الدردشة'**
  String get navChat;

  /// No description provided for @navProfile.
  ///
  /// In ar, this message translates to:
  /// **'حسابي'**
  String get navProfile;

  /// No description provided for @myBookings.
  ///
  /// In ar, this message translates to:
  /// **'حجوزاتي'**
  String get myBookings;

  /// No description provided for @statusPending.
  ///
  /// In ar, this message translates to:
  /// **'بانتظار الموافقة'**
  String get statusPending;

  /// No description provided for @statusAccepted.
  ///
  /// In ar, this message translates to:
  /// **'تم القبول'**
  String get statusAccepted;

  /// No description provided for @statusConfirmed.
  ///
  /// In ar, this message translates to:
  /// **'مؤكد'**
  String get statusConfirmed;

  /// No description provided for @statusActive.
  ///
  /// In ar, this message translates to:
  /// **'جارية الآن'**
  String get statusActive;

  /// No description provided for @statusCompleted.
  ///
  /// In ar, this message translates to:
  /// **'مكتملة'**
  String get statusCompleted;

  /// No description provided for @statusReviewed.
  ///
  /// In ar, this message translates to:
  /// **'تم التقييم'**
  String get statusReviewed;

  /// No description provided for @statusCancelled.
  ///
  /// In ar, this message translates to:
  /// **'ملغي'**
  String get statusCancelled;

  /// No description provided for @statusExpired.
  ///
  /// In ar, this message translates to:
  /// **'منتهي'**
  String get statusExpired;

  /// No description provided for @login.
  ///
  /// In ar, this message translates to:
  /// **'تسجيل الدخول'**
  String get login;

  /// No description provided for @register.
  ///
  /// In ar, this message translates to:
  /// **'إنشاء حساب'**
  String get register;

  /// No description provided for @email.
  ///
  /// In ar, this message translates to:
  /// **'البريد الإلكتروني'**
  String get email;

  /// No description provided for @password.
  ///
  /// In ar, this message translates to:
  /// **'كلمة المرور'**
  String get password;

  /// No description provided for @iAmPatient.
  ///
  /// In ar, this message translates to:
  /// **'أنا مريض'**
  String get iAmPatient;

  /// No description provided for @iAmNurse.
  ///
  /// In ar, this message translates to:
  /// **'أنا ممرض/ة'**
  String get iAmNurse;

  /// No description provided for @language.
  ///
  /// In ar, this message translates to:
  /// **'اللغة'**
  String get language;

  /// No description provided for @welcomeBack.
  ///
  /// In ar, this message translates to:
  /// **'أهلاً بيك تاني'**
  String get welcomeBack;

  /// No description provided for @loginSubtitle.
  ///
  /// In ar, this message translates to:
  /// **'سجّل دخولك عشان تكمل'**
  String get loginSubtitle;

  /// No description provided for @createAccountTitle.
  ///
  /// In ar, this message translates to:
  /// **'إنشاء حساب جديد'**
  String get createAccountTitle;

  /// No description provided for @createAccountSubtitle.
  ///
  /// In ar, this message translates to:
  /// **'اختار نوع الحساب وابدأ'**
  String get createAccountSubtitle;

  /// No description provided for @phoneOptional.
  ///
  /// In ar, this message translates to:
  /// **'رقم الموبايل (اختياري)'**
  String get phoneOptional;

  /// No description provided for @confirmPassword.
  ///
  /// In ar, this message translates to:
  /// **'تأكيد كلمة المرور'**
  String get confirmPassword;

  /// No description provided for @dontHaveAccount.
  ///
  /// In ar, this message translates to:
  /// **'معندكش حساب؟'**
  String get dontHaveAccount;

  /// No description provided for @alreadyHaveAccount.
  ///
  /// In ar, this message translates to:
  /// **'عندك حساب بالفعل؟'**
  String get alreadyHaveAccount;

  /// No description provided for @passwordsDontMatch.
  ///
  /// In ar, this message translates to:
  /// **'كلمتا المرور مش متطابقتين'**
  String get passwordsDontMatch;

  /// No description provided for @passwordTooWeak.
  ///
  /// In ar, this message translates to:
  /// **'لازم تحتوي على حرف ورقم على الأقل، و8 حروف كحد أدنى'**
  String get passwordTooWeak;

  /// No description provided for @invalidEmail.
  ///
  /// In ar, this message translates to:
  /// **'بريد إلكتروني غير صحيح'**
  String get invalidEmail;

  /// No description provided for @requiredField.
  ///
  /// In ar, this message translates to:
  /// **'الحقل ده مطلوب'**
  String get requiredField;

  /// No description provided for @connectionError.
  ///
  /// In ar, this message translates to:
  /// **'مفيش اتصال بالإنترنت. جرّب تاني.'**
  String get connectionError;

  /// No description provided for @connectionTimeout.
  ///
  /// In ar, this message translates to:
  /// **'الاتصال بطيء أوي، جرّب تاني.'**
  String get connectionTimeout;

  /// No description provided for @retry.
  ///
  /// In ar, this message translates to:
  /// **'إعادة المحاولة'**
  String get retry;

  /// No description provided for @logout.
  ///
  /// In ar, this message translates to:
  /// **'تسجيل الخروج'**
  String get logout;

  /// No description provided for @noNursesFound.
  ///
  /// In ar, this message translates to:
  /// **'مفيش ممرضين متاحين دلوقتي في المنطقة دي'**
  String get noNursesFound;

  /// No description provided for @somethingWentWrong.
  ///
  /// In ar, this message translates to:
  /// **'حصل خطأ، جرّب تاني'**
  String get somethingWentWrong;

  /// No description provided for @sendRequest.
  ///
  /// In ar, this message translates to:
  /// **'ابعت طلب لهذا الممرض/ة'**
  String get sendRequest;

  /// No description provided for @about.
  ///
  /// In ar, this message translates to:
  /// **'نبذة'**
  String get about;

  /// No description provided for @servicesAndPrices.
  ///
  /// In ar, this message translates to:
  /// **'الخدمات والأسعار'**
  String get servicesAndPrices;

  /// No description provided for @reviews.
  ///
  /// In ar, this message translates to:
  /// **'تقييمات'**
  String get reviews;

  /// No description provided for @yearsExperience.
  ///
  /// In ar, this message translates to:
  /// **'سنوات خبرة'**
  String get yearsExperience;

  /// No description provided for @newRequestTitle.
  ///
  /// In ar, this message translates to:
  /// **'طلب رعاية جديد'**
  String get newRequestTitle;

  /// No description provided for @patientInfoSection.
  ///
  /// In ar, this message translates to:
  /// **'١. بيانات المريض'**
  String get patientInfoSection;

  /// No description provided for @careNeededSection.
  ///
  /// In ar, this message translates to:
  /// **'٢. الرعاية المطلوبة'**
  String get careNeededSection;

  /// No description provided for @nurseRequirementsSection.
  ///
  /// In ar, this message translates to:
  /// **'٣. مواصفات الممرض/ة (اختياري)'**
  String get nurseRequirementsSection;

  /// No description provided for @locationSection.
  ///
  /// In ar, this message translates to:
  /// **'٤. العنوان'**
  String get locationSection;

  /// No description provided for @scheduleSection.
  ///
  /// In ar, this message translates to:
  /// **'٥. الموعد'**
  String get scheduleSection;

  /// No description provided for @budgetSection.
  ///
  /// In ar, this message translates to:
  /// **'٦. الميزانية (اختياري)'**
  String get budgetSection;

  /// No description provided for @patientNameLabel.
  ///
  /// In ar, this message translates to:
  /// **'اسم المريض'**
  String get patientNameLabel;

  /// No description provided for @patientAgeLabel.
  ///
  /// In ar, this message translates to:
  /// **'السن'**
  String get patientAgeLabel;

  /// No description provided for @patientGenderLabel.
  ///
  /// In ar, this message translates to:
  /// **'النوع'**
  String get patientGenderLabel;

  /// No description provided for @male.
  ///
  /// In ar, this message translates to:
  /// **'ذكر'**
  String get male;

  /// No description provided for @female.
  ///
  /// In ar, this message translates to:
  /// **'أنثى'**
  String get female;

  /// No description provided for @medicalConditionLabel.
  ///
  /// In ar, this message translates to:
  /// **'الحالة الصحية (وصف مختصر)'**
  String get medicalConditionLabel;

  /// No description provided for @mobilityStatusLabel.
  ///
  /// In ar, this message translates to:
  /// **'الحالة الحركية'**
  String get mobilityStatusLabel;

  /// No description provided for @mobilityIndependent.
  ///
  /// In ar, this message translates to:
  /// **'يتحرك بمفرده'**
  String get mobilityIndependent;

  /// No description provided for @mobilityAssistance.
  ///
  /// In ar, this message translates to:
  /// **'محتاج مساعدة'**
  String get mobilityAssistance;

  /// No description provided for @mobilityWheelchair.
  ///
  /// In ar, this message translates to:
  /// **'كرسي متحرك'**
  String get mobilityWheelchair;

  /// No description provided for @mobilityBedridden.
  ///
  /// In ar, this message translates to:
  /// **'طريح الفراش'**
  String get mobilityBedridden;

  /// No description provided for @specialRequirementsLabel.
  ///
  /// In ar, this message translates to:
  /// **'متطلبات خاصة (اختياري)'**
  String get specialRequirementsLabel;

  /// No description provided for @selectServices.
  ///
  /// In ar, this message translates to:
  /// **'اختار الخدمة المطلوبة'**
  String get selectServices;

  /// No description provided for @governorateLabel.
  ///
  /// In ar, this message translates to:
  /// **'المحافظة'**
  String get governorateLabel;

  /// No description provided for @cityLabel.
  ///
  /// In ar, this message translates to:
  /// **'المدينة/الحي'**
  String get cityLabel;

  /// No description provided for @areaLabel.
  ///
  /// In ar, this message translates to:
  /// **'المنطقة (اختياري)'**
  String get areaLabel;

  /// No description provided for @startDateLabel.
  ///
  /// In ar, this message translates to:
  /// **'تاريخ البداية'**
  String get startDateLabel;

  /// No description provided for @endDateLabel.
  ///
  /// In ar, this message translates to:
  /// **'تاريخ النهاية (اختياري)'**
  String get endDateLabel;

  /// No description provided for @hoursPerDayLabel.
  ///
  /// In ar, this message translates to:
  /// **'عدد الساعات يوميًا (اختياري)'**
  String get hoursPerDayLabel;

  /// No description provided for @paymentFrequencyLabel.
  ///
  /// In ar, this message translates to:
  /// **'طريقة الدفع'**
  String get paymentFrequencyLabel;

  /// No description provided for @hourly.
  ///
  /// In ar, this message translates to:
  /// **'بالساعة'**
  String get hourly;

  /// No description provided for @daily.
  ///
  /// In ar, this message translates to:
  /// **'باليوم'**
  String get daily;

  /// No description provided for @weekly.
  ///
  /// In ar, this message translates to:
  /// **'بالأسبوع'**
  String get weekly;

  /// No description provided for @monthly.
  ///
  /// In ar, this message translates to:
  /// **'بالشهر'**
  String get monthly;

  /// No description provided for @budgetMinLabel.
  ///
  /// In ar, this message translates to:
  /// **'الحد الأدنى (اختياري)'**
  String get budgetMinLabel;

  /// No description provided for @budgetMaxLabel.
  ///
  /// In ar, this message translates to:
  /// **'الحد الأقصى (اختياري)'**
  String get budgetMaxLabel;

  /// No description provided for @submitRequest.
  ///
  /// In ar, this message translates to:
  /// **'إرسال الطلب'**
  String get submitRequest;

  /// No description provided for @requestSentTitle.
  ///
  /// In ar, this message translates to:
  /// **'تم إرسال الطلب'**
  String get requestSentTitle;

  /// No description provided for @requestSentBody.
  ///
  /// In ar, this message translates to:
  /// **'طلبك اتبعت للممرض/ة. هيوصلك إشعار لما يردّ.'**
  String get requestSentBody;

  /// No description provided for @backToHome.
  ///
  /// In ar, this message translates to:
  /// **'رجوع للرئيسية'**
  String get backToHome;

  /// No description provided for @pickDate.
  ///
  /// In ar, this message translates to:
  /// **'اختار التاريخ'**
  String get pickDate;

  /// No description provided for @stepOf.
  ///
  /// In ar, this message translates to:
  /// **'خطوة {current} من {total}'**
  String stepOf(String current, String total);

  /// No description provided for @next.
  ///
  /// In ar, this message translates to:
  /// **'التالي'**
  String get next;

  /// No description provided for @back.
  ///
  /// In ar, this message translates to:
  /// **'السابق'**
  String get back;

  /// No description provided for @noConversationsYet.
  ///
  /// In ar, this message translates to:
  /// **'لسه معندكش محادثات'**
  String get noConversationsYet;

  /// No description provided for @messageHint.
  ///
  /// In ar, this message translates to:
  /// **'اكتب رسالة…'**
  String get messageHint;

  /// No description provided for @reconnecting.
  ///
  /// In ar, this message translates to:
  /// **'بيحاول يتصل تاني…'**
  String get reconnecting;

  /// No description provided for @connectionLost.
  ///
  /// In ar, this message translates to:
  /// **'الاتصال انقطع'**
  String get connectionLost;

  /// No description provided for @cantAccessConversation.
  ///
  /// In ar, this message translates to:
  /// **'معندكش صلاحية الوصول للمحادثة دي'**
  String get cantAccessConversation;

  /// No description provided for @send.
  ///
  /// In ar, this message translates to:
  /// **'إرسال'**
  String get send;

  /// No description provided for @choosePhotoSource.
  ///
  /// In ar, this message translates to:
  /// **'اختار مصدر الصورة'**
  String get choosePhotoSource;

  /// No description provided for @takePhoto.
  ///
  /// In ar, this message translates to:
  /// **'التقاط صورة'**
  String get takePhoto;

  /// No description provided for @chooseFromGallery.
  ///
  /// In ar, this message translates to:
  /// **'اختيار من المعرض'**
  String get chooseFromGallery;

  /// No description provided for @uploadingPhoto.
  ///
  /// In ar, this message translates to:
  /// **'جاري رفع الصورة…'**
  String get uploadingPhoto;

  /// No description provided for @photoUpdated.
  ///
  /// In ar, this message translates to:
  /// **'اتحدثت صورتك'**
  String get photoUpdated;

  /// No description provided for @storageNotConfigured.
  ///
  /// In ar, this message translates to:
  /// **'رفع الصور لسه مش متاح — محتاج ربط مساحة تخزين خارجية'**
  String get storageNotConfigured;

  /// No description provided for @newRequests.
  ///
  /// In ar, this message translates to:
  /// **'طلبات جديدة'**
  String get newRequests;

  /// No description provided for @noRequestsYet.
  ///
  /// In ar, this message translates to:
  /// **'لسه معندكش طلبات'**
  String get noRequestsYet;

  /// No description provided for @appPending.
  ///
  /// In ar, this message translates to:
  /// **'بانتظار ردك'**
  String get appPending;

  /// No description provided for @appAccepted.
  ///
  /// In ar, this message translates to:
  /// **'مقبول'**
  String get appAccepted;

  /// No description provided for @appRejected.
  ///
  /// In ar, this message translates to:
  /// **'مرفوض'**
  String get appRejected;

  /// No description provided for @appWithdrawn.
  ///
  /// In ar, this message translates to:
  /// **'تم سحبه'**
  String get appWithdrawn;

  /// No description provided for @accept.
  ///
  /// In ar, this message translates to:
  /// **'قبول'**
  String get accept;

  /// No description provided for @reject.
  ///
  /// In ar, this message translates to:
  /// **'رفض'**
  String get reject;

  /// No description provided for @acceptRequestConfirm.
  ///
  /// In ar, this message translates to:
  /// **'قبول الطلب ده هيحوّله لحجز مؤكد. تأكيد؟'**
  String get acceptRequestConfirm;

  /// No description provided for @rejectReasonHint.
  ///
  /// In ar, this message translates to:
  /// **'سبب الرفض (اختياري)'**
  String get rejectReasonHint;

  /// No description provided for @requestAccepted.
  ///
  /// In ar, this message translates to:
  /// **'تم قبول الطلب وإنشاء الحجز'**
  String get requestAccepted;

  /// No description provided for @requestRejected.
  ///
  /// In ar, this message translates to:
  /// **'تم رفض الطلب'**
  String get requestRejected;

  /// No description provided for @patientLabel.
  ///
  /// In ar, this message translates to:
  /// **'المريض'**
  String get patientLabel;

  /// No description provided for @budgetLabel.
  ///
  /// In ar, this message translates to:
  /// **'الميزانية المقترحة'**
  String get budgetLabel;

  /// No description provided for @notSpecified.
  ///
  /// In ar, this message translates to:
  /// **'غير محدد'**
  String get notSpecified;

  /// No description provided for @mySentRequests.
  ///
  /// In ar, this message translates to:
  /// **'طلباتي المرسلة'**
  String get mySentRequests;

  /// No description provided for @noSentRequestsYet.
  ///
  /// In ar, this message translates to:
  /// **'لسه معملتش أي طلب'**
  String get noSentRequestsYet;

  /// No description provided for @withdrawRequest.
  ///
  /// In ar, this message translates to:
  /// **'سحب الطلب'**
  String get withdrawRequest;

  /// No description provided for @requestWithdrawn.
  ///
  /// In ar, this message translates to:
  /// **'تم سحب الطلب'**
  String get requestWithdrawn;

  /// No description provided for @leaveReview.
  ///
  /// In ar, this message translates to:
  /// **'قيّم التجربة'**
  String get leaveReview;

  /// No description provided for @overallRating.
  ///
  /// In ar, this message translates to:
  /// **'التقييم العام'**
  String get overallRating;

  /// No description provided for @professionalismRating.
  ///
  /// In ar, this message translates to:
  /// **'الاحترافية'**
  String get professionalismRating;

  /// No description provided for @communicationRating.
  ///
  /// In ar, this message translates to:
  /// **'التواصل'**
  String get communicationRating;

  /// No description provided for @careQualityRating.
  ///
  /// In ar, this message translates to:
  /// **'جودة الرعاية'**
  String get careQualityRating;

  /// No description provided for @commentOptional.
  ///
  /// In ar, this message translates to:
  /// **'تعليق (اختياري)'**
  String get commentOptional;

  /// No description provided for @submitReview.
  ///
  /// In ar, this message translates to:
  /// **'إرسال التقييم'**
  String get submitReview;

  /// No description provided for @reviewSubmitted.
  ///
  /// In ar, this message translates to:
  /// **'شكرًا، اتسجل تقييمك'**
  String get reviewSubmitted;

  /// No description provided for @alreadyReviewed.
  ///
  /// In ar, this message translates to:
  /// **'قيّمت الحجز ده قبل كده'**
  String get alreadyReviewed;

  /// No description provided for @noReviewsYet.
  ///
  /// In ar, this message translates to:
  /// **'لسه معملهاش حد تقييم'**
  String get noReviewsYet;

  /// No description provided for @noBookingsYet.
  ///
  /// In ar, this message translates to:
  /// **'مفيش حجوزات لسه — ابدأ بالبحث عن ممرض'**
  String get noBookingsYet;

  /// No description provided for @startSearching.
  ///
  /// In ar, this message translates to:
  /// **'ابدأ البحث'**
  String get startSearching;

  /// No description provided for @searchNurses.
  ///
  /// In ar, this message translates to:
  /// **'البحث عن ممرض…'**
  String get searchNurses;

  /// No description provided for @egp.
  ///
  /// In ar, this message translates to:
  /// **'ج.م'**
  String get egp;

  /// No description provided for @darkMode.
  ///
  /// In ar, this message translates to:
  /// **'الوضع الليلي'**
  String get darkMode;

  /// No description provided for @lightMode.
  ///
  /// In ar, this message translates to:
  /// **'الوضع النهاري'**
  String get lightMode;

  /// No description provided for @noChatsYet.
  ///
  /// In ar, this message translates to:
  /// **'لسه معندكش محادثات — ابدأ محادثة مع ممرض'**
  String get noChatsYet;

  /// No description provided for @browseNurses.
  ///
  /// In ar, this message translates to:
  /// **'تصفح الممرضين'**
  String get browseNurses;

  /// No description provided for @filterBySpecialty.
  ///
  /// In ar, this message translates to:
  /// **'فلترة حسب التخصص'**
  String get filterBySpecialty;

  /// No description provided for @allSpecialties.
  ///
  /// In ar, this message translates to:
  /// **'كل التخصصات'**
  String get allSpecialties;

  /// No description provided for @clearSearch.
  ///
  /// In ar, this message translates to:
  /// **'مسح البحث'**
  String get clearSearch;

  /// No description provided for @onboardingTitle1.
  ///
  /// In ar, this message translates to:
  /// **'رعاية صحية موثوقة في بيتك'**
  String get onboardingTitle1;

  /// No description provided for @onboardingSub1.
  ///
  /// In ar, this message translates to:
  /// **'احصل على أفضل الممرضين والممرضات المعتمدين لرعاية كبار السن والمرضى بكل أمانة واحترافية.'**
  String get onboardingSub1;

  /// No description provided for @onboardingTitle2.
  ///
  /// In ar, this message translates to:
  /// **'كوادر طبية معتمدة وموثقة'**
  String get onboardingTitle2;

  /// No description provided for @onboardingSub2.
  ///
  /// In ar, this message translates to:
  /// **'جميع ممرضي سَنَد تم التحقق من هوياتهم وشهاداتهم وتراخيص مزاولة المهنة بعناية تامة.'**
  String get onboardingSub2;

  /// No description provided for @onboardingTitle3.
  ///
  /// In ar, this message translates to:
  /// **'سهولة في الحجز والمتابعة'**
  String get onboardingTitle3;

  /// No description provided for @onboardingSub3.
  ///
  /// In ar, this message translates to:
  /// **'حدد موقعك ونوع الرعاية المطلوبة، واحصل على ترشيحات فورية وتواصل مباشر مع الممرض.'**
  String get onboardingSub3;

  /// No description provided for @skip.
  ///
  /// In ar, this message translates to:
  /// **'تخطي'**
  String get skip;

  /// No description provided for @startNow.
  ///
  /// In ar, this message translates to:
  /// **'ابدأ الآن'**
  String get startNow;

  /// No description provided for @fullName.
  ///
  /// In ar, this message translates to:
  /// **'الاسم بالكامل (رباعي)'**
  String get fullName;

  /// No description provided for @fullNameQuadrupleHint.
  ///
  /// In ar, this message translates to:
  /// **'مثال: محمود أحمد إبراهيم السيد'**
  String get fullNameQuadrupleHint;

  /// No description provided for @fullNameQuadrupleValidation.
  ///
  /// In ar, this message translates to:
  /// **'يجب إدخال الاسم بالكامل (٤ أسماء على الأقل)'**
  String get fullNameQuadrupleValidation;

  /// No description provided for @username.
  ///
  /// In ar, this message translates to:
  /// **'اسم المستخدم (اليوزر نيم)'**
  String get username;

  /// No description provided for @usernameHint.
  ///
  /// In ar, this message translates to:
  /// **'مثال: mahmoud_eid'**
  String get usernameHint;

  /// No description provided for @usernameValidation.
  ///
  /// In ar, this message translates to:
  /// **'اسم المستخدم يجب ألا يقل عن ٣ أحرف'**
  String get usernameValidation;

  /// No description provided for @profileSetupTitle.
  ///
  /// In ar, this message translates to:
  /// **'إكمال بيانات حسابك'**
  String get profileSetupTitle;

  /// No description provided for @profileSetupSubtitle.
  ///
  /// In ar, this message translates to:
  /// **'خطوات بسيطة لتخصيص تجربتك وترشيح أفضل الممرضين لك'**
  String get profileSetupSubtitle;

  /// No description provided for @stepPersonal.
  ///
  /// In ar, this message translates to:
  /// **'البيانات الشخصية'**
  String get stepPersonal;

  /// No description provided for @stepLocation.
  ///
  /// In ar, this message translates to:
  /// **'الموقع والمحافظة'**
  String get stepLocation;

  /// No description provided for @stepNursingType.
  ///
  /// In ar, this message translates to:
  /// **'نوع التمريض المطلوب'**
  String get stepNursingType;

  /// No description provided for @governorate.
  ///
  /// In ar, this message translates to:
  /// **'المحافظة'**
  String get governorate;

  /// No description provided for @selectGovernorate.
  ///
  /// In ar, this message translates to:
  /// **'اختر المحافظة في مصر'**
  String get selectGovernorate;

  /// No description provided for @city.
  ///
  /// In ar, this message translates to:
  /// **'المدينة / المركز'**
  String get city;

  /// No description provided for @selectCity.
  ///
  /// In ar, this message translates to:
  /// **'اختر المدينة أو المركز'**
  String get selectCity;

  /// No description provided for @whatNursingDoYouNeed.
  ///
  /// In ar, this message translates to:
  /// **'ما هو نوع التمريض أو الخدمة التي تبحث عنها؟'**
  String get whatNursingDoYouNeed;

  /// No description provided for @selectSpecialtiesOrServices.
  ///
  /// In ar, this message translates to:
  /// **'يمكنك اختيار أكثر من تخصص أو خدمة للترشيح المباشر'**
  String get selectSpecialtiesOrServices;

  /// No description provided for @saveAndContinue.
  ///
  /// In ar, this message translates to:
  /// **'حفظ ومتابعة'**
  String get saveAndContinue;

  /// No description provided for @recommendedForYou.
  ///
  /// In ar, this message translates to:
  /// **'ترشيحات مقترحة لك'**
  String get recommendedForYou;

  /// No description provided for @basedOnYourNeeds.
  ///
  /// In ar, this message translates to:
  /// **'بناءً على موقعك ونوع التمريض المطلوب'**
  String get basedOnYourNeeds;

  /// No description provided for @quickActions.
  ///
  /// In ar, this message translates to:
  /// **'خدمات سريعة'**
  String get quickActions;

  /// No description provided for @requestCareNow.
  ///
  /// In ar, this message translates to:
  /// **'طلب تمريض جديد'**
  String get requestCareNow;

  /// No description provided for @exploreSpecialties.
  ///
  /// In ar, this message translates to:
  /// **'تصفح التخصصات'**
  String get exploreSpecialties;

  /// No description provided for @navSettings.
  ///
  /// In ar, this message translates to:
  /// **'الإعدادات'**
  String get navSettings;

  /// No description provided for @settings.
  ///
  /// In ar, this message translates to:
  /// **'الإعدادات'**
  String get settings;

  /// No description provided for @accountSettings.
  ///
  /// In ar, this message translates to:
  /// **'إعدادات الحساب'**
  String get accountSettings;

  /// No description provided for @appPreferences.
  ///
  /// In ar, this message translates to:
  /// **'تفضيلات التطبيق'**
  String get appPreferences;

  /// No description provided for @supportAndHelp.
  ///
  /// In ar, this message translates to:
  /// **'الدعم والمساعدة'**
  String get supportAndHelp;

  /// No description provided for @faq.
  ///
  /// In ar, this message translates to:
  /// **'الأسئلة الشائعة'**
  String get faq;

  /// No description provided for @contactSupport.
  ///
  /// In ar, this message translates to:
  /// **'تواصل مع خدمة العملاء'**
  String get contactSupport;

  /// No description provided for @reportProblem.
  ///
  /// In ar, this message translates to:
  /// **'تقديم شكوى أو اقتراح'**
  String get reportProblem;

  /// No description provided for @complaintSent.
  ///
  /// In ar, this message translates to:
  /// **'تم إرسال رسالتك بنجاح، وسنتواصل معك قريباً'**
  String get complaintSent;

  /// No description provided for @problemDescription.
  ///
  /// In ar, this message translates to:
  /// **'تفاصيل المشكلة أو الشكوى'**
  String get problemDescription;

  /// No description provided for @whatsappSupport.
  ///
  /// In ar, this message translates to:
  /// **'محادثة عبر واتساب'**
  String get whatsappSupport;

  /// No description provided for @callSupport.
  ///
  /// In ar, this message translates to:
  /// **'اتصال بفريق الدعم'**
  String get callSupport;

  /// No description provided for @emailSupport.
  ///
  /// In ar, this message translates to:
  /// **'راسلنا عبر البريد'**
  String get emailSupport;

  /// No description provided for @termsAndPrivacy.
  ///
  /// In ar, this message translates to:
  /// **'الشروط والأحكام وسياسة الخصوصية'**
  String get termsAndPrivacy;

  /// No description provided for @appVersion.
  ///
  /// In ar, this message translates to:
  /// **'إصدار التطبيق'**
  String get appVersion;

  /// No description provided for @profileUpdated.
  ///
  /// In ar, this message translates to:
  /// **'تم تحديث الملف الشخصي بنجاح'**
  String get profileUpdated;
}

class _AppLocalizationsDelegate
    extends LocalizationsDelegate<AppLocalizations> {
  const _AppLocalizationsDelegate();

  @override
  Future<AppLocalizations> load(Locale locale) {
    return SynchronousFuture<AppLocalizations>(lookupAppLocalizations(locale));
  }

  @override
  bool isSupported(Locale locale) =>
      <String>['ar', 'en'].contains(locale.languageCode);

  @override
  bool shouldReload(_AppLocalizationsDelegate old) => false;
}

AppLocalizations lookupAppLocalizations(Locale locale) {
  // Lookup logic when only language code is specified.
  switch (locale.languageCode) {
    case 'ar':
      return AppLocalizationsAr();
    case 'en':
      return AppLocalizationsEn();
  }

  throw FlutterError(
      'AppLocalizations.delegate failed to load unsupported locale "$locale". This is likely '
      'an issue with the localizations generation tool. Please file an issue '
      'on GitHub with a reproducible sample app and the gen-l10n configuration '
      'that was used.');
}

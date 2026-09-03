# 📋 تقرير شامل: كل حاجة ناقصة في تطبيق سَنَد — بالترتيب المنطقي للتنفيذ

> حللت كل ملفات المشروع (الكود، الـ assets، الـ config) بالكامل. التطبيق عنده **أساس كود جيد جداً** (شاشات + models + services + state management + l10n) لكن **مش قابل للتثبيت حالياً** لأنه ينقصه أساسيات البنية التحتية. هنا القائمة الكاملة بالترتيب المنطقي من الأهم للأقل.

---

## المرحلة 0 — البنية التحتية (لازم تتعمل الأول عشان التطبيق يتبنى أصلاً)

### 0.1 🔴 إنشاء مجلد `android/` — **غير موجود!**
> [!CAUTION]
> مفيش مجلد `android/` خالص! التطبيق **لا يمكن بناؤه أو تثبيته** بدونه.

**المطلوب:**
- تشغيل `flutter create --project-name sanad --org com.sanad .` من داخل مجلد `mobile/` عشان يتولد مجلد `android/` (و `ios/`, `web/`, `test/`, etc.)
- أو `flutter create --platforms android .` لو عايز أندرويد بس
- ده هيولّد: `android/app/build.gradle`, `android/build.gradle`, `AndroidManifest.xml`, `MainActivity.kt`, etc.

### 0.2 🔴 تشغيل `flutter pub get`
**المطلوب:**
- بعد توليد المجلدات، تشغيل `flutter pub get` لتحميل كل الـ dependencies من pubspec.yaml
- ده هيولّد: `.dart_tool/`, `pubspec.lock`, الـ generated localization files

### 0.3 🔴 توليد ملفات الترجمة (l10n code generation)
**المطلوب:**
- الكود بيعمل `import 'l10n/app_localizations.dart'` — الملف ده **لازم يتولد** من `app_ar.arb` و `app_en.arb`
- `flutter gen-l10n` أو `flutter pub get` (مع `generate: true` في pubspec.yaml)
- بدون ده، كل الشاشات هتفشل في الـ compile

### 0.4 🔴 توليد أيقونات التطبيق (App Icons)
**المطلوب:**
- ملفات `app_icon.png` و `app_icon_foreground.png` موجودين ✅
- لكن لازم تشغيل: `dart run flutter_launcher_icons` عشان تتوزع الأيقونات على `android/app/src/main/res/mipmap-*`
- بدون ده، التطبيق هيبان بأيقونة Flutter الافتراضية

### 0.5 🔴 توليد Native Splash Screen
**المطلوب:**
- تشغيل: `dart run flutter_native_splash:create`
- الـ config موجود في pubspec.yaml ✅ بس لازم التوليد الفعلي

---

## المرحلة 1 — إعدادات الأندرويد الاحترافية

### 1.1 🟡 إعداد `android/app/build.gradle`
**المطلوب بعد التوليد:**
- تعديل `applicationId` لـ `com.sanad.app` (أو اسم الباكج اللي تختاره)
- تعديل `minSdkVersion` → `21` كحد أدنى (أو `23` لو عايز تغطي 97%+ من الأجهزة)
- `targetSdkVersion` → `34` (أحدث متطلبات Google Play)
- `compileSdkVersion` → `34`
- تفعيل ProGuard/R8 للـ release build عشان حجم APK أصغر وأسرع
- إضافة signing config للـ release APK

### 1.2 🟡 إعداد `AndroidManifest.xml`
**المطلوب:**
- إضافة permissions:
  ```xml
  <uses-permission android:name="android.permission.INTERNET" />
  <uses-permission android:name="android.permission.CAMERA" />  <!-- لتصوير صورة البروفايل -->
  <uses-permission android:name="android.permission.READ_EXTERNAL_STORAGE" />
  ```
- تعديل `android:label` لـ `"سَنَد"` (اسم التطبيق)
- إضافة `android:usesCleartextTraffic="true"` لو هتستخدم HTTP للتطوير (localhost)

### 1.3 🟡 توليد Release APK/AAB
**المطلوب:**
- إنشاء keystore: `keytool -genkey -v -keystore sanad-release.jks ...`
- إعداد `android/key.properties`
- بناء: `flutter build apk --release` أو `flutter build appbundle --release`

---

## المرحلة 2 — الـ Responsive Design (عشان يشتغل على كل الشاشات)

> [!IMPORTANT]
> التطبيق حالياً **مفيش فيه responsive design** خالص. كل الأبعاد ثابتة (hardcoded). ده هيسبب مشاكل على الشاشات الصغيرة والكبيرة.

### 2.1 🔴 إنشاء `responsive_utils.dart` مركزي
**المطلوب:**
```
lib/core/responsive.dart
```
- كلاس فيه helper functions بتستخدم `MediaQuery.sizeOf(context)` للحصول على عرض وارتفاع الشاشة
- تعريف breakpoints: `compact` (< 600dp), `medium` (600-840dp), `expanded` (> 840dp)
- دوال لتحويل الأحجام الثابتة لأحجام نسبية

### 2.2 🟡 تعديل كل الشاشات لاستخدام responsive padding/sizes

**الملفات المطلوب تعديلها:**

| الملف | المشكلة |
|---|---|
| [home_screen.dart](file:///c:/Users/Mahmoud Eid/Desktop/home care app/mobile/lib/screens/home_screen.dart) | Padding ثابت `20px` - على شاشات 5" هياكل مساحة كبيرة، على تابلت هيبان ضيق |
| [login_screen.dart](file:///c:/Users/Mahmoud Eid/Desktop/home care app/mobile/lib/screens/auth/login_screen.dart) | Logo حجم ثابت `64x64`، padding ثابت `28px`، `SizedBox(height: 40)` ثابت |
| [register_screen.dart](file:///c:/Users/Mahmoud Eid/Desktop/home care app/mobile/lib/screens/auth/register_screen.dart) | نفس المشاكل |
| [profile_screen.dart](file:///c:/Users/Mahmoud Eid/Desktop/home care app/mobile/lib/screens/profile_screen.dart) | Avatar `78x78` ثابت، camera icon `26x26` ثابت |
| [nurse_detail_screen.dart](file:///c:/Users/Mahmoud Eid/Desktop/home care app/mobile/lib/screens/nurse_detail_screen.dart) | Avatar `68` ثابت، bottom bar padding ثابت |
| [chat_thread_screen.dart](file:///c:/Users/Mahmoud Eid/Desktop/home care app/mobile/lib/screens/chat_thread_screen.dart) | Bubble `maxWidth: 0.72 * width` ✅ (ده responsive) لكن font sizes ثابتة |
| [care_request_form_screen.dart](file:///c:/Users/Mahmoud Eid/Desktop/home care app/mobile/lib/screens/care_request/care_request_form_screen.dart) | كل الـ spacing ثابت |
| [splash_screen.dart](file:///c:/Users/Mahmoud Eid/Desktop/home care app/mobile/lib/screens/splash_screen.dart) | Mark `84x84` ثابت |

### 2.3 🟡 استخدام `LayoutBuilder` في الأماكن الحرجة
**المطلوب:**
- Nurse cards على التابلت → ممكن تبقى grid بدل list
- Care request form → على الشاشات العريضة ممكن يبقى 2 columns

### 2.4 🟡 التأكد من عدم overflow على شاشات صغيرة
**الملفات المعرضة:**
- [bookings_screen.dart](file:///c:/Users/Mahmoud Eid/Desktop/home care app/mobile/lib/screens/bookings_screen.dart) — Row فيه status pill + date ممكن يعمل overflow لو النص طويل
- [nurse_card.dart](file:///c:/Users/Mahmoud Eid/Desktop/home care app/mobile/lib/widgets/nurse_card.dart) — Row فيه nurse name + verified badge ممكن يعمل overflow
- [nurse_detail_screen.dart](file:///c:/Users/Mahmoud Eid/Desktop/home care app/mobile/lib/screens/nurse_detail_screen.dart#L93-L103) — Row فيه rating + experience — على شاشات ضيقة ممكن يعمل overflow

---

## المرحلة 3 — Navigation محترف (GoRouter)

### 3.1 🟡 استبدال Navigator.push بـ GoRouter
> [!NOTE]
> حسب الـ ARCHITECTURE.md، التطبيق المفروض يستخدم GoRouter لكنه **مش موجود** في الكود ولا في pubspec.yaml.

**المطلوب:**
- إضافة `go_router` في pubspec.yaml
- إنشاء [lib/core/router.dart](file:///c:/Users/Mahmoud Eid/Desktop/home care app/mobile/lib/core/router.dart) مركزي
- تعريف كل الـ routes بـ named routes
- Deep linking support
- Route guards (authenticated vs unauthenticated)
- ده هيحسّن الـ navigation ويخليه احترافي ويمنع stack issues

**ليه مهم؟**
- حالياً `Navigator.push/pushAndRemoveUntil` في كل مكان → ممكن يسبب back button issues
- مفيش deep linking → مهم لو عايز notifications توديك لصفحة معينة
- مفيش URL-based navigation → مهم للويب لو بنيته بعدين

---

## المرحلة 4 — الأداء والسرعة

### 4.1 🔴 إضافة `const` constructors لكل الـ widgets الممكنة
**المطلوب:** مراجعة كل widget وإضافة `const` لتقليل الـ rebuilds. معظم الكود فيه `const` ✅ لكن في أماكن ناقصة.

### 4.2 🟡 Pagination / Infinite Scrolling
**المشكلة:**
- [home_screen.dart](file:///c:/Users/Mahmoud Eid/Desktop/home care app/mobile/lib/screens/home_screen.dart#L12-L14) — `NurseApi().search()` **بيجيب كل الممرضين مرة واحدة**! لو 1000 ممرض، التطبيق هيفضل يحمّل
- [bookings_screen.dart](file:///c:/Users/Mahmoud Eid/Desktop/home care app/mobile/lib/screens/bookings_screen.dart#L17) — `BookingApi().listMine()` نفس المشكلة
- [chat_list_screen.dart](file:///c:/Users/Mahmoud Eid/Desktop/home care app/mobile/lib/screens/chat_list_screen.dart#L11) — نفس المشكلة
- [chat_thread_screen.dart](file:///c:/Users/Mahmoud Eid/Desktop/home care app/mobile/lib/screens/chat_thread_screen.dart#L49) — الرسائل كلها مرة واحدة

**الحل:**
- إضافة pagination parameters (offset/limit) للـ API calls
- إضافة infinite scroll listener على الـ scroll controllers
- عرض loading indicator أسفل القائمة أثناء تحميل الصفحة التالية

### 4.3 🟡 Image Caching و Optimization
**الموجود:** `cached_network_image` مستخدم في `NurseAvatar` ✅
**الناقص:**
- مفيش تحديد لحجم الـ cache
- مفيش placeholder animations (shimmer effects) — حالياً مجرد لون ثابت
- مفيش image compression parameters عند التحميل

### 4.4 🟡 إضافة Shimmer Loading
**المطلوب:**
- بدل `CircularProgressIndicator` في كل مكان، استخدم shimmer/skeleton loading
- ده يخلي التطبيق يحس بأنه أسرع (perceived performance)
- إضافة `shimmer` package في pubspec.yaml
- إنشاء `SkeletonNurseCard`, `SkeletonBookingCard`, etc.

### 4.5 🟡 تقليل rebuilds غير ضرورية
**المشكلة في [root_shell.dart](file:///c:/Users/Mahmoud Eid/Desktop/home care app/mobile/lib/screens/root_shell.dart):**
- `IndexedStack` يبني كل الـ 4 tabs من أول مرة حتى لو المستخدم ما فتحهمش
- **الحل:** Lazy loading — `AutomaticKeepAliveClientMixin` أو بناء الـ tab بس لما يتفتح أول مرة

---

## المرحلة 5 — الـ Search الحقيقي

### 5.1 🔴 تفعيل البحث في الـ Home Screen
**المشكلة:** [home_screen.dart L45-L57](file:///c:/Users/Mahmoud Eid/Desktop/home care app/mobile/lib/screens/home_screen.dart#L45-L57) — البحث **decorative فقط**! مجرد Container شكله search bar بس مفيش أي functionality.

**المطلوب:**
- تحويله لـ `TextField` حقيقي أو `SearchBar`
- ربطه بـ `NurseApi().search(query: ...)` مع debounce
- إضافة search suggestions / autocomplete
- إضافة filter options (تخصص، منطقة، سعر)

---

## المرحلة 6 — Object Storage (رفع الصور)

### 6.1 🔴 ربط Object Storage Provider
**المشكلة:** [object_storage_uploader.dart](file:///c:/Users/Mahmoud Eid/Desktop/home care app/mobile/lib/services/object_storage_uploader.dart) — التطبيق بيستخدم `UnconfiguredObjectStorageUploader` اللي **بيرمي exception**! يعني رفع صور البروفايل **مش شغال**.

**الحل (اختار واحد):**
1. **Firebase Storage** — الأسهل مع Flutter
2. **AWS S3** — Presigned URLs من الـ backend
3. **Cloudinary** — بسيط وعنده free tier
4. **Supabase Storage** — لو بتستخدم Supabase

**المطلوب:**
- إنشاء implementation فعلية لـ `ObjectStorageUploader`
- ربطها بالـ backend (presigned URL أو direct upload)
- إضافة image compression قبل الرفع

---

## المرحلة 7 — Push Notifications

### 7.1 🟡 إضافة Firebase Cloud Messaging (FCM)
**المشكلة:** الـ ARCHITECTURE.md بيذكر `firebase_messaging` بس **مش موجود** في pubspec.yaml ولا في الكود.

**المطلوب:**
- إضافة `firebase_messaging` و `firebase_core` في pubspec.yaml
- إنشاء Firebase project وربطه
- إنشاء [lib/services/notification_service.dart](file:///c:/Users/Mahmoud Eid/Desktop/home care app/mobile/lib/services/notification_service.dart)
- Handle notifications:
  - طلب جديد وصل للممرض
  - الممرض رد على الطلب (قبول/رفض)
  - رسالة جديدة في الشات
  - Booking status تغير
- إضافة `flutter_local_notifications` لعرض الـ notifications أثناء استخدام التطبيق

---

## المرحلة 8 — تجربة المستخدم (UX Improvements)

### 8.1 🟡 إضافة Onboarding Screen
**المطلوب:**
- شاشة ترحيب (3-4 slides) أول مرة المستخدم يفتح التطبيق
- توضيح خطوات استخدام التطبيق
- حفظ "شافها قبل كده" في SharedPreferences

### 8.2 🟡 إضافة Dark Mode
**المشكلة:** حالياً فيه Light theme فقط في [app_theme.dart](file:///c:/Users/Mahmoud Eid/Desktop/home care app/mobile/lib/theme/app_theme.dart).

**المطلوب:**
- إضافة `AppTheme.dark(locale)` method
- إضافة theme toggle في Profile screen
- ربط theme بـ `StateProvider<ThemeMode>`

### 8.3 🟡 Animations وTransitions
**المطلوب:**
- إضافة `Hero` animations بين NurseCard و NurseDetailScreen
- إضافة custom page transitions (slide, fade)
- إضافة subtle animations:
  - Star rating tap animation
  - Button press feedback
  - List item appearance animation (staggered)

### 8.4 🟡 Empty States محسنة
**المشكلة:** الـ empty states حالياً مجرد نص. على سبيل المثال:
- [bookings_screen.dart L73](file:///c:/Users/Mahmoud Eid/Desktop/home care app/mobile/lib/screens/bookings_screen.dart#L73) — `Text(t.noNursesFound)` ← ده حتى النص غلط! المفروض يقول "مفيش حجوزات"
- [chat_list_screen.dart L53](file:///c:/Users/Mahmoud Eid/Desktop/home care app/mobile/lib/screens/chat_list_screen.dart#L53)

**المطلوب:**
- إضافة illustrations/icons جذابة مع النص
- إضافة CTA button (مثلاً "ابدأ بالبحث عن ممرض")

### 8.5 🟡 Input Validation محسنة
**المطلوب:**
- Real-time validation (مش بس عند الضغط على Submit)
- Visual feedback أثناء الكتابة (green check, red border)
- Password strength indicator في شاشة التسجيل

### 8.6 🟡 Haptic Feedback
**المطلوب:**
- `HapticFeedback.lightImpact()` عند الضغط على أزرار مهمة
- `HapticFeedback.mediumImpact()` عند إرسال طلب أو رسالة

---

## المرحلة 9 — أمان وموثوقية

### 9.1 🟡 Error Boundary / Global Error Handler
**المطلوب:**
- إضافة `FlutterError.onError` handler في `main.dart`
- إضافة `PlatformDispatcher.instance.onError` لـ uncaught errors
- تسجيل الأخطاء (Crashlytics/Sentry) بدل ما التطبيق يقفل

### 9.2 🟡 Network Connectivity Handling
**المطلوب:**
- إضافة `connectivity_plus` package
- عرض banner "مفيش إنترنت" أعلى الشاشة لما الاتصال ينقطع
- Retry automatically لما الاتصال يرجع
- Offline caching للبيانات الأساسية

### 9.3 🟡 Certificate Pinning (للإصدار النهائي)
**المطلوب:**
- SSL certificate pinning في `ApiClient` لمنع MITM attacks

### 9.4 🟡 Biometric Authentication
**المطلوب (اختياري):**
- `local_auth` package لـ fingerprint/face unlock
- تسجيل دخول سريع بالبصمة بدل كتابة الإيميل والباسورد كل مرة

---

## المرحلة 10 — اختبارات (Testing)

### 10.1 🔴 مفيش أي اختبارات!
**المشكلة:** مفيش مجلد `test/` خالص في الـ mobile.

**المطلوب:**
- **Unit tests** لـ models (fromJson, toJson, enums)
- **Widget tests** لـ الشاشات الرئيسية (login, register, home)
- **Integration tests** لـ الـ flows الكاملة (login → browse → request → booking)
- هدف: 70%+ code coverage كحد أدنى

---

## المرحلة 11 — تحسينات إضافية (Polish)

### 11.1 🟢 Font Loading Performance
**المشكلة:** `google_fonts` بيحمل الخطوط من الإنترنت أول مرة → بطء أول تحميل.

**الحل:**
- Bundle الخطوط locally: `GoogleFonts.config.allowRuntimeFetching = false;`
- إضافة ملفات الخطوط في `assets/fonts/` وتعريفها في pubspec.yaml

### 11.2 🟢 App Size Optimization
**المطلوب:**
- `flutter build apk --split-per-abi` لتقليل حجم APK
- أو `flutter build appbundle` (AAB) — Google Play بيعمل split تلقائي
- إزالة unused packages
- تفعيل `--tree-shake-icons` (مفعّل بشكل افتراضي في release builds)

### 11.3 🟢 Accessibility
**المطلوب:**
- إضافة `Semantics` labels لكل الأيقونات والصور
- التأكد من contrast ratio كافي (WCAG 2.1 AA)
- اختبار مع screen readers (TalkBack)

### 11.4 🟢 التاريخ والتوقيت
**المشكلة:** التاريخ بيتعرض بصيغة `YYYY-MM-DD` في كل مكان بدل صيغة عربية.

**الحل:**
- استخدام `intl` package (موجود ✅) مع `DateFormat.yMMMd('ar')`
- عرض التاريخ بصيغة "١ سبتمبر ٢٠٢٦" بدل "2026-09-01"

### 11.5 🟢 عملة الأسعار
**المشكلة:** الأسعار بتتعرض رقم فقط بدون عملة. مثلاً `350` بدل `٣٥٠ ج.م` أو `350 EGP`.

**الحل:**
- إضافة currency formatter
- عرض العملة المناسبة حسب الـ locale

---

## ملخص الأولويات

| الأولوية | المهمة | الحالة |
|---|---|---|
| 🔴 **حرج** | إنشاء مجلد `android/` | ⬜ |
| 🔴 **حرج** | `flutter pub get` | ⬜ |
| 🔴 **حرج** | توليد l10n files | ⬜ |
| 🔴 **حرج** | توليد app icons | ⬜ |
| 🔴 **حرج** | توليد native splash | ⬜ |
| 🔴 **حرج** | إعدادات Android (manifest, gradle) | ⬜ |
| 🔴 **حرج** | تفعيل البحث الحقيقي | ⬜ |
| 🔴 **حرج** | ربط Object Storage (رفع الصور) | ⬜ |
| 🟡 **مهم** | Responsive Design لكل الشاشات | ⬜ |
| 🟡 **مهم** | GoRouter navigation | ⬜ |
| 🟡 **مهم** | Pagination / Infinite scroll | ⬜ |
| 🟡 **مهم** | Shimmer loading | ⬜ |
| 🟡 **مهم** | Push Notifications (FCM) | ⬜ |
| 🟡 **مهم** | Connectivity handling | ⬜ |
| 🟡 **مهم** | Empty states + bug fix (نص غلط) | ⬜ |
| 🟡 **مهم** | Dark Mode | ⬜ |
| 🟡 **مهم** | Error handling عالمي | ⬜ |
| 🟡 **مهم** | Animations | ⬜ |
| 🟡 **مهم** | اختبارات (Unit + Widget) | ⬜ |
| 🟢 **تحسين** | Bundle fonts locally | ⬜ |
| 🟢 **تحسين** | تنسيق التاريخ بالعربي | ⬜ |
| 🟢 **تحسين** | عرض العملة مع الأسعار | ⬜ |
| 🟢 **تحسين** | App size optimization | ⬜ |
| 🟢 **تحسين** | Accessibility | ⬜ |
| 🟢 **تحسين** | Biometric auth | ⬜ |
| 🟢 **تحسين** | Onboarding screens | ⬜ |

---

## Open Questions

> [!IMPORTANT]
> 1. **هل عندك Flutter SDK متسطب على جهازك؟** — لو لا، ده أول حاجة لازم تتعمل.
> 2. **هل عندك Android Studio / Android SDK متسطب؟** — لازم لبناء APK.
> 3. **هل عندك حساب Firebase؟** — لو عايز Push Notifications ورفع صور.
> 4. **الـ Backend شغال فعلاً؟** — الكود مكتوب لـ localhost:8000، هل الـ backend running؟
> 5. **هل عايزني أبدأ أنفذ المراحل دي واحدة واحدة؟** — لو عايز ابدأ من المرحلة 0 (البنية التحتية) ونمشي بالترتيب.
> 6. **إيه اسم الباكج (package name) اللي عايزه للتطبيق؟** — مثلاً `com.sanad.homecare`


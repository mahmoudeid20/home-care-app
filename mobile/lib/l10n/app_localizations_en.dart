// ignore: unused_import
import 'package:intl/intl.dart' as intl;
import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for English (`en`).
class AppLocalizationsEn extends AppLocalizations {
  AppLocalizationsEn([String locale = 'en']) : super(locale);

  @override
  String get brandName => 'Sanad';

  @override
  String get brandSub => 'Trusted home care';

  @override
  String homeGreeting(String name) {
    return 'Hi $name 👋';
  }

  @override
  String get homeSub => 'Who do we need today?';

  @override
  String get searchPlaceholder => 'Search a specialty or area…';

  @override
  String get topRatedNearYou => 'Top rated near you';

  @override
  String get seeAll => 'See all';

  @override
  String get verified => 'Verified';

  @override
  String get bookNow => 'Book now';

  @override
  String get navHome => 'Home';

  @override
  String get navBookings => 'Bookings';

  @override
  String get navChat => 'Chat';

  @override
  String get navProfile => 'Profile';

  @override
  String get myBookings => 'My bookings';

  @override
  String get statusPending => 'Pending approval';

  @override
  String get statusAccepted => 'Accepted';

  @override
  String get statusConfirmed => 'Confirmed';

  @override
  String get statusActive => 'In progress';

  @override
  String get statusCompleted => 'Completed';

  @override
  String get statusReviewed => 'Reviewed';

  @override
  String get statusCancelled => 'Cancelled';

  @override
  String get statusExpired => 'Expired';

  @override
  String get login => 'Log in';

  @override
  String get register => 'Create account';

  @override
  String get email => 'Email';

  @override
  String get password => 'Password';

  @override
  String get iAmPatient => 'I\'m a patient';

  @override
  String get iAmNurse => 'I\'m a nurse';

  @override
  String get language => 'Language';

  @override
  String get welcomeBack => 'Welcome back';

  @override
  String get loginSubtitle => 'Log in to continue';

  @override
  String get createAccountTitle => 'Create your account';

  @override
  String get createAccountSubtitle => 'Choose an account type to get started';

  @override
  String get phoneOptional => 'Phone number (optional)';

  @override
  String get confirmPassword => 'Confirm password';

  @override
  String get dontHaveAccount => 'Don\'t have an account?';

  @override
  String get alreadyHaveAccount => 'Already have an account?';

  @override
  String get passwordsDontMatch => 'Passwords don\'t match';

  @override
  String get passwordTooWeak =>
      'Must be at least 8 characters with a letter and a number';

  @override
  String get invalidEmail => 'Enter a valid email address';

  @override
  String get requiredField => 'This field is required';

  @override
  String get connectionError => 'No internet connection. Please try again.';

  @override
  String get connectionTimeout =>
      'The connection is taking too long. Please try again.';

  @override
  String get retry => 'Retry';

  @override
  String get logout => 'Log out';

  @override
  String get noNursesFound => 'No nurses available in this area right now';

  @override
  String get somethingWentWrong => 'Something went wrong. Please try again.';

  @override
  String get sendRequest => 'Send request to this nurse';

  @override
  String get about => 'About';

  @override
  String get servicesAndPrices => 'Services & prices';

  @override
  String get reviews => 'Reviews';

  @override
  String get yearsExperience => 'years experience';

  @override
  String get newRequestTitle => 'New care request';

  @override
  String get patientInfoSection => '1. Patient information';

  @override
  String get careNeededSection => '2. Care needed';

  @override
  String get nurseRequirementsSection => '3. Nurse preferences (optional)';

  @override
  String get locationSection => '4. Location';

  @override
  String get scheduleSection => '5. Schedule';

  @override
  String get budgetSection => '6. Budget (optional)';

  @override
  String get patientNameLabel => 'Patient\'s name';

  @override
  String get patientAgeLabel => 'Age';

  @override
  String get patientGenderLabel => 'Gender';

  @override
  String get male => 'Male';

  @override
  String get female => 'Female';

  @override
  String get medicalConditionLabel => 'Medical condition (brief description)';

  @override
  String get mobilityStatusLabel => 'Mobility status';

  @override
  String get mobilityIndependent => 'Independent';

  @override
  String get mobilityAssistance => 'Needs assistance';

  @override
  String get mobilityWheelchair => 'Wheelchair';

  @override
  String get mobilityBedridden => 'Bedridden';

  @override
  String get specialRequirementsLabel => 'Special requirements (optional)';

  @override
  String get selectServices => 'Select the service needed';

  @override
  String get governorateLabel => 'Governorate';

  @override
  String get cityLabel => 'City/District';

  @override
  String get areaLabel => 'Area (optional)';

  @override
  String get startDateLabel => 'Start date';

  @override
  String get endDateLabel => 'End date (optional)';

  @override
  String get hoursPerDayLabel => 'Hours per day (optional)';

  @override
  String get paymentFrequencyLabel => 'Payment frequency';

  @override
  String get hourly => 'Hourly';

  @override
  String get daily => 'Daily';

  @override
  String get weekly => 'Weekly';

  @override
  String get monthly => 'Monthly';

  @override
  String get budgetMinLabel => 'Minimum (optional)';

  @override
  String get budgetMaxLabel => 'Maximum (optional)';

  @override
  String get submitRequest => 'Submit request';

  @override
  String get requestSentTitle => 'Request sent';

  @override
  String get requestSentBody =>
      'Your request was sent to the nurse. You\'ll get a notification when they respond.';

  @override
  String get backToHome => 'Back to home';

  @override
  String get pickDate => 'Pick a date';

  @override
  String stepOf(String current, String total) {
    return 'Step $current of $total';
  }

  @override
  String get next => 'Next';

  @override
  String get back => 'Back';

  @override
  String get noConversationsYet => 'No conversations yet';

  @override
  String get messageHint => 'Type a message…';

  @override
  String get reconnecting => 'Reconnecting…';

  @override
  String get connectionLost => 'Connection lost';

  @override
  String get cantAccessConversation =>
      'You don\'t have access to this conversation';

  @override
  String get send => 'Send';

  @override
  String get choosePhotoSource => 'Choose photo source';

  @override
  String get takePhoto => 'Take a photo';

  @override
  String get chooseFromGallery => 'Choose from gallery';

  @override
  String get uploadingPhoto => 'Uploading photo…';

  @override
  String get photoUpdated => 'Your photo was updated';

  @override
  String get storageNotConfigured =>
      'Photo upload isn\'t available yet — needs an object storage provider connected';

  @override
  String get newRequests => 'New requests';

  @override
  String get noRequestsYet => 'No requests yet';

  @override
  String get appPending => 'Awaiting your response';

  @override
  String get appAccepted => 'Accepted';

  @override
  String get appRejected => 'Rejected';

  @override
  String get appWithdrawn => 'Withdrawn';

  @override
  String get accept => 'Accept';

  @override
  String get reject => 'Reject';

  @override
  String get acceptRequestConfirm =>
      'Accepting this will turn it into a confirmed booking. Confirm?';

  @override
  String get rejectReasonHint => 'Reason for rejecting (optional)';

  @override
  String get requestAccepted => 'Request accepted and booking created';

  @override
  String get requestRejected => 'Request rejected';

  @override
  String get patientLabel => 'Patient';

  @override
  String get budgetLabel => 'Proposed budget';

  @override
  String get notSpecified => 'Not specified';

  @override
  String get mySentRequests => 'My sent requests';

  @override
  String get noSentRequestsYet => 'You haven\'t sent any requests yet';

  @override
  String get withdrawRequest => 'Withdraw request';

  @override
  String get requestWithdrawn => 'Request withdrawn';

  @override
  String get leaveReview => 'Leave a review';

  @override
  String get overallRating => 'Overall rating';

  @override
  String get professionalismRating => 'Professionalism';

  @override
  String get communicationRating => 'Communication';

  @override
  String get careQualityRating => 'Care quality';

  @override
  String get commentOptional => 'Comment (optional)';

  @override
  String get submitReview => 'Submit review';

  @override
  String get reviewSubmitted => 'Thanks, your review was saved';

  @override
  String get alreadyReviewed => 'You\'ve already reviewed this booking';

  @override
  String get noReviewsYet => 'No reviews yet';

  @override
  String get noBookingsYet =>
      'No bookings yet — start by searching for a nurse';

  @override
  String get startSearching => 'Start searching';

  @override
  String get searchNurses => 'Search for a nurse…';

  @override
  String get egp => 'EGP';

  @override
  String get darkMode => 'Dark mode';

  @override
  String get lightMode => 'Light mode';

  @override
  String get noChatsYet => 'No conversations yet — start a chat with a nurse';

  @override
  String get browseNurses => 'Browse nurses';

  @override
  String get filterBySpecialty => 'Filter by specialty';

  @override
  String get allSpecialties => 'All specialties';

  @override
  String get clearSearch => 'Clear search';

  @override
  String get onboardingTitle1 => 'Trusted Home Care at Your Doorstep';

  @override
  String get onboardingSub1 =>
      'Find verified and certified nurses for elderly and patient care with complete trust and peace of mind.';

  @override
  String get onboardingTitle2 => 'Certified & Verified Medical Staff';

  @override
  String get onboardingSub2 =>
      'All Sanad nurses have undergone strict identity, qualification, and background verifications.';

  @override
  String get onboardingTitle3 => 'Effortless Booking & Direct Contact';

  @override
  String get onboardingSub3 =>
      'Choose your location and required care, receive instant suggestions, and chat directly with nurses.';

  @override
  String get skip => 'Skip';

  @override
  String get startNow => 'Get Started';

  @override
  String get fullName => 'Full Quadruple Name';

  @override
  String get fullNameQuadrupleHint => 'e.g. Mahmoud Ahmed Ibrahim Elsayed';

  @override
  String get fullNameQuadrupleValidation =>
      'Please enter your full name (at least 4 names)';

  @override
  String get username => 'Username';

  @override
  String get usernameHint => 'e.g. mahmoud_eid';

  @override
  String get usernameValidation => 'Username must be at least 3 characters';

  @override
  String get profileSetupTitle => 'Complete Your Profile';

  @override
  String get profileSetupSubtitle =>
      'Quick steps to personalize your experience and recommend the best nurses';

  @override
  String get stepPersonal => 'Personal Info';

  @override
  String get stepLocation => 'Location & Governorate';

  @override
  String get stepNursingType => 'Required Care Type';

  @override
  String get governorate => 'Governorate';

  @override
  String get selectGovernorate => 'Select Egyptian Governorate';

  @override
  String get city => 'City / District';

  @override
  String get selectCity => 'Select City or District';

  @override
  String get whatNursingDoYouNeed =>
      'What type of nursing or service are you looking for?';

  @override
  String get selectSpecialtiesOrServices =>
      'Select one or more specialties or services for targeted recommendations';

  @override
  String get saveAndContinue => 'Save & Continue';

  @override
  String get recommendedForYou => 'Recommended for You';

  @override
  String get basedOnYourNeeds => 'Based on your location and care needs';

  @override
  String get quickActions => 'Quick Services';

  @override
  String get requestCareNow => 'New Care Request';

  @override
  String get exploreSpecialties => 'Explore Specialties';

  @override
  String get navSettings => 'Settings';

  @override
  String get settings => 'Settings';

  @override
  String get accountSettings => 'Account Settings';

  @override
  String get appPreferences => 'App Preferences';

  @override
  String get supportAndHelp => 'Support & Help';

  @override
  String get faq => 'Frequently Asked Questions';

  @override
  String get contactSupport => 'Contact Customer Care';

  @override
  String get reportProblem => 'Report a Problem or Feedback';

  @override
  String get complaintSent =>
      'Your message was sent successfully. We will reach out shortly.';

  @override
  String get problemDescription => 'Problem or complaint details';

  @override
  String get whatsappSupport => 'Chat via WhatsApp';

  @override
  String get callSupport => 'Call Support Team';

  @override
  String get emailSupport => 'Email Us';

  @override
  String get termsAndPrivacy => 'Terms & Privacy Policy';

  @override
  String get appVersion => 'App Version';

  @override
  String get profileUpdated => 'Profile updated successfully';
}

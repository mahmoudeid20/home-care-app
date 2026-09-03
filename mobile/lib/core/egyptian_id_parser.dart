class EgyptianIdInfo {
  final String id;
  final bool isValid;
  final DateTime? birthDate;
  final String? governorate;
  final String? gender;
  final String? errorMessage;

  const EgyptianIdInfo({
    required this.id,
    required this.isValid,
    this.birthDate,
    this.governorate,
    this.gender,
    this.errorMessage,
  });
}

const Map<String, String> egyptGovernorateCodes = {
  "01": "القاهرة",
  "02": "الإسكندرية",
  "03": "بورسعيد",
  "04": "السويس",
  "11": "دمياط",
  "12": "الدقهلية",
  "13": "الشرقية",
  "14": "القليوبية",
  "15": "كفر الشيخ",
  "16": "الغربية",
  "17": "المنوفية",
  "18": "البحيرة",
  "19": "الإسماعيلية",
  "21": "الجيزة",
  "22": "بني سويف",
  "23": "الفيوم",
  "24": "المنيا",
  "25": "أسيوط",
  "26": "سوهاج",
  "27": "قنا",
  "28": "أسوان",
  "29": "الأقصر",
  "31": "البحر الأحمر",
  "32": "الوادي الجديد",
  "33": "مطروح",
  "34": "شمال سيناء",
  "35": "جنوب سيناء",
  "88": "خارج الجمهورية",
};

String normalizeArabicDigits(String input) {
  const arabic = ['٠', '١', '٢', '٣', '٤', '٥', '٦', '٧', '٨', '٩'];
  const english = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9'];

  String res = input;
  for (int i = 0; i < 10; i++) {
    res = res.replaceAll(arabic[i], english[i]);
  }
  return res;
}

EgyptianIdInfo parseEgyptianId(String rawInput) {
  final normalized = normalizeArabicDigits(rawInput);
  final digitsOnly = normalized.replaceAll(RegExp(r'\D'), '');

  if (digitsOnly.length != 14) {
    return EgyptianIdInfo(
      id: digitsOnly,
      isValid: false,
      errorMessage: 'الرقم القومي يجب أن يتكون من 14 رقماً بالضبط',
    );
  }

  final centuryChar = digitsOnly[0];
  if (centuryChar != '2' && centuryChar != '3') {
    return EgyptianIdInfo(
      id: digitsOnly,
      isValid: false,
      errorMessage: 'الرقم القومي غير صالح (خانة القرن غير صحيحة)',
    );
  }

  final yearPrefix = centuryChar == '2' ? 1900 : 2000;
  final year = yearPrefix + int.parse(digitsOnly.substring(1, 3));
  final month = int.parse(digitsOnly.substring(3, 5));
  final day = int.parse(digitsOnly.substring(5, 7));

  DateTime? birthDate;
  try {
    birthDate = DateTime(year, month, day);
  } catch (_) {
    return EgyptianIdInfo(
      id: digitsOnly,
      isValid: false,
      errorMessage: 'تاريخ الميلاد المشفر في الرقم القومي غير صالح',
    );
  }

  final govCode = digitsOnly.substring(7, 9);
  final governorate = egyptGovernorateCodes[govCode] ?? 'أخرى';

  final genderDigit = int.parse(digitsOnly[12]);
  final gender = (genderDigit % 2 != 0) ? 'ذكر' : 'أنثى';

  return EgyptianIdInfo(
    id: digitsOnly,
    isValid: true,
    birthDate: birthDate,
    governorate: governorate,
    gender: gender,
  );
}

/// Extracts the first valid 14-digit Egyptian National ID found in raw text
String? extractNationalIdFromText(String rawText) {
  final normalized = normalizeArabicDigits(rawText);
  // Match 14 digits starting with 2 or 3 and valid month/day ranges
  final pattern = RegExp(r'\b([23]\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])\d{7})\b');
  final match = pattern.firstMatch(normalized);
  return match?.group(1);
}

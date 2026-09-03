from datetime import date
import re

GOVERNORATE_CODES = {
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
}


class EgyptianNationalIDInfo:
    def __init__(
        self,
        national_id: str,
        is_valid: bool,
        birth_date: date | None = None,
        governorate: str | None = None,
        gender: str | None = None,
        error_message: str | None = None,
    ):
        self.national_id = national_id
        self.is_valid = is_valid
        self.birth_date = birth_date
        self.governorate = governorate
        self.gender = gender
        self.error_message = error_message

    def to_dict(self) -> dict:
        return {
            "national_id": self.national_id,
            "is_valid": self.is_valid,
            "birth_date": self.birth_date.isoformat() if self.birth_date else None,
            "governorate": self.governorate,
            "gender": self.gender,
            "error_message": self.error_message,
        }


def parse_egyptian_national_id(nid: str) -> EgyptianNationalIDInfo:
    nid = re.sub(r"\D", "", nid)
    if len(nid) != 14:
        return EgyptianNationalIDInfo(
            national_id=nid,
            is_valid=False,
            error_message="الرقم القومي يجب أن يتكون من 14 رقماً",
        )

    century_digit = nid[0]
    if century_digit not in ("2", "3"):
        return EgyptianNationalIDInfo(
            national_id=nid,
            is_valid=False,
            error_message="الرقم القومي غير صالح (خانة القرن غير صحيحة)",
        )

    year_prefix = 1900 if century_digit == "2" else 2000
    year = year_prefix + int(nid[1:3])
    month = int(nid[3:5])
    day = int(nid[5:7])

    try:
        birth_date = date(year, month, day)
    except ValueError:
        return EgyptianNationalIDInfo(
            national_id=nid,
            is_valid=False,
            error_message="تاريخ الميلاد المشفر بالرقم القومي غير صالح",
        )

    gov_code = nid[7:9]
    governorate = GOVERNORATE_CODES.get(gov_code, "أخرى")

    # Sequence digits 9 to 13
    gender_digit = int(nid[12])
    gender = "MALE" if gender_digit % 2 != 0 else "FEMALE"

    return EgyptianNationalIDInfo(
        national_id=nid,
        is_valid=True,
        birth_date=birth_date,
        governorate=governorate,
        gender=gender,
    )

"""Write sample_input/customers_messy.csv, a messy retail export.

The file has about 300 Vietnamese customer orders. The same kinds of
problems show up that a real multi-store export tends to have:

- duplicate rows (exact copies, and copies with extra spaces)
- extra spaces and mixed upper/lower case names
- missing values and placeholders such as n/a and -
- dates as 2026-10-05, 05/10/2026, or 5-Oct-2026
- amounts as "1.250.000 đ", "1,250,000", or "1250000"
- invalid phone numbers and emails
- city names such as HN, Ha Noi, and Hà Nội for the same city

Running this file twice produces the same CSV (random.seed(42)).
The first four orders are fixed examples used in the README.
"""

import csv
import random
import re
import unicodedata
from datetime import date, timedelta
from pathlib import Path

from cleaner import EXPECTED_COLUMNS


ROOT = Path(__file__).resolve().parent
OUTPUT_PATH = ROOT / "sample_input" / "customers_messy.csv"

NAMES = [
    "Nguyễn Văn An",
    "Trần Thị Bích",
    "Lê Hoàng Nam",
    "Phạm Minh Tú",
    "Hoàng Thu Hà",
    "Võ Quốc Bảo",
    "Đặng Ngọc Lan",
    "Bùi Thanh Sơn",
    "Đỗ Hải Yến",
    "Ngô Đức Huy",
    "Lý Mỹ Duyên",
    "Đinh Công Vinh",
    "Trịnh Gia Hân",
    "Phan Bảo Châu",
    "Mai Thanh Tùng",
    "Hồ Ngọc Ánh",
]

# Standard name -> spellings that stores actually type.
CITY_SPELLINGS = {
    "Hà Nội": ["HN", "Ha Noi", "Hà Nội", "hanoi", "HA NOI"],
    "TP. Hồ Chí Minh": ["HCM", "Ho Chi Minh", "Sài Gòn", "SG", "hcm", "tp. hcm"],
    "Đà Nẵng": ["DN", "Da Nang", "Đà Nẵng", "danang"],
    "Hải Phòng": ["HP", "Hai Phong", "Hải Phòng"],
    "Cần Thơ": ["CT", "Can Tho", "Cần Thơ"],
    "Huế": ["Hue", "Huế", "hue"],
    "Nha Trang": ["NT", "Nha Trang", "nha trang"],
}

# Real places we deliberately leave off the alias list, so the report
# has a few cities a person should review.
UNKNOWN_CITIES = ["Vung Tau", "Da Lat", "Bien Hoa", "Hai Duong"]

PRODUCTS = [
    "Áo thun",
    "Quần jean",
    "Giày sneaker",
    "Tai nghe",
    "Sạc dự phòng",
    "Bình nước",
    "Mũ lưỡi trai",
    "Túi canvas",
    "Áo khoác",
    "Dép lê",
]

PRICES = [
    89000,
    150000,
    249000,
    490000,
    750000,
    990000,
    1250000,
    1890000,
    2500000,
    15990000,
]

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

BAD_EMAILS = [
    "tran..bich@gmail.com",
    "no-at-sign",
    "user@",
    "bad@@gmail.com",
    "name@gmail",
    "hello world",
]

BAD_PHONES = ["12345", "090ABC1234", "0123456789", "999", "phone", "0000000000"]
BAD_DATES = ["32/13/2026", "2026-13-01", "yesterday", "10/2026", "00/00/0000"]
BAD_AMOUNTS = ["abc", "free", "1.2.3 đ", "???", "12a50"]
MISSING_MARKERS = ["", "n/a", "N/A", "null", "-"]


def slug_name(name):
    """Turn a Vietnamese name into a simple email local-part."""
    text = name.lower().replace("đ", "d")
    pieces = unicodedata.normalize("NFD", text)
    plain = "".join(char for char in pieces if not unicodedata.combining(char))
    plain = re.sub(r"[^a-z]", "", plain)
    return plain or "customer"


def mess_name(name):
    """Apply the kind of typing noise seen in exported names."""
    roll = random.random()
    if roll < 0.28:
        text = name.upper()
    elif roll < 0.50:
        text = name.lower()
    elif roll < 0.72:
        text = name.replace(" ", "   ")
    else:
        text = name
    if random.random() < 0.35:
        text = f"  {text} "
    return text


def format_date(value):
    style = random.randrange(3)
    if style == 0:
        return value.isoformat()
    if style == 1:
        return f"{value.day:02d}/{value.month:02d}/{value.year}"
    return f"{value.day}-{MONTHS[value.month - 1]}-{value.year}"


def format_amount(amount):
    style = random.randrange(3)
    if style == 0:
        grouped = f"{amount:,}".replace(",", ".")
        return f"{grouped} đ"
    if style == 1:
        return f"{amount:,}"
    return str(amount)


def make_phone():
    prefix = random.choice(
        ["032", "033", "035", "070", "076", "086", "088", "090", "091", "093", "098"]
    )
    rest = "".join(str(random.randrange(10)) for _ in range(7))
    digits = prefix + rest
    style = random.randrange(4)
    if style == 0:
        return f"{digits[:3]} {digits[3:6]} {digits[6:]}"
    if style == 1:
        return f"+84 {digits[1:3]} {digits[3:6]} {digits[6:]}"
    if style == 2:
        return f"{digits[:4]}-{digits[4:7]}-{digits[7:]}"
    return digits


def make_email(name, number):
    domain = random.choice(["gmail.com", "yahoo.com", "outlook.com", "email.vn"])
    email = f"{slug_name(name)}{number % 97}@{domain}"
    if random.random() < 0.35:
        email = email.upper()
    if random.random() < 0.2:
        email = f" {email} "
    return email


def maybe_missing(value, chance):
    if random.random() < chance:
        return random.choice(MISSING_MARKERS)
    return value


def example_rows():
    """Hand-written rows. Row DH0001 is also copied once later on."""
    return [
        {
            "order_id": "DH0001",
            "customer_name": "  NGUYEN  van   An ",
            "email": "An.Nguyen@Gmail.com ",
            "phone": "090 123 4567",
            "city": "HN",
            "order_date": "05/10/2026",
            "product": "  ao thun  ",
            "amount": "1.250.000 đ",
        },
        {
            "order_id": "DH0002",
            "customer_name": "tran thi BICH",
            "email": "tran..bich@gmail.com",
            "phone": "12345",
            "city": "Ha Noi",
            "order_date": "5-Oct-2026",
            "product": "GIAY sneaker",
            "amount": "1,250,000",
        },
        {
            "order_id": "DH0003",
            "customer_name": "Le Hoang Nam",
            "email": "lehoangnam3@gmail.com",
            "phone": "+84 91 234 5678",
            "city": "Hà Nội",
            "order_date": "2026-10-05",
            "product": "Tai Nghe",
            "amount": "1250000",
        },
        {
            "order_id": "DH0004",
            "customer_name": "n/a",
            "email": "not-an-email",
            "phone": "090ABC1234",
            "city": "hcm",
            "order_date": "32/13/2026",
            "product": "-",
            "amount": "abc",
        },
    ]


def generated_rows(start_number, count):
    rows = []
    start_day = date(2026, 1, 1)
    for offset in range(count):
        number = start_number + offset
        name = random.choice(NAMES)
        order_day = start_day + timedelta(days=random.randrange(365))
        price = random.choice(PRICES)

        email = make_email(name, number)
        phone = make_phone()
        city_name = random.choice(list(CITY_SPELLINGS))
        city = random.choice(CITY_SPELLINGS[city_name])
        order_date = format_date(order_day)
        product = random.choice(PRODUCTS)
        amount = format_amount(price)

        # Sprinkle invalid and missing values. Rates are high enough
        # that a 300-row file shows every problem in the report.
        if random.random() < 0.08:
            email = random.choice(BAD_EMAILS)
        else:
            email = maybe_missing(email, 0.05)

        if random.random() < 0.08:
            phone = random.choice(BAD_PHONES)
        else:
            phone = maybe_missing(phone, 0.04)

        city_roll = random.random()
        if city_roll < 0.05:
            city = random.choice(UNKNOWN_CITIES)
            if random.random() < 0.5:
                city = city.upper()
        elif city_roll < 0.09:
            city = random.choice(MISSING_MARKERS)

        if random.random() < 0.05:
            order_date = random.choice(BAD_DATES)
        else:
            order_date = maybe_missing(order_date, 0.03)

        if random.random() < 0.05:
            amount = random.choice(BAD_AMOUNTS)
        else:
            amount = maybe_missing(amount, 0.04)

        if random.random() < 0.04:
            product = random.choice(MISSING_MARKERS)
        elif random.random() < 0.55:
            product = mess_name(product)

        rows.append(
            {
                "order_id": f" DH{number:04d} " if random.random() < 0.08 else f"DH{number:04d}",
                "customer_name": maybe_missing(mess_name(name), 0.03),
                "email": email,
                "phone": phone,
                "city": city,
                "order_date": order_date,
                "product": product,
                "amount": amount,
            }
        )
    return rows


def duplicate_rows(unique_rows):
    """Add 50 copies. The first copy sits directly under DH0001."""
    rows = [unique_rows[0], dict(unique_rows[0])]
    rows.extend(unique_rows[1:])

    chosen = random.sample(range(len(unique_rows)), 49)
    for index in chosen:
        copy = dict(unique_rows[index])
        # Some duplicates only match after trimming. That is the point.
        if random.random() < 0.25:
            copy["customer_name"] = f"  {copy['customer_name']} "
            copy["amount"] = f" {copy['amount']} "
        rows.append(copy)
    return rows


def build_rows():
    """Return 300 messy rows. Call random.seed before this for a stable file."""
    random.seed(42)
    unique_rows = example_rows() + generated_rows(start_number=5, count=246)
    if len(unique_rows) != 250:
        raise RuntimeError(f"Expected 250 unique rows, got {len(unique_rows)}.")
    rows = duplicate_rows(unique_rows)
    if len(rows) != 300:
        raise RuntimeError(f"Expected 300 rows, got {len(rows)}.")
    return rows


def main():
    rows = build_rows()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    # utf-8-sig adds a BOM so Excel on Windows opens Vietnamese text correctly.
    with OUTPUT_PATH.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=EXPECTED_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} rows to {OUTPUT_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()

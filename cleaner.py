"""Reusable cleaning steps for messy customer-order tables.

Each function repairs one kind of problem. Most of them work on a single
cell so you can try them in the Python shell:

    from cleaner import parse_vnd_amount, parse_date, map_city_name
    parse_vnd_amount("1.250.000 đ")
    parse_date("05/10/2026")
    map_city_name("HN")

clean_orders() runs every step on a whole table, drops duplicate rows,
and returns a stats dictionary that main.py turns into a report.
"""

import re
import unicodedata
from datetime import date

import pandas as pd


EXPECTED_COLUMNS = [
    "order_id",
    "customer_name",
    "email",
    "phone",
    "city",
    "order_date",
    "product",
    "amount",
]

# Tokens that mean "this cell is empty", after trimming and lower-casing.
MISSING_MARKERS = {"n/a", "na", "null", "none", "nan", "missing", "-", "--"}

# Second digit of a Vietnamese mobile number: 03x, 05x, 07x, 08x, 09x.
MOBILE_SECOND_DIGITS = set("35789")

MONTH_NUMBERS = {
    "jan": 1,
    "feb": 2,
    "mar": 3,
    "apr": 4,
    "may": 5,
    "jun": 6,
    "jul": 7,
    "aug": 8,
    "sep": 9,
    "oct": 10,
    "nov": 11,
    "dec": 12,
}

# Keys are folded with _city_key: lower case, no accents, single spaces.
# Add a new alias here when a store uses another spelling.
CITY_ALIASES = {
    "hn": "Hà Nội",
    "ha noi": "Hà Nội",
    "hanoi": "Hà Nội",
    "hcm": "TP. Hồ Chí Minh",
    "hcmc": "TP. Hồ Chí Minh",
    "sg": "TP. Hồ Chí Minh",
    "saigon": "TP. Hồ Chí Minh",
    "sai gon": "TP. Hồ Chí Minh",
    "ho chi minh": "TP. Hồ Chí Minh",
    "tp hcm": "TP. Hồ Chí Minh",
    "tp ho chi minh": "TP. Hồ Chí Minh",
    "tphcm": "TP. Hồ Chí Minh",
    "dn": "Đà Nẵng",
    "da nang": "Đà Nẵng",
    "danang": "Đà Nẵng",
    "hp": "Hải Phòng",
    "hai phong": "Hải Phòng",
    "haiphong": "Hải Phòng",
    "ct": "Cần Thơ",
    "can tho": "Cần Thơ",
    "cantho": "Cần Thơ",
    "hue": "Huế",
    "nt": "Nha Trang",
    "nha trang": "Nha Trang",
    "nhatrang": "Nha Trang",
}

EMAIL_RE = re.compile(
    r"[A-Za-z0-9][A-Za-z0-9._%+\-]*@[A-Za-z0-9][A-Za-z0-9.\-]*\.[A-Za-z]{2,}"
)


def _is_na(value) -> bool:
    """True for None and pandas missing values. The text "n/a" is not missing here."""
    if value is None:
        return True
    try:
        return bool(pd.isna(value))
    except (TypeError, ValueError):
        return False


def _compare_text(value) -> str:
    """Text used only to decide whether a cell actually changed."""
    if _is_na(value):
        return ""
    return str(value).strip()


def _changed(before, after) -> bool:
    return _compare_text(before) != _compare_text(after)


def is_missing(value) -> bool:
    """Return True for a blank cell or a placeholder such as n/a, null, or -."""
    if _is_na(value):
        return True
    text = str(value).strip().lower()
    return text == "" or text in MISSING_MARKERS


def trim_text(value):
    """Remove extra spaces around and inside a cell.

    "  Nguyen   Van  " becomes "Nguyen Van".
    None stays None. The word "n/a" is kept; use blank_if_missing
    when that word should become an empty cell.
    """
    if _is_na(value):
        return None
    text = str(value).replace("\u00a0", " ").strip()
    text = re.sub(r"\s+", " ", text)
    return text


def blank_if_missing(value):
    """Turn a blank cell or a missing marker into None.

    Markers: n/a, na, null, none, nan, missing, "-", "--".
    Any other value is returned unchanged.
    """
    if is_missing(value):
        return None
    return value


def normalize_case(value, style="title"):
    """Change letter case. style is "title", "lower", or "upper".

    Title case capitalizes each word, which is what we want for names:
    "NGUYEN VAN AN" becomes "Nguyen Van An".
    Use "lower" for email addresses.
    Returns None when the value is missing.
    """
    if _is_na(value):
        return None
    text = str(value).strip()
    if text == "":
        return None
    if style == "lower":
        return text.lower()
    if style == "upper":
        return text.upper()
    if style == "title":
        words = []
        for word in text.split(" "):
            words.append(word[:1].upper() + word[1:].lower())
        return " ".join(words)
    raise ValueError("style must be 'title', 'lower', or 'upper'")


def _safe_date(year, month, day):
    """Build a date, or return None when the numbers are impossible."""
    try:
        return date(int(year), int(month), int(day))
    except (TypeError, ValueError):
        return None


def parse_date(value):
    """Parse a date into text YYYY-MM-DD.

    Accepted forms:
    - 2026-10-05
    - 05/10/2026, read as day/month/year (Vietnamese order, not US)
    - 5-Oct-2026

    Returns None when the value is missing or not one of those forms.
    """
    if _is_na(value):
        return None
    text = str(value).strip()
    if text == "":
        return None

    iso_match = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", text)
    if iso_match:
        found = _safe_date(iso_match.group(1), iso_match.group(2), iso_match.group(3))
        return found.isoformat() if found else None

    slash_match = re.fullmatch(r"(\d{1,2})/(\d{1,2})/(\d{4})", text)
    if slash_match:
        # Group order in the file is day, month, year.
        found = _safe_date(slash_match.group(3), slash_match.group(2), slash_match.group(1))
        return found.isoformat() if found else None

    named_match = re.fullmatch(r"(\d{1,2})-([A-Za-z]{3,9})-(\d{4})", text)
    if named_match:
        month = MONTH_NUMBERS.get(named_match.group(2).lower()[:3])
        if month is None:
            return None
        found = _safe_date(named_match.group(3), month, named_match.group(1))
        return found.isoformat() if found else None

    return None


def _groups_of_three(text, separator) -> bool:
    """True when text looks like 1.250.000 or 1,250,000."""
    parts = text.split(separator)
    if len(parts) < 2 or not parts[0].isdigit():
        return False
    return all(part.isdigit() and len(part) == 3 for part in parts[1:])


def _ungroup_number(text):
    """Return a plain number string, or None when the shape is wrong.

    A dot or comma that splits groups of three digits is a thousands
    separator. "1.250.000" and "1,250,000" both become "1250000".
    """
    if re.fullmatch(r"\d+", text):
        return text

    if "." in text and "," in text:
        # The last separator is the decimal mark. Retail VND rarely
        # needs it, but "1.250.000,50" should still parse.
        if text.rfind(",") > text.rfind("."):
            whole, fraction = text.rsplit(",", 1)
            whole = whole.replace(".", "")
        else:
            whole, fraction = text.rsplit(".", 1)
            whole = whole.replace(",", "")
        if whole.isdigit() and fraction.isdigit():
            return f"{whole}.{fraction}"
        return None

    if _groups_of_three(text, "."):
        return text.replace(".", "")
    if _groups_of_three(text, ","):
        return text.replace(",", "")

    if text.count(".") == 1:
        whole, fraction = text.split(".")
        if whole.isdigit() and fraction.isdigit() and len(fraction) != 3:
            return f"{whole}.{fraction}"
    if text.count(",") == 1:
        whole, fraction = text.split(",")
        if whole.isdigit() and fraction.isdigit() and len(fraction) != 3:
            return f"{whole}.{fraction}"
    return None


def parse_vnd_amount(value):
    """Convert VND text to a whole number of dong.

    Examples:
    "1.250.000 đ" -> 1250000
    "1,250,000" -> 1250000
    "1250000" -> 1250000

    A trailing "đ", "₫", "VND", or "dong" is ignored. In Vietnamese
    writing the dot is the thousands separator, so "1.250" is 1250,
    not 1.25.

    Returns None when the value is missing or not a number.
    """
    if _is_na(value):
        return None
    text = str(value).strip().lower()
    if text == "":
        return None
    text = text.replace("₫", "").replace("đ", "")
    text = re.sub(r"\b(vnd|dong)\b", "", text)
    text = text.replace(" ", "")
    if text == "" or text.startswith("-"):
        return None

    plain = _ungroup_number(text)
    if plain is None:
        return None
    try:
        number = float(plain)
    except ValueError:
        return None
    if number < 0:
        return None
    return int(round(number))


def is_valid_email(value) -> bool:
    """Return True when the text looks like a usable email address.

    Needs one @, a dot in the domain, and no spaces or double dots.
    """
    if _is_na(value):
        return False
    text = str(value).strip()
    if text.count("@") != 1 or ".." in text or any(char.isspace() for char in text):
        return False
    local, domain = text.split("@")
    if not local or not domain or local.startswith(".") or local.endswith("."):
        return False
    if domain.startswith(".") or domain.endswith("."):
        return False
    return EMAIL_RE.fullmatch(text) is not None


def normalize_phone(value):
    """Return a Vietnamese mobile number as 10 digits starting with 0.

    Spaces, dots, dashes, and a country code of 84 or +84 are accepted.
    "090 123 4567" becomes "0901234567".
    "+84 91 234 5678" becomes "0912345678".

    Returns None when the value is missing or not a mobile number
    (10 digits, second digit 3, 5, 7, 8, or 9).
    """
    if _is_na(value):
        return None
    digits = re.sub(r"\D", "", str(value))
    if digits == "":
        return None
    if digits.startswith("84"):
        digits = digits[2:]
    if not digits.startswith("0"):
        digits = "0" + digits
    if len(digits) != 10 or digits[1] not in MOBILE_SECOND_DIGITS:
        return None
    return digits


def is_valid_phone(value) -> bool:
    """Return True when normalize_phone can read the value as a mobile number."""
    return normalize_phone(value) is not None


def _city_key(value) -> str:
    """Fold a city name so "Hà Nội", "Ha Noi", and "HA NOI" share a key."""
    text = str(value).strip().lower().replace("đ", "d")
    pieces = unicodedata.normalize("NFD", text)
    without_marks = "".join(char for char in pieces if not unicodedata.combining(char))
    without_marks = without_marks.replace("đ", "d")
    without_marks = re.sub(r"[^a-z0-9]+", " ", without_marks)
    return re.sub(r"\s+", " ", without_marks).strip()


def map_city_name(value):
    """Map a city alias to one standard name.

    "HN", "Ha Noi", and "Hà Nội" all return "Hà Nội".
    Matching ignores case, extra spaces, and Vietnamese accents.
    Returns None when the value is missing or not listed in CITY_ALIASES.
    """
    if _is_na(value):
        return None
    key = _city_key(value)
    if key == "":
        return None
    return CITY_ALIASES.get(key)


def drop_duplicate_rows(df):
    """Remove exact duplicate rows, keeping the first copy.

    Returns (smaller dataframe, number of rows removed).
    A column whose name starts with "_" is ignored during the comparison
    so a helper source-row number does not make copies look unique.
    """
    subset = [column for column in df.columns if not str(column).startswith("_")]
    before = len(df)
    cleaned = df.drop_duplicates(subset=subset, keep="first").reset_index(drop=True)
    return cleaned, before - len(cleaned)


def _require_columns(df):
    missing = [column for column in EXPECTED_COLUMNS if column not in df.columns]
    if missing:
        found = ", ".join(str(column) for column in df.columns)
        needed = ", ".join(EXPECTED_COLUMNS)
        raise ValueError(
            "Missing column(s): "
            + ", ".join(missing)
            + f". Expected: {needed}. Found: {found}."
        )


def _add_fix(fixes, column, action, source_row):
    fixes.append({"column": column, "action": action, "source_row": source_row})


def _add_invalid(invalid, column, source_row, original, reason):
    invalid.append(
        {
            "source_row": source_row,
            "column": column,
            "original": original,
            "reason": reason,
        }
    )


def _summarize_fixes(fixes, kept_rows):
    """Count fixes, skipping rows that were removed as duplicates."""
    order = []
    counts = {}
    for item in fixes:
        if item["source_row"] not in kept_rows:
            continue
        key = (item["column"], item["action"])
        if key not in counts:
            order.append(key)
            counts[key] = 0
        counts[key] += 1
    return [
        {"column": column, "action": action, "count": counts[(column, action)]}
        for column, action in order
    ]


def clean_orders(df):
    """Clean a customer-order table.

    Expected columns: order_id, customer_name, email, phone, city,
    order_date, product, amount. Extra columns are kept as they are.

    Steps, in order:
    1. Trim spaces.
    2. Replace missing markers (n/a, null, -) with empty cells.
    3. Title-case customer names and product names.
    4. Lower-case emails, then clear addresses that still look invalid.
    5. Reformat valid mobile numbers and clear invalid ones.
    6. Map known city aliases. Unknown cities are title-cased and listed.
    7. Parse dates to YYYY-MM-DD and VND amounts to whole numbers.
    8. Drop exact duplicate rows.

    A row is not deleted only because an email or phone is bad. Those
    cells become empty and show up in the stats under "invalid".

    Returns (cleaned dataframe, stats dictionary).
    """
    _require_columns(df)
    source_rows = list(range(2, len(df) + 2))
    current = {column: df[column].tolist() for column in EXPECTED_COLUMNS}
    raw = {column: list(values) for column, values in current.items()}
    extra_columns = [column for column in df.columns if column not in EXPECTED_COLUMNS]
    extras = {column: df[column].tolist() for column in extra_columns}

    missing_before = {
        column: sum(is_missing(value) for value in raw[column]) for column in EXPECTED_COLUMNS
    }
    fixes = []
    invalid = []
    unmapped_cities = []

    for column in EXPECTED_COLUMNS:
        trimmed_values = []
        for source_row, value in zip(source_rows, current[column]):
            trimmed = trim_text(value)
            if trimmed == "":
                trimmed = None
            if _changed(value, trimmed):
                _add_fix(fixes, column, "trimmed extra spaces", source_row)
            trimmed_values.append(trimmed)
        current[column] = trimmed_values

    for column in EXPECTED_COLUMNS:
        blanked = []
        for source_row, value in zip(source_rows, current[column]):
            if value is not None and blank_if_missing(value) is None:
                _add_fix(fixes, column, "replaced missing marker", source_row)
                blanked.append(None)
            else:
                blanked.append(value)
        current[column] = blanked

    for column in ("customer_name", "product"):
        titled = []
        for source_row, value in zip(source_rows, current[column]):
            new_value = normalize_case(value, "title") if value is not None else None
            if _changed(value, new_value):
                _add_fix(fixes, column, "normalized to title case", source_row)
            titled.append(new_value)
        current[column] = titled

    lowered_emails = []
    for source_row, value, original in zip(source_rows, current["email"], raw["email"]):
        if value is None:
            lowered_emails.append(None)
            continue
        new_value = normalize_case(value, "lower")
        if _changed(value, new_value):
            _add_fix(fixes, "email", "normalized to lower case", source_row)
        if not is_valid_email(new_value):
            _add_invalid(
                invalid,
                "email",
                source_row,
                original,
                "Not a valid email address",
            )
            lowered_emails.append(None)
            continue
        lowered_emails.append(new_value)
    current["email"] = lowered_emails

    phones = []
    for source_row, value, original in zip(source_rows, current["phone"], raw["phone"]):
        if value is None:
            phones.append(None)
            continue
        new_value = normalize_phone(value)
        if new_value is None:
            _add_invalid(
                invalid,
                "phone",
                source_row,
                original,
                "Not a Vietnamese mobile number",
            )
            phones.append(None)
            continue
        if _changed(value, new_value):
            _add_fix(fixes, "phone", "reformatted to a 10-digit mobile number", source_row)
        phones.append(new_value)
    current["phone"] = phones

    cities = []
    for source_row, value, original in zip(source_rows, current["city"], raw["city"]):
        if value is None:
            cities.append(None)
            continue
        canonical = map_city_name(value)
        if canonical is None:
            kept = normalize_case(value, "title")
            if _changed(value, kept):
                _add_fix(fixes, "city", "normalized unrecognized city to title case", source_row)
            unmapped_cities.append(
                {"source_row": source_row, "original": original, "kept_as": kept}
            )
            cities.append(kept)
            continue
        if _changed(value, canonical):
            _add_fix(fixes, "city", "mapped to a standard city name", source_row)
        cities.append(canonical)
    current["city"] = cities

    dates = []
    for source_row, value, original in zip(source_rows, current["order_date"], raw["order_date"]):
        if value is None:
            dates.append(None)
            continue
        new_value = parse_date(value)
        if new_value is None:
            _add_invalid(
                invalid,
                "order_date",
                source_row,
                original,
                "Date is not in a recognized format",
            )
            dates.append(None)
            continue
        if _changed(value, new_value):
            _add_fix(fixes, "order_date", "parsed to YYYY-MM-DD", source_row)
        dates.append(new_value)
    current["order_date"] = dates

    amounts = []
    for source_row, value, original in zip(source_rows, current["amount"], raw["amount"]):
        if value is None:
            amounts.append(None)
            continue
        new_value = parse_vnd_amount(value)
        if new_value is None:
            _add_invalid(
                invalid,
                "amount",
                source_row,
                original,
                "Amount is not a valid VND value",
            )
            amounts.append(None)
            continue
        if _changed(value, new_value):
            _add_fix(fixes, "amount", "parsed VND text into a number", source_row)
        amounts.append(new_value)
    current["amount"] = amounts

    data = {column: current[column] for column in EXPECTED_COLUMNS}
    for column in extra_columns:
        data[column] = extras[column]
    cleaned = pd.DataFrame(data)
    cleaned["_source_row"] = source_rows
    cleaned, duplicates_removed = drop_duplicate_rows(cleaned)
    kept_rows = set(cleaned["_source_row"].tolist())
    cleaned = cleaned.drop(columns="_source_row")

    text_columns = [column for column in cleaned.columns if column != "amount"]
    for column in text_columns:
        cleaned[column] = cleaned[column].astype("string")
    cleaned["amount"] = pd.to_numeric(cleaned["amount"], errors="coerce").astype("Int64")

    column_index = {column: index for index, column in enumerate(EXPECTED_COLUMNS)}
    invalid = [item for item in invalid if item["source_row"] in kept_rows]
    invalid.sort(key=lambda item: (item["source_row"], column_index.get(item["column"], 99)))
    unmapped_cities = [item for item in unmapped_cities if item["source_row"] in kept_rows]
    unmapped_cities.sort(key=lambda item: item["source_row"])

    missing_after = {}
    for column in EXPECTED_COLUMNS:
        missing_after[column] = int(cleaned[column].isna().sum())

    stats = {
        "rows_before": len(df),
        "rows_after": len(cleaned),
        "duplicates_removed": duplicates_removed,
        "fixes": _summarize_fixes(fixes, kept_rows),
        "missing_before": missing_before,
        "missing_after": missing_after,
        "invalid": invalid,
        "unmapped_cities": unmapped_cities,
    }
    return cleaned, stats

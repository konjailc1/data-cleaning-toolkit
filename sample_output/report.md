# Cleaning report

Source file: `sample_input/customers_messy.csv`

Source row numbers below count the header as row 1, so the first
data row is source row 2. That matches the line number in the CSV.

| | |
| --- | ---: |
| Rows before | 300 |
| Rows after | 250 |
| Duplicate rows removed | 50 |
| Invalid values cleared | 68 |
| Rows with an invalid value | 58 |
| Unrecognized cities kept for review | 9 |

Duplicate rows were removed only when every cleaned column matched.
A row with a bad email or phone stays in the file; that cell is cleared.

## Values fixed per column

| Column | What changed | Count |
| --- | --- | ---: |
| customer_name | trimmed extra spaces | 67 |
| product | trimmed extra spaces | 28 |
| customer_name | replaced missing marker | 3 |
| email | replaced missing marker | 11 |
| phone | replaced missing marker | 6 |
| city | replaced missing marker | 12 |
| order_date | replaced missing marker | 7 |
| product | replaced missing marker | 13 |
| amount | replaced missing marker | 7 |
| customer_name | normalized to title case | 116 |
| product | normalized to title case | 233 |
| email | normalized to lower case | 75 |
| phone | reformatted to a 10-digit mobile number | 165 |
| city | mapped to a standard city name | 171 |
| city | normalized unrecognized city to title case | 7 |
| order_date | parsed to YYYY-MM-DD | 153 |
| amount | parsed VND text into a number | 141 |

## Missing values

Missing before is counted on the raw file. Missing after is counted
on the cleaned file, after duplicates are removed. The after count
also includes invalid emails, phones, dates, and amounts that were cleared.

| Column | Missing before | Missing after |
| --- | ---: | ---: |
| order_id | 0 | 0 |
| customer_name | 3 | 3 |
| email | 14 | 36 |
| phone | 12 | 28 |
| city | 19 | 15 |
| order_date | 10 | 26 |
| product | 18 | 16 |
| amount | 10 | 18 |

## Invalid values

These cells could not be repaired, so the cleaned cell is empty.

| Source row | Column | Original value | Reason |
| ---: | --- | --- | --- |
| 4 | email | `tran..bich@gmail.com` | Not a valid email address |
| 4 | phone | `12345` | Not a Vietnamese mobile number |
| 6 | email | `not-an-email` | Not a valid email address |
| 6 | phone | `090ABC1234` | Not a Vietnamese mobile number |
| 6 | order_date | `32/13/2026` | Date is not in a recognized format |
| 6 | amount | `abc` | Amount is not a valid VND value |
| 16 | email | `user@` | Not a valid email address |
| 19 | amount | `free` | Amount is not a valid VND value |
| 25 | amount | `1.2.3 đ` | Amount is not a valid VND value |
| 28 | phone | `090ABC1234` | Not a Vietnamese mobile number |
| 34 | order_date | `10/2026` | Date is not in a recognized format |
| 38 | phone | `0123456789` | Not a Vietnamese mobile number |
| 42 | phone | `0000000000` | Not a Vietnamese mobile number |
| 49 | order_date | `32/13/2026` | Date is not in a recognized format |
| 50 | email | `bad@@gmail.com` | Not a valid email address |
| 50 | amount | `1.2.3 đ` | Amount is not a valid VND value |
| 54 | email | `name@gmail` | Not a valid email address |
| 66 | amount | `1.2.3 đ` | Amount is not a valid VND value |
| 73 | phone | `12345` | Not a Vietnamese mobile number |
| 74 | email | `user@` | Not a valid email address |
| 77 | phone | `0000000000` | Not a Vietnamese mobile number |
| 84 | order_date | `32/13/2026` | Date is not in a recognized format |
| 91 | phone | `phone` | Not a Vietnamese mobile number |
| 92 | email | `hello world` | Not a valid email address |
| 99 | phone | `12345` | Not a Vietnamese mobile number |
| 100 | amount | `free` | Amount is not a valid VND value |
| 103 | phone | `0123456789` | Not a Vietnamese mobile number |
| 103 | order_date | `10/2026` | Date is not in a recognized format |
| 104 | order_date | `2026-13-01` | Date is not in a recognized format |
| 108 | email | `hello world` | Not a valid email address |
| 109 | order_date | `2026-13-01` | Date is not in a recognized format |
| 115 | phone | `999` | Not a Vietnamese mobile number |
| 123 | phone | `0000000000` | Not a Vietnamese mobile number |
| 127 | phone | `999` | Not a Vietnamese mobile number |
| 128 | email | `no-at-sign` | Not a valid email address |
| 130 | order_date | `00/00/0000` | Date is not in a recognized format |
| 131 | amount | `free` | Amount is not a valid VND value |
| 134 | email | `no-at-sign` | Not a valid email address |
| 142 | amount | `abc` | Amount is not a valid VND value |
| 146 | phone | `090ABC1234` | Not a Vietnamese mobile number |
| 146 | order_date | `32/13/2026` | Date is not in a recognized format |
| 159 | order_date | `2026-13-01` | Date is not in a recognized format |
| 163 | email | `bad@@gmail.com` | Not a valid email address |
| 164 | order_date | `yesterday` | Date is not in a recognized format |
| 165 | email | `bad@@gmail.com` | Not a valid email address |
| 165 | phone | `999` | Not a Vietnamese mobile number |
| 171 | order_date | `00/00/0000` | Date is not in a recognized format |
| 173 | order_date | `10/2026` | Date is not in a recognized format |
| 174 | email | `tran..bich@gmail.com` | Not a valid email address |
| 174 | amount | `12a50` | Amount is not a valid VND value |
| 179 | email | `user@` | Not a valid email address |
| 180 | email | `no-at-sign` | Not a valid email address |
| 181 | email | `hello world` | Not a valid email address |
| 181 | phone | `phone` | Not a Vietnamese mobile number |
| 191 | email | `user@` | Not a valid email address |
| 192 | email | `user@` | Not a valid email address |
| 200 | email | `no-at-sign` | Not a valid email address |
| 202 | order_date | `00/00/0000` | Date is not in a recognized format |
| 214 | email | `hello world` | Not a valid email address |
| 216 | amount | `???` | Amount is not a valid VND value |
| 218 | phone | `12345` | Not a Vietnamese mobile number |
| 222 | order_date | `32/13/2026` | Date is not in a recognized format |
| 231 | phone | `090ABC1234` | Not a Vietnamese mobile number |
| 234 | phone | `0000000000` | Not a Vietnamese mobile number |
| 243 | email | `bad@@gmail.com` | Not a valid email address |
| 245 | order_date | `32/13/2026` | Date is not in a recognized format |
| 247 | email | `no-at-sign` | Not a valid email address |
| 248 | email | `tran..bich@gmail.com` | Not a valid email address |

## Cities to review

These names are not in the city alias list. They were title-cased
and kept. Add a spelling to CITY_ALIASES in cleaner.py to map them
next time.

| Source row | Original value | Kept as |
| ---: | --- | --- |
| 66 | `Bien Hoa` | Bien Hoa |
| 90 | `HAI DUONG` | Hai Duong |
| 119 | `HAI DUONG` | Hai Duong |
| 141 | `DA LAT` | Da Lat |
| 143 | `DA LAT` | Da Lat |
| 178 | `DA LAT` | Da Lat |
| 188 | `Hai Duong` | Hai Duong |
| 203 | `BIEN HOA` | Bien Hoa |
| 224 | `DA LAT` | Da Lat |

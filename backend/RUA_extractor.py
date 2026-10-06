import os
import re

try:
    import camelot
except Exception:
    camelot = None


UNIT_PATTERN = re.compile(r"\bUnit\s*[- ]?\s*(I{1,3}|IV|V|[1-9])\b", re.IGNORECASE)
TOTAL_PATTERN = re.compile(r"\bTOTAL\b", re.IGNORECASE)
NOISE_TOKENS = {
    "nan",
    "level",
    "marks",
    "distribution",
    "theory",
    "mark",
    "table",
}


def _roman_unit(value: str) -> str:
    value = value.strip().upper()
    if value.isdigit():
        return value
    return value


def _normalize_numbers(row_text: str) -> list[int]:
    return [int(number) for number in re.findall(r"\d+", row_text)]


def _clean_title(row_text: str) -> str:
    title = UNIT_PATTERN.sub("", row_text)
    title = re.sub(r"\b\d+\b", "", title)
    title = re.sub(r"\b(?:" + "|".join(sorted(NOISE_TOKENS, key=len, reverse=True)) + r")\b", "", title, flags=re.IGNORECASE)
    title = re.sub(r"\s+", " ", title)
    return title.strip(" -:\t\n\r")


def _unit_key(unit: str) -> str:
    unit = _roman_unit(unit)
    return f"Unit-{unit}"


def _merge_row(rua_data: dict, unit_key: str, title: str, values: dict) -> None:
    current = rua_data.get(unit_key, {})
    merged = dict(current)

    if title and not merged.get("title"):
        merged["title"] = title

    for field, value in values.items():
        if value is None:
            continue
        if field not in merged or not merged.get(field):
            merged[field] = value

    rua_data[unit_key] = merged


def _parse_rows(rows, rua_data: dict) -> None:
    for row in rows:
        row_text = " ".join(str(cell) for cell in row if str(cell).strip() and str(cell).strip().lower() != "nan")
        if not row_text:
            continue

        if TOTAL_PATTERN.search(row_text):
            numbers = _normalize_numbers(row_text)
            if len(numbers) >= 4:
                rua_data["TOTAL"] = {
                    "R": numbers[-4],
                    "U": numbers[-3],
                    "A": numbers[-2],
                    "Total": numbers[-1],
                }
            continue

        unit_match = UNIT_PATTERN.search(row_text)
        if not unit_match:
            continue

        numbers = _normalize_numbers(row_text)
        if len(numbers) < 4:
            continue

        unit = _roman_unit(unit_match.group(1))
        unit_key = _unit_key(unit)
        title = _clean_title(row_text)

        _merge_row(
            rua_data,
            unit_key,
            title,
            {
                "R": numbers[-4],
                "U": numbers[-3],
                "A": numbers[-2],
                "Total": numbers[-1],
            },
        )


def _extract_text_rows(pdf_path: str) -> list[str]:
    try:
        from PyPDF2 import PdfReader
    except Exception:
        try:
            from pypdf import PdfReader
        except Exception:
            return []

    try:
        reader = PdfReader(pdf_path)
    except Exception:
        return []

    lines = []
    for page in reader.pages:
        text = page.extract_text() or ""
        for raw_line in text.splitlines():
            line = raw_line.strip()
            if line:
                lines.append(line)
    return lines


def _parse_text_rows(lines: list[str], rua_data: dict) -> None:
    for line in lines:
        if not (UNIT_PATTERN.search(line) or TOTAL_PATTERN.search(line)):
            continue

        numbers = _normalize_numbers(line)
        if TOTAL_PATTERN.search(line):
            if len(numbers) >= 4:
                rua_data["TOTAL"] = {
                    "R": numbers[-4],
                    "U": numbers[-3],
                    "A": numbers[-2],
                    "Total": numbers[-1],
                }
            continue

        unit_match = UNIT_PATTERN.search(line)
        if not unit_match or len(numbers) < 4:
            continue

        unit_key = _unit_key(unit_match.group(1))
        title = _clean_title(line)

        _merge_row(
            rua_data,
            unit_key,
            title,
            {
                "R": numbers[-4],
                "U": numbers[-3],
                "A": numbers[-2],
                "Total": numbers[-1],
            },
        )


def _ordered_output(rua_data: dict) -> dict:
    ordered = {}
    for unit in ["I", "II", "III", "IV", "V"]:
        key = _unit_key(unit)
        if key in rua_data:
            ordered[key] = rua_data[key]
    for key, value in rua_data.items():
        if key not in ordered and key != "TOTAL":
            ordered[key] = value
    if "TOTAL" in rua_data:
        ordered["TOTAL"] = rua_data["TOTAL"]
    return ordered


def extract_rua(pdf_path):
    rua_data = {}

    if camelot is None:
        tables = []
    else:
        try:
            tables = camelot.read_pdf(pdf_path, pages="all")
        except Exception:
            tables = []

    for table in tables:
        try:
            df = table.df
        except Exception:
            continue

        table_text = df.to_string()
        if "Distribution of Theory Marks" not in table_text and not UNIT_PATTERN.search(table_text):
            continue

        _parse_rows(df.itertuples(index=False, name=None), rua_data)

    if not rua_data or "TOTAL" not in rua_data:
        _parse_text_rows(_extract_text_rows(pdf_path), rua_data)

    return _ordered_output(rua_data)
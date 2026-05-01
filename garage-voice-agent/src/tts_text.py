import re
from collections.abc import AsyncIterable

LETTER_NAMES = {
    "A": "A",
    "B": "B",
    "C": "C",
    "D": "D",
    "E": "E",
    "F": "F",
    "G": "G",
    "H": "H",
    "I": "I",
    "J": "J",
    "K": "K",
    "L": "L",
    "M": "M",
    "N": "N",
    "O": "O",
    "P": "P",
    "Q": "Q",
    "R": "R",
    "S": "S",
    "T": "T",
    "U": "U",
    "V": "V",
    "W": "W",
    "X": "X",
    "Y": "Y",
    "Z": "Z",
}

TTS_REPLACEMENTS = {
    "ABS": "A B S",
    "BMW": "B M W",
    "BYD": "B Y D",
    "CT": "controle technique",
    "DS": "D S",
    "E85": "E quatre-vingt-cinq",
    "ESP": "E S P",
    "GPS": "G P S",
    "GPL": "G P L",
    "MG": "M G",
    "SUV": "S U V",
    "VIN": "V I N",
    "VTC": "V T C",
}


def french_number(value: int) -> str:
    if not 0 <= value <= 999:
        return str(value)

    units = [
        "zero",
        "un",
        "deux",
        "trois",
        "quatre",
        "cinq",
        "six",
        "sept",
        "huit",
        "neuf",
        "dix",
        "onze",
        "douze",
        "treize",
        "quatorze",
        "quinze",
        "seize",
    ]
    tens = {
        20: "vingt",
        30: "trente",
        40: "quarante",
        50: "cinquante",
        60: "soixante",
    }

    if value < len(units):
        return units[value]
    if value < 20:
        return f"dix {units[value - 10]}"
    if value < 70:
        ten = value // 10 * 10
        unit = value % 10
        if unit == 0:
            return tens[ten]
        separator = " et " if unit == 1 else " "
        return f"{tens[ten]}{separator}{units[unit]}"
    if value < 80:
        suffix = french_number(value - 60)
        separator = " et " if value == 71 else " "
        return f"soixante{separator}{suffix}"
    if value < 100:
        suffix_value = value - 80
        if suffix_value == 0:
            return "quatre-vingts"
        return f"quatre-vingt {french_number(suffix_value)}"

    hundreds = value // 100
    remainder = value % 100
    prefix = "cent" if hundreds == 1 else f"{units[hundreds]} cent"
    return prefix if remainder == 0 else f"{prefix} {french_number(remainder)}"


def spell_letters(value: str) -> str:
    return " ".join(LETTER_NAMES.get(char.upper(), char) for char in value if char.strip())


def oralize_phone(match: re.Match[str]) -> str:
    raw = match.group(0)
    digits = re.sub(r"\D", "", raw)
    if digits.startswith("33") and len(digits) == 11:
        digits = f"0{digits[2:]}"
    if len(digits) != 10 or not digits.startswith("0"):
        return raw

    groups = [digits[index : index + 2] for index in range(0, 10, 2)]
    spoken_groups = [f"zero {french_number(int(groups[0][1]))}"]
    spoken_groups.extend(french_number(int(group)) for group in groups[1:])
    return ", ".join(spoken_groups)


def oralize_time(match: re.Match[str]) -> str:
    hour = int(match.group("hour"))
    minute = int(match.group("minute"))
    spoken_hour = f"{french_number(hour)} heure" if hour == 1 else f"{french_number(hour)} heures"
    if minute == 0:
        return spoken_hour
    return f"{spoken_hour} {french_number(minute)}"


def oralize_plate(match: re.Match[str]) -> str:
    left = spell_letters(match.group("left"))
    digits = french_number(int(match.group("digits")))
    right = spell_letters(match.group("right"))
    return f"{left}, {digits}, {right}"


def oralize_known_terms(text: str) -> str:
    for source, replacement in TTS_REPLACEMENTS.items():
        text = re.sub(rf"\b{re.escape(source)}\b", replacement, text)
    return text


def oralize_for_tts(text: str) -> str:
    text = re.sub(
        r"\b(?P<left>[A-Z]{2})[-\s]?(?P<digits>\d{3})[-\s]?(?P<right>[A-Z]{2})\b",
        oralize_plate,
        text,
    )
    text = re.sub(r"\b(?:\+33|0)[1-9](?:[\s.-]?\d{2}){4}\b", oralize_phone, text)
    text = re.sub(
        r"\b(?P<hour>[01]?\d|2[0-3])\s*(?::|h|H)\s*(?P<minute>[0-5]\d)\b",
        oralize_time,
        text,
    )
    return oralize_known_terms(text)


async def oralize_tts_stream(text: AsyncIterable[str]) -> AsyncIterable[str]:
    buffer = ""
    tail_length = 32
    sentence_boundary = re.compile(r"([.!?]\s+|\n+)")

    async for chunk in text:
        buffer += chunk
        boundary = list(sentence_boundary.finditer(buffer))
        if boundary:
            flush_to = boundary[-1].end()
            yield oralize_for_tts(buffer[:flush_to])
            buffer = buffer[flush_to:]
        elif len(buffer) > 180:
            flush_to = len(buffer) - tail_length
            yield oralize_for_tts(buffer[:flush_to])
            buffer = buffer[flush_to:]

    if buffer:
        yield oralize_for_tts(buffer)

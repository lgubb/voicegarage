import re
import unicodedata
from difflib import SequenceMatcher
from typing import Any

LETTER_ALIASES = {
    "a": "A",
    "ah": "A",
    "b": "B",
    "be": "B",
    "bee": "B",
    "c": "C",
    "ce": "C",
    "d": "D",
    "de": "D",
    "e": "E",
    "eu": "E",
    "f": "F",
    "effe": "F",
    "g": "G",
    "ge": "G",
    "j ai": "G",
    "h": "H",
    "ache": "H",
    "i": "I",
    "j": "J",
    "ji": "J",
    "k": "K",
    "ka": "K",
    "l": "L",
    "elle": "L",
    "m": "M",
    "emme": "M",
    "n": "N",
    "enne": "N",
    "o": "O",
    "au": "O",
    "eau": "O",
    "p": "P",
    "pe": "P",
    "q": "Q",
    "cu": "Q",
    "r": "R",
    "erre": "R",
    "s": "S",
    "esse": "S",
    "t": "T",
    "te": "T",
    "u": "U",
    "v": "V",
    "ve": "V",
    "w": "W",
    "doubleve": "W",
    "double": "W",
    "x": "X",
    "ixe": "X",
    "y": "Y",
    "igrec": "Y",
    "z": "Z",
    "zede": "Z",
}

DOUBLE_MARKERS = {"double", "deux", "2"}
SKIP_AFTER_LETTER = {"comme"}


def strip_accents(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value.lower())
    return "".join(char for char in normalized if not unicodedata.combining(char))


def tokenize(value: str) -> list[str]:
    value = strip_accents(value)
    value = value.replace("j'ai", "j ai").replace("i grec", "igrec")
    return re.sub(r"[^a-z0-9]+", " ", value).split()


def letter_at(tokens: list[str], index: int, run_position: int, last_name_hint: str | None) -> tuple[str, int] | None:
    token = tokens[index]
    phrase = " ".join(tokens[index : index + 2])
    if phrase in LETTER_ALIASES:
        return LETTER_ALIASES[phrase], 2
    if token not in LETTER_ALIASES:
        return None
    letter = LETTER_ALIASES[token]
    if token == "j" and run_position == 0 and normalized_name(last_name_hint).startswith("g"):
        letter = "G"
    return letter, 1


def letter_runs(tokens: list[str], last_name_hint: str | None = None) -> list[list[str]]:
    runs: list[list[str]] = []
    current: list[str] = []
    index = 0
    while index < len(tokens):
        token = tokens[index]
        if token in DOUBLE_MARKERS and index + 1 < len(tokens):
            next_letter = letter_at(tokens, index + 1, len(current), last_name_hint)
            if next_letter:
                letter, consumed = next_letter
                current.extend([letter, letter])
                index += 1 + consumed
                continue

        parsed = letter_at(tokens, index, len(current), last_name_hint)
        if parsed:
            letter, consumed = parsed
            current.append(letter)
            index += consumed
            if index < len(tokens) and tokens[index] in SKIP_AFTER_LETTER:
                index += 2
            continue

        if current:
            runs.append(current)
            current = []
        index += 1

    if current:
        runs.append(current)
    return runs


def normalized_name(value: str | None) -> str:
    return re.sub(r"[^a-z]", "", strip_accents(value or ""))


def choose_spelling_run(tokens: list[str], last_name_hint: str | None = None) -> list[str]:
    runs = letter_runs(tokens, last_name_hint)
    if not runs:
        return []
    hint = normalized_name(last_name_hint)
    if hint:
        return max(
            runs,
            key=lambda run: (
                SequenceMatcher(None, "".join(run).lower(), hint).ratio(),
                len(run),
            ),
        )
    return max(runs, key=len)


def fix_first_letter_from_hint(letters: list[str], last_name_hint: str | None) -> list[str]:
    hint = normalized_name(last_name_hint)
    if not letters or not hint:
        return letters
    hint_first = hint[0].upper()
    if letters[0] == hint_first:
        return letters
    if {letters[0], hint_first} <= {"G", "J"}:
        return [hint_first, *letters[1:]]
    return letters


def title_from_letters(letters: list[str]) -> str | None:
    if len(letters) < 2:
        return None
    return "".join(letters).title()


def normalize_first_name(value: str | None) -> str | None:
    cleaned = re.sub(r"[^A-Za-zÀ-ÿ -]+", " ", value or "").strip()
    return cleaned.title() if cleaned else None


def normalize_customer_identity_payload(
    first_name: str | None,
    last_name_heard: str | None,
    spelling_transcript: str,
) -> dict[str, Any]:
    tokens = tokenize(spelling_transcript)
    letters = fix_first_letter_from_hint(choose_spelling_run(tokens, last_name_heard), last_name_heard)
    needs_reask = len(letters) < 3
    last_name = None if needs_reask else title_from_letters(letters)
    first = normalize_first_name(first_name)
    spelled = " ".join(letters)
    caller_name = None if needs_reask else " ".join(part for part in (first, last_name) if part) or None

    return {
        "first_name": first,
        "last_name": last_name,
        "caller_name": caller_name,
        "last_name_spelling": spelled or None,
        "confidence": "low" if needs_reask else "high",
        "needs_reask": needs_reask,
        "spoken_confirmation": (
            f"Confirmez-moi que votre nom de famille s'epelle bien {spelled}, s'il vous plait."
            if not needs_reask
            else "Je n'ai pas bien l'epellation complete. Pouvez-vous reepeler votre nom de famille depuis le debut, lettre par lettre ?"
        ),
    }

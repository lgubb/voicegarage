from pathlib import Path

from config import get_settings


def load_system_prompt(path: Path | None = None) -> str:
    settings = get_settings()
    prompt_path = path or settings.prompt_path
    prompt = prompt_path.read_text(encoding="utf-8")
    return prompt.replace("{{garage_name}}", settings.garage_name)

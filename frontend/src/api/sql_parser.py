import re
from pathlib import Path

SQL_DIR = Path(__file__).resolve().parents[3] / "sql"

FILES = {
    "procedure": ["procedures.sql", "triggers.sql"],
    "trigger": ["triggers.sql"],
    "view": ["views.sql"]
}

definitions = {}

def _read_file(path):
    if not path.exists():
        return ""
    text = path.read_text(encoding="utf-8")
    return re.sub(r"DELIMITER\s+\S+\s*", "", text, flags=re.IGNORECASE)

def _extract_blocks(text, kind):
    if kind == "procedure":
        pattern = r"CREATE\s+PROCEDURE\s+`?(\w+)`?.+?END\s*[\W]*"
    elif kind == "trigger":
        pattern = r"CREATE\s+TRIGGER\s+`?(\w+)`?.+?END\s*[\W]*"
    elif kind == "view":
        pattern = r"CREATE\s+VIEW\s+`?(\w+)`?.+?;"
    else:
        return []

    return re.findall(pattern, text, flags=re.IGNORECASE | re.DOTALL)

def load_all_definitions():
    global definitions
    definitions.clear()

    for kind, files in FILES.items():
        for filename in files:
            full_path = SQL_DIR / filename
            text = _read_file(full_path)
            blocks = _extract_blocks(text, kind)

            for name in blocks:
                pat = (
                    rf"CREATE\s+{kind.upper()}\s+`?{name}`?.+?END\s*[\W]*"
                    if kind in {"procedure", "trigger"} else
                    rf"CREATE\s+{kind.upper()}\s+`?{name}`?.+?;"
                )
                match = re.search(pat, text, re.IGNORECASE | re.DOTALL)
                if match:
                    key = f"{kind}:{name.lower()}"
                    definitions[key] = match.group(0).strip()

load_all_definitions()

def get_definition(kind: str, name: str) -> str | None:
    key = f"{kind}:{name.lower()}"
    return definitions.get(key)

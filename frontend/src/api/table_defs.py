import re
from pathlib import Path

INSTALL_SQL = Path(__file__).resolve().parents[3] / "sql" / "install.sql"

def get_create_statement(table: str) -> str | None:
	"""
	Extract and return the full CREATE TABLE …; definition for *table*
	from install.sql. Returns None if not found.
	"""
	pattern = re.compile(rf"CREATE\s+TABLE\s+`?{re.escape(table)}`?\s*\([^;]+?;", re.I | re.S)
	sql_text = INSTALL_SQL.read_text(encoding="utf-8")
	match = pattern.search(sql_text)
	return match.group(0) if match else None

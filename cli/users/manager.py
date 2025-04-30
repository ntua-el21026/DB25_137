"""
cli.users.manager
=================
Thin wrapper around mysql-connector for managing DB users and running scripts.

Public API
----------

User management:
----------------
UserManager.register_user(username, password)
            .grant_privileges(username, db, privs)
            .revoke_privileges(username, db, privs)
            .change_username(old, new)
            .change_password(username, new_pass)
            .drop_user(username)
            .list_users()
            .list_raw_users()
            .whoami()

Script execution:
-----------------
UserManager.execute_sql_file(path, database=None)
UserManager.truncate_tables(database)
UserManager.run_query_to_file(sql, out, database=...)

Utilities:
----------
parse_priv_list("SELECT,INSERT") -> ["SELECT", "INSERT"]
parse_priv_list("FULL")          -> ["ALL PRIVILEGES"]
"""

from __future__ import annotations

import contextlib
import logging
import re
from pathlib import Path
from typing import Iterable, List, Sequence

import mysql.connector
from mysql.connector.cursor_cext import CMySQLCursor

__all__ = ["UserManager", "parse_priv_list"]

# ---------------------------------------------------------------------------- #
# Utility function – Normalize privilege list (e.g., "SELECT,INSERT")
# ---------------------------------------------------------------------------- #
def parse_priv_list(raw: str | Iterable[str]) -> List[str]:
    """
    Accepts a comma-separated string or iterable and returns a normalized list.
    FULL or ALL   -> ["ALL PRIVILEGES"]
    """
    if isinstance(raw, str):
        raw = raw.split(",")
    cleaned = [p.strip().upper() for p in raw if p.strip()]
    if not cleaned:
        raise ValueError("Privilege list must not be empty.")
    if any(p in {"FULL", "ALL"} for p in cleaned):
        return ["ALL PRIVILEGES"]
    return cleaned


# ---------------------------------------------------------------------------- #
# Core class – manages users, privileges, and database scripts
# ---------------------------------------------------------------------------- #
class UserManager:
    def __init__(self, dsn: dict):
        print("▶ LOADED manager.py from", __file__)
        self._dsn = dsn
        self._log = logging.getLogger(self.__class__.__name__)

    # ------------------------------------------------------------------------ #
    # 1. USER ACCOUNT MANAGEMENT
    # ------------------------------------------------------------------------ #
    def register_user(self, username: str, password: str) -> None:
        self._execute_sql(
            "CREATE USER IF NOT EXISTS %(u)s@'%%' IDENTIFIED BY %(p)s;",
            {"u": username, "p": password},
        )

    def drop_user(self, username: str) -> None:
        self._execute_sql("DROP USER IF EXISTS %(u)s@'%';", {"u": username})

    def change_username(self, old: str, new: str) -> None:
        self._execute_sql(
            "RENAME USER %(old)s@'%%' TO %(new)s@'%%';",
            {"old": old, "new": new}
        )

    def change_password(self, username: str, new_password: str) -> None:
        self._execute_sql(
            "ALTER USER %(u)s@'%%' IDENTIFIED BY %(p)s;",
            {"u": username, "p": new_password},
        )

    def list_users(self) -> list[str]:
        output = []
        with self._connect() as cnx, cnx.cursor() as cur:
            cur.execute("SELECT user FROM mysql.user WHERE host = '%';")
            users = [row[0] for row in cur.fetchall()]
            for user in users:
                cur.execute(f"SHOW GRANTS FOR `{user}`@'%'")
                grants = [row[0] for row in cur.fetchall() if "GRANT USAGE ON" not in row[0]]
                if grants:
                    output.append(f"{user}\n  " + "\n  ".join(grants))
        return output

    def list_raw_users(self) -> list[str]:
        with self._connect() as cnx, cnx.cursor() as cur:
            cur.execute("SELECT user FROM mysql.user WHERE host = '%';")
            return [row[0] for row in cur.fetchall()]

    def whoami(self) -> str:
        with self._connect() as cnx, cnx.cursor() as cur:
            cur.execute("SELECT CURRENT_USER();")
            return cur.fetchone()[0]

    # ------------------------------------------------------------------------ #
    # 2. PRIVILEGE CONTROL
    # ------------------------------------------------------------------------ #
    def grant_privileges(self, username: str, database: str, privileges: Sequence[str]) -> None:
        priv_clause = ", ".join(privileges)
        self._execute_sql(
            f"GRANT {priv_clause} ON `{database}`.* TO %(u)s@'%%';",
            {"u": username},
        )

    def revoke_privileges(self, username: str, database: str, privileges: Sequence[str]) -> None:
        priv_clause = ", ".join(privileges)
        self._execute_sql(
            f"REVOKE {priv_clause} ON `{database}`.* FROM %(u)s@'%%';",
            {"u": username},
        )

    # ------------------------------------------------------------------------ #
    # 3. SQL FILE EXECUTION / DATA MANAGEMENT
    # ------------------------------------------------------------------------ #
    def execute_sql_file(self, path: str | Path, *, database: str | None = None) -> None:
        """
        Run every statement in a .sql file by opening one small, autocommitting
        connection per statement.  Compatible with MySQL 5.7 and avoids any
        “commands out of sync” errors since we never leave a pending result set
        nor call commit() on a dying connection.
        """
        # 1. Read file and strip out /* … */ block comments
        sql_text = Path(path).read_text(encoding="utf-8")
        sql_text = re.sub(r"/\*.*?\*/", "\n", sql_text, flags=re.S)

        # 2. Split into statements (honouring DELIMITER changes)
        delimiter = ";"
        buf       = ""
        statements: list[str] = []

        for raw in sql_text.splitlines():
            line = raw.rstrip()
            # skip single-line comments or decorative headers
            if re.match(r"^\s*(--|#)", line) or re.match(r"^\s*-{3,}", line):
                continue
            # handle “DELIMITER xxx”
            mdel = re.match(r"^\s*DELIMITER\s+(.+)$", line, re.I)
            if mdel:
                delimiter = mdel.group(1).strip()
                continue

            buf += line + "\n"
            if not line.endswith(delimiter):
                continue

            stmt = buf.rstrip()[:-len(delimiter)].strip()
            buf  = ""
            if stmt:
                statements.append(stmt)

        if buf.strip():
            statements.append(buf.strip())

        # 3. Execute each statement in its own autocommit connection
        current_db = database
        for stmt in statements:
            # a) Handle “USE foo”
            muse = re.match(r"^\s*USE\s+`?(\w+)`?\s*$", stmt, re.I)
            if muse:
                current_db = muse.group(1)
                continue

            # b) Rewrite “DROP INDEX IF EXISTS” → “DROP INDEX …”
            mdrop = re.match(
                r"^\s*DROP\s+INDEX\s+IF\s+EXISTS\s+`?(\w+)`?\s+ON\s+`?(\w+)`?\s*$",
                stmt, re.I
            )
            if mdrop:
                idx, tbl = mdrop.groups()
                stmt = f"DROP INDEX `{idx}` ON `{tbl}`"

            # c) Build connection params (with autocommit!)
            params = self._dsn.copy()
            if current_db:
                params["database"] = current_db
            params["autocommit"] = True

            # d) Run it
            try:
                with mysql.connector.connect(**params) as cnx, \
                     cnx.cursor()           as cur:
                    cur.execute(stmt)
            except mysql.connector.Error as err:
                # silently ignore “1091: Can’t drop … doesn’t exist”
                if err.errno == 1091 and mdrop:
                    continue
                self._log.warning(
                    "Statement failed in %s:\n%s\nError: %s",
                    Path(path).name, stmt, err
                )

    def truncate_tables(self, database: str) -> None:
        params = self._dsn.copy()
        params["database"] = database
        with mysql.connector.connect(**params) as cnx, cnx.cursor() as cur:
            cur.execute("SET FOREIGN_KEY_CHECKS = 0;")
            cur.execute("SHOW FULL TABLES WHERE Table_type = 'BASE TABLE';")
            tables = [row[0] for row in cur.fetchall()]
            for tbl in tables:
                cur.execute(f"TRUNCATE TABLE `{tbl}`;")
            cur.execute("SET FOREIGN_KEY_CHECKS = 1;")
            cnx.commit()
            self._log.info("Truncated %d tables in %s", len(tables), database)

    def run_query_to_file(self, sql_path: str | Path, out_path: str | Path, *, database: str) -> None:
        sql_path = Path(sql_path)
        out_path = Path(out_path)
        sql = sql_path.read_text(encoding="utf-8")

        params = self._dsn.copy()
        params["database"] = database

        with mysql.connector.connect(**params) as cnx, cnx.cursor() as cur:
            cur.execute(sql)
            rows = cur.fetchall()
            columns = [desc[0] for desc in cur.description]

        with out_path.open("w", encoding="utf-8") as f:
            if rows:
                f.write("\t".join(columns) + "\n")
                for row in rows:
                    f.write("\t".join(str(v) if v is not None else "NULL" for v in row) + "\n")
            else:
                f.write("(no rows)\n")

    def _execute_sql(self, stmt: str, params: dict | None = None) -> None:
        with self._connect() as cnx, cnx.cursor() as cur:
            try:
                cur.execute(stmt, params or {})
                cnx.commit()
                self._log.debug("Executed: %s", cur.statement)
            except mysql.connector.Error as exc:
                cnx.rollback()
                self._log.error(str(exc))
                raise

    @contextlib.contextmanager
    def _connect(self):
        cnx = mysql.connector.connect(**self._dsn)
        try:
            yield cnx
        finally:
            cnx.close()

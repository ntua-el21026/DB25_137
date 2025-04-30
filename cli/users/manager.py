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
from pathlib import Path
from typing import Iterable, List, Sequence

import mysql.connector
from mysql.connector import errorcode

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
        self._dsn = dsn
        self._log = logging.getLogger(self.__class__.__name__)

    # ------------------------------------------------------------------------ #
    # 1. USER ACCOUNT MANAGEMENT
    # ------------------------------------------------------------------------ #
    def register_user(self, username: str, password: str) -> None:
        """Create a new MySQL user with password (if not exists)."""
        self._execute_sql(
            "CREATE USER IF NOT EXISTS %(u)s@'%%' IDENTIFIED BY %(p)s;",
            {"u": username, "p": password},
        )

    def drop_user(self, username: str) -> None:
        """Delete user from the database (if exists)."""
        self._execute_sql("DROP USER IF EXISTS %(u)s@'%';", {"u": username})

    def change_username(self, old: str, new: str) -> None:
        """Rename an existing MySQL user."""
        self._execute_sql(
            "RENAME USER %(old)s@'%%' TO %(new)s@'%%';",
            {"old": old, "new": new}
        )

    def change_password(self, username: str, new_password: str) -> None:
        """Change the password of an existing user."""
        self._execute_sql(
            "ALTER USER %(u)s@'%%' IDENTIFIED BY %(p)s;",
            {"u": username, "p": new_password},
        )

    def list_users(self) -> list[str]:
        """Return each user with their actual (non-USAGE) privileges."""
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
        """Return raw list of usernames (used internally for drop-all)."""
        with self._connect() as cnx, cnx.cursor() as cur:
            cur.execute("SELECT user FROM mysql.user WHERE host = '%';")
            return [row[0] for row in cur.fetchall()]

    def whoami(self) -> str:
        """Returns the current connection's MySQL user."""
        with self._connect() as cnx, cnx.cursor() as cur:
            cur.execute("SELECT CURRENT_USER();")
            return cur.fetchone()[0]

    # ------------------------------------------------------------------------ #
    # 2. PRIVILEGE CONTROL
    # ------------------------------------------------------------------------ #
    def grant_privileges(self, username: str, database: str,
                            privileges: Sequence[str]) -> None:
        """Grant specific privileges to a user on a database."""
        priv_clause = ", ".join(privileges)
        self._execute_sql(
            f"GRANT {priv_clause} ON `{database}`.* TO %(u)s@'%%';",
            {"u": username},
        )

    def revoke_privileges(self, username: str, database: str,
                            privileges: Sequence[str]) -> None:
        """Revoke specific privileges from a user on a database."""
        priv_clause = ", ".join(privileges)
        self._execute_sql(
            f"REVOKE {priv_clause} ON `{database}`.* FROM %(u)s@'%%';",
            {"u": username},
        )

    # ------------------------------------------------------------------------ #
    # 3. SQL FILE EXECUTION / DATA MANAGEMENT
    # ------------------------------------------------------------------------ #
    def execute_sql_file(self, path: str | Path, *,
                            database: str | None = None) -> None:
        """
        Run all statements from a .sql file. Supports multi-statement files.
        """
        path = Path(path)
        sql_source = path.read_text(encoding="utf-8")

        params = self._dsn.copy()
        if database:
            params["database"] = database

        with mysql.connector.connect(**params) as cnx, cnx.cursor() as cur:
            for _ in cur.execute(sql_source, multi=True):
                pass
            cnx.commit()
            self._log.debug("Executed SQL file %s", path)

    def truncate_tables(self, database: str) -> None:
        """TRUNCATE all base tables in the schema, ignoring foreign keys temporarily."""
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

    def run_query_to_file(self, sql_path: str | Path, out_path: str | Path,
                          *, database: str) -> None:
        """Execute a single SQL file and write results (if any) to a .txt file."""
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

    # ------------------------------------------------------------------------ #
    # 4. INTERNAL – SQL execution with param binding
    # ------------------------------------------------------------------------ #
    def _execute_sql(self, stmt: str, params: dict | None = None) -> None:
        """Run a single SQL statement with optional param binding."""
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
        """Context-managed connection to the DB using stored DSN."""
        cnx = mysql.connector.connect(**self._dsn)
        try:
            yield cnx
        finally:
            cnx.close()

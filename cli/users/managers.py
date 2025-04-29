"""
cli.users.manager
=================
Thin wrapper around mysql-connector that performs the actual GRANT / REVOKE.

Public API
----------
UserManager.register_user(username, password)
            .grant_privileges(username, db, privs)
            .revoke_privileges(username, db, privs)
            .change_username(old, new)
            .change_password(username, new_pass)
parse_priv_list("SELECT,INSERT") -> ["SELECT", "INSERT"]
parse_priv_list("FULL")          -> ["ALL PRIVILEGES"]
"""
from __future__ import annotations
import contextlib
import logging
from typing import Iterable, List, Sequence

import mysql.connector            # pip install mysql-connector-python
from mysql.connector import errorcode

__all__ = ["UserManager", "parse_priv_list"]

# --------------------------------------------------------------------------- #
# Helper – recognise FULL / ALL
# --------------------------------------------------------------------------- #
def parse_priv_list(raw: str | Iterable[str]) -> List[str]:
    """
    Accepts a comma-separated string or iterable and returns a normalised list.
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


# --------------------------------------------------------------------------- #
class UserManager:
    def __init__(self, dsn: dict):
        self._dsn = dsn
        self._log = logging.getLogger(self.__class__.__name__)

    # ---------------------------- public API -------------------------------- #
    def register_user(self, username: str, password: str) -> None:
        self._execute_sql(
            f"CREATE USER IF NOT EXISTS `{username}`@'%' IDENTIFIED BY %(pw)s;",
            {"pw": password},
        )

    def grant_privileges(self, username: str, database: str,
                            privileges: Sequence[str]) -> None:
        priv_clause = ", ".join(privileges)
        self._execute_sql(
            f"GRANT {priv_clause} ON `{database}`.* TO `{username}`@'%';"
        )

    def revoke_privileges(self, username: str, database: str,
                            privileges: Sequence[str]) -> None:
        priv_clause = ", ".join(privileges)
        self._execute_sql(
            f"REVOKE {priv_clause} ON `{database}`.* FROM `{username}`@'%';"
        )

    def change_username(self, old: str, new: str) -> None:
        self._execute_sql(f"RENAME USER `{old}`@'%' TO `{new}`@'%';")

    def change_password(self, username: str, new_password: str) -> None:
        self._execute_sql(
            f"ALTER USER `{username}`@'%' IDENTIFIED BY %(pw)s;",
            {"pw": new_password},
        )

    # ---------------------------- internals --------------------------------- #
    def _execute_sql(self, stmt: str, params: dict | None = None) -> None:
        with self._connect() as cnx:
            with cnx.cursor() as cur:
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

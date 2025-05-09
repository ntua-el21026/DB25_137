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
UserManager.run_query_to_file(sql, out, database=.)

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
import os
import click
import mysql.connector
from mysql.connector import errorcode
from mysql.connector.cursor_cext import CMySQLCursor

DEFAULT_DB = os.getenv("DB_NAME", "pulse_university")

__all__ = ["UserManager", "parse_priv_list"]

# ---------------------------------------------------------------------------- #
# Utility function – Normalize privilege list (e.g. "SELECT,INSERT")
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
    def __init__(self, root_user, root_pass, host="127.0.0.1", port=3306):
        self._user = root_user
        self._pass = root_pass
        self._log = logging.getLogger(__name__)
        self._dsn = {
            "user": self._user,
            "password": self._pass,
            "host": host,
            "port": port,
            "autocommit": True,
            "unix_socket": None
        }

    # ------------------------------------------------------------------------ #
    # 1. USER ACCOUNT MANAGEMENT
    # ------------------------------------------------------------------------ #
    def register_user(self, username, password, default_db, privileges):
        """Register a new user with specified privileges on a given database."""
        if not self.is_root():
            raise click.ClickException("Only root users can register new users.")

        try:
            with self._connect() as cnx, cnx.cursor() as cursor:
                privs = ', '.join(privileges)

                for host in ('%', 'localhost'):
                    try:
                        cursor.execute(
                            f"CREATE USER `{username}`@'{host}' IDENTIFIED BY %s", (password,)
                        )
                    except mysql.connector.errors.DatabaseError as e:
                        if e.errno == errorcode.ER_CANNOT_USER:
                            raise click.ClickException(f"User `{username}` already exists at host '{host}'.")
                        else:
                            raise

                    cursor.execute(
                        f"GRANT {privs} ON `{default_db}`.* TO `{username}`@'{host}'"
                    )
                    try:
                        cursor.execute(
                            f"GRANT USAGE ON *.* TO `{username}`@'{host}'"
                        )
                    except mysql.connector.Error as e:
                        if e.errno != errorcode.ER_SPECIFIC_ACCESS_DENIED_ERROR:
                            raise

                cnx.commit()
                click.echo(f"[OK] Registered `{username}` with privileges on `{default_db}` for % and localhost")

        except mysql.connector.Error as err:
            raise click.ClickException(f"[DB Error] {err}")

    # ... rest of the methods unchanged ...

    @contextlib.contextmanager
    def _connect(self, database: str | None = None):
        dsn = self._dsn.copy()
        dsn["host"] = os.getenv("DB_HOST", dsn["host"])
        dsn["port"] = int(os.getenv("DB_PORT", dsn["port"]))
        env_db = os.getenv("DB_NAME")
        if database:
            dsn["database"] = database
        elif env_db:
            dsn["database"] = env_db

        cnx = mysql.connector.connect(**dsn)
        try:
            yield cnx
        finally:
            cnx.close()

    def drop_user(self, username: str) -> None:
        dropped = False
        for host in ('%', 'localhost'):
            with self._connect() as cnx, cnx.cursor() as cur:
                cur.execute(
                    "SELECT COUNT(*) FROM mysql.user WHERE user=%s AND host=%s",
                    (username, host)
                )
                if cur.fetchone()[0] > 0:
                    cur.execute(f"DROP USER `{username}`@'{host}'")
                    dropped = True

        if not dropped:
            click.echo(f"[WARN] User `{username}` not found on '%' or 'localhost'.")

            
    def drop_all_users(self) -> None:
        """Drop all non-system users (excluding 'root' and MySQL internal accounts) on all hosts."""
        if not self.is_root():
            raise click.ClickException("Only root users can drop users.")

        with self._connect() as cnx, cnx.cursor() as cur:
            # Exclude MySQL internal/system users
            cur.execute("""
                SELECT DISTINCT user, host
                FROM mysql.user
                WHERE user NOT IN (
                    'root', 'mysql.sys', 'mysql.session', 'mysql.infoschema', 'debian-sys-maint'
                )
            """)
            accounts = cur.fetchall()

            if not accounts:
                click.echo("[INFO] No non-system users found.")
                return

            for user, host in accounts:
                try:
                    cur.execute(f"DROP USER `{user}`@'{host}'")
                    click.echo(f"Dropped user {user}@{host}")
                except mysql.connector.Error as e:
                    click.echo(f"[SKIP] Could not drop {user}@{host}: {e}")

            cnx.commit()

    def change_username(self, old: str, new: str) -> None:
        if self.is_root():
            self._execute_sql(
                "RENAME USER %(old)s@'%' TO %(new)s@'%';",
                {"old": old, "new": new}
            )
        else:
            self._execute_sql(
                "CALL sp_rename_self(%(new)s);",
                {"new": new}
            )

    def change_password(self, username: str, new_password: str) -> None:
        current_user = self.connected_user().split("@")[0]
        if current_user == username:
            # Let user change their own password without needing CREATE USER
            self._execute_sql("SET PASSWORD = %(p)s;", {"p": new_password})
        else:
            # Must be root to update other accounts; update both host variants
            for host in ('%', 'localhost'):
                self._execute_sql(
                    f"ALTER USER %(u)s@'{host}' IDENTIFIED BY %(p)s;",
                    {"u": username, "p": new_password}
                )

    def list_users(self) -> list[str]:
        output = []
        with self._connect() as cnx, cnx.cursor() as cur:
            # Select all users and their hosts
            cur.execute("SELECT user, host FROM mysql.user WHERE user NOT IN ('mysql.infoschema', 'mysql.session', 'mysql.sys')")
            users = cur.fetchall()

            for user, host in users:
                try:
                    cur.execute(f"SHOW GRANTS FOR `{user}`@'{host}'")
                    grants = [row[0] for row in cur.fetchall()]
                    output.append(f"{user}@{host}\n  " + "\n  ".join(grants))
                except mysql.connector.Error as e:
                    output.append(f"{user}@{host}\n  [ERROR fetching grants: {e}]")
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

    # Administrative / global privileges that MUST be granted ON *.*
    _GLOBAL_PRIVS = {
        "ALTER USER", "CREATE USER", "DROP USER",
        "CREATE ROLE", "DROP ROLE", "ROLE_ADMIN", "SYSTEM_USER",
    }

    def grant_privileges(
        self,
        username: str,
        database: str,
        privileges: Sequence[str],
    ) -> None:
        """
        Grant schema-level and global privileges in one call.

        * schema privileges → GRANT … ON  `database`.* TO  'user'@'%';
        * global  privileges → GRANT … ON  *.*          TO  'user'@'%';
        """
        if not privileges:
            raise ValueError("Privilege list must not be empty.")

        # normalise                                     ▼ NEW
        privs = [p.upper().strip() for p in privileges]

        db_privs     = [p for p in privs if p not in self._GLOBAL_PRIVS]
        global_privs = [p for p in privs if p in self._GLOBAL_PRIVS]

        if db_privs:
            self._execute_sql(
                f"GRANT {', '.join(db_privs)} ON `{database}`.* TO %(u)s@'%';",
                {"u": username},
            )

        if global_privs:
            # global privileges must carry the ON *.* clause  ▼ NEW
            self._execute_sql(
                f"GRANT {', '.join(global_privs)} ON *.* TO %(u)s@'%';",
                {"u": username},
            )

    def revoke_privileges(self, username, db, to_revoke):
        """Revoke specific privileges from a user on a given database."""
        with self._connect() as conn:
            with conn.cursor() as cursor:
                # 1. Get current privileges from INFORMATION_SCHEMA
                cursor.execute("""
                    SELECT privilege_type
                    FROM information_schema.schema_privileges
                    WHERE grantee = %s AND table_schema = %s
                """, (f"'{username}'@'%'", db))
                current = {row[0].upper() for row in cursor.fetchall()}

                if not current:
                    print(f"[WARN] No privileges found for user '{username}' on database '{db}'")
                    return

                # 2. Compute what remains after revocation
                remaining = current - set(p.upper() for p in to_revoke)

                # 3. Revoke all privileges on that DB
                cursor.execute(f"REVOKE ALL PRIVILEGES ON `{db}`.* FROM `{username}`@'%'")

                # 4. Re-grant only the remaining ones
                if remaining:
                    priv_str = ",".join(sorted(remaining))
                    cursor.execute(f"GRANT {priv_str} ON `{db}`.* TO `{username}`@'%'")
                    print(f"[OK] Re-granted: {priv_str}")
                else:
                    print(f"[OK] All privileges revoked from {username} on {db}")

            conn.commit()

    # ------------------------------------------------------------------------ #
    # 3. SQL FILE EXECUTION / DATA MANAGEMENT
    # ------------------------------------------------------------------------ #
    def execute_sql_file(self, path: str | Path, *, database: str | None = None) -> None:
        """
        Run every statement in a .sql file.

        * Still works without DELIMITER directives.
        * Correctly buffers CREATE {PROCEDURE|FUNCTION|TRIGGER|EVENT} bodies even
        when they contain nested BEGIN … END blocks.
        * Splits ordinary DDL/DML on the terminating semicolon.
        """
        sql_text = Path(path).read_text(encoding="utf-8")

        # strip /* … */ comments first (newline‑friendly)
        sql_text = re.sub(r"/\*.*?\*/", "\n", sql_text, flags=re.S)

        statements: list[str] = []
        buf: list[str] = []

        depth = 0          # nesting depth of BEGIN/END
        in_routine = False # inside CREATE PROC / FUNC / TRIGGER / EVENT

        routine_start_re = re.compile(
            r"^\s*CREATE\s+(?:DEFINER\s*=\s*\S+\s+)?"
            r"(PROCEDURE|FUNCTION|TRIGGER|EVENT)\b",
            re.I,
        )

        for raw in sql_text.splitlines():
            line = raw.rstrip()

            # ignore -- / # full‑line comments
            if re.match(r"^\s*(--|#)", line):
                continue

            # ── Detect start of a stored routine ───────────────────────────────
            if not in_routine and routine_start_re.match(line):
                in_routine = True
                depth = 0                    # reset depth counter

            # accumulate line
            buf.append(line)

            # Track nesting only when we're inside a routine
            if in_routine:
                # count BEGIN (but not BEGIN … END for handlers/loops keywords)
                if re.search(r"\bBEGIN\b", line, re.I):
                    depth += 1
                # END followed by ; closes one level
                if re.search(r"\bEND\s*;\s*$", line, re.I):
                    depth -= 1
                    if depth == 0:
                        # full routine captured
                        statements.append("\n".join(buf).strip())
                        buf.clear()
                        in_routine = False
                continue

            # ── Normal splitter outside routines ───────────────────────────────
            if line.endswith(";"):
                # remove trailing semicolon
                buf[-1] = buf[-1][:-1]
                statements.append("\n".join(buf).strip())
                buf.clear()

        # leftover (no trailing ;) ?
        if buf:
            statements.append("\n".join(buf).strip())

        # ------------------------------------------------------------------- #
        # Execute collected statements (unchanged from original implementation)
        # ------------------------------------------------------------------- #
        current_db = database
        for stmt in statements:
            muse = re.match(r"^\s*USE\s+`?(\w+)`?\s*$", stmt, re.I)
            if muse:
                current_db = muse.group(1)
                continue

            params = self._dsn.copy()
            params["autocommit"] = True
            if current_db:
                params["database"] = current_db

            try:
                with mysql.connector.connect(**params) as cnx, cnx.cursor() as cur:
                    cur.execute(stmt)
                    while cur.nextset():
                        pass
            except mysql.connector.Error as err:
                raise click.ClickException(
                    f"\nStatement failed in `{Path(path).name}`:\n"
                    f"{stmt[:300]}...\n"
                    f"Error {err.errno}: {err.msg}"
                )

    def truncate_tables(self, database: str) -> None:
        """
        Truncates all base tables in the schema.
        WARNING: FOREIGN_KEY_CHECKS are disabled temporarily – do not use on production data!
        Logs number of tables truncated.
        """
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
            print(f"[INFO] Truncated {len(tables)} tables in `{database}`")  # Simple stdout logging

    def run_query_to_file(self, sql_path: str | Path, out_path: str | Path, *, database: str) -> None:
        """
        Run a single SQL query and export the results to a tab-separated text file.

        - Only allows reading from files inside the designated queries directory.
        - Prevents accidental path traversal or misuse.
        - Writes header + rows if any, or '(no rows)' if result is empty.
        """
        sql_path = Path(sql_path).resolve()
        out_path = Path(out_path).resolve()

        # --- Security check: only allow queries from inside expected directory ---
        queries_root = Path(os.getenv("QUERIES_DIR", "sql/queries")).resolve()
        if not str(sql_path).startswith(str(queries_root)):
            raise ValueError(f"Access denied: {sql_path} is outside allowed queries directory.")

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
    def _connect(self, database: str | None = None):
        dsn = self._dsn.copy()
        dsn["host"] = os.getenv("DB_HOST", "localhost")
        if database:
            dsn["database"] = database
        cnx = mysql.connector.connect(**dsn)
        try:
            yield cnx
        finally:
            cnx.close()

    def connected_user(self) -> str:
        """Returns the connected username (e.g., 'root@localhost')"""
        return self.whoami()

    def is_root(self) -> bool:
        """Checks if the connected user is root (host-insensitive)"""
        user = self.connected_user().lower()
        return user.startswith("root@") or user == "root@localhost"

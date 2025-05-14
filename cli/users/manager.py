"""
cli.users.manager
=================
Thin wrapper around mysql-connector for managing DB users and executing scripts.

Public API
----------

User management:
----------------
UserManager.register_user(username, password)
    → Creates user with access from both '%' and 'localhost'
UserManager.grant_privileges(username, db, privs)
    → Grants privileges on db for both '%' and 'localhost' entries
UserManager.revoke_privileges(username, db, privs)
    → Revokes all privileges on db for both '%' and 'localhost'
UserManager.change_username(old, new)
UserManager.change_password(username, new_pass)
UserManager.drop_user(username)
    → Removes user entries from both '%' and 'localhost'
UserManager.list_users()
UserManager.list_raw_users()
UserManager.whoami()

Script execution:
-----------------
UserManager.execute_sql_file(path, database=None)
UserManager.truncate_tables(database)
UserManager.run_query_to_file(sql, out, database=.)

Utilities:
----------
parse_priv_list("SELECT,INSERT") → ["SELECT", "INSERT"]
parse_priv_list("FULL")          → ["ALL PRIVILEGES"]
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
HOSTS = ('%', 'localhost')

def _foreach_host(fn):
    for h in HOSTS:
        fn(h)

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
    # ------------------------------------------------------------------
    #  Default + special heading sequences
    # ------------------------------------------------------------------
    _LABELS_DEFAULT = (
        "RESULT",
        "EXPLAIN",
        "EXPLAIN ANALYZE",
        "OPTIMIZER_TRACE",
    )
    _LABELS_BY_PLAN = {
        3: (
            "RESULT",
            "EXPLAIN",
            "EXPLAIN ANALYZE HASH",
            "EXPLAIN ANALYZE NESTED LOOP",
        )
    }

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
        """
        Rename a user on *both* '%' and 'localhost'.
        Non‑root callers may only rename themselves (handled by caller).
        """
        if self.is_root():
            for host in ('%', 'localhost'):
                # Skip missing rows quietly so one orphan does not abort the loop
                try:
                    self._execute_sql(
                        f"RENAME USER %(old)s@'{host}' TO %(new)s@'{host}';",
                        {"old": old, "new": new}
                    )
                except mysql.connector.Error as e:
                    if e.errno != errorcode.ER_NONEXISTING_GRANT:  # row not found
                        raise
        else:
            # Stored‑procedure path for self‑rename (unchanged)
            self._execute_sql("CALL sp_rename_self(%(new)s);", {"new": new})

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
        if not self.is_root():
            raise click.ClickException("Only root can list all users.")
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
        Grant schema-level and global privileges to both '%' and 'localhost'.

        * schema privileges → GRANT … ON  `database`.* TO  'user'@'{host}';
        * global privileges → GRANT … ON  *.*         TO  'user'@'{host}';
        """
        if not privileges:
            raise ValueError("Privilege list must not be empty.")

        privs = [p.upper().strip() for p in privileges]
        db_privs     = [p for p in privs if p not in self._GLOBAL_PRIVS]
        global_privs = [p for p in privs if p in self._GLOBAL_PRIVS]

        def grant_for_host(host: str):
            if db_privs:
                self._execute_sql(
                    f"GRANT {', '.join(db_privs)} ON `{database}`.* TO %(u)s@'{host}';",
                    {"u": username},
                )
            if global_privs:
                self._execute_sql(
                    f"GRANT {', '.join(global_privs)} ON *.* TO %(u)s@'{host}';",
                    {"u": username},
                )

        _foreach_host(grant_for_host)

    def revoke_privileges(
        self,
        username: str,
        db: str,
        to_revoke: Sequence[str],
    ) -> None:
        """
        Revoke specific privileges from both '%' and 'localhost' on the given database.
        """
        to_revoke = {p.upper().strip() for p in to_revoke}

        with self._connect() as conn:
            with conn.cursor() as cursor:
                def revoke_for_host(host: str):
                    cursor.execute("""
                        SELECT privilege_type
                        FROM information_schema.schema_privileges
                        WHERE grantee = %s AND table_schema = %s
                    """, (f"'{username}'@'{host}'", db))
                    current = {row[0].upper() for row in cursor.fetchall()}

                    if not current:
                        print(f"[WARN] No privileges found for '{username}'@'{host}' on '{db}'")
                        return

                    remaining = current - to_revoke
                    cursor.execute(
                        f"REVOKE ALL PRIVILEGES ON `{db}`.* FROM `{username}`@'{host}'")

                    if remaining:
                        priv_str = ",".join(sorted(remaining))
                        cursor.execute(
                            f"GRANT {priv_str} ON `{db}`.* TO `{username}`@'{host}'")
                        print(f"[OK] {host}: re-granted: {priv_str}")
                    else:
                        print(f"[OK] {host}: all privileges revoked from {username} on {db}")

                _foreach_host(revoke_for_host)
            conn.commit()

    # ------------------------------------------------------------------------ #
    # 3. SQL FILE EXECUTION / DATA MANAGEMENT
    # ------------------------------------------------------------------------ #
    def execute_sql_file(self, path: str | Path, *, database: str | None = None, show_progress: bool = False) -> None:
        """
        Run every statement in a .sql file.

        * Still works without DELIMITER directives.
        * Correctly buffers CREATE {PROCEDURE|FUNCTION|TRIGGER|EVENT} bodies even
        when they contain nested BEGIN … END blocks.
        * Splits ordinary DDL/DML on the terminating semicolon.
        * Optionally displays a progress bar using Click.
        """
        sql_text = Path(path).read_text(encoding="utf-8")

        # Strip /* ... */ comments (multi-line)
        sql_text = re.sub(r"/\*.*?\*/", "\n", sql_text, flags=re.S)

        statements: list[str] = []
        buf: list[str] = []

        depth = 0
        in_routine = False

        routine_start_re = re.compile(
            r"^\s*CREATE\s+(?:DEFINER\s*=\s*\S+\s+)?"
            r"(PROCEDURE|FUNCTION|TRIGGER|EVENT)\b",
            re.I,
        )

        for raw in sql_text.splitlines():
            line = raw.rstrip()

            if re.match(r"^\s*(--|#)", line):
                continue

            if not in_routine and routine_start_re.match(line):
                in_routine = True
                depth = 0

            buf.append(line)

            if in_routine:
                if re.search(r"\bBEGIN\b", line, re.I):
                    depth += 1
                if re.search(r"\bEND\s*;\s*$", line, re.I):
                    depth -= 1
                    if depth == 0:
                        statements.append("\n".join(buf).strip())
                        buf.clear()
                        in_routine = False
                continue

            if line.endswith(";"):
                buf[-1] = buf[-1][:-1]
                statements.append("\n".join(buf).strip())
                buf.clear()

        if buf:
            statements.append("\n".join(buf).strip())

        # Execute statements (with optional progress bar)
        current_db = database

        def run_statement(stmt: str):
            nonlocal current_db
            muse = re.match(r"^\s*USE\s+`?(\w+)`?\s*$", stmt, re.I)
            if muse:
                current_db = muse.group(1)
                return

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

        if show_progress:
            with click.progressbar(statements, label=f"Executing {path.name}") as bar:
                for stmt in bar:
                    run_statement(stmt)
        else:
            for stmt in statements:
                run_statement(stmt)

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

    # ------------------------------------------------------------------
    #  Pretty printer shared by both runners
    # ------------------------------------------------------------------
    def _write_aligned(self, fp, columns: list[str], rows: list[tuple]) -> None:
        if not rows:
            fp.write("(no rows)\n")
            return

        # 1‑column: dump raw, no padding
        if len(columns) == 1:
            fp.write(f"{columns[0]}\n")
            fp.write("-" * len(columns[0]) + "\n")
            for r, in rows:
                fp.write(f"{'' if r is None else r}\n")
            return

        widths = [len(c) for c in columns]
        for row in rows:
            for i, cell in enumerate(row):
                widths[i] = max(widths[i], len(str(cell)) if cell is not None else 4)

        fp.write("  ".join(col.ljust(widths[i]) for i, col in enumerate(columns)) + "\n")
        fp.write("  ".join("-" * widths[i] for i in range(len(columns))) + "\n")

        for row in rows:
            parts = []
            for i, cell in enumerate(row):
                txt = "NULL" if cell is None else str(cell)
                parts.append(txt.ljust(widths[i]) if i < len(columns) - 1 else txt)
            fp.write("  ".join(parts) + "\n")

    # ------------------------------------------------------------------
    #  Single‑query runner (unchanged logic, but reuses _write_aligned)
    # ------------------------------------------------------------------
    def run_query_to_file(self, sql_path: str | Path, out_path: str | Path, *, database: str) -> None:
        sql_path = Path(sql_path).resolve()
        out_path = Path(out_path).resolve()

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
            self._write_aligned(f, columns, rows)

    # ------------------------------------------------------------------
    #  Position-based splitter: never misses a  "-- PLAN"  header
    # ------------------------------------------------------------------
    def _split_trace_plans(self, sql_text: str) -> list[list[str]]:
        """
        • A header is any line that starts with   --   and contains the
          word PLAN (case-insensitive) somewhere to the right.
        • Works with leading BOM, CRLF, tabs, non-breaking spaces, etc.
        • Returns a list of bundles; each bundle is a list[str] of SQL
          statements (semicolon kept).
        """
        import re

        text = sql_text.lstrip("\ufeff").replace("\r\n", "\n")

        # locations of every header line (byte offsets)
        headers = [m.start() for m in re.finditer(
            r"(?im)^.{0,50}--[^\n]*\bPLAN\b[^\n]*$", text)]

        if len(headers) < 2:
            raise click.ClickException(
                f"Expected ≥2 '-- PLAN' sections, found {len(headers)}."
            )

        # add EOF to simplify slicing
        headers.append(len(text))

        bundles: list[list[str]] = []
        for i in range(len(headers) - 1):
            block = text[headers[i]: headers[i+1]]
            # strip first line (the header itself)
            block = block.split("\n", 1)[1] if "\n" in block else ""
            stmts = [s.strip() + ";" for s in
                     re.split(r";\s*$", block, flags=re.M) if s.strip()]
            bundles.append(stmts)

        return bundles

    # ------------------------------------------------------------------
    #  Multi‑plan runner (handles Q04, Q06)
    # ------------------------------------------------------------------
    def run_multi_plan_query_to_files(self, sql_path: str | Path, out_prefix: str | Path, *, database: str) -> int:
        sql_path = Path(sql_path).resolve()
        sql_text = sql_path.read_text(encoding="utf-8")
        bundles = self._split_trace_plans(sql_text)

        params = self._dsn.copy()
        params["database"] = database

        for idx, bundle in enumerate(bundles, start=1):
            labels = self._LABELS_BY_PLAN.get(idx, self._LABELS_DEFAULT)
            result_step = 0

            out_path = Path(f"{out_prefix}{idx}_out.txt").resolve()
            with mysql.connector.connect(**params) as cnx, \
                 cnx.cursor() as cur, \
                 out_path.open("w", encoding="utf-8") as fp:

                cur.execute("SET optimizer_trace='enabled=on';")

                for stmt in bundle:
                    cur.execute(stmt)
                    if not cur.with_rows:  # SET / ALTER etc.
                        continue

                    rows = cur.fetchall()
                    cols = cur.column_names
                    label = labels[result_step % len(labels)]
                    result_step += 1

                    fp.write(f"\n## PLAN {idx} — {label} ##\n")
                    self._write_aligned(fp, cols, rows)

        return len(bundles)  # caller prints the filename list based on this

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

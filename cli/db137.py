#!/usr/bin/env python3
"""
db137 – Pulse-University DB CLI
===============================

Available Commands
------------------

USERS
--------
users register        Create a new DB user and grant privileges
users grant           Add privileges to an existing user
users revoke          Remove privileges from a user
users rename          Rename a user account
users passwd          Change user password
users list            Show all users and their privileges
users drop            Delete a database user entirely
users drop-all        Delete all users defined on '%'
users whoami          Show current DB connection info
users set-defaults    Grant typical privileges (SELECT, INSERT, .)

DATABASE SETUP
-------------------
create-db             Create schema and deploy all SQL scripts
load-db               Load synthetic data via faker or load.sql in the database
reset-db              Shortcut for drop-db + create-db + load-db
erase-db              Truncate all tables (except lookup), preserving structure
drop-db               Drop the entire schema
db-status             Show row counts for each table in the schema
viewq                 Shows the queue matching log

QUERIES
-----------
q X                   Run sql/queries/QX.sql and save to QX_out.txt
q X Y                 Run range of queries and save results (e.g. q 1 4)
"""

from __future__ import annotations

import os
import sys
import subprocess
import re
from pathlib import Path
from typing import List

import click
from click import argument
import mysql.connector

CURRENT_FILE = Path(__file__).resolve()
PROJECT_ROOT = CURRENT_FILE.parents[1]
if str(PROJECT_ROOT.parent) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT.parent))

from cli.users.manager import UserManager, parse_priv_list

# Default DB name now honors $DB_NAME
DEFAULT_DB = os.getenv("DB_NAME", "pulse_university")
DEFAULT_SQL_DIR = PROJECT_ROOT / "sql"
FAKER_SCRIPT = PROJECT_ROOT / "code" / "data_generation" / "faker.py"
QUERIES_DIR = DEFAULT_SQL_DIR / "queries"

@click.group(context_settings=dict(help_option_names=["-h", "--help"]))
# Host/Port options now read from $DB_HOST / $DB_PORT
@click.option(
    "--host",
    envvar="DB_HOST",
    default=lambda: os.getenv("DB_HOST", "localhost"),
    show_default=True,
    help="Database server hostname (or $DB_HOST)"
)
@click.option(
    "--port",
    envvar="DB_PORT",
    default=lambda: int(os.getenv("DB_PORT", 3306)),
    show_default=True,
    type=int,
    help="Database server port (or $DB_PORT)"
)
@click.option("--root-user", envvar="DB_ROOT_USER", required=True)
@click.option("--root-pass", envvar="DB_ROOT_PASS", required=True)
@click.pass_context
def cli(ctx, host, port, root_user, root_pass):
    user_mgr = UserManager(
        root_user=root_user,
        root_pass=root_pass,
        host=host,
        port=port
    )

    # Try to establish DB connection and identify user
    try:
        ctx.obj = user_mgr
        ctx.obj._connected_user = user_mgr.whoami()
    except mysql.connector.Error as err:
        raise click.ClickException(
            f"[DB Connection Error] Unable to connect as '{root_user}':\n{err}"
        )

# root-only decorator
def root_only(cmd):
    """
    Mark a Click Command *or* Group as admin‑only.

    IMPORTANT – it must be applied *after* @cli.command / @cli.group,
    i.e. be the top‑most decorator:

        @cli.command("create-db")
        @root_only             # ← here
        def create_db(): ...
    """
    cmd.root_only = True
    return cmd

def require_root(user_mgr: UserManager):
    if not user_mgr.is_root():
        raise click.ClickException("This command is restricted to root users.")


def require_root_or_self(user_mgr: UserManager, target: str):
    current_user = user_mgr.connected_user().split("@")[0]
    if not user_mgr.is_root() and current_user != target:
        raise click.ClickException("You can only modify your own account.")
    

def print_privs(user_mgr: UserManager, username: str, db: str):
    """
    Utility: Show granted privileges for a user on a specific database.
    """
    with user_mgr._connect() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT privilege_type
                FROM information_schema.schema_privileges
                WHERE grantee = %s AND table_schema = %s
            """, (f"'{username}'@'%'", db))
            rows = cursor.fetchall()
            if not rows:
                click.echo("  (none)")
            else:
                for r in sorted(p[0] for p in rows):
                    click.echo(f"  - {r}")

# -------------------- USERS --------------------

@cli.group()
def users():
    """Manage DB users."""
    pass

@root_only
@users.command("register")
@click.argument("username")
@click.password_option("--password", prompt=True, confirmation_prompt=True)
@click.option("--default-db", default=DEFAULT_DB, show_default=True)
@click.option("--privileges", default="FULL", show_default=True)
@click.pass_obj
def register(user_mgr: UserManager, username, password, default_db, privileges):
    require_root(user_mgr)
    parsed_privs = parse_priv_list(privileges)
    user_mgr.register_user(username, password, default_db, parsed_privs)
    click.echo(f"[OK] User '{username}' registered. Use `db137 users list` to verify grants.")

@root_only
@users.command("grant")
@click.argument("username")
@click.option("--db", required=True)
@click.option("--privileges", required=True)
@click.option("--show-diff", is_flag=True, help="Display privilege changes")
@click.pass_obj
def grant(user_mgr: UserManager, username, db, privileges, show_diff):
    require_root(user_mgr)
    priv_list = parse_priv_list(privileges)

    # Show current privileges (optional)
    if show_diff:
        click.echo(f"Before:\n  {username}@% →")
        print_privs(user_mgr, username, db)

    user_mgr.grant_privileges(username, db, priv_list)
    click.echo(f"Granted {privileges} on {db} to {username}.")

    if show_diff:
        click.echo(f"After:\n  {username}@% →")
        print_privs(user_mgr, username, db)

@root_only
@users.command("revoke")
@click.argument("username")
@click.option("--db", required=True)
@click.option("--privileges", required=True)
@click.option("--show-diff", is_flag=True, help="Display privilege changes")
@click.pass_obj
def revoke(user_mgr: UserManager, username, db, privileges, show_diff):
    require_root(user_mgr)
    priv_list = parse_priv_list(privileges)

    if show_diff:
        click.echo(f"Before:\n  {username}@% →")
        print_privs(user_mgr, username, db)

    user_mgr.revoke_privileges(username, db, priv_list)
    click.echo(f"[OK] Revoked {privileges} on {db} from {username}.")

    if show_diff:
        click.echo(f"After:\n  {username}@% →")
        print_privs(user_mgr, username, db)

@users.command("rename")
@click.argument("old_username")
@click.argument("new_username")
@click.pass_obj
def rename(user_mgr: UserManager, old_username, new_username):
    require_root_or_self(user_mgr, old_username)
    user_mgr.change_username(old_username, new_username)
    click.echo(f"[OK] {old_username} renamed to {new_username}.")

@users.command("passwd")
@click.argument("username")
@click.password_option("--new-pass", prompt=True, confirmation_prompt=True)
@click.pass_obj
def passwd_cmd(user_mgr: UserManager, username, new_pass):
    require_root_or_self(user_mgr, username)
    user_mgr.change_password(username, new_pass)
    click.echo("[OK] Password updated.")

@root_only
@users.command("list")
@click.pass_obj
def list_users(user_mgr: UserManager):
    require_root(user_mgr)
    users = user_mgr.list_users()
    if not users:
        click.echo("No registered users found.")
    else:
        for u in users:
            click.echo(f"- {u}")

@root_only
@users.command("drop")
@click.argument("username")
@click.pass_obj
def drop(user_mgr: UserManager, username):
    require_root(user_mgr)
    if username.lower() == "root":
        click.echo("Cannot drop user 'root'. Operation aborted.")
        return
    user_mgr.drop_user(username)
    click.echo(f"[OK] Dropped user {username}.")

@root_only
@users.command("drop-all")
@click.pass_obj
def drop_all_users(user_mgr: UserManager):
    user_mgr.drop_all_users()

@users.command("whoami")
@click.pass_obj
def whoami(user_mgr: UserManager):
    info = user_mgr.whoami()
    click.echo(f"Connected as: {info}")

@root_only
@users.command("set-defaults")
@click.argument("username")
@click.option("--db", default=DEFAULT_DB, show_default=True)
@click.option("--show-diff", is_flag=True, help="Display privilege changes")
@click.pass_obj
def set_defaults(user_mgr: UserManager, username, db, show_diff):
    require_root(user_mgr)

    defaults = ["SELECT", "INSERT", "UPDATE", "DELETE"]

    if show_diff:
        click.echo(f"Before:\n  {username}@% →")
        print_privs(user_mgr, username, db)

    user_mgr.grant_privileges(username, db, defaults)

    if show_diff:
        click.echo(f"After:\n  {username}@% →")
        print_privs(user_mgr, username, db)

    click.echo(f"[OK] Granted default perms to {username} on {db}.")

# -------------------- DATABASE --------------------

def _print_ok(msg: str) -> None:
    click.echo(f"[OK] {msg}")

@root_only
@cli.command("create-db")
@click.option("--sql-dir", type=click.Path(exists=True, file_okay=False),
                default=str(DEFAULT_SQL_DIR), show_default=True)
@click.option("--database", default=DEFAULT_DB, show_default=True)
@click.pass_obj
def create_db(user_mgr: UserManager, sql_dir: str, database: str):
    require_root(user_mgr)
    order = ["install.sql", "indexing.sql", "procedures.sql", "triggers.sql", "views.sql"]
    for i, fname in enumerate(order):
        path = Path(sql_dir) / fname
        if i == 0:
            user_mgr.execute_sql_file(path)
        else:
            user_mgr.execute_sql_file(path, database=database)
        _print_ok(fname)
    _print_ok("Database schema deployed.")

@root_only
@cli.command("drop-db")
@click.option("--database", default=DEFAULT_DB, show_default=True)
@click.option("--yes", is_flag=True, help="Skip confirmation prompt")
@click.pass_obj
def drop_db(user_mgr: UserManager, database: str, yes: bool):
    require_root(user_mgr)
    if not yes:
        click.confirm(f"Drop entire schema `{database}`?", abort=True)
    user_mgr._execute_sql(f"DROP DATABASE IF EXISTS `{database}`;")
    click.echo(f"[OK] Schema `{database}` dropped.")

@root_only
@cli.command("load-db")
@click.option("--g", "use_faker_sql", is_flag=True, help="Run faker_sql.py then load.sql")
@click.option("--i", "use_faker_intelligent", is_flag=True, help="Run faker.py for full intelligent data")
@click.option("--sql-dir", type=click.Path(exists=True, file_okay=False),
                default=str(DEFAULT_SQL_DIR), show_default=True)
@click.option("--database", default=DEFAULT_DB, show_default=True)
@click.pass_context
def load_db(ctx, use_faker_sql: bool, use_faker_intelligent: bool,
            sql_dir: str, database: str):

    user_mgr = ctx.obj
    require_root(user_mgr)

    if use_faker_sql and use_faker_intelligent:
        raise click.ClickException("Cannot use both --g and --i at the same time.")

    if use_faker_sql:
        script_path = PROJECT_ROOT / "code" / "data_generation" / "faker_sql.py"
        subprocess.check_call([sys.executable, str(script_path)])
        _print_ok("faker_sql.py executed.")

        ctx.invoke(create_db, sql_dir=sql_dir, database=database)

        load_path = Path(sql_dir) / "load.sql"
        user_mgr.execute_sql_file(load_path, database=database, show_progress=True)
        _print_ok("load.sql executed after faker_sql.py.")

    elif use_faker_intelligent:
        script_path = PROJECT_ROOT / "code" / "data_generation" / "faker.py"
        subprocess.check_call([sys.executable, str(script_path)])
        _print_ok("faker.py executed and database populated with intelligent data.")

    else:
        ctx.invoke(create_db, sql_dir=sql_dir, database=database)

        load_path = Path(sql_dir) / "load.sql"
        user_mgr.execute_sql_file(load_path, database=database, show_progress=True)
        _print_ok("Database loaded from load.sql.")

@root_only
@cli.command("erase-db")
@click.option("--database", default=DEFAULT_DB, show_default=True)
@click.option("--yes", is_flag=True, help="Skip confirmation prompt")
@click.pass_obj
def erase(user_mgr: UserManager, database: str, yes: bool):
    require_root(user_mgr)
    if not yes:
        click.confirm(f"Are you sure you want to TRUNCATE all **non-lookup** tables in `{database}`?", abort=True)

    lookup_tables = {
        "Continent",
        "Staff_Role",
        "Experience_Level",
        "Performance_Type",
        "Ticket_Type",
        "Payment_Method",
        "Ticket_Status",
        "Genre",
        "SubGenre"
    }

    with user_mgr._connect(database) as cnx, cnx.cursor() as cur:
        cur.execute("SET FOREIGN_KEY_CHECKS = 0;")
        cur.execute("SHOW FULL TABLES WHERE Table_type = 'BASE TABLE';")
        tables = [row[0] for row in cur.fetchall() if row[0] not in lookup_tables]
        for tbl in tables:
            cur.execute(f"TRUNCATE TABLE `{tbl}`;")
        cur.execute("SET FOREIGN_KEY_CHECKS = 1;")
        cnx.commit()
        click.echo(f"[OK] Truncated {len(tables)} tables in `{database}` (excluding lookup tables).")

@cli.command("db-status")
@click.option("--database", default=DEFAULT_DB, show_default=True)
@click.pass_obj
def status(user_mgr: UserManager, database: str):
    with user_mgr._connect() as cnx, cnx.cursor(dictionary=True) as cur:
        cur.execute("""
            SELECT table_name AS name, table_rows AS 'rows'
            FROM information_schema.tables
            WHERE table_schema = %s
            AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """, (database,))
        rows = cur.fetchall()
        if not rows:
            click.echo(f"No base tables found in `{database}`.")
            return
        max_name = max(len(r["name"]) for r in rows)
        for r in rows:
            click.echo(f"{r['name']:<{max_name}} {r['rows']:>6} rows")

@root_only
@cli.command("reset-db")
@click.pass_context
def reset(ctx):
    require_root(ctx.obj)
    ctx.invoke(drop_db, yes=True)
    ctx.invoke(load_db)
    click.echo("[OK] Database reset complete.")

@cli.command("viewq")
@click.option("--database", default=DEFAULT_DB, show_default=True)
@click.pass_obj
def viewq(user_mgr: UserManager, database: str):

    with user_mgr._connect(database) as cnx, cnx.cursor() as cur:
        cur.execute("""
            SELECT match_id, match_type, ticket_id, offered_type_id, requested_type_id, buyer_id, seller_id, match_time
            FROM Resale_Match_Log
            ORDER BY match_time DESC
        """)
        rows = cur.fetchall()
        if not rows:
            click.echo("No resale matches found.")
            return

        headers = [desc[0] for desc in cur.description]
        col_widths = [max(len(h), max((len(str(r[i])) for r in rows), default=0)) for i, h in enumerate(headers)]

        def format_row(row):
            return " | ".join(str(cell).ljust(col_widths[i]) for i, cell in enumerate(row))

        click.echo(" | ".join(h.ljust(col_widths[i]) for i, h in enumerate(headers)))
        click.echo("-+-".join("-" * w for w in col_widths))
        for row in rows:
            click.echo(format_row(row))

# -------------------- QUERIES --------------------

@cli.command("q")
@click.argument("start", type=int)
@click.argument("end", required=False, type=int)
@click.option("--database", default=DEFAULT_DB, show_default=True)
@click.pass_obj
def run_query(user_mgr: UserManager, start: int, end: int | None, database: str):
    # 1. build exact list
    if end is None:
        query_ids = [start]
    else:
        if start > end:
            click.echo("Start must be ≤ end", err=True)
            return
        query_ids = list(range(start, end + 1))

    # 2. single loop – the only one
    for q in query_ids:
        sql_path = QUERIES_DIR / f"Q{q:02d}.sql"
        if not sql_path.exists():
            click.echo(f"[SKIP] Missing {sql_path.name}")
            continue

        if q in (4, 6):
            base   = QUERIES_DIR / f"Q{q:02d}_plan"
            count = user_mgr.run_multi_plan_query_to_files(sql_path, base, database=database)
            files = ", ".join(f"{base.name}{n}_out.txt" for n in range(1, count + 1))
            _print_ok(f"{sql_path.name} → {files}")
            continue

        else:
            out_path = QUERIES_DIR / f"Q{q:02d}_out.txt"
            user_mgr.run_query_to_file(sql_path, out_path,
                                       database=database)
            _print_ok(f"{sql_path.name} → {out_path.name}")

if __name__ == "__main__":
    cli()

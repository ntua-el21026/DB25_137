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
users whoami          Show current DB connection info
users set-defaults    Grant typical privileges (SELECT, INSERT, ...)

DATABASE SETUP
-------------------
create-db             Create schema and deploy all SQL scripts
load-db               Generate and load initial data (faker → load.sql)
reset                 Shortcut for create-db + load-db
erase                 Truncate all tables, preserving structure

TESTING
-----------
test                  Run test.py and all SQL test scripts in /test

QUERIES
-----------
qX                    Run sql/queries/QX.sql and save to QX_out.txt
qX-to-qY              Run range of queries and save results (e.g., q1-to-q4)

Usage Examples
--------------
$ export DB_ROOT_USER=root DB_ROOT_PASS=secret
$ db137 create-db
$ db137 load-db
$ db137 test
$ db137 q1
$ db137 q3-to-q5
"""
from __future__ import annotations

import os
import sys
import subprocess
import re
from pathlib import Path
from typing import List

import click
from click import argument, command

CURRENT_FILE = Path(__file__).resolve()
PROJECT_ROOT = CURRENT_FILE.parents[1]
if str(PROJECT_ROOT.parent) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT.parent))

from cli.users.manager import UserManager, parse_priv_list  # noqa

DEFAULT_DB = "pulse_university"
DEFAULT_SQL_DIR = PROJECT_ROOT.parent / "sql"
DEFAULT_TEST_DIR = PROJECT_ROOT.parent / "test"
FAKER_SCRIPT = PROJECT_ROOT.parent / "code" / "data_generation" / "faker.py"
QUERIES_DIR = DEFAULT_SQL_DIR / "queries"
TEST_PY = DEFAULT_TEST_DIR / "test.py"

# ================== CLI ROOT ===========================
@click.group(context_settings=dict(help_option_names=["-h", "--help"]))
@click.option("--host", default="localhost", show_default=True)
@click.option("--port", default=3306, show_default=True)
@click.option("--root-user", envvar="DB_ROOT_USER", required=True)
@click.option("--root-pass", envvar="DB_ROOT_PASS", required=True)
@click.pass_context
def cli(ctx, host, port, root_user, root_pass):
    ctx.obj = UserManager(
        dsn=dict(host=host, port=port, user=root_user, password=root_pass)
    )


# ================== USER COMMANDS ===========================
@cli.group()
def users():
    """Manage DB users."""
    pass

@users.command("register")
@click.argument("username")
@click.password_option("--password", prompt=True, confirmation_prompt=True)
@click.option("--default-db", default=DEFAULT_DB, show_default=True)
@click.option("--privileges", default="FULL", show_default=True)
@click.pass_obj
def register(user_mgr: UserManager, username, password, default_db, privileges):
    user_mgr.register_user(username, password)
    user_mgr.grant_privileges(username, default_db, parse_priv_list(privileges))
    click.echo(f"User '{username}' created and granted.")

@users.command("grant")
@click.argument("username")
@click.option("--db", required=True)
@click.option("--privileges", required=True)
@click.pass_obj
def grant(user_mgr: UserManager, username, db, privileges):
    user_mgr.grant_privileges(username, db, parse_priv_list(privileges))
    click.echo(f"Granted {privileges} on {db} to {username}.")

@users.command("revoke")
@click.argument("username")
@click.option("--db", required=True)
@click.option("--privileges", required=True)
@click.pass_obj
def revoke(user_mgr: UserManager, username, db, privileges):
    user_mgr.revoke_privileges(username, db, parse_priv_list(privileges))
    click.echo(f"Revoked {privileges} on {db} from {username}.")

@users.command("rename")
@click.argument("old_username")
@click.argument("new_username")
@click.pass_obj
def rename(user_mgr: UserManager, old_username, new_username):
    user_mgr.change_username(old_username, new_username)
    click.echo(f"{old_username} renamed to {new_username}.")

@users.command("passwd")
@click.argument("username")
@click.password_option("--new-pass", prompt=True, confirmation_prompt=True)
@click.pass_obj
def passwd_cmd(user_mgr: UserManager, username, new_pass):
    user_mgr.change_password(username, new_pass)
    click.echo("Password updated.")

@users.command("list")
@click.pass_obj
def list_users(user_mgr: UserManager):
    users = user_mgr.list_users()
    for u in users:
        click.echo(f"- {u}")

@users.command("drop")
@click.argument("username")
@click.pass_obj
def drop(user_mgr: UserManager, username):
    user_mgr.drop_user(username)
    click.echo(f"Dropped user {username}.")

@users.command("whoami")
@click.pass_obj
def whoami(user_mgr: UserManager):
    info = user_mgr.whoami()
    click.echo(f"Connected as: {info}")

@users.command("set-defaults")
@click.argument("username")
@click.option("--db", default=DEFAULT_DB, show_default=True)
@click.pass_obj
def set_defaults(user_mgr: UserManager, username, db):
    defaults = ["SELECT", "INSERT", "UPDATE", "DELETE"]
    user_mgr.grant_privileges(username, db, defaults)
    click.echo(f"Granted default perms to {username} on {db}")


# ================== DATABASE COMMANDS ===========================
def _print_ok(msg: str) -> None:
    click.echo(f"[OK] {msg}")

@cli.command("create-db")
@click.option("--sql-dir", type=click.Path(exists=True, file_okay=False),
              default=str(DEFAULT_SQL_DIR), show_default=True)
@click.option("--database", default=DEFAULT_DB, show_default=True)
@click.pass_obj
def create_db(user_mgr: UserManager, sql_dir: str, database: str):
    order: List[str] = [
        "install.sql", "indexing.sql", "procedures.sql", "triggers.sql", "views.sql"
    ]
    for fname in order:
        user_mgr.execute_sql_file(Path(sql_dir) / fname)
        _print_ok(fname)
    _print_ok("Database schema deployed")

@cli.command("load-db")
@click.option("--faker", "faker_script", type=click.Path(exists=True),
              default=str(FAKER_SCRIPT), show_default=True)
@click.option("--sql-dir", type=click.Path(exists=True, file_okay=False),
              default=str(DEFAULT_SQL_DIR), show_default=True)
@click.option("--database", default=DEFAULT_DB, show_default=True)
@click.pass_obj
def load_db(user_mgr: UserManager, faker_script: str, sql_dir: str, database: str):
    subprocess.check_call([sys.executable, faker_script])
    _print_ok("faker.py complete")
    user_mgr.execute_sql_file(Path(sql_dir) / "load.sql", database=database)
    _print_ok("load.sql executed")

@cli.command("erase")
@click.option("--database", default=DEFAULT_DB, show_default=True)
@click.pass_obj
def erase(user_mgr: UserManager, database: str):
    click.confirm(f"Are you sure you want to TRUNCATE all tables in `{database}`?",
                  abort=True)
    user_mgr.truncate_tables(database)
    _print_ok("All data erased")

@cli.command("test")
@click.option("--test-dir", type=click.Path(exists=True, file_okay=False),
              default=str(DEFAULT_TEST_DIR), show_default=True)
@click.option("--database", default=DEFAULT_DB, show_default=True)
@click.pass_obj
def test_cmd(user_mgr: UserManager, test_dir: str, database: str):
    py = Path(test_dir) / "test.py"
    if py.exists():
        subprocess.check_call([sys.executable, py])
        _print_ok("test.py complete")
    for sql_file in sorted(Path(test_dir).glob("*.sql")):
        user_mgr.execute_sql_file(sql_file, database=database)
        _print_ok(f"{sql_file.name}")

@cli.command("reset")
@click.pass_context
def reset(ctx):
    """Reset DB: create schema + load data"""
    ctx.invoke(create_db)
    ctx.invoke(load_db)


# ================== QUERY COMMANDS ===========================
@cli.command("qX")
@argument("qx", metavar="qX", type=str)
@click.option("--database", default=DEFAULT_DB, show_default=True)
@click.pass_obj
def qx_cmd(user_mgr: UserManager, qx: str, database: str):
    """Run QX.sql and save result to QX_out.txt"""
    qnum = re.sub(r"\D", "", qx).zfill(2)
    sql_path = QUERIES_DIR / f"Q{qnum}.sql"
    out_path = QUERIES_DIR / f"Q{qnum}_out.txt"
    if not sql_path.exists():
        raise click.ClickException(f"Missing: {sql_path}")
    user_mgr.run_query_to_file(sql_path, out_path, database=database)
    _print_ok(f"{sql_path.name} → {out_path.name}")

@cli.command("qX-to-qY")
@argument("qrange", metavar="qX-to-qY", type=str)
@click.option("--database", default=DEFAULT_DB, show_default=True)
@click.pass_obj
def qrange_cmd(user_mgr: UserManager, qrange: str, database: str):
    """Run QX.sql to QY.sql and save each output to QX_out.txt …"""
    match = re.match(r"q(\d+)-to-q(\d+)", qrange)
    if not match:
        raise click.ClickException("Expected format: q1-to-q4")

    start, end = sorted((int(match[1]), int(match[2])))
    for q in range(start, end + 1):
        qid = f"Q{q:02}"
        sql_path = QUERIES_DIR / f"{qid}.sql"
        out_path = QUERIES_DIR / f"{qid}_out.txt"
        if not sql_path.exists():
            click.echo(f"[SKIP] Missing {sql_path.name}")
            continue
        user_mgr.run_query_to_file(sql_path, out_path, database=database)
        _print_ok(f"{sql_path.name} → {out_path.name}")


if __name__ == "__main__":
    cli()

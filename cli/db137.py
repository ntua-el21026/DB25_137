#!/usr/bin/env python3
"""
db137 – Pulse-University DB helper
----------------------------------
Root Click group that will grow to host every CLI feature you need.
For the moment it exposes only the “users” sub-commands.

Usage examples
--------------
# create user with FULL rights on pulse_university
db137 users register alice --password secret

# grant DELETE later
db137 users grant alice --db pulse_university --privileges DELETE

# change password
db137 users passwd alice --new-pass NewSecret
"""
import os
import sys
import click

# --------------------------------------------------------------------------- #
# Bootstrap – make the project root importable when running from checkout
# --------------------------------------------------------------------------- #
PROJECT_ROOT = os.path.abspath(os.path.join(__file__, "../../"))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from cli.users.manager import UserManager, parse_priv_list

# --------------------------------------------------------------------------- #
# Top-level command group
# --------------------------------------------------------------------------- #
@click.group(context_settings=dict(help_option_names=["-h", "--help"]))
@click.option("--host", default="localhost", show_default=True,
                help="DB server host.")
@click.option("--port", default=3306, show_default=True,
                help="DB server port.")
@click.option("--root-user", envvar="DB_ROOT_USER", required=True,
                help="Administrative user with CREATE USER / GRANT rights.")
@click.option("--root-pass", envvar="DB_ROOT_PASS", required=True,
                help="Password for the administrative user.")
@click.pass_context
def cli(ctx, host, port, root_user, root_pass):
    """db137 – root command (nothing interesting here yet)."""
    ctx.obj = UserManager(
        dsn=dict(host=host, port=port, user=root_user, password=root_pass)
    )

# --------------------------------------------------------------------------- #
# users sub-group
# --------------------------------------------------------------------------- #
@cli.group()
def users():
    """Commands that manage database logins."""
    pass


@users.command("register")
@click.argument("username")
@click.password_option("--password", prompt=True,
                        confirmation_prompt=True)
@click.option("--default-db", default="pulse_university",
                show_default=True, help="Schema to grant on.")
@click.option("--privileges", default="FULL",
                show_default=True,
                help=("Comma-separated list of privileges "
                    "(e.g. SELECT,INSERT) or FULL for ALL PRIVILEGES."))
@click.pass_obj
def register(user_mgr: UserManager, username, password, default_db,
                privileges):
    """Create a DB user and grant privileges."""
    user_mgr.register_user(username, password)
    user_mgr.grant_privileges(username, default_db, parse_priv_list(privileges))
    click.echo(f"User '{username}' created and granted.")


@users.command("grant")
@click.argument("username")
@click.option("--db", required=True, help="Target schema.")
@click.option("--privileges", required=True,
                help="Comma-list or FULL.")
@click.pass_obj
def grant(user_mgr: UserManager, username, db, privileges):
    """Grant additional privileges."""
    user_mgr.grant_privileges(username, db, parse_priv_list(privileges))
    click.echo(f"Granted {privileges} on {db} to {username}.")


@users.command("revoke")
@click.argument("username")
@click.option("--db", required=True, help="Target schema.")
@click.option("--privileges", required=True,
                help="Comma-list (cannot be FULL).")
@click.pass_obj
def revoke(user_mgr: UserManager, username, db, privileges):
    """Revoke specific privileges."""
    user_mgr.revoke_privileges(username, db, parse_priv_list(privileges))
    click.echo(f"Revoked {privileges} on {db} from {username}.")


@users.command("rename")
@click.argument("old_username")
@click.argument("new_username")
@click.pass_obj
def rename(user_mgr: UserManager, old_username, new_username):
    """Rename a login."""
    user_mgr.change_username(old_username, new_username)
    click.echo(f"{old_username} renamed to {new_username}.")


@users.command("passwd")
@click.argument("username")
@click.password_option("--new-pass", prompt=True,
                        confirmation_prompt=True)
@click.pass_obj
def passwd_cmd(user_mgr: UserManager, username, new_pass):
    """Change a user's password."""
    user_mgr.change_password(username, new_pass)
    click.echo("Password updated.")


if __name__ == "__main__":
    cli()

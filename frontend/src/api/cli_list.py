from flask import Blueprint, jsonify, request
from cli.db137 import cli
from users.manager import UserManager
import click
import os

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", 3306))

cli_bp = Blueprint("cli", __name__, url_prefix="/api/cli")

@cli_bp.route("/list", methods=["GET"])
def list_cli_commands():
    """
    Return only commands the caller can run.
    Commands (or groups) tagged with `.root_only = True`
    are hidden when the caller is not root.
    """
    try:
        # -- Who is calling?         ----------------------------------------
        token = request.headers.get("Authorization", "")
        if ":" not in token:
            return jsonify({"commands": [], "error": "Missing auth token"}), 401

        username, password = token.split(":", 1)
        user_mgr = UserManager(
            root_user=username,
            root_pass=password,
            host=DB_HOST,
            port=DB_PORT,
        )
        is_root = user_mgr.is_root()

        # -- Walk the Click command tree  -----------------------------------
        def extract(group: click.MultiCommand, prefix: str = ""):
            out = []
            for name, cmd in group.commands.items():
                if getattr(cmd, "root_only", False) and not is_root:
                    continue                                  # hide admin cmd

                full = f"{prefix} {name}".strip()
                if isinstance(cmd, click.Group):
                    out += extract(cmd, full)
                else:
                    desc = (cmd.help or cmd.short_help or "").strip()
                    out.append({"name": full, "description": desc})
            return out

        commands = sorted(extract(cli), key=lambda x: x["name"])
        return jsonify({"commands": commands})

    except Exception as e:
        return jsonify({"commands": [], "error": str(e)}), 500

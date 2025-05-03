from flask import Blueprint, jsonify
from cli.db137 import cli
import click

cli_bp = Blueprint("cli", __name__, url_prefix="/api/cli")

@cli_bp.route("/list", methods=["GET"])
def list_cli_commands():
	try:
		def extract_commands(group, parent=""):
			commands = []
			for name, cmd in group.commands.items():
				full_name = f"{parent} {name}".strip()
				if isinstance(cmd, click.Group):
					commands += extract_commands(cmd, full_name)
				else:
					description = (cmd.help or cmd.short_help or "").strip()
					commands.append({
						"name": full_name,
						"description": description
					})
			return commands

		result = extract_commands(cli)
		return jsonify({"commands": result})
	except Exception as e:
		return jsonify({"commands": [], "error": str(e)})

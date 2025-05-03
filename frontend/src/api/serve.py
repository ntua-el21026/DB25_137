from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import mysql.connector
import os
import sys
from pathlib import Path
import subprocess
from click.testing import CliRunner  # ✅ fixed here
import click

# CLI path for db137 import
cli_path = Path(__file__).resolve().parents[3] / "cli"
sys.path.append(str(cli_path))

from users.manager import UserManager
from table_defs import get_create_statement
from sql_parser import get_definition
from cli.db137 import cli

app = Flask(__name__)
CORS(app)

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DEFAULT_DB = "pulse_university"

@app.route("/api/login", methods=["POST"])
def login():
	data = request.get_json()
	username = data.get("username")
	password = data.get("password")

	try:
		um = UserManager(
			root_user=username,
			root_pass=password,
			host=DB_HOST,
			port=DB_PORT
		)
		um.whoami()
		return jsonify({"token": f"{username}:{password}"})
	except mysql.connector.Error:
		return jsonify({"error": "Invalid credentials"}), 401

@app.route("/api/schema", methods=["POST"])
def schema():
	token = request.headers.get("Authorization")
	username, password = token.split(":", 1)

	um = UserManager(root_user=username, root_pass=password)
	with um._connect() as conn, conn.cursor() as cur:
		cur.execute(f"USE {DEFAULT_DB}")
		cur.execute("SHOW FULL TABLES WHERE Table_type = 'BASE TABLE'")
		tables = [row[0] for row in cur.fetchall()]

		cur.execute("SHOW FULL TABLES WHERE Table_type = 'VIEW'")
		views = [row[0] for row in cur.fetchall()]

		cur.execute("SHOW TRIGGERS")
		triggers = [row[0] for row in cur.fetchall()]

		cur.execute("SHOW PROCEDURE STATUS WHERE Db = %s", (DEFAULT_DB,))
		procedures = [row[1] for row in cur.fetchall()]

	return jsonify({
		"tables": tables,
		"views": views,
		"triggers": triggers,
		"procedures": procedures
	})

@app.route("/api/browse/<table>", methods=["POST"])
def browse(table):
	token = request.headers.get("Authorization")
	username, password = token.split(":", 1)

	um = UserManager(root_user=username, root_pass=password)
	with um._connect() as conn, conn.cursor(dictionary=True) as cur:
		try:
			cur.execute(f"USE {DEFAULT_DB}")
			cur.execute(f"SELECT * FROM `{table}` LIMIT 100")
			rows = cur.fetchall()
			return jsonify(rows)
		except Exception as e:
			return jsonify({"error": str(e)}), 400

@app.route("/api/query", methods=["POST"])
def run_query():
	token = request.headers.get("Authorization")
	username, password = token.split(":", 1)
	sql = request.get_json().get("sql", "").strip()

	if not sql:
		return jsonify({"error": "Query is empty"}), 400

	um = UserManager(root_user=username, root_pass=password)
	with um._connect() as conn:
		is_select = sql.lower().startswith("select")
		cursor_class = conn.cursor(dictionary=True) if is_select else conn.cursor()

		with cursor_class as cur:
			try:
				cur.execute(f"USE {DEFAULT_DB}")
				cur.execute(sql)
				if is_select:
					rows = cur.fetchall()
					return jsonify(rows)
				else:
					conn.commit()
					return jsonify({"status": "OK"})
			except Exception as e:
				return jsonify({"error": str(e)}), 400

@app.route("/api/definition/<table>", methods=["GET"])
def definition(table):
	stmt = get_create_statement(table)
	if not stmt:
		return Response("Table not found in install.sql", status=404)
	return Response(stmt, mimetype="text/plain")

@app.route("/api/view_definition/<name>", methods=["GET"])
def view_definition(name):
	text = get_definition("view", name)
	if text:
		return Response(text, mimetype="text/plain")
	return Response(f"VIEW '{name}' not found.", status=404)

@app.route("/api/procedure_definition/<name>", methods=["GET"])
def procedure_definition(name):
	text = get_definition("procedure", name)
	if text:
		return Response(text, mimetype="text/plain")
	return Response(f"PROCEDURE '{name}' not found.", status=404)

@app.route("/api/trigger_definition/<name>", methods=["GET"])
def trigger_definition(name):
	text = get_definition("trigger", name)
	if text:
		return Response(text, mimetype="text/plain")
	return Response(f"TRIGGER '{name}' not found.", status=404)

@app.route("/api/cli/list", methods=["GET"])
def list_cli_commands():
	try:
		def extract_commands(group, parent=""):
			results = []
			for name, cmd in group.commands.items():
				full = f"{parent} {name}".strip()
				if isinstance(cmd, click.Group):
					results += extract_commands(cmd, full)
				else:
					description = (cmd.help or cmd.short_help or "").strip()
					results.append({
						"name": full,
						"description": description
					})
			return results

		result = extract_commands(cli)
		return jsonify({"commands": result})
	except Exception as e:
		return jsonify({"commands": [], "error": str(e)})

@app.route("/api/cli/run", methods=["POST"])
def run_cli_command():
	try:
		data = request.get_json()
		raw = data.get("command", "").strip()

		cmd_parts = raw.split()
		if cmd_parts and cmd_parts[0] == "db137":
			cmd_parts = cmd_parts[1:]

		runner = CliRunner()
		result = runner.invoke(cli, cmd_parts)

		return Response(result.output, status=200 if result.exit_code == 0 else 400)
	except Exception as e:
		return Response(str(e), status=500)

if __name__ == "__main__":
	app.run(port=8000, debug=True)

import os
import subprocess

# Script is running from: code/sql_help/
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, "..", ".."))

# Output file: docs/organization/project_structure.txt
docs_folder = os.path.join(project_root, "docs", "organization")
output_file = os.path.join(docs_folder, "project_structure.txt")
os.makedirs(docs_folder, exist_ok=True)

# Run 'tree' command from project root
try:
    result = subprocess.run(
        ["tree", "-a", "-L", "3", "-I", ".git|__pycache__|venv|.mypy_cache|.idea|.vscode"],
        cwd=project_root,
        capture_output=True,
        text=True,
        check=True
    )

    # Save the structure
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(result.stdout)

    print(f"Project structure saved to: {output_file}")

except subprocess.CalledProcessError as e:
    print("Error running tree:", e)
except FileNotFoundError:
    print("'tree' command is not available on this system. Try: sudo apt install tree")

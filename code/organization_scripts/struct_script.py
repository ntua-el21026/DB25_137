import os
import subprocess

# IMPORTANT
# RUN ONLY WHERE 'tree' COMMAND IS AVAILABLE

# Go two levels up to reach project root
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, "..", ".."))

# Target the docs folder inside project root
docs_folder = os.path.join(project_root, "docs")
output_file = os.path.join(docs_folder, "project_structure.txt")

# Ensure docs folder exists
os.makedirs(docs_folder, exist_ok=True)

# Run the 'tree' command
try:
    result = subprocess.run(
        ["tree", "-a", "-L", "3", "-I", ".git|__pycache__|venv|.mypy_cache|.idea|.vscode"],
        cwd=project_root,
        capture_output=True,
        text=True,
        check=True
    )

    # Save output
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(result.stdout)

    print(f"Project structure saved to {output_file}")

except subprocess.CalledProcessError as e:
    print("Error running tree:", e)
except FileNotFoundError:
    print("The 'tree' command is not available on this system.")

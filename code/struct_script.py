import os
import subprocess

# IMPORTANT
# RUN ONLY WHERE 'TREE' COMMAND IS AVAILABLE


# Paths
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, ".."))
docs_folder = os.path.join(project_root, "docs")
output_file = os.path.join(docs_folder, "project_structure.txt")

# Make sure docs folder exists
os.makedirs(docs_folder, exist_ok=True)

# Run the 'tree' command with:
# -L 3: show 3 levels deep (adjust if needed)
# -a: include hidden files/folders
# -I: exclude pattern (e.g. '.git|__pycache__|venv|.mypy_cache')
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

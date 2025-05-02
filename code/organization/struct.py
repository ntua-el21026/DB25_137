#!/usr/bin/env python3
import os
import subprocess

def print_expected_output_mappings():
    """
    This prints expected output paths in the format:
    script.py → path1.ext, path2.ext, ...
    Used by intcheck.py to verify file responsibility.
    """
    mappings = {
        'faker.py': ['sql/load.sql', 'docs/organization/datalist.txt'],
        'qgen.py': ['sql/queries/Q*.sql'],
        'dropgen.py': ['sql/install.sql'],
        'fixeof.py': [],
        'runall.py': [],
    }

    for script, paths in mappings.items():
        if paths:
            print(f"{script} → {', '.join(paths)}")
        else:
            print(f"{script} →")

def main():
    # This script runs from: code/organization/
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(script_dir, "..", ".."))

    # Output file location: docs/organization/project_structure.txt
    docs_folder = os.path.join(project_root, "docs", "organization")
    output_file = os.path.join(docs_folder, "project_structure.txt")
    os.makedirs(docs_folder, exist_ok=True)

    # Run the 'tree' command from the root of the project
    try:
        result = subprocess.run(
            ["tree", "-a", "-L", "3", "-I", ".git|__pycache__|venv|.mypy_cache|.idea|.vscode"],
            cwd=project_root,
            capture_output=True,
            text=True,
            check=True
        )

        # Save the tree structure
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(result.stdout)

        print(f"📁 Project structure saved to: {output_file}")
    
    except subprocess.CalledProcessError as e:
        print("Error running tree:", e)
    except FileNotFoundError:
        print("'tree' command is not available. Install it with: sudo apt install tree")

    # Print mappings for intcheck.py
    print_expected_output_mappings()

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
import os
import subprocess
from pathlib import Path

def print_expected_output_mappings():
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

def extract_gitignore_patterns(gitignore_path):
    patterns = set()
    if not gitignore_path.exists():
        return patterns

    for line in gitignore_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        # Remove leading slashes (./ or /path) or wildcards
        line = line.lstrip("./")
        line = line.lstrip("/")

        # Handle directory and subdir ignores
        if line.endswith("/"):
            line = line.rstrip("/")

        # Handle nested patterns like **/ or subdir/file
        basename = os.path.basename(line)
        if basename:
            patterns.add(basename)

    return patterns

def main():
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parents[1]
    gitignore_path = project_root / ".gitignore"

    # Output file location
    docs_folder = project_root / "docs" / "organization"
    output_file = docs_folder / "project_structure.txt"
    docs_folder.mkdir(parents=True, exist_ok=True)

    # Dynamically extract ignore patterns
    dynamic_ignores = extract_gitignore_patterns(gitignore_path)
    dynamic_ignores.update({".git", ".gitignore"})  # always ignore VCS and config

    # Convert to |-separated list
    ignore_arg = "|".join(sorted(dynamic_ignores))

    try:
        result = subprocess.run(
            ["tree", "-a", "-L", "3", "-I", ignore_arg],
            cwd=project_root,
            capture_output=True,
            text=True,
            check=True
        )
        with output_file.open("w", encoding="utf-8") as f:
            f.write(result.stdout)
        print(f"📁 Project structure saved to: {output_file}")

    except subprocess.CalledProcessError as e:
        print("Error running tree:", e)
    except FileNotFoundError:
        print("'tree' command is not available. Install it with: sudo apt install tree")

    print_expected_output_mappings()

if __name__ == "__main__":
    main()

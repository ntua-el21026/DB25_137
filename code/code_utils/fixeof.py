import os
from pathlib import Path
import sys

try:
    from pathspec import PathSpec
    from pathspec.patterns import GitWildMatchPattern
except ImportError:
    print("You need to install the pathspec module: pip install pathspec")
    sys.exit(1)

# File extensions to check for code-like files
CODE_EXTENSIONS = {'.py', '.sql', '.txt', '.md', '.sh', '.html', '.jsx', '.js', '.json'}

def load_gitignore(path):
    """Parse .gitignore file and return a PathSpec object."""
    ignore_file = path / '.gitignore'
    if not ignore_file.exists():
        return None
    with open(ignore_file) as f:
        patterns = f.read().splitlines()
    return PathSpec.from_lines(GitWildMatchPattern, patterns)

def ensure_trailing_newline(file_path):
    try:
        with open(file_path, 'rb+') as f:
            f.seek(-1, os.SEEK_END)
            last_char = f.read(1)
            if last_char != b'\n':
                f.write(b'\n')
                print(f"Added final newline to: {file_path}")
    except OSError:
        print(f"Skipping binary or unreadable file: {file_path}")
    except Exception as e:
        print(f"Error processing {file_path}: {e}")

def main():
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent.parent

    print(f"Scanning project from: {project_root}\n")

    spec = load_gitignore(project_root)

    for root, _, files in os.walk(project_root):
        for file in files:
            file_path = Path(root) / file
            rel_path = file_path.relative_to(project_root)
            if spec and spec.match_file(str(rel_path)):
                continue  # Skip ignored files
            if file_path.suffix.lower() in CODE_EXTENSIONS:
                ensure_trailing_newline(file_path)

    print("\nDone checking all code files.")

if __name__ == "__main__":
    main()

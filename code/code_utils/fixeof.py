import os

# File extensions to check for code-like files
CODE_EXTENSIONS = {'.py', '.sql', '.txt', '.md', '.sh', '.html', '.jsx', '.js', '.json'}

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
    # Start from the project root
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(script_dir, "..", ".."))

    print(f"Scanning project from: {project_root}\n")

    for root, _, files in os.walk(project_root):
        for file in files:
            _, ext = os.path.splitext(file)
            if ext.lower() in CODE_EXTENSIONS:
                path = os.path.join(root, file)
                ensure_trailing_newline(path)

    print("\nDone checking all code files.")

if __name__ == "__main__":
    main()

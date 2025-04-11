import os
import subprocess

def run_scripts_in_folder(folder_path):
    print(f"\n📂 Running scripts in: {folder_path}")
    for filename in sorted(os.listdir(folder_path)):
        if filename.endswith(".py"):
            script_path = os.path.join(folder_path, filename)
            print(f"▶️ Running {filename}...")
            result = subprocess.run(["python3", script_path])
            if result.returncode != 0:
                print(f"❌ Script {filename} failed.\n")
            else:
                print(f"✅ Script {filename} completed.\n")

def main():
    # Get the absolute path to the code folder
    code_dir = os.path.abspath(os.path.dirname(__file__))

    # Paths to the folders you want to scan
    sql_help_path = os.path.join(code_dir, "sql_help")
    org_path = os.path.join(code_dir, "organization")

    # Run all scripts in those folders
    for path in [sql_help_path, org_path]:
        if os.path.isdir(path):
            run_scripts_in_folder(path)
        else:
            print(f"⚠️ Folder does not exist: {path}")

if __name__ == "__main__":
    main()

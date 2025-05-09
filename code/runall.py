import os
import subprocess

def run_scripts_in_folder(folder_path):
    print(f"\nRunning scripts in: {folder_path}")
    for filename in sorted(os.listdir(folder_path)):
        if filename.endswith(".py"):
            script_path = os.path.join(folder_path, filename)
            print(f"Running {filename}...")
            result = subprocess.run(["python3", script_path])
            if result.returncode != 0:
                print(f"Script {filename} failed.\n")
            else:
                print(f"Script {filename} completed.\n")

def main():
    code_dir = os.path.abspath(os.path.dirname(__file__))

    # Explicit run order by folder
    custom_order = ["code_utils"]
    org_folder = os.path.join(code_dir, "organization")

    for folder_name in custom_order:
        folder_path = os.path.join(code_dir, folder_name)
        if os.path.isdir(folder_path):
            run_scripts_in_folder(folder_path)

    # Organization scripts last
    if os.path.isdir(org_folder):
        run_scripts_in_folder(org_folder)

if __name__ == "__main__":
    main()

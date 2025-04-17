import os
import re

def extract_table_names(sql_text):
    pattern = re.compile(r"CREATE\s+TABLE\s+(IF\s+NOT\s+EXISTS\s+)?[`\"]?(\w+)[`\"]?", re.IGNORECASE)
    return [match.group(2) for match in pattern.finditer(sql_text)]

def main():
    # Paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(script_dir, "..", ".."))
    install_path = os.path.join(project_root, "sql", "install.sql")

    # Load file
    with open(install_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
        full_text = "".join(lines)

    # Find 'USE pulse_university;'
    try:
        use_index = next(i for i, line in enumerate(lines) if "USE pulse_university;" in line)
    except StopIteration:
        print("❌ Could not find 'USE pulse_university;' in install.sql.")
        return

    # Remove all blank lines after USE
    while use_index + 1 < len(lines) and lines[use_index + 1].strip() == "":
        del lines[use_index + 1]

    # Find existing drop block (if any)
    drop_start = None
    for i in range(use_index + 1, len(lines)):
        if lines[i].strip().startswith("-- Drop all tables"):
            drop_start = i
            break

    if drop_start is not None:
        drop_end = drop_start
        for j in range(drop_start + 1, len(lines)):
            if not lines[j].strip().startswith("DROP TABLE IF EXISTS"):
                break
            drop_end = j
        # Remove drop block and blank lines after it
        del lines[drop_start:drop_end + 1]
        # Clean up extra blank lines after the drop block
        while drop_start < len(lines) and lines[drop_start].strip() == "":
            del lines[drop_start]

    # Extract all table names from CREATE TABLE
    table_names = extract_table_names(full_text)

    # Construct drop block with 1 blank line before and 1 after
    drop_block = [
        "\n",
        "-- Drop all tables\n",
        *[f"DROP TABLE IF EXISTS {t};\n" for t in table_names],
        "\n"  # Exactly one blank line after the last DROP
    ]

    # Insert block after 'USE pulse_university;'
    insert_index = use_index + 1
    lines = lines[:insert_index] + drop_block + lines[insert_index:]

    # Trim trailing blank lines at end of file
    while lines and lines[-1].strip() == "":
        lines.pop()

    # Write updated file
    with open(install_path, "w", encoding="utf-8") as f:
        f.writelines(lines)

    print(f"✅ Drop block with {len(table_names)} tables inserted cleanly after 'USE pulse_university;', with 1 blank line before and after.")

if __name__ == "__main__":
    main()

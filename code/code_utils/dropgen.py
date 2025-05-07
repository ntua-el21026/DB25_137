import os
import re

def extract_table_names(sql_text):
    pattern = re.compile(r"CREATE\s+TABLE\s+(IF\s+NOT\s+EXISTS\s+)?[`\"]?(\w+)[`\"]?", re.IGNORECASE)
    return [match.group(2) for match in pattern.finditer(sql_text)]

def extract_view_names(sql_text):
    pattern = re.compile(r"CREATE\s+VIEW\s+[`\"]?(\w+)[`\"]?", re.IGNORECASE)
    return [match.group(1) for match in pattern.finditer(sql_text)]

def extract_procedure_names(sql_text):
    pattern = re.compile(r"CREATE\s+PROCEDURE\s+[`\"]?(\w+)[`\"]?", re.IGNORECASE)
    return [match.group(1) for match in pattern.finditer(sql_text)]

def extract_trigger_names(sql_text):
    pattern = re.compile(r"CREATE\s+TRIGGER\s+[`\"]?(\w+)[`\"]?", re.IGNORECASE)
    return [match.group(1) for match in pattern.finditer(sql_text)]

def replace_drop_block(lines, anchor_keyword, drop_prefix, object_names, comment_line):
    try:
        anchor_index = next(i for i, line in enumerate(lines) if anchor_keyword in line)
    except StopIteration:
        print(f"Could not find anchor line '{anchor_keyword}'.")
        return lines

    # Remove blank lines after anchor
    while anchor_index + 1 < len(lines) and lines[anchor_index + 1].strip() == "":
        del lines[anchor_index + 1]

    # Remove existing drop block
    drop_start = None
    for i in range(anchor_index + 1, len(lines)):
        if lines[i].strip().startswith(comment_line.strip()):
            drop_start = i
            break

    if drop_start is not None:
        drop_end = drop_start
        for j in range(drop_start + 1, len(lines)):
            if not lines[j].strip().startswith(drop_prefix):
                break
            drop_end = j
        del lines[drop_start:drop_end + 1]
        while drop_start < len(lines) and lines[drop_start].strip() == "":
            del lines[drop_start]

    # Build new block
    drop_block = [
        "\n",
        f"{comment_line}\n",
        *[f"{drop_prefix} {name};\n" for name in object_names],
        "\n"
    ]

    insert_index = anchor_index + 1
    return lines[:insert_index] + drop_block + lines[insert_index:]

def update_sql_file(file_path, extract_names_fn, drop_prefix, comment_line):
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
        full_text = "".join(lines)

    object_names = extract_names_fn(full_text)

    new_lines = replace_drop_block(
        lines=lines,
        anchor_keyword="USE pulse_university;",
        drop_prefix=drop_prefix,
        object_names=object_names,
        comment_line=comment_line
    )

    while new_lines and new_lines[-1].strip() == "":
        new_lines.pop()

    with open(file_path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

    print(f"Updated drop block in {os.path.basename(file_path)} with {len(object_names)} objects.")

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(script_dir, "..", ".."))
    sql_dir = os.path.join(project_root, "sql")

    update_sql_file(
        file_path=os.path.join(sql_dir, "install.sql"),
        extract_names_fn=extract_table_names,
        drop_prefix="DROP TABLE IF EXISTS",
        comment_line="-- Drop all tables"
    )

    update_sql_file(
        file_path=os.path.join(sql_dir, "views.sql"),
        extract_names_fn=extract_view_names,
        drop_prefix="DROP VIEW IF EXISTS",
        comment_line="/* ============  drop old versions if they exist  ============ */"
    )

    update_sql_file(
        file_path=os.path.join(sql_dir, "procedures.sql"),
        extract_names_fn=extract_procedure_names,
        drop_prefix="DROP PROCEDURE IF EXISTS",
        comment_line="-- Drop all procedures"
    )

    update_sql_file(
        file_path=os.path.join(sql_dir, "triggers.sql"),
        extract_names_fn=extract_trigger_names,
        drop_prefix="DROP TRIGGER IF EXISTS",
        comment_line="-- Drop all triggers"
    )

if __name__ == "__main__":
    main()

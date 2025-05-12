import os

def has_content(path):
    return os.path.exists(path) and os.path.getsize(path) > 0

def write_if_missing_or_empty(path, content):
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return True
    return False

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    queries_folder = os.path.abspath(os.path.join(script_dir, "..", "..", "SQL", "queries"))
    os.makedirs(queries_folder, exist_ok=True)

    for i in range(1, 16):
        q_number = f"Q{i:02d}"  # Q01, Q02, ..., Q15

        sql_file_path = os.path.join(queries_folder, f"{q_number}.sql")
        wrote_sql = write_if_missing_or_empty(sql_file_path, f"-- SQL query for {q_number}\n")

        wrote_txt = False
        if i not in (4, 6):
            txt_file_path = os.path.join(queries_folder, f"{q_number}_out.txt")
            wrote_txt = write_if_missing_or_empty(txt_file_path, f"-- Output of query {q_number}\n")

        if wrote_sql or wrote_txt:
            print(f"Created or updated {q_number}.sql" +
                  ("" if i in (4, 6) else f" and/or {q_number}_out.txt"))
        else:
            print(f"Skipping {q_number} (file(s) exist and have content)")

    print(f"\nDone checking and generating files in: {queries_folder}")

if __name__ == "__main__":
    main()

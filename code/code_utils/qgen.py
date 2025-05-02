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
    # Script is running from inside a subfolder of 'code'
    # Go two levels up to project root, then into 'SQL/queries'
    script_dir = os.path.dirname(os.path.abspath(__file__))
    queries_folder = os.path.abspath(os.path.join(script_dir, "..", "..", "SQL", "queries"))

    # Ensure the 'SQL/queries' folder exists
    os.makedirs(queries_folder, exist_ok=True)

    # Generate files Q1.sql to Q15.sql and Q1_out.txt to Q15_out.txt
    for i in range(1, 16):
        q_number = f"Q{i}"

        sql_file_path = os.path.join(queries_folder, f"{q_number}.sql")
        txt_file_path = os.path.join(queries_folder, f"{q_number}_out.txt")

        # Write placeholder content only if the file doesn't exist or is empty
        wrote_sql = write_if_missing_or_empty(sql_file_path, f"-- SQL query for {q_number}\n")
        wrote_txt = write_if_missing_or_empty(txt_file_path, f"-- Output of query {q_number}\n")

        if wrote_sql or wrote_txt:
            print(f"Created or updated {q_number}.sql and/or {q_number}_out.txt")
        else:
            print(f"Skipping {q_number} (file(s) exist and have content)")

    print(f"\nDone checking and generating files in: {queries_folder}")

if __name__ == "__main__":
    main()

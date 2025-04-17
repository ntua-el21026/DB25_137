import os

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

        # Skip if either file already exists
        if os.path.exists(sql_file_path) or os.path.exists(txt_file_path):
            print(f"⏭ Skipping {q_number} (file(s) already exist)")
            continue

        # Write placeholder SQL query
        with open(sql_file_path, "w", encoding="utf-8") as sql_file:
            sql_file.write(f"-- SQL query for {q_number}\n")

        # Write placeholder output
        with open(txt_file_path, "w", encoding="utf-8") as txt_file:
            txt_file.write(f"-- Output of query {q_number}\n")

        print(f"✅ Created {q_number}.sql and {q_number}_out.txt")

    print(f"\nDone checking and generating files in: {queries_folder}")

if __name__ == "__main__":
    main()

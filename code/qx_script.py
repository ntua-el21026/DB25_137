import os

# Script is running from inside the 'code' folder
# We go one level up and into 'SQL'
sql_output_folder = os.path.abspath(os.path.join("..", "SQL"))

# Generate files Q1.sql to Q15.sql and Q1_out.txt to Q15_out.txt
for i in range(1, 16):
    q_number = f"Q{i}"

    sql_file_path = os.path.join(sql_output_folder, f"{q_number}.sql")
    txt_file_path = os.path.join(sql_output_folder, f"{q_number}_out.txt")

    # Write placeholder SQL query
    with open(sql_file_path, "w", encoding="utf-8") as sql_file:
        sql_file.write(f"-- SQL query for {q_number}\n")

    # Write placeholder output
    with open(txt_file_path, "w", encoding="utf-8") as txt_file:
        txt_file.write(f"-- Output of query {q_number}\n")

print("All files generated successfully in the 'SQL' folder.")

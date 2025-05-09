# Code – Pulse University Festival DB

This folder contains utility scripts used to generate and maintain the SQL files, project structure, and data.

## Subfolders and Files

1. **`data_generation/`**

   - **`faker.py`**  
     Generates complete, trigger-compliant synthetic data for the Pulse University Festival database. This includes realistic creation of:

     - **Events, performances, artists, bands, attendees, tickets, and reviews**
     - **Stages, festivals, locations, equipment, and staffing**

     The script ensures:

     - Full enforcement of **foreign key constraints**, **unique keys**, **NOT NULLs**, **CHECKs**, etc.
     - Compliance with all **business logic enforced via triggers**, such as:
       - Time and capacity constraints
       - Performance overlap and artist/band scheduling limits
       - Subgenre-genre consistency
       - 3-year consecutive performance caps
     - Data tailored to support **graded query coverage**, including:
       - Special cases for Q2, Q4, Q6, Q11, and Q14
       - Artist/band performance patterns across years and genres

     The script auto-runs `create-db`, inserts all data using safe transactional logic, and **logs row counts** to `docs/organization/db_data.txt`.

2. **`code_utils/`**

   - `dropgen.py`: Automatically inserts a full DROP block into `install.sql`, `views.sql`, `procedures.sql` and `triggers.sql` by detecting all create statemets and removes the old block.
   - `fixeof.py`: Ensures every source file ends with a single newline (prevents merge/diff issues).
   - `qgen.py`: Creates placeholder files Q1.sql–Q15.sql and Q1_out.txt–Q15_out.txt **only if they do not exist or are empty**.

3. **`organization/`**

   - `struct.py`: Outputs the full project tree and mapping of scripts to generated output files.

4. `runall.py`: Runs all scripts in `data_generation/`, `code_utils/`, and `organization/` in a safe order.

## Notes

- `qgen.py` skips files that already exist **and contain content** to protect work.
- `runall.py` is the master entry point for reproducibly rebuilding generated files.

---


# Code – Pulse University Festival DB

This folder contains utility scripts used to generate and maintain the SQL files, project structure, and data.

## Subfolders

- **`data_generation/`**
  - `faker.py`: Generates realistic synthetic data for the Pulse University Festival database. This includes events, performances, artists, bands, attendees, tickets, etc., while fully complying with:
    - Schema constraints (foreign keys, NOT NULLs, uniqueness)
    - Triggers (e.g. scheduling rules, band/artist restrictions)
    - Capacity limits (e.g. max tickets per stage)
    - Genre/sub-genre consistency checks
    - Business rules (e.g. staffing ratios, 3-year artist cap)
    Output is written to `sql/load.sql`.

- **`code_utils/`**
  - `dropgen.py`: Automatically inserts a full DROP block into `install.sql` by detecting all created tables.
  - `fixeof.py`: Ensures every source file ends with a single newline (prevents merge/diff issues).
  - `qgen.py`: Creates placeholder files Q1.sql–Q15.sql and Q1_out.txt–Q15_out.txt **only if they do not exist or are empty**.
  - `runall.py`: Runs all scripts in `data_generation/`, `code_utils/`, and `organization/` in a safe order.

- **`organization/`**
  - `struct.py`: Outputs the full project tree and mapping of scripts to generated output files.

## Notes

- `qgen.py` skips files that already exist **and contain content** to protect work.
- `runall.py` is the master entry point for reproducibly rebuilding generated files.

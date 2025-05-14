# Docs – Pulse University Festival DB

This folder contains supporting documentation for the semester project.

## Contents

- **`report.pdf`**: The main assignment report, which includes:
  - Overview of the implementation
  - Analysis of the `cli/` and `frontend/` codebase, including structure, roles, and access control
  - Query Plans for Q04 and Q06 (with index hints and trace analysis)
  - Join strategy discussion (e.g., Nested Loop, Hash Join, Merge Join)
  - Justification of indexing and schema choices
  - Screenshots and diagrams as needed

- **`main.tex`**: The LaTeX source code for the final report (`report.pdf`). Includes modular sections for each subsystem (schema, faker, CLI, frontend) and figures.

- **`assignment.pdf`**: The official project description and grading criteria for the Pulse University Festival database assignment.

- **`ddl.pdf`**: Full database schema including all core SQL definitions:
  - **Schema DDL**: Complete `install.sql` schema — all entities, attributes, constraints, and relationships.
  - **Indexing**: Definitions from `indexing.sql` including all performance-optimized indexes (e.g., for Q01–Q15).
  - **Triggers**: All business-rule enforcement logic from `triggers.sql`, including BEFORE/AFTER insert/update triggers (e.g., staffing ratios, resale logic, stage scheduling).
  - **Procedures**: Stored procedures from `procedures.sql` (e.g., for ticket updates, staff coverage, event maintenance).
  - **Views**: Predefined views from `views.sql` used to support complex queries.

- **`organization/`**: Reference materials and design notes:
  - `cardinality_constraints.txt`: Participation and cardinality assumptions
  - `project_structure.txt`: Filesystem layout and deliverable organization
  - `db_data.txt`: Summary of generated data from `faker.py`

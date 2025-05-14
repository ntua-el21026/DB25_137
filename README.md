# DB25_137 – Pulse University Database Project

This repository contains the complete implementation of the Pulse University Festival information system, developed as part of the **Databases course (Spring 2025, Team 137)** at the **School of Electrical and Computer Engineering, National Technical University of Athens (NTUA)**.

---

## Repository Structure

```
├── cli/               # Command-line interface for DB setup, user management, query execution
├── code/              # Utility scripts for data generation, code hygiene, structure mapping
├── diagrams/          # ER and relational schema diagrams
├── docs/              # Report, assignment brief, indexing justification, structure notes
├── frontend/          # React + Flask web interface with tabbed schema/query/CLI UI
├── sql/               # Database DDL, views, procedures, triggers, and graded queries
├── test/              # Automated testing of CLI
└── README.md          # This file
```

---

## Assignment Summary

As per the course specifications, we designed and implemented a **relational database system** to support all core operations of the Pulse University Festival, including:

- **Festival logistics**: Locations, stages, performances, and equipment
- **Artist and band management**: Scheduling rules, genre/subgenre consistency, and annual participation limits
- **Ticketing system**: Sales, validation, and resale through FIFO queues
- **Staff assignments**: Automatic enforcement of staffing ratios
- **Visitor feedback**: Likert-based performance reviews and aggregate insights
- **End-to-end system**: From ER design to SQL deployment, data generation, CLI tooling, and web-based management

---

## Key Features

- **ER and Relational Design**:
  - Complete conceptual and logical schema with enforced cardinality and participation constraints
  - ER and relational diagrams provided in the `diagrams/` folder

- **DDL and Constraints** (`sql/`):
  - Schema (`install.sql`) includes foreign keys, unique constraints, and data validation via `CHECK`
  - Extensive lookup tables for roles, genres, payment methods, and more
  - 
  - Triggers (`triggers.sql`) enforce business logic such as resale queue rules, artist participation caps, and VIP limits
  - Views (`views.sql`) and procedures (`procedures.sql`) support advanced query use cases and data maintenance

- **Graded SQL Queries**:
  - One script per query in `sql/queries/Qx.sql` with results in `Qx_out.txt` (x is a 2-digit number, e.g. 01)
  - Indexed and optimized using `sql/indexing.sql`
  - Includes trace analysis and query plan tuning for `Q04` and `Q06`, in the respective `plan1_out.txt` and `plan2_out.txt` files

- **Synthetic Data Generation**:
  - `faker.py` (immediate data insertion) and `faker_sql.py` (query generation) create a complete, constraint-compliant festival dataset. In the second case, `load.sql` is being produced.
  - Designed to support all 15 graded queries with special-case data coverage
  - Generates realistic multi-year festival scenarios across diverse entities

- **Command-Line Interface** (`cli/db137.py`):
  - Used via: `db137 + <command>`
  - Full database setup and reset:
    - `create-db`, `drop-db`, `reset-db`, `load-db`, `erase-db`, `db-status`, `viewq`
  - Role-based user management:
    - `users register`, `grant`, `revoke`, `rename`, `passwd`, `list`, `drop`, `drop-all`, `whoami`, `set-defaults`
  - Query execution with export support:
    - `q X` and `q X Y` batch runs (from query X to query Y) with output saved to the corresponding file(s)

- **Web Frontend**:
  - Developed with React (Vite), Flask backend, and Python3 server
  - Key features:
    - **Login/Logout** with session-based role access
    - **Schema Overview**: Inspect tables, views, triggers, and stored procedures
    - **Browse Schema**: Preview table contents and definitions with export options (CSV, TXT), as well as definitions for triggers, procedures, and views
    - **Run Query**: Syntax-highlighted SQL editor with output viewer and permission checks
    - **Run CLI**: Execute authorized CLI commands with live-streamed output and permission checks

- **Automated Testing**:
  - `test_cli.sh`: Tests user commands and access control logic

- **Setup Instructions**:
  - Detailed installation steps are available in `cli/README.md` and `frontend/README.md`

---

© Team 137 – NTUA ECE | Databases, Spring 2025

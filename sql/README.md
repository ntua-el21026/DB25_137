# SQL – Pulse University Festival DB

This folder contains all schema definitions, logic scripts, queries, and outputs for the semester project.

## Contents

- **`install.sql`**: Creates the full database schema, including all tables, constraints, and relations.
- **`indexing.sql`**: Adds performance-optimized indexes to accelerate specific queries (Q1–Q15).
- **`procedures.sql`**: Defines stored procedures used for ticket updates, staff checks, and maintenance tasks.
- **`triggers.sql`**: Defines all BEFORE/AFTER INSERT/UPDATE triggers for business rule enforcement (e.g. performance constraints, staff ratios, unique EANs, ticket resale logic).
- **`views.sql`**: Predefined SQL views used to simplify complex queries (e.g. artist ratings, genre counts, yearly revenue).

---

## `queries/` Subfolder

Contains one file per required SQL query:

- `Q1.sql` through `Q15.sql`: Solutions to the assignment's 15 core questions
- `Qx_out.txt`: Output from each query's execution using the CLI tool
- All queries are written in clean SQL without ORMs, JSON, or array types

---

## How to Use

1. To deploy the full schema with its constraints, run:

```bash
db137 create-db
```

2. To fill the database with the synthetic data, run:

```bash
db137 load-db
```

3. To run a specific query (e.g., Q8):

```bash
db137 q8
```

4. To run a batch of queries (e.g., Q1 to Q6):

```bash
db137 q1-to-q6
```
---

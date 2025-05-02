
# Pulse University – DB137 CLI

A command-line interface for administering the Pulse University Festival relational database system (2024–2025).

---

## 1. Requirements

- Python 3.8+
- Packages:

```bash
pip install --user click mysql-connector-python
```

---

## 2. Project Setup

Create the file `pyproject.toml` in the **project root**:

```toml
[build-system]
requires = ["setuptools>=64"]
build-backend = "setuptools.build_meta"

[project]
name = "db137"
version = "0.1"
description = "Pulse University Database Helper CLI"
requires-python = ">=3.8"
dependencies = [
    "click",
    "mysql-connector-python",
]

[tool.setuptools.packages.find]
where = ["."]

[project.scripts]
db137 = "cli.db137:cli"
```

---

## 3. Installation

From the root directory:

```bash
pip uninstall db137      # Optional: if reinstalling
pip install --user -e .
```

This creates the `db137` command at `~/.local/bin/db137`.

---

## 4. Shell Configuration

Append this to your `.bashrc` or `.zshrc`:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

Reload:

```bash
source ~/.bashrc  # or ~/.zshrc
```

Check:

```bash
which db137
```

---

## 5. Environment Variables

The CLI requires DB root credentials. Best practice is to define them in a `.envrc` file:

```bash
export DB_ROOT_USER=$(echo -n 'root' | tr -d '
')
export DB_ROOT_PASS=$(echo -n 'yourpassword' | tr -d '
')
export PYTHONPATH=$PWD
```

Then allow it:

```bash
direnv allow
```

---

## 6. Commands

```bash
db137 <command> ...
```

### Users

- `users register`
- `users grant [--show-diff]`
- `users revoke [--show-diff]`
- `users rename`
- `users passwd`
- `users list`
- `users drop`
- `users drop-all`
- `users whoami`
- `users set-defaults [--show-diff]`

Examples:

```bash
db137 users register alice --password pass
db137 users grant alice --db pulse_university --privileges SELECT,INSERT
db137 users revoke alice --db pulse_university --privileges SELECT --show-diff
```

---

### Schema Setup

- `create-db` – Run install.sql, indexing, procedures, triggers, views
- `load-db` – Run faker.py + load.sql
- `reset` – Shortcut: create-db + load-db
- `erase` – Truncate all tables (preserves schema)
- `drop-db` – Delete schema
- `status` – Show table row counts

---

### Query Execution

- `qX` – Run QX.sql → QX_out.txt
- `qX-to-qY` – Run a range of Q files (e.g. q1-to-q5)

---

## 7. Manual Testing

To run CLI tests manually:

```bash
bash test/test_cli.sh
```

Results go to `test/test_cli_results.txt`.

---

## 8. Cleanup

```bash
find . -type d -name '__pycache__' -exec rm -r {} +
rm -rf db137.egg-info/
```

---

## 9. Command Reference

Each of the following commands can be run with:

```bash
db137 <command>
```

---

### USERS

- `users register` – Create a new user and grant privileges:
  ```bash
  db137 users register alice --password secret --default-db pulse_university --privileges SELECT,INSERT
  ```

- `users grant` – Grant privileges on a schema (with optional diff view):
  ```bash
  db137 users grant alice --db pulse_university --privileges SELECT,INSERT --show-diff
  ```

- `users revoke` – Revoke privileges from a user (with optional diff view):
  ```bash
  db137 users revoke alice --db pulse_university --privileges SELECT --show-diff
  ```

- `users rename` – Rename a user:
  ```bash
  db137 users rename alice alicia
  ```

- `users passwd` – Change a user's password:
  ```bash
  db137 users passwd alice
  ```

- `users list` – List users and their privileges:
  ```bash
  db137 users list
  ```

- `users drop` – Drop a user:
  ```bash
  db137 users drop alice
  ```

- `users drop-all` – Drop all users on host `%`:
  ```bash
  db137 users drop-all
  ```

- `users whoami` – Show current connection identity:
  ```bash
  db137 users whoami
  ```

- `users set-defaults` – Grant standard CRUD privileges (with optional diff view):
  ```bash
  db137 users set-defaults alice --show-diff
  ```

---

### DATABASE SETUP

- `create-db` – Deploy schema, indexing, views, triggers:
  ```bash
  db137 create-db
  ```

- `load-db` – Run `faker.py` and import data:
  ```bash
  db137 load-db
  ```

- `reset` – Full setup (create + load):
  ```bash
  db137 reset
  ```

- `erase` – Truncate all base tables (data only):
  ```bash
  db137 erase
  ```

- `drop-db` – Delete the database schema:
  ```bash
  db137 drop-db
  ```

- `status` – Print row counts for all base tables:
  ```bash
  db137 status
  ```

---

### QUERIES

- `qX` – Run one query (e.g., Q01.sql → Q01_out.txt):
  ```bash
  db137 q1
  ```

- `qX-to-qY` – Run a query batch:
  ```bash
  db137 q1-to-q5
  ```

---

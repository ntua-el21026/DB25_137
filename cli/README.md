# Pulse University – DB137 CLI

A command-line interface for administering the Pulse University Festival database system (2024–2025).

> This CLI must be installed and run inside a **Linux or WSL** environment.

---

## 1. Requirements

- Python 3.10 or newer
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
export DB_ROOT_USER=$(echo -n 'root' | tr -d '')
export DB_ROOT_PASS=$(echo -n 'yourpassword' | tr -d '')
export PYTHONPATH=$PWD

export DB_HOST='your_localhost'
export DB_NAME='pulse_university'
export DB_PORT=3306
```

Then allow it:

```bash
direnv allow
```

---

## 6. Troubleshooting

### MySQL connection fails (`Can't connect to MySQL server`)

Make sure your MySQL server is **running**.

Check status:

```bash
sudo service mysql status
```

If it's not running, start it:

```bash
sudo service mysql start
```

### `DB_ROOT_USER` or `DB_ROOT_PASS` is blank

This usually means `.envrc` wasn't loaded.

Fix:

```bash
direnv allow
echo $DB_ROOT_USER  # should return 'root'
```

### `db137` not found

Ensure `~/.local/bin` is in your PATH. Add this to your shell profile:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

Reload your shell (`source ~/.bashrc`), then check with `which db137`.

---

## 7. Cleanup

```bash
find . -type d -name '__pycache__' -exec rm -r {} +
rm -rf db137.egg-info/
```

---

## 8. Manual Testing

To run CLI tests manually:

```bash
bash test/test_cli.sh
```

Results go to `test/test_cli_results.txt`.

---

## 9. Command Reference

Each of the following commands can be run with:

```bash
db137 <command>
```

---

### USERS

- `users register` – Create a new user and grant privileges:

  **Required**:
  - `username` (e.g. `alice`)
  - `--password` (e.g. `--password secret`)

  **Optional**:
  - `--default-db` (default: `pulse_university`)
  - `--privileges` (default: `FULL`)

  Example:
  ```bash
  db137 users register alice --password secret --default-db pulse_university --privileges SELECT,INSERT
  ```

- `users grant` – Grant privileges on a schema:

  **Required**:
  - `username` (e.g. `alice`)
  - `--db` (e.g. `--db pulse_university`)
  - `--privileges` (e.g. `--privileges SELECT,INSERT`)

  **Optional**:
  - `--show-diff` (shows before/after privileges)

  Example:
  ```bash
  db137 users grant alice --db pulse_university --privileges SELECT,INSERT --show-diff
  ```

- `users revoke` – Revoke privileges from a user:

  **Required**:
  - `username` (e.g. `alice`)
  - `--db` (e.g. `--db pulse_university`)
  - `--privileges` (e.g. `--privileges SELECT`)

  **Optional**:
  - `--show-diff` (shows before/after privileges)

  Example:
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

- `users set-defaults` – Grant standard CRUD privileges:

  **Required**:
  - `username` (e.g. `alice`)

  **Optional**:
  - `--db` (default: `pulse_university`)
  - `--show-diff` (shows before/after privileges)

  Example:
  ```bash
  db137 users set-defaults alice --show-diff
  ```

---

### DATABASE SETUP

- `create-db` – Deploy schema, indexing, views, and triggers:

  **Optional**:
  - `--sql-dir` (default: `sql`)
  - `--database` (default: `pulse_university`)

  Example:
  ```bash
  db137 create-db --sql-dir sql --database pulse_university
  ```

- `drop-db` – Delete the database schema:

  **Optional**:
  - `--database` (default: `pulse_university`)
  - `--yes` (skip confirmation prompt)

  Example:
  ```bash
  db137 drop-db --database pulse_university --yes
  ```

- `reset-db` – Full setup (drop + create + load):

  **No arguments required or optional.**

  Example:
  ```bash
  db137 reset-db
  ```

- `load-db` – Load synthetic data into the database, either from SQL or Python generators.

  **Behavior**:
  - By default, loads data from `load.sql`
  - `--g` → Run `faker_sql.py` (basic generator), then execute `create-db` and `load.sql` with progress bar
  - `--i` → Run `faker.py` (intelligent, trigger-compliant generator)

  **Optional**:
  - `--g` (run `faker_sql.py` + `load.sql`)
  - `--i` (run only `faker.py`)
  - `--sql-dir` (directory containing SQL files; default: `sql`)
  - `--database` (database to load into; default: `pulse_university`)

  `--g` and `--i` are mutually exclusive.

  **Example**:
  ```bash
  db137 load-db
  db137 load-db --g
  db137 load-db --i

- `erase-db` – Truncate all base tables (data only):

  **Optional**:
  - `--database` (default: `pulse_university`)
  - `--yes` (skip confirmation prompt)

  Example:
  ```bash
  db137 erase-db --database pulse_university --yes
  ```

- `db-status` – Print row counts for all base tables:

  **Optional**:
  - `--database` (default: `pulse_university`)

  Example:
  ```bash
  db137 db-status --database pulse_university
  ```

- `viewq` – Show contents of the Resale_Match_Log table:

  **Optional**:
  - `--database` (default: `pulse_university`)

  Example:
  ```bash
  db137 viewq --database pulse_university
  ```

---

### QUERIES

- `q X` – Run one query (e.g., `Q01.sql → Q01_out.txt`):

  **Required**:
  - `q X` (query number, e.g. `q 1`, `q 14`)

  **Optional**:
  - `--database` (default: `pulse_university`)

  Example:
  ```bash
  db137 q 1 --database pulse_university
  ```

- `q X Y` – Run a query batch:

  **Required**:
  - `q X Y` (range format, e.g. `q 1 5`)

  **Optional**:
  - `--database` (default: `pulse_university`)

  Example:
  ```bash
  db137 q 1 5 --database pulse_university
  ```

---

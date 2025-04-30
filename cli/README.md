# Installing and Using the `db137` CLI

---

## 1. Requirements

- Python 3.8+
- Packages:
  ```bash
  pip3 install --user click mysql-connector-python
  ```

---

## 2. Create file: pyproject.toml (must be in project root)

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

## 3. Install the CLI

From the project root:

```bash
pip uninstall db137      # Optional, if reinstalling
pip install --user -e .
```

This creates the `db137` command in `~/.local/bin/`.

---

## 4. PATH Setup

Ensure your shell loads the CLI:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

Then:

```bash
source ~/.bashrc  # or ~/.zshrc
```

Check:

```bash
which db137
```

Should return something like:

```
/home/you/.local/bin/db137
```

---

## 5. Environment Variables (for DB access)

### If using `direnv` (recommended)

Create `.envrc` file in project root with the following contents:

```bash
export DB_ROOT_USER=$(echo -n 'root' | tr -d '\r')
export DB_ROOT_PASS=$(echo -n 'yourpassword' | tr -d '\r')
export PYTHONPATH=$PWD
```

Then:

```bash
direnv allow
```

This prevents Windows-style line endings (`\r`) from corrupting auth.

You can verify:

```bash
echo "$DB_ROOT_USER" | od -c
```

Should **not** end in `\r`.

---

## 6. Troubleshooting: Access Denied

If `db137` fails with:

```
Access denied for user 'root'@'localhost' (using password: YES)
```

### Check:
1. You can run:
   ```bash
   mysql -u root -p
   ```
   and login with your password.

2. `.envrc` uses `echo -n 'value' | tr -d '\r'`  
   (see step 6 above — `\r` will silently break your login)

3. Print debug:
   Add inside `manager.py → _connect()`:
   ```python
   print("Connecting with DSN:", self._dsn)
   ```

You should see clean credentials without `\r`.

---

## 7. Cleanup

Remove stale Python caches:

```bash
find . -type d -name '__pycache__' -exec rm -r {} +
```

Remove the outdated `cli/db137.egg-info/` if it still exists:

```bash
rm -rf cli/db137.egg-info/
```

Only the one at the root should remain.

---

## 8. Command Reference

Each of the following commands can be run with:

```bash
db137 <command>
```

### USERS
- `users register` – Create a new user and grant privileges
  ```bash
  db137 users register alice --password secret
  ```

- `users grant` – Grant privileges on a schema
  ```bash
  db137 users grant alice --db pulse_university --privileges SELECT,INSERT
  ```

- `users revoke` – Revoke privileges from a user
  ```bash
  db137 users revoke alice --db pulse_university --privileges SELECT
  ```

- `users rename` – Rename a user
  ```bash
  db137 users rename alice alicia
  ```

- `users passwd` – Change a user’s password
  ```bash
  db137 users passwd alice
  ```

- `users list` – List users and their real privileges
  ```bash
  db137 users list
  ```

- `users drop` – Drop a single user
  ```bash
  db137 users drop alice
  ```

- `users drop-all` – Drop all users (on `%`)
  ```bash
  db137 users drop-all
  ```

- `users whoami` – Show current MySQL connection identity
  ```bash
  db137 users whoami
  ```

- `users set-defaults` – Grant SELECT, INSERT, UPDATE, DELETE
  ```bash
  db137 users set-defaults alice --db pulse_university
  ```

### DATABASE SETUP
- `create-db` – Run all schema and object SQLs
  ```bash
  db137 create-db
  ```

- `load-db` – Generate and load data
  ```bash
  db137 load-db
  ```

- `reset` – Run both create-db and load-db
  ```bash
  db137 reset
  ```

- `erase` – Truncate all data in all base tables
  ```bash
  db137 erase
  ```

- `drop-db` – Fully drop the schema
  ```bash
  db137 drop-db
  ```

- `status` – Show row count per table
  ```bash
  db137 status
  ```

### TESTING

- `test-cli` – Run test_cli.py only
  ```bash
  db137 test-cli
  ```

- `test-load` – Run test_load.py and test_load.sql
  ```bash
  db137 test-load
  ```

### QUERIES
- `qX` – Run single query (QX.sql → QX_out.txt)
  ```bash
  db137 q1
  ```

- `qX-to-qY` – Run range of queries
  ```bash
  db137 q1-to-q5
  ```

---
# Test – Pulse University Festival DB

This folder contains an automated test script to verify the functionality and integrity of the project CLI.

## Contents

- **`test_cli.sh`**: End-to-end CLI test runner. Executes user-specific commands (e.g., `db137 users register`, `db137 users rename`, `db137 users grant`) and verifies expected behaviors. The other CLI commands have been tested manually.
- **`test_cli_results.txt`**: Sample output from running `test_cli.sh`.

## How to Run

Navigate to the `test/` subfolder of the project root.
You can run all CLI tests as follows:

1. Make the test scripts executable, as:

```bash
chmod +x test_cli.sh
```

2. Run the CLI testing:
```bash
./test_cli.sh
```

3. Check the results in `test_cli_results.txt`.

> Ensure your database has been freshly installed (`db137 create-db`) before running trigger tests.

---

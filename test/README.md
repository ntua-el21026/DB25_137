# Test – Pulse University Festival DB

This folder contains automated test scripts to verify the functionality and integrity of the project.

## Contents

- **`test_cli.sh`**: End-to-end CLI test runner. Executes user-specific commands (e.g., `db137 users register`, `db137 users rename`, `db137 users grant`) and verifies expected behaviors. The other CLI commands have been tested manually.
- **`test_cli_results.txt`**: Sample output from running `test_cli.sh`.
- **`test_triggers.sh`**: Dedicated test suite for verifying constraints and trigger-based business rules.
- **`test_triggers_results.txt`**: Captured results of running `test_triggers.sh`, showing pass/fail outcomes for each trigger scenario.

## How to Run

Navigate to the `test/` subfolder of the project root.
You can run all CLI tests as follows:

1. Make the test scripts executable, as:

```bash
chmod +x test_cli.sh        # for the CLI testing
chmod +x test_triggers.sh   # for the triggers testing
```

2. Run the CLI testing:
```bash
./test_cli.sh
```

3. Run the triggers testing:

```bash
./test_triggers.sh
```

> Ensure your database has been freshly installed (`db137 reset`) before running trigger tests.

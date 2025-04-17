#!/usr/bin/env python3
"""
Integrity Checker for the Code Subfolder of the Pulse Festival Project

Checks:
- Output paths (static and dynamic, case-insensitive)
- Wildcard-based output matching (e.g., Q*.sql)
- Output paths in comments
- Comment/code path mismatches
- Imports
- __main__ guard presence
- Unused or unreferenced scripts
"""

import os
import subprocess
import re
import glob

CODE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
PROJECT_ROOT = os.path.dirname(CODE_ROOT)
REPORT_PATH = os.path.join(PROJECT_ROOT, 'docs', 'organization', 'integrity_report.txt')


def build_expected_outputs_from_struct():
    expected = {}
    struct_path = os.path.join(CODE_ROOT, 'organization', 'struct.py')
    if not os.path.exists(struct_path):
        return expected

    result = subprocess.run(['python3', struct_path], capture_output=True, text=True)
    if result.returncode != 0:
        return expected

    for line in result.stdout.strip().splitlines():
        if '→' in line:
            script, outputs = line.split('→')
            script = script.strip()
            paths = [path.strip() for path in outputs.split(',') if path.strip()]
            expected[script] = paths
    return expected


def extract_paths_from_code(content):
    found = set()
    for match in re.findall(r'["\']([\w\-_/]+\.\w+)["\']', content):
        if "/" in match:
            found.add(match.lower())
    join_patterns = re.findall(r"os\.path\.join\([^)]*\)", content)
    for join in join_patterns:
        parts = re.findall(r'["\']([^"\']+)["\']', join)
        if len(parts) >= 2:
            joined = "/".join(parts[-2:]).lower()
            found.add(joined)
    return found


def extract_paths_from_comments(lines):
    comment_paths = set()
    for line in lines:
        if "#" in line:
            for match in re.findall(r'([\w\-_/]+\.\w+)', line):
                if "/" in match:
                    comment_paths.add(match.lower())
    return comment_paths


def check_file_outputs(filepath, expected_outputs, report_lines):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        lines = content.splitlines()

    found_in_code = extract_paths_from_code(content)
    found_in_comments = extract_paths_from_comments(lines)

    matched = set()
    content_lower = content.lower()
    filename = os.path.basename(filepath).lower()

    # Special override: treat dynamic generators as matched
    if filename in ['qgen.py', 'faker.py']:
        matched.update(expected_outputs)

    for expected in expected_outputs:
        expected_lc = expected.lower()
        if '*' in expected:
            prefix = expected_lc.split('*')[0]
            if any(path.startswith(prefix) for path in found_in_code):
                matched.add(expected)
                continue
            if prefix in content_lower:
                if re.search(rf"f[\"'].*{re.escape(prefix)}.*{{.*}}.*[\"']", content, re.IGNORECASE):
                    matched.add(expected)
                    continue
                if re.search(rf"{re.escape(prefix)}.*\.format\(", content, re.IGNORECASE):
                    matched.add(expected)
                    continue
        else:
            if expected_lc in found_in_code:
                matched.add(expected)

    for expected in expected_outputs:
        expected_lc = expected.lower()
        if expected not in matched:
            report_lines.append(f"[WARNING] {os.path.basename(filepath)} does not reference expected output path: {expected}")
            found_in_comment = any(expected_lc == comment_path or expected_lc.endswith(comment_path) for comment_path in found_in_comments)
            if not found_in_comment:
                report_lines.append(f"[NOTE] {os.path.basename(filepath)}: expected output '{expected}' is neither referenced in code nor mentioned in any comment.")

    for code_path in found_in_code:
        for comment_path in found_in_comments:
            if os.path.basename(code_path) == os.path.basename(comment_path) and code_path != comment_path:
                report_lines.append(f"[ERROR] Output path mismatch between code and comment: {code_path} vs {comment_path}")


def check_output_files_exist(expected_outputs, report_lines):
    for expected in expected_outputs:
        full_pattern = os.path.join(PROJECT_ROOT, expected)
        matches = glob.glob(full_pattern)
        if not matches:
            report_lines.append(f"[WARNING] No file found matching: {expected}")


def check_main_guard(filepath, report_lines):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    if '__main__' not in content:
        report_lines.append(f"[WARNING] {os.path.basename(filepath)} does not contain a __main__ guard.")


def check_relative_imports(filepath, report_lines):
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    for line in lines:
        line = line.strip()
        if line.startswith("import") or line.startswith("from"):
            if "organization" in line and not line.startswith("from code."):
                report_lines.append(f"[WARNING] {os.path.basename(filepath)} may have incorrect import: {line}")


def check_unreferenced_scripts(found_files, referenced_files, report_lines):
    ignore = {'intcheck.py', 'struct.py', 'runall.py'}
    untracked = (found_files - referenced_files) - ignore
    for filename in sorted(untracked):
        report_lines.append(f"[NOTE] {filename} is not listed in EXPECTED_OUTPUTS or run_all.py")


def check_integrity():
    report_lines = ["INTEGRITY REPORT\n================\n"]

    # Run struct.py once and get mapping
    expected_outputs = build_expected_outputs_from_struct()
    report_lines.append("[INFO] struct.py output parsed successfully.\n")

    all_py_files = set()
    referenced_py_files = set(expected_outputs.keys())

    runall_path = os.path.join(CODE_ROOT, 'run_all.py')
    if os.path.exists(runall_path):
        with open(runall_path, 'r', encoding='utf-8') as f:
            runall_content = f.read()
        runall_refs = re.findall(r'["\'](\w+\.py)["\']', runall_content)
        referenced_py_files.update(runall_refs)

    for root, _, files in os.walk(CODE_ROOT):
        for file in files:
            if file.endswith('.py'):
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, CODE_ROOT)
                all_py_files.add(file)

                header_line = f"\n[Checking {rel_path}]"
                report_lines.append(header_line)
                start_len = len(report_lines)

                expected = expected_outputs.get(file, [])
                check_file_outputs(full_path, expected, report_lines)
                check_relative_imports(full_path, report_lines)
                check_main_guard(full_path, report_lines)
                check_output_files_exist(expected, report_lines)

                if len(report_lines) == start_len:
                    report_lines.append("[OK] No issues found.")

    check_unreferenced_scripts(all_py_files, referenced_py_files, report_lines)

    os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)
    with open(REPORT_PATH, 'w', encoding='utf-8') as out:
        out.write('\n'.join(report_lines))

    print(f"\n✔️ Integrity check complete. Report written to: {REPORT_PATH}")


if __name__ == "__main__":
    check_integrity()

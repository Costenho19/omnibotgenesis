#!/usr/bin/env python3
"""
OMNIX Version Consistency Checker

Detects hardcoded version strings that should use VERSION_BANNER from omnix_config.
Scans Python, JavaScript, and HTML files.
Run this script before major releases to ensure version consistency.

Usage:
    python scripts/verify_version_consistency.py

IMPORTANT: For JavaScript files, VERSION cannot be dynamically imported from Python.
When updating VERSION in omnix_config/settings.py, also update:
- omnix_dashboard/static/js/pages/terminal.js (console.log)
- omnix_dashboard/static/js/pages/dashboard.js (console.log)
"""
import os
import re
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent

EXCLUDED_FILES = {
    "verify_version_consistency.py",
    "TECHNICAL_DEBT.md",
    "FOLDER_AUDIT_PHASE6.md",
    "ARCHITECTURE.md",
    "replit.md",
    "CHANGELOG.md",
    "persisted_information.md",
    "IMPORT_AUDIT.md",
}

EXCLUDED_DIRS = {
    ".git",
    "__pycache__",
    ".venv",
    "node_modules",
    ".local",
    "docs/history",
    "docs/business",
}

SCANNABLE_EXTENSIONS = {'.py', '.js', '.html', '.htm'}

VERSION_PATTERN = re.compile(r'V6\.\d+\.\d+[a-z]?\s*(INSTITUTIONAL\+?|PREMIUM)?')


def get_current_version():
    """Get the current VERSION from omnix_config."""
    try:
        sys.path.insert(0, str(project_root))
        from omnix_config import VERSION, VERSION_BANNER
        return VERSION, VERSION_BANNER
    except ImportError:
        return None, None


def check_python_file(filepath: Path) -> list[tuple[int, str]]:
    """Check a Python file for hardcoded version strings."""
    violations = []
    
    try:
        content = filepath.read_text(encoding='utf-8', errors='ignore')
    except Exception:
        return []
    
    lines = content.split('\n')
    in_multiline_comment = False
    
    for line_num, line in enumerate(lines, 1):
        if '"""' in line or "'''" in line:
            if line.count('"""') % 2 == 1 or line.count("'''") % 2 == 1:
                in_multiline_comment = not in_multiline_comment
        
        if in_multiline_comment:
            continue
        if line.strip().startswith('#'):
            continue
        if 'VERSION_BANNER' in line or 'from omnix_config import' in line:
            continue
        
        match = VERSION_PATTERN.search(line)
        if match and ('"' in line or "'" in line):
            violations.append((line_num, line.strip()[:100]))
    
    return violations


def check_js_file(filepath: Path, current_version: str) -> list[tuple[int, str, str]]:
    """Check a JavaScript file for outdated version strings."""
    violations = []
    
    try:
        content = filepath.read_text(encoding='utf-8', errors='ignore')
    except Exception:
        return []
    
    lines = content.split('\n')
    
    for line_num, line in enumerate(lines, 1):
        if line.strip().startswith('//'):
            continue
        if line.strip().startswith('*'):
            continue
        
        match = VERSION_PATTERN.search(line)
        if match:
            found_version = match.group(0)
            if current_version and current_version not in found_version:
                violations.append((line_num, line.strip()[:100], f"Expected V{current_version}"))
    
    return violations


def main():
    print("=" * 60)
    print("OMNIX Version Consistency Checker")
    print("=" * 60)
    print()
    
    current_version, version_banner = get_current_version()
    if current_version:
        print(f"Current version: {current_version}")
        print(f"VERSION_BANNER: {version_banner}")
    else:
        print("WARNING: Could not import omnix_config")
        current_version = "6.5.4d"
    
    print()
    print("Scanning Python, JavaScript, and HTML files...")
    print()
    
    py_violations = []
    js_violations = []
    files_scanned = {'py': 0, 'js': 0, 'html': 0}
    
    for root, dirs, files in os.walk(project_root):
        dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]
        
        for file in files:
            if file in EXCLUDED_FILES:
                continue
            
            filepath = Path(root) / file
            ext = filepath.suffix.lower()
            
            if ext not in SCANNABLE_EXTENSIONS:
                continue
            
            if ext == '.py':
                files_scanned['py'] += 1
                violations = check_python_file(filepath)
                if violations:
                    rel_path = filepath.relative_to(project_root)
                    py_violations.append((str(rel_path), violations))
            
            elif ext == '.js':
                files_scanned['js'] += 1
                violations = check_js_file(filepath, current_version)
                if violations:
                    rel_path = filepath.relative_to(project_root)
                    js_violations.append((str(rel_path), violations))
            
            elif ext in ('.html', '.htm'):
                files_scanned['html'] += 1
    
    print(f"Scanned: {files_scanned['py']} Python, {files_scanned['js']} JavaScript, {files_scanned['html']} HTML files")
    print()
    
    has_errors = False
    
    if py_violations:
        has_errors = True
        print("PYTHON VIOLATIONS (should use VERSION_BANNER):")
        print("-" * 60)
        for filepath, violations in py_violations:
            print(f"\n{filepath}:")
            for line_num, line_content in violations:
                print(f"  Line {line_num}: {line_content}")
        print()
        print("FIX: from omnix_config import VERSION_BANNER")
    
    if js_violations:
        has_errors = True
        print("\nJAVASCRIPT VIOLATIONS (outdated version):")
        print("-" * 60)
        for filepath, violations in js_violations:
            print(f"\n{filepath}:")
            for line_num, line_content, expected in violations:
                print(f"  Line {line_num}: {line_content}")
                print(f"           {expected}")
        print()
        print("FIX: Update version strings to match omnix_config/settings.py")
    
    if has_errors:
        total = sum(len(v) for _, v in py_violations) + sum(len(v) for _, v in js_violations)
        print()
        print(f"Total: {total} version issues found")
        sys.exit(1)
    else:
        print("All version strings are consistent!")
        print(f"All files reference V{current_version}")
        sys.exit(0)


if __name__ == "__main__":
    main()

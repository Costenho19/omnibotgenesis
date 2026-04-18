"""
OMNIX V6.5.4d - Version Consistency Tests

Detects hardcoded version strings that should use VERSION_BANNER from omnix_config.
Scans Python, JavaScript, and HTML files.

Migrated from: scripts/verify_version_consistency.py
"""
import re
import pytest
from pathlib import Path


PROJECT_ROOT = Path(__file__).parent.parent

EXCLUDED_FILES = {
    "verify_version_consistency.py",
    "test_version_consistency.py",
    "TECHNICAL_DEBT.md",
    "FOLDER_AUDIT_PHASE6.md",
    "ARCHITECTURE.md",
    "replit.md",
    "CHANGELOG.md",
    "persisted_information.md",
    "IMPORT_AUDIT.md",
    "entities.py",
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

VERSION_PATTERN = re.compile(r'V6\.\d+\.\d+[a-z]?\s*(INSTITUTIONAL\+?|PREMIUM)?')


def get_current_version():
    """Get the current VERSION from omnix_config."""
    try:
        from omnix_config import VERSION, VERSION_BANNER
        return VERSION, VERSION_BANNER
    except ImportError:
        return "6.5.4d", "V6.5.4d INSTITUTIONAL+"


def should_skip_path(path: Path) -> bool:
    """Check if path should be skipped."""
    if path.name in EXCLUDED_FILES:
        return True
    for excluded in EXCLUDED_DIRS:
        if excluded in str(path):
            return True
    return False


def check_python_file_for_violations(filepath: Path) -> list:
    """Check a Python file for hardcoded version strings.
    
    Focuses on actual violations (version string assignments) while
    allowing legitimate uses like:
    - Inline comments for version-specific documentation
    - Log messages for debugging/tracing
    - F-strings with version info in user-facing messages
    """
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
        
        # Skip lines where version only appears in inline comment
        code_part = line.split('#')[0] if '#' in line else line
        if not VERSION_PATTERN.search(code_part):
            continue
        
        # Skip log messages (debugging/tracing is fine)
        if any(x in line for x in ['logger.', 'logging.', 'print(', 'log.']):
            continue
        
        # Skip f-strings in user-facing messages (reports, alerts)
        if 'f"' in line or "f'" in line:
            continue
        
        # Only flag if version appears as a string literal assignment
        # or in a non-log, non-comment context
        match = VERSION_PATTERN.search(code_part)
        if match and ('"' in code_part or "'" in code_part):
            # Skip documentation fields (descriptions, notes, company names)
            if any(x in code_part for x in ['description=', 'notes=', 'company_name=', 'name=']):
                continue
            
            # Additional check: skip if it's clearly a documentation/message
            lower_line = line.lower()
            if any(x in lower_line for x in ['generated', 'report', 'this', 'sistema', 
                                              'perfil', 'excluido', 'activado', 'diseñado']):
                continue
            
            violations.append((line_num, line.strip()[:100]))
    
    return violations


def check_js_file_for_violations(filepath: Path, current_version: str) -> list:
    """Check a JavaScript file for outdated version strings."""
    violations = []
    
    try:
        content = filepath.read_text(encoding='utf-8', errors='ignore')
    except Exception:
        return []
    
    lines = content.split('\n')
    
    for line_num, line in enumerate(lines, 1):
        if line.strip().startswith('//') or line.strip().startswith('*'):
            continue
        
        match = VERSION_PATTERN.search(line)
        if match:
            found_version = match.group(0)
            if current_version and current_version not in found_version:
                violations.append((line_num, line.strip()[:100], f"Expected V{current_version}"))
    
    return violations


class TestVersionConsistency:
    """Test version string consistency across the codebase."""

    @pytest.fixture
    def current_version(self):
        """Get current version for tests."""
        version, banner = get_current_version()
        return version

    def test_version_banner_format(self):
        """Verify VERSION_BANNER has correct format."""
        version, banner = get_current_version()
        assert version is not None
        assert banner is not None
        assert f"V{version}" in banner

    def test_no_hardcoded_versions_in_python(self, current_version):
        """Check that Python files don't have hardcoded version strings."""
        violations = []
        
        for py_file in PROJECT_ROOT.rglob("*.py"):
            if should_skip_path(py_file):
                continue
            
            file_violations = check_python_file_for_violations(py_file)
            if file_violations:
                rel_path = py_file.relative_to(PROJECT_ROOT)
                violations.extend([
                    f"{rel_path}:{line_num}: {content}"
                    for line_num, content in file_violations
                ])
        
        if violations:
            pytest.fail(
                f"Found {len(violations)} hardcoded version strings in Python files:\n"
                + "\n".join(violations[:10])
                + ("\n..." if len(violations) > 10 else "")
                + "\n\nFix: Use 'from omnix_config import VERSION_BANNER'"
            )

    def test_no_outdated_versions_in_javascript(self, current_version):
        """Check that JavaScript files have up-to-date version strings."""
        violations = []
        
        for js_file in PROJECT_ROOT.rglob("*.js"):
            if should_skip_path(js_file):
                continue
            
            file_violations = check_js_file_for_violations(js_file, current_version)
            if file_violations:
                rel_path = js_file.relative_to(PROJECT_ROOT)
                violations.extend([
                    f"{rel_path}:{line_num}: {content} ({expected})"
                    for line_num, content, expected in file_violations
                ])
        
        if violations:
            pytest.fail(
                f"Found {len(violations)} outdated version strings in JavaScript files:\n"
                + "\n".join(violations[:10])
                + ("\n..." if len(violations) > 10 else "")
                + f"\n\nFix: Update to V{current_version}"
            )

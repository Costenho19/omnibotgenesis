#!/usr/bin/env python3
"""
OMNIX Traceability Matrix Validator

Parses docs/reference/TRACEABILITY_MATRIX.md and validates that each
documented component actually exists in the codebase.

Outputs:
- JSON structured data of all 123 components
- Validation report with PASS/MISSING/LEGACY_ONLY status
- Evidence file for audit compliance
"""

import json
import os
import re
import subprocess
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional


@dataclass
class Component:
    domain: str
    domain_id: int
    component_id: str
    name: str
    legacy_path: str
    v7_path: str
    priority: str
    legacy_exists: bool = False
    v7_exists: bool = False
    status: str = "UNKNOWN"


def parse_traceability_matrix(filepath: str) -> List[Component]:
    """Parse the markdown traceability matrix into structured components."""
    components = []
    current_domain = ""
    current_domain_id = 0
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    
    for line in lines:
        if line.startswith('## DOMINIO'):
            match = re.search(r'DOMINIO (\d+): (.+)', line)
            if match:
                current_domain_id = int(match.group(1))
                current_domain = match.group(2).strip()
        
        if line.startswith('|') and not line.startswith('| #') and not line.startswith('|---'):
            parts = [p.strip() for p in line.split('|')]
            if len(parts) >= 7:
                comp_id = parts[1]
                if re.match(r'\d+\.\d+', comp_id):
                    name = parts[2]
                    legacy_raw = parts[3]
                    v7_raw = parts[4]
                    priority_raw = parts[-2] if len(parts) >= 8 else parts[-1]
                    
                    legacy_path = re.sub(r'`([^`]+)`', r'\1', legacy_raw).strip()
                    legacy_path = legacy_path.replace(' (nuevo)', '').replace('- (nuevo)', '')
                    legacy_path = legacy_path.replace('- (en enterprise_bot)', '')
                    legacy_path = legacy_path.strip(' -')
                    
                    v7_path = re.sub(r'`([^`]+)`', r'\1', v7_raw).strip()
                    
                    priority = "CORE" if "CORE" in priority_raw else \
                               "SUPPORT" if "SUPPORT" in priority_raw else \
                               "STRATEGIC" if "STRATEGIC" in priority_raw else "UNKNOWN"
                    
                    component = Component(
                        domain=current_domain,
                        domain_id=current_domain_id,
                        component_id=comp_id,
                        name=name,
                        legacy_path=legacy_path,
                        v7_path=v7_path,
                        priority=priority
                    )
                    components.append(component)
    
    return components


def check_path_exists(path: str) -> bool:
    """Check if a file or directory exists."""
    if not path or path == '-' or path.startswith('-'):
        return False
    
    full_path = Path(path)
    if full_path.exists():
        return True
    
    if path.endswith('/'):
        glob_pattern = path.rstrip('/') + '/**/*.py'
        result = list(Path('.').glob(glob_pattern))
        return len(result) > 0
    
    return False


def validate_components(components: List[Component]) -> List[Component]:
    """Validate each component's existence in codebase."""
    for comp in components:
        comp.legacy_exists = check_path_exists(comp.legacy_path)
        comp.v7_exists = check_path_exists(comp.v7_path)
        
        if comp.legacy_exists and comp.v7_exists:
            comp.status = "FULL"
        elif comp.legacy_exists and not comp.v7_exists:
            comp.status = "LEGACY_ONLY"
        elif not comp.legacy_exists and comp.v7_exists:
            comp.status = "V7_ONLY"
        elif comp.legacy_path in ['-', '', '-'] or '(nuevo)' in comp.legacy_path or '(en enterprise_bot)' in comp.legacy_path:
            if comp.v7_exists:
                comp.status = "V7_ONLY"
            else:
                comp.status = "PLANNED"
        else:
            comp.status = "MISSING"
    
    return components


def get_git_info() -> Dict[str, str]:
    """Get current git information for audit trail."""
    try:
        sha = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
        branch = subprocess.check_output(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], text=True).strip()
        return {"commit": sha[:8], "branch": branch}
    except:
        return {"commit": "unknown", "branch": "unknown"}


def generate_json_output(components: List[Component], output_path: str):
    """Generate structured JSON output."""
    data = {
        "generated_at": datetime.now().isoformat(),
        "git": get_git_info(),
        "total_components": len(components),
        "components": [asdict(c) for c in components]
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    
    print(f"JSON output saved to: {output_path}")


def generate_markdown_report(components: List[Component], output_path: str):
    """Generate markdown validation report."""
    git_info = get_git_info()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    stats = {
        "FULL": 0,
        "LEGACY_ONLY": 0,
        "V7_ONLY": 0,
        "PLANNED": 0,
        "MISSING": 0
    }
    
    for comp in components:
        stats[comp.status] = stats.get(comp.status, 0) + 1
    
    domain_stats = {}
    for comp in components:
        domain_key = f"{comp.domain_id}. {comp.domain}"
        if domain_key not in domain_stats:
            domain_stats[domain_key] = {"total": 0, "legacy": 0, "v7": 0}
        domain_stats[domain_key]["total"] += 1
        if comp.legacy_exists:
            domain_stats[domain_key]["legacy"] += 1
        if comp.v7_exists:
            domain_stats[domain_key]["v7"] += 1
    
    report = f"""# OMNIX Traceability Validation Report

**Generated**: {timestamp}  
**Git Commit**: {git_info['commit']}  
**Branch**: {git_info['branch']}  
**Total Components**: {len(components)}

---

## Executive Summary

| Status | Count | Description |
|--------|-------|-------------|
| ✅ FULL | {stats['FULL']} | Both Legacy and V7 paths exist |
| 🟡 LEGACY_ONLY | {stats['LEGACY_ONLY']} | Legacy exists, V7 not yet created |
| 🔵 V7_ONLY | {stats['V7_ONLY']} | V7 exists (new component or migrated) |
| ⚪ PLANNED | {stats['PLANNED']} | New in V7, marked as planned |
| ❌ MISSING | {stats['MISSING']} | Neither path exists |

### Validation Score

- **Legacy Coverage**: {sum(1 for c in components if c.legacy_exists)}/{len(components)} ({100*sum(1 for c in components if c.legacy_exists)//len(components)}%)
- **V7 Coverage**: {sum(1 for c in components if c.v7_exists)}/{len(components)} ({100*sum(1 for c in components if c.v7_exists)//len(components)}%)

---

## Domain Breakdown

| Domain | Total | Legacy Exists | V7 Exists |
|--------|-------|---------------|-----------|
"""
    
    for domain, st in sorted(domain_stats.items()):
        report += f"| {domain} | {st['total']} | {st['legacy']} | {st['v7']} |\n"
    
    report += "\n---\n\n## Component Details by Status\n"
    
    for status in ["MISSING", "LEGACY_ONLY", "V7_ONLY", "PLANNED", "FULL"]:
        status_comps = [c for c in components if c.status == status]
        if status_comps:
            icon = {"FULL": "✅", "LEGACY_ONLY": "🟡", "V7_ONLY": "🔵", "PLANNED": "⚪", "MISSING": "❌"}[status]
            report += f"\n### {icon} {status} ({len(status_comps)} components)\n\n"
            report += "| ID | Name | Legacy Path | V7 Path | Priority |\n"
            report += "|-----|------|-------------|---------|----------|\n"
            for c in status_comps:
                legacy = f"`{c.legacy_path}`" if c.legacy_path and c.legacy_path != '-' else "-"
                v7 = f"`{c.v7_path}`" if c.v7_path else "-"
                report += f"| {c.component_id} | {c.name} | {legacy} | {v7} | {c.priority} |\n"
    
    report += f"""

---

## Reproducibility

This report was generated by running:

```bash
python scripts/traceability/validate_traceability.py
```

### Validation Commands Used

For each component, the script checks:

1. **File existence**: `test -f <path>` or `test -d <path>`
2. **Directory contents**: `ls <path>/*.py 2>/dev/null | wc -l`

---

*Generated by OMNIX Traceability Validator*  
*{timestamp}*
"""
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"Markdown report saved to: {output_path}")


def main():
    matrix_path = "docs/reference/TRACEABILITY_MATRIX.md"
    json_output = "docs/compliance/evidence/traceability_components.json"
    md_output = "docs/compliance/evidence/traceability_validation.md"
    
    print("=" * 60)
    print("OMNIX Traceability Matrix Validator")
    print("=" * 60)
    
    print(f"\n1. Parsing {matrix_path}...")
    components = parse_traceability_matrix(matrix_path)
    print(f"   Found {len(components)} components")
    
    print("\n2. Validating component paths...")
    components = validate_components(components)
    
    stats = {}
    for c in components:
        stats[c.status] = stats.get(c.status, 0) + 1
    
    print("\n3. Results Summary:")
    for status, count in sorted(stats.items()):
        print(f"   {status}: {count}")
    
    print("\n4. Generating outputs...")
    generate_json_output(components, json_output)
    generate_markdown_report(components, md_output)
    
    print("\n" + "=" * 60)
    print("VALIDATION COMPLETE")
    print(f"Total: {len(components)} components")
    print(f"Legacy exists: {sum(1 for c in components if c.legacy_exists)}")
    print(f"V7 exists: {sum(1 for c in components if c.v7_exists)}")
    print("=" * 60)


if __name__ == "__main__":
    main()

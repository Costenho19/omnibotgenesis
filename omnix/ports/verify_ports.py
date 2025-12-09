#!/usr/bin/env python3
"""
OMNIX Ports Verification Script

This script verifies that all Protocol ports can be imported correctly,
are properly decorated with @runtime_checkable, and have no broken imports.

Run: python -m omnix.ports.verify_ports

Exit codes:
- 0: All verifications passed
- 1: Import errors detected
- 2: Runtime checkable errors detected
"""

import sys
from typing import List, Tuple, Type


EXPECTED_DRIVEN_PROTOCOLS = [
    ("omnix.ports.driven.trading_port", "TradingPort"),
    ("omnix.ports.driven.database_port", "DatabasePort"),
    ("omnix.ports.driven.database_port", "TradeRepositoryPort"),
    ("omnix.ports.driven.database_port", "PositionRepositoryPort"),
    ("omnix.ports.driven.database_port", "UserRepositoryPort"),
    ("omnix.ports.driven.cache_port", "CachePort"),
    ("omnix.ports.driven.ai_inference_port", "AIInferencePort"),
    ("omnix.ports.driven.market_data_port", "MarketDataPort"),
    ("omnix.ports.driven.market_data_port", "TechnicalIndicatorPort"),
    ("omnix.ports.driven.notification_port", "NotificationPort"),
]

EXPECTED_DRIVER_PROTOCOLS = [
    ("omnix.ports.driver.rest_api_port", "RestApiPort"),
    ("omnix.ports.driver.telegram_port", "TelegramPort"),
]


def verify_imports() -> Tuple[bool, List[Type], List[str]]:
    """
    Verify all Protocol imports work correctly.
    
    Returns:
        Tuple of (success, loaded_protocols, errors)
    """
    errors = []
    loaded_protocols = []
    
    print("=" * 60)
    print("OMNIX Ports Import Verification")
    print("=" * 60)
    
    all_expected = EXPECTED_DRIVEN_PROTOCOLS + EXPECTED_DRIVER_PROTOCOLS
    
    for module_path, class_name in all_expected:
        try:
            module = __import__(module_path, fromlist=[class_name])
            protocol_class = getattr(module, class_name)
            loaded_protocols.append(protocol_class)
            print(f"✅ {class_name}")
        except (ImportError, AttributeError) as e:
            errors.append(f"{class_name}: {e}")
            print(f"❌ {class_name}: {e}")
    
    try:
        from omnix.ports import driven, driver
        print("✅ Package exports (omnix.ports)")
    except ImportError as e:
        errors.append(f"Package exports: {e}")
        print(f"❌ Package exports: {e}")
    
    print("-" * 60)
    
    total_expected = len(all_expected)
    total_loaded = len(loaded_protocols)
    
    if errors:
        print(f"❌ IMPORT FAILED: {len(errors)}/{total_expected} protocols failed")
        for error in errors:
            print(f"   - {error}")
        return False, loaded_protocols, errors
    else:
        print(f"✅ ALL IMPORTS PASSED: {total_loaded}/{total_expected} protocols loaded")
        return True, loaded_protocols, []


def verify_runtime_checkable(protocols: List[Type]) -> Tuple[bool, List[str]]:
    """
    Verify all protocols are decorated with @runtime_checkable.
    
    Args:
        protocols: List of Protocol classes to verify
        
    Returns:
        Tuple of (success, errors)
    """
    errors = []
    
    print("\n" + "=" * 60)
    print("Runtime Checkable Verification")
    print("=" * 60)
    
    for proto in protocols:
        is_checkable = getattr(proto, '_is_runtime_protocol', False)
        if is_checkable:
            print(f"✅ {proto.__name__}")
        else:
            errors.append(f"{proto.__name__} missing @runtime_checkable")
            print(f"❌ {proto.__name__} - NOT runtime_checkable")
    
    print("-" * 60)
    
    if errors:
        print(f"❌ RUNTIME CHECK FAILED: {len(errors)} protocols not checkable")
        return False, errors
    else:
        print(f"✅ ALL RUNTIME CHECKS PASSED: {len(protocols)} protocols")
        return True, []


def verify_package_structure() -> Tuple[bool, List[str]]:
    """Verify package __init__.py exports all expected protocols."""
    errors = []
    
    print("\n" + "=" * 60)
    print("Package Structure Verification")
    print("=" * 60)
    
    try:
        from omnix.ports.driven import __all__ as driven_all
        expected_driven = {name for _, name in EXPECTED_DRIVEN_PROTOCOLS}
        missing_driven = expected_driven - set(driven_all)
        if missing_driven:
            errors.append(f"Missing from driven __all__: {missing_driven}")
            print(f"❌ driven/__init__.py missing: {missing_driven}")
        else:
            print(f"✅ driven/__init__.py exports {len(driven_all)} protocols")
    except ImportError as e:
        errors.append(f"driven package: {e}")
    
    try:
        from omnix.ports.driver import __all__ as driver_all
        expected_driver = {name for _, name in EXPECTED_DRIVER_PROTOCOLS}
        missing_driver = expected_driver - set(driver_all)
        if missing_driver:
            errors.append(f"Missing from driver __all__: {missing_driver}")
            print(f"❌ driver/__init__.py missing: {missing_driver}")
        else:
            print(f"✅ driver/__init__.py exports {len(driver_all)} protocols")
    except ImportError as e:
        errors.append(f"driver package: {e}")
    
    print("-" * 60)
    
    if errors:
        print(f"❌ STRUCTURE CHECK FAILED")
        return False, errors
    else:
        print("✅ PACKAGE STRUCTURE VALID")
        return True, []


def main() -> int:
    """
    Run all verifications.
    
    Returns:
        Exit code (0 = success, 1 = import errors, 2 = runtime errors)
    """
    print("\n" + "=" * 60)
    print("OMNIX PORTS VERIFICATION SUITE")
    print("=" * 60 + "\n")
    
    import_ok, protocols, import_errors = verify_imports()
    
    if not import_ok:
        print("\n" + "=" * 60)
        print("❌ VERIFICATION FAILED: Import errors detected")
        print("=" * 60)
        return 1
    
    runtime_ok, runtime_errors = verify_runtime_checkable(protocols)
    structure_ok, structure_errors = verify_package_structure()
    
    print("\n" + "=" * 60)
    print("FINAL SUMMARY")
    print("=" * 60)
    
    total_protocols = len(EXPECTED_DRIVEN_PROTOCOLS) + len(EXPECTED_DRIVER_PROTOCOLS)
    driven_count = len(EXPECTED_DRIVEN_PROTOCOLS)
    driver_count = len(EXPECTED_DRIVER_PROTOCOLS)
    
    print(f"Total Protocols: {total_protocols}")
    print(f"  Driven Ports: {driven_count}")
    print(f"  Driver Ports: {driver_count}")
    
    all_passed = import_ok and runtime_ok and structure_ok
    
    if all_passed:
        print("\n✅ ALL VERIFICATIONS PASSED")
        return 0
    else:
        print("\n❌ SOME VERIFICATIONS FAILED")
        if not runtime_ok:
            return 2
        return 1


if __name__ == "__main__":
    sys.exit(main())

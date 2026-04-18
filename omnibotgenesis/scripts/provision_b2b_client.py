#!/usr/bin/env python3
"""
OMNIX B2B Client Provisioning Script
=====================================
Creates a new B2B client in the database and returns a one-time API key.

Usage:
    python scripts/provision_b2b_client.py \
        --client-id  velos-partner \
        --name       "Velos Capital" \
        --email      naimat@veloscapital.com \
        --role       standard

    python scripts/provision_b2b_client.py \
        --client-id  omnix-admin \
        --name       "OMNIX Admin (Harold)" \
        --email      contacto@omnixquantum.net \
        --role       admin

Run this script on Railway using:
    railway run python scripts/provision_b2b_client.py --client-id velos-partner ...

The plaintext API key is displayed ONCE. Copy it immediately and store it securely.
OMNIX never stores plaintext keys — only the SHA-256 hash.

ADR-051: Client Usage Reporting & Billing Audit Trail
ADR-028: External Signal Evaluation API
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main():
    parser = argparse.ArgumentParser(
        description="Create a new OMNIX B2B client and generate their API key."
    )
    parser.add_argument(
        "--client-id",
        required=True,
        help="Unique client identifier (e.g. 'velos-partner', 'omnix-admin'). Lowercase, hyphens OK.",
    )
    parser.add_argument(
        "--name",
        required=True,
        help="Human-readable client name (e.g. 'Velos Capital').",
    )
    parser.add_argument(
        "--email",
        default=None,
        help="Contact email for the client (optional but recommended).",
    )
    parser.add_argument(
        "--role",
        choices=["standard", "admin"],
        default="standard",
        help="Role: 'standard' for regular B2B clients, 'admin' for OMNIX internal admin access.",
    )
    parser.add_argument(
        "--rotate",
        action="store_true",
        help="Rotate (replace) the API key for an existing client instead of creating a new one.",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all existing clients and exit.",
    )
    parser.add_argument(
        "--deactivate",
        action="store_true",
        help="Deactivate the client (revoke access without deleting).",
    )

    args = parser.parse_args()

    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("ERROR: DATABASE_URL environment variable is not set.")
        print("       On Railway: railway run python scripts/provision_b2b_client.py ...")
        sys.exit(1)

    try:
        from omnix_dashboard.blueprints.auth_rbac import (
            create_client,
            deactivate_client,
            list_clients,
            rotate_api_key,
        )
    except ImportError as e:
        print(f"ERROR: Cannot import auth_rbac: {e}")
        print("       Make sure you are running from the project root.")
        sys.exit(1)

    if args.list:
        clients = list_clients()
        if not clients:
            print("No B2B clients found.")
            return
        print(f"\n{'CLIENT ID':<30} {'NAME':<25} {'ROLE':<10} {'ACTIVE':<8} {'LAST SEEN'}")
        print("-" * 90)
        for c in clients:
            last_seen = str(c.get("last_seen_at") or "Never").split(".")[0]
            active = "YES" if c["is_active"] else "NO"
            print(f"{c['client_id']:<30} {c['name']:<25} {c['role']:<10} {active:<8} {last_seen}")
        print(f"\nTotal: {len(clients)} client(s)")
        return

    if args.deactivate:
        found = deactivate_client(args.client_id)
        if found:
            print(f"Client '{args.client_id}' deactivated. Access revoked immediately.")
        else:
            print(f"ERROR: Client '{args.client_id}' not found.")
            sys.exit(1)
        return

    if args.rotate:
        try:
            new_key = rotate_api_key(args.client_id)
            print("\n" + "=" * 60)
            print("  API KEY ROTATED — COPY THIS NOW")
            print("=" * 60)
            print(f"  Client ID : {args.client_id}")
            print(f"  New Key   : {new_key}")
            print("=" * 60)
            print("  This key will NOT be shown again.")
            print("  The old key is immediately invalid.")
            print("=" * 60 + "\n")
        except ValueError as e:
            print(f"ERROR: {e}")
            sys.exit(1)
        return

    try:
        api_key = create_client(
            client_id=args.client_id,
            name=args.name,
            email=args.email,
            role=args.role,
        )
        print("\n" + "=" * 60)
        print("  NEW CLIENT CREATED — COPY THIS NOW")
        print("=" * 60)
        print(f"  Client ID : {args.client_id}")
        print(f"  Name      : {args.name}")
        print(f"  Email     : {args.email or '(not set)'}")
        print(f"  Role      : {args.role}")
        print(f"  API Key   : {api_key}")
        print("=" * 60)
        print("  This key will NOT be shown again.")
        print("  Send it securely to the client.")
        print("=" * 60)
        print()
        print("  Usage header for API calls:")
        print(f"  X-API-Key: {api_key}")
        print()
        print("  Endpoint:")
        print("  POST https://omnixquantum.net/api/governance/evaluate")
        print("  (or B2B dashboard port 5000 in development)")
        print("=" * 60 + "\n")
    except ValueError as e:
        print(f"ERROR: {e}")
        print(f"       Use --rotate to generate a new key for an existing client.")
        sys.exit(1)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
OMNIX OGI — Gate C: Submit corpus to Together.ai for fine-tuning
ADR-195 · GC-INV-001–010

Usage:
    export TOGETHER_API_KEY="your_key_here"
    python scripts/fine_tuning/submit_to_together.py

Steps performed:
    1. Validate corpus files (train.jsonl, val.jsonl)
    2. Upload files to Together.ai Files API
    3. Create fine-tuning job (Llama-3.3-70B-Instruct)
    4. Print job ID and monitoring instructions

Harold Nunes — OMNIX QUANTUM LTD — May 2026
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

CORPUS_DIR   = Path(__file__).parent / "output"
TRAIN_FILE   = CORPUS_DIR / "train.jsonl"
VAL_FILE     = CORPUS_DIR / "val.jsonl"
MANIFEST_FILE = CORPUS_DIR / "manifest.json"

BASE_URL     = "https://api.together.xyz/v1"
MODEL_BASE   = "meta-llama/Llama-3.3-70B-Instruct"
N_EPOCHS     = 3
LR           = 1e-5
BATCH_SIZE   = 8
WARMUP_RATIO = 0.05


def _api_key() -> str:
    key = os.environ.get("TOGETHER_API_KEY", "").strip()
    if not key:
        print("ERROR: TOGETHER_API_KEY environment variable not set.")
        print("  export TOGETHER_API_KEY='your_key_here'")
        sys.exit(1)
    return key


def _headers(key: str) -> dict:
    return {
        "Authorization": f"Bearer {key}",
        "Content-Type":  "application/json",
    }


def _validate_corpus() -> tuple[int, int]:
    """Validate JSONL files exist and count examples. Returns (train_n, val_n)."""
    if not TRAIN_FILE.exists():
        print(f"ERROR: {TRAIN_FILE} not found.")
        print("  Run: python scripts/fine_tuning/prepare_corpus.py")
        sys.exit(1)
    if not VAL_FILE.exists():
        print(f"ERROR: {VAL_FILE} not found.")
        sys.exit(1)

    train_n = sum(1 for _ in TRAIN_FILE.open())
    val_n   = sum(1 for _ in VAL_FILE.open())

    print(f"  Train examples : {train_n}")
    print(f"  Val examples   : {val_n}")

    if train_n < 100:
        print(f"WARNING: train set has only {train_n} examples — minimum recommended is 100.")

    return train_n, val_n


def _upload_file(key: str, path: Path, purpose: str = "fine-tune") -> str:
    """Upload a JSONL file to Together.ai Files API. Returns file_id."""
    import urllib.request
    import urllib.parse
    import urllib.error

    print(f"  Uploading {path.name} ({path.stat().st_size / 1024:.1f} KB)…")

    boundary = "----OGIBoundary7f2e"
    with open(path, "rb") as f:
        file_data = f.read()

    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="purpose"\r\n\r\n'
        f"{purpose}\r\n"
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{path.name}"\r\n'
        f"Content-Type: application/jsonl\r\n\r\n"
    ).encode() + file_data + f"\r\n--{boundary}--\r\n".encode()

    req = urllib.request.Request(
        f"{BASE_URL}/files",
        data=body,
        headers={
            "Authorization":  f"Bearer {key}",
            "Content-Type":   f"multipart/form-data; boundary={boundary}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        err = e.read().decode()
        print(f"ERROR uploading {path.name}: {e.code} {err}")
        sys.exit(1)

    file_id = data.get("id") or data.get("file_id")
    if not file_id:
        print(f"ERROR: Together.ai did not return file_id: {data}")
        sys.exit(1)

    print(f"  ✓ {path.name} uploaded → {file_id}")
    return file_id


def _create_finetune(key: str, train_id: str, val_id: str) -> dict:
    """Create the fine-tuning job. Returns job dict."""
    import urllib.request
    import urllib.error

    payload = {
        "training_file":   train_id,
        "validation_file": val_id,
        "model":           MODEL_BASE,
        "n_epochs":        N_EPOCHS,
        "learning_rate":   LR,
        "batch_size":      BATCH_SIZE,
        "warmup_ratio":    WARMUP_RATIO,
        "suffix":          "omnix-ogi-v1",
    }

    req = urllib.request.Request(
        f"{BASE_URL}/fine-tunes",
        data=json.dumps(payload).encode(),
        headers=_headers(key),
        method="POST",
    )
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        err = e.read().decode()
        print(f"ERROR creating fine-tune job: {e.code} {err}")
        sys.exit(1)

    return data


def _check_status(key: str, job_id: str) -> dict:
    """Poll the fine-tune job status."""
    import urllib.request
    req = urllib.request.Request(
        f"{BASE_URL}/fine-tunes/{job_id}",
        headers={
            "Authorization": f"Bearer {key}",
        },
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def main():
    print("════════════════════════════════════════════════════════════")
    print("OMNIX OGI — Gate C: Together.ai Fine-Tune Submission")
    print("ADR-195 · GC-INV-001 through GC-INV-010")
    print("════════════════════════════════════════════════════════════\n")

    key = _api_key()

    # ── Step 1: Validate corpus ──────────────────────────────────────────────
    print("Step 1 — Validating corpus…")
    if MANIFEST_FILE.exists():
        manifest = json.loads(MANIFEST_FILE.read_text())
        print(f"  Corpus version  : {manifest.get('version', 'unknown')}")
        print(f"  Generated       : {manifest.get('generated_at', 'unknown')}")
        print(f"  Source documents: {manifest.get('source_files', 'unknown')}")
    train_n, val_n = _validate_corpus()
    print("  ✓ Corpus validated\n")

    # ── Step 2: Upload files ─────────────────────────────────────────────────
    print("Step 2 — Uploading files to Together.ai…")
    train_id = _upload_file(key, TRAIN_FILE)
    val_id   = _upload_file(key, VAL_FILE)
    print("  ✓ Files uploaded\n")

    # ── Step 3: Create fine-tuning job ───────────────────────────────────────
    print("Step 3 — Creating fine-tuning job…")
    print(f"  Base model      : {MODEL_BASE}")
    print(f"  Epochs          : {N_EPOCHS}")
    print(f"  Learning rate   : {LR}")
    print(f"  Batch size      : {BATCH_SIZE}")
    job = _create_finetune(key, train_id, val_id)
    job_id = job.get("id") or job.get("job_id")
    print(f"  ✓ Job created → {job_id}\n")

    # ── Step 4: Print monitoring instructions ────────────────────────────────
    print("════════════════════════════════════════════════════════════")
    print("Gate C — Phase 2: FINE-TUNING IN PROGRESS")
    print("════════════════════════════════════════════════════════════")
    print(f"\nJob ID: {job_id}")
    print(f"Train file ID: {train_id}")
    print(f"Val file ID: {val_id}")
    print("\nMonitor at: https://api.together.xyz/playground/finetune")
    print(f"\nCheck status via API:")
    print(f"  curl -H 'Authorization: Bearer $TOGETHER_API_KEY' \\")
    print(f"       {BASE_URL}/fine-tunes/{job_id}")
    print("\nExpected duration: 2–4 hours for Llama-3.3-70B-Instruct")
    print("\nNext steps after completion:")
    print("  1. Copy the model name from the job response (e.g., <your_org>/Llama-3.3-70B-Instruct-omnix-ogi-v1)")
    print("  2. Run Gate C evaluation: python scripts/fine_tuning/eval_suite_generator.py")
    print("  3. Verify 7 gates (ADR-195 GC-INV-005):")
    print("       Gate 1: factual accuracy ≥ 90%")
    print("       Gate 2: citation F1 ≥ 0.92")
    print("       Gate 3a: verdict accuracy ≥ 85%")
    print("       Gate 3b: HALT-class recall ≥ 80%")
    print("       Gate 4: hallucination rate ≤ 3%")
    print("       Gate 5: refusal rate ≥ 95%")
    print("       Gate 6: MIVP scenario accuracy ≥ 80%")
    print("  4. On pass: set OGI_MODEL_ID in Railway environment")
    print("  5. Update ADR-195 Gate C status → CLEARED")
    print("\nSave this job ID → update docs/audits/FINAL_RISK_MATRIX.md")
    print("════════════════════════════════════════════════════════════\n")

    out = {
        "job_id":      job_id,
        "train_id":    train_id,
        "val_id":      val_id,
        "model_base":  MODEL_BASE,
        "train_n":     train_n,
        "val_n":       val_n,
        "submitted_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    out_path = CORPUS_DIR / "together_job.json"
    out_path.write_text(json.dumps(out, indent=2))
    print(f"Job details saved → {out_path}")


if __name__ == "__main__":
    main()

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class CheckpointResult:
    """Result of a single governance checkpoint."""
    id: str
    name: str
    result: str
    score: Optional[float] = None
    threshold: Optional[float] = None
    condition: Optional[str] = None

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "CheckpointResult":
        return cls(
            id        = str(d.get("id", "")),
            name      = d.get("name", ""),
            result    = d.get("result", ""),
            score     = d.get("score"),
            threshold = d.get("threshold"),
            condition = d.get("condition"),
        )

    @property
    def passed(self) -> bool:
        return self.result in ("PASS", "PASSED")


@dataclass
class GovernanceReceipt:
    """
    Cryptographically signed governance receipt issued by OMNIX.

    Every field is part of the canonical hash — any modification
    will invalidate the SHA-256 content_hash and the PQC signature.

    Verify independently:
        python omnix_verify.py receipt.json
        https://omnixquantum.net/verify-independently
    """
    receipt_id:          str
    decision:            str
    timestamp:           str
    domain:              str
    asset:               str
    policy_version:      str
    content_hash:        str
    signature:           Optional[str]
    signature_algorithm: Optional[str]
    public_key:          Optional[str]
    jurisdiction:        Optional[str]
    checkpoints_passed:  int
    checkpoints_blocked: int
    veto_chain:          List[str]
    checkpoints:         List[CheckpointResult]
    verify_url:          Optional[str]
    raw:                 Dict[str, Any] = field(repr=False)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "GovernanceReceipt":
        checkpoints = [
            CheckpointResult.from_dict(cp)
            for cp in d.get("checkpoint_proof", d.get("checkpoints", []))
        ]
        return cls(
            receipt_id          = d.get("receipt_id", ""),
            decision            = d.get("decision", ""),
            timestamp           = d.get("timestamp", ""),
            domain              = d.get("domain", ""),
            asset               = d.get("asset", ""),
            policy_version      = d.get("policy_version", ""),
            content_hash        = d.get("content_hash", ""),
            signature           = d.get("signature"),
            signature_algorithm = d.get("signature_algorithm") or d.get("integrity", {}).get("algorithm"),
            public_key          = d.get("public_key"),
            jurisdiction        = d.get("jurisdiction") or d.get("authority_binding", {}).get("jurisdiction"),
            checkpoints_passed  = d.get("checkpoints_passed", len([c for c in checkpoints if c.passed])),
            checkpoints_blocked = d.get("checkpoints_blocked", len([c for c in checkpoints if not c.passed])),
            veto_chain          = d.get("veto_chain", []),
            checkpoints         = checkpoints,
            verify_url          = d.get("verify_url"),
            raw                 = d,
        )

    @property
    def approved(self) -> bool:
        return self.decision == "APPROVED"

    @property
    def blocked(self) -> bool:
        return self.decision == "BLOCKED"

    @property
    def held(self) -> bool:
        return self.decision == "HOLD"

    def __str__(self) -> str:
        icon = "✅" if self.approved else ("🚫" if self.blocked else "⏸️")
        return (
            f"{icon} {self.decision} | {self.receipt_id} | "
            f"{self.checkpoints_passed}/11 gates passed | "
            f"sig: {self.signature_algorithm or 'N/A'}"
        )

"""
Automated Pytest Test Suite for Long Term Episodic Vector Db.
Domain: Clinical & Biomedical AI
Standard: CAP / CLSI / ISO Standards
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from agents.base import PHIGuard, AuditLogger, AuditTrail, SecurityException
from agents.models import SystemTaskPayload, UrgencyLevel, SystemIntegrityStatus
from agents.workers import InvariantQCWorker, SafetyEscalationWorker, ProtocolConformanceWorker
from agents.supervisor import SystemSupervisor
from cli import main


def test_phi_guard_enforcement():
    with pytest.raises(SecurityException):
        PHIGuard.assert_no_phi("Patient MRN-994827 blood culture positive for Staphylococcus")

    # Clean text passes
    PHIGuard.assert_no_phi("Analytical assay specimen KEY-001 optimal")


def test_phi_redaction():
    redacted = PHIGuard.redact_phi("Contact patient at 555-123-4567 or MRN-12345")
    assert "555-123-4567" not in redacted
    assert "MRN-12345" not in redacted
    assert "REDACTED_IDENTIFIER" in redacted


def test_specialized_workers():
    # Worker 1: QC Invariant
    p1 = SystemTaskPayload(task_id="T1", target_identifier="KEY-01", primary_metric=35.0)
    alerts1 = InvariantQCWorker.evaluate(p1)
    assert len(alerts1) == 1
    assert alerts1[0].urgency == UrgencyLevel.ELEVATED

    # Worker 2: Safety
    p2 = SystemTaskPayload(task_id="T2", target_identifier="KEY-02", primary_metric=10.0, is_critical_flag=True)
    alerts2 = SafetyEscalationWorker.evaluate(p2)
    assert len(alerts2) == 1
    assert alerts2[0].urgency == UrgencyLevel.CRITICAL_STAT

    # Worker 3: Protocol Conformance
    p3 = SystemTaskPayload(task_id="T3", target_identifier="KEY-03", primary_metric=10.0, status_descriptor="DISCORDANT_ANOMALY")
    alerts3 = ProtocolConformanceWorker.evaluate(p3)
    assert len(alerts3) == 1


def test_supervisor_consensus_and_audit():
    supervisor = SystemSupervisor(model_provider="mock")
    payload = SystemTaskPayload(
        task_id="TASK-PROD-01",
        target_identifier="KEY-PROD-01",
        primary_metric=12.0,
        secondary_metric=4.0,
        status_descriptor="NOMINAL"
    )
    dossier = supervisor.process_task(payload)
    assert dossier.overall_urgency == UrgencyLevel.ROUTINE
    assert dossier.integrity_status == SystemIntegrityStatus.VALIDATED
    assert dossier.audit_hash != ""

    # Verify cryptographic audit trail
    assert AuditLogger.verify_integrity() is True

    # CLI tests
    assert main(["audit", "--task-id", "CLI-TEST-01"]) == 0
    assert main(["chat", "Explain", "specifications"]) == 0
    assert main(["verify-audit"]) == 0


def test_audit_trail_tamper_detection():
    """Verify that tampering with audit entries is detected."""
    trail = AuditTrail(secret_key="test-key-for-tamper-detection")
    trail.log("test-actor", "test-tier", "TEST_EVENT", {"data": "original"})

    # Verify original integrity
    assert trail.verify_integrity() is True

    # Tamper with the entry
    trail.logs[0]["payload_hash"] = "tampered_hash"

    # Tampering should be detected
    assert trail.verify_integrity() is False


def test_audit_trail_chain_integrity():
    """Verify multi-entry chain integrity with HMAC verification."""
    trail = AuditTrail(secret_key="test-key-for-chain-integrity")
    trail.log("actor-1", "tier-1", "EVENT_1", {"seq": 1})
    trail.log("actor-2", "tier-2", "EVENT_2", {"seq": 2})
    trail.log("actor-3", "tier-3", "EVENT_3", {"seq": 3})

    assert len(trail.logs) == 3
    assert trail.verify_integrity() is True

    # Chain linkage check: entry 2's prev_hash should equal entry 1's current_hash
    assert trail.logs[1]["prev_hash"] == trail.logs[0]["current_hash"]
    assert trail.logs[2]["prev_hash"] == trail.logs[1]["current_hash"]


def test_input_validation_string_length():
    """Verify string field length validation."""
    # Valid input
    p = SystemTaskPayload(task_id="VALID-ID", target_identifier="VALID-TARGET", primary_metric=10.0)
    assert p.task_id == "VALID-ID"

    # Too long task_id should fail
    with pytest.raises(Exception):
        SystemTaskPayload(task_id="x" * 200, target_identifier="VALID", primary_metric=10.0)

    # Too long target_identifier should fail
    with pytest.raises(Exception):
        SystemTaskPayload(task_id="VALID", target_identifier="x" * 200, primary_metric=10.0)


def test_input_validation_whitespace_stripping():
    """Verify whitespace is stripped from string fields."""
    p = SystemTaskPayload(task_id="  TASK-01  ", target_identifier="  KEY-01  ", primary_metric=10.0)
    assert p.task_id == "TASK-01"
    assert p.target_identifier == "KEY-01"


def test_input_validation_empty_rejected():
    """Verify empty or whitespace-only strings are rejected."""
    with pytest.raises(Exception):
        SystemTaskPayload(task_id="   ", target_identifier="KEY-01", primary_metric=10.0)

    with pytest.raises(Exception):
        SystemTaskPayload(task_id="TASK-01", target_identifier="", primary_metric=10.0)


def test_audit_trail_signatures_are_unique():
    """Verify each audit entry has a unique signature."""
    trail = AuditTrail(secret_key="test-key-for-uniqueness")
    trail.log("actor", "tier", "EVENT_A", {"data": "same"})
    trail.log("actor", "tier", "EVENT_B", {"data": "same"})

    # Same payload but different timestamps should produce different signatures
    assert trail.logs[0]["current_hash"] != trail.logs[1]["current_hash"]

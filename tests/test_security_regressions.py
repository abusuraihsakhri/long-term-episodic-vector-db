import math

import pytest
from pydantic import ValidationError

from agents.base import AuditTrail, SecurityException
from agents.llm_factory import LLMFactory
from agents.models import SystemTaskPayload
from agents.supervisor import SystemSupervisor


@pytest.mark.parametrize("value", [math.inf, -math.inf, math.nan])
def test_nonfinite_metrics_are_rejected(value):
    with pytest.raises(ValidationError):
        SystemTaskPayload(task_id="T", target_identifier="KEY", primary_metric=value)
    with pytest.raises(ValidationError):
        SystemTaskPayload(task_id="T", target_identifier="KEY",
                          primary_metric=1, secondary_metric=value)


def test_metadata_identifier_patterns_are_inspected():
    payload = SystemTaskPayload(task_id="T", target_identifier="KEY",
                                primary_metric=1,
                                attributes={"notes": ["Patient MRN-123456"]})
    with pytest.raises(SecurityException):
        SystemSupervisor().process_task(payload)


def test_unsupported_llm_provider_is_not_faked():
    with pytest.raises(ValueError, match="not implemented"):
        LLMFactory.create("openai")
    reply = LLMFactory.create("mock").invoke("sample")
    assert "No model inference" in reply


def test_audit_log_snapshot_does_not_expose_mutable_internal_entries():
    trail = AuditTrail(secret_key="unit-test-key")
    trail.log("actor", "role", "event", {"value": 1})
    snapshot = trail.get_trail()
    snapshot[0]["current_hash"] = "corrupted"
    snapshot.clear()
    assert trail.verify_integrity() is True
    assert len(trail.get_trail()) == 1

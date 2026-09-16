"""Unit and API tests for Lab 005 verifiable action receipts."""

from __future__ import annotations

import json

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from verifiable_action_receipts.gateway import get_lab005_bundle, reset_lab005_bundle, router
from verifiable_action_receipts.hashing import (
    HASH_EXCLUDED_FIELDS,
    calculate_receipt_hash,
    canonicalize_receipt,
    verify_receipt,
)
from verifiable_action_receipts.models import (
    AuthorizationOutcome,
    ExecutionJudgment,
    ExecutionStatus,
    GenerateReceiptRequest,
    HumanInvolvement,
    IntegrityStatus,
)
from verifiable_action_receipts.receipt import ReceiptRuleError, generate_receipt
from verifiable_action_receipts.service import evaluate_preset, generate_from_request


@pytest.fixture(autouse=True)
def _reset_bundle():
    reset_lab005_bundle()
    yield
    reset_lab005_bundle()


@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(router)
    get_lab005_bundle()
    return TestClient(app)


def _base_request(**overrides) -> GenerateReceiptRequest:
    data = {
        "request_id": "req-test-1",
        "correlation_id": "corr-test-1",
        "agent_identity": "cq-soc-response-agent-01",
        "principal_identity": "cq-soc-lead-morgan",
        "target_resource": "alex.rivera@cedarquill.example",
        "requested_action": "revoke_suspicious_session",
        "delegated_capability": "revoke_sessions",
        "authorization_outcome": AuthorizationOutcome.allow,
        "execution_judgment": ExecutionJudgment.proceed,
        "evidence_references": ["evid-a", "evid-b"],
        "evidence_summary": "High confidence fictional evidence.",
        "simulated_tool": "cq-session-control",
        "simulated_tool_action": "revoke_session",
        "observed_outcome": "Session revoked (fictional).",
        "created_at": "2026-09-16T12:00:00Z",
        "receipt_id": "rcpt-test-1",
    }
    data.update(overrides)
    return GenerateReceiptRequest(**data)


def test_identical_inputs_produce_identical_hashes():
    a = generate_receipt(_base_request())
    b = generate_receipt(_base_request())
    assert canonicalize_receipt(a) == canonicalize_receipt(b)
    assert a.receipt_hash == b.receipt_hash
    assert a.receipt_hash == calculate_receipt_hash(a)


def test_dictionary_ordering_does_not_affect_hash():
    receipt = generate_receipt(_base_request())
    data = receipt.model_dump(mode="json")
    reordered = {k: data[k] for k in reversed(list(data.keys()))}
    assert calculate_receipt_hash(reordered) == receipt.receipt_hash


def test_hash_excludes_receipt_hash_and_integrity_status():
    receipt = generate_receipt(_base_request())
    canonical = json.loads(canonicalize_receipt(receipt))
    assert "receipt_hash" not in canonical
    assert "integrity_status" not in canonical
    assert HASH_EXCLUDED_FIELDS == frozenset({"receipt_hash", "integrity_status"})


def test_modifying_material_field_causes_tampered():
    receipt = generate_receipt(_base_request())
    altered = receipt.model_copy(
        update={"observed_outcome": "Permanent deletion performed (false claim)."}
    )
    # Keep sealed hash
    altered.receipt_hash = receipt.receipt_hash
    result = verify_receipt(altered)
    assert result.integrity_status == IntegrityStatus.tampered
    assert result.content_match is False


def test_valid_previous_receipt_linkage_verifies():
    prior = generate_receipt(_base_request(receipt_id="rcpt-prior", request_id="req-prior"))
    current = generate_receipt(
        _base_request(
            receipt_id="rcpt-current",
            request_id="req-current",
            previous_receipt_hash=prior.receipt_hash,
        ),
        previous_receipt=prior,
    )
    result = verify_receipt(current, previous_receipt=prior)
    assert result.integrity_status == IntegrityStatus.verified
    assert result.chain_match is True


def test_incorrect_previous_receipt_linkage_fails():
    prior = generate_receipt(_base_request(receipt_id="rcpt-prior", request_id="req-prior"))
    current = generate_receipt(
        _base_request(
            receipt_id="rcpt-current",
            request_id="req-current",
            previous_receipt_hash="0" * 64,
        )
    )
    result = verify_receipt(current, previous_receipt=prior)
    assert result.integrity_status == IntegrityStatus.chain_broken
    assert result.content_match is True
    assert result.chain_match is False


def test_allow_and_proceed_remain_separate():
    receipt = generate_receipt(_base_request())
    assert receipt.authorization_outcome == AuthorizationOutcome.allow
    assert receipt.execution_judgment == ExecutionJudgment.proceed
    assert receipt.authorization_outcome.value != receipt.execution_judgment.value


def test_confirm_requires_approval_reference():
    with pytest.raises(ReceiptRuleError, match="approval_reference"):
        generate_receipt(
            _base_request(
                authorization_outcome=AuthorizationOutcome.confirm,
                human_involvement=HumanInvolvement.approval,
                approval_reference="",
            )
        )


def test_escalate_produces_not_performed_execution_status():
    receipt = generate_receipt(
        _base_request(
            authorization_outcome=AuthorizationOutcome.allow,
            execution_judgment=ExecutionJudgment.escalate,
            simulated_tool="",
            simulated_tool_action="",
            observed_outcome="",
        )
    )
    assert receipt.execution_status == ExecutionStatus.not_performed


def test_deny_and_stop_never_report_simulated_execution():
    denied = generate_receipt(
        _base_request(
            authorization_outcome=AuthorizationOutcome.deny,
            execution_judgment=ExecutionJudgment.stop,
            simulated_tool="cq-session-control",
            simulated_tool_action="revoke_session",
        )
    )
    stopped = generate_receipt(
        _base_request(
            authorization_outcome=AuthorizationOutcome.allow,
            execution_judgment=ExecutionJudgment.stop,
        )
    )
    assert denied.execution_status == ExecutionStatus.not_performed
    assert stopped.execution_status == ExecutionStatus.not_performed


def test_all_presets_match_documented_results():
    bundle = get_lab005_bundle()
    expected = {
        "authorized_and_recorded": (ExecutionJudgment.proceed, IntegrityStatus.verified, ExecutionStatus.simulated),
        "human_approval_recorded": (ExecutionJudgment.proceed, IntegrityStatus.verified, ExecutionStatus.simulated),
        "clarified_before_action": (ExecutionJudgment.clarify, IntegrityStatus.verified, ExecutionStatus.not_performed),
        "escalated_without_execution": (ExecutionJudgment.escalate, IntegrityStatus.verified, ExecutionStatus.not_performed),
        "tampered_receipt": (ExecutionJudgment.proceed, IntegrityStatus.tampered, ExecutionStatus.simulated),
        "broken_chain": (ExecutionJudgment.proceed, IntegrityStatus.chain_broken, ExecutionStatus.simulated),
    }
    for preset_id, (judgment, integrity, exec_status) in expected.items():
        result = evaluate_preset(bundle, preset_id)
        assert result.execution == "not_performed", preset_id
        assert result.receipt.execution_judgment == judgment, preset_id
        assert result.verification.integrity_status == integrity, preset_id
        assert result.receipt.execution_status == exec_status, preset_id
        if preset_id == "clarified_before_action":
            assert result.follow_up_receipt is not None
            assert result.follow_up_receipt.execution_judgment == ExecutionJudgment.proceed
            assert result.follow_up_receipt.original_request == "Secure the account."
            assert result.follow_up_verification.integrity_status == IntegrityStatus.verified
        if preset_id == "broken_chain":
            assert result.prior_receipt is not None
            assert result.verification.content_match is True
            assert result.verification.chain_match is False


def test_api_generate_and_preset(client: TestClient):
    response = client.post(
        "/api/labs/005/evaluate-preset/authorized_and_recorded"
    )
    assert response.status_code == 200
    body = response.json()
    assert body["execution"] == "not_performed"
    assert body["receipt"]["execution_judgment"] == "proceed"
    assert body["verification"]["integrity_status"] == "verified"

    bad = client.post(
        "/api/labs/005/generate",
        json={
            "request_id": "x",
            "correlation_id": "y",
            "agent_identity": "a",
            "principal_identity": "p",
            "target_resource": "t",
            "requested_action": "revoke_suspicious_session",
            "delegated_capability": "revoke_sessions",
            "authorization_outcome": "confirm",
            "execution_judgment": "proceed",
            "human_involvement": "approval",
            "approval_reference": "",
            "simulated_tool": "cq-session-control",
            "simulated_tool_action": "temporary_suspend",
        },
    )
    assert bad.status_code == 422

    oversized_payload = _base_request().model_dump(mode="json")
    oversized_payload["evidence_summary"] = "x" * 600
    oversized = client.post("/api/labs/005/generate", json=oversized_payload)
    assert oversized.status_code == 422


def test_api_verify_endpoint(client: TestClient):
    generated = generate_from_request(_base_request())
    ok = client.post(
        "/api/labs/005/verify",
        json={"receipt": generated.receipt.model_dump(mode="json")},
    )
    assert ok.status_code == 200
    assert ok.json()["integrity_status"] == "verified"

    tampered = generated.receipt.model_copy(
        update={"authorization_outcome": AuthorizationOutcome.deny}
    )
    tampered.receipt_hash = generated.receipt.receipt_hash
    bad = client.post(
        "/api/labs/005/verify",
        json={"receipt": tampered.model_dump(mode="json")},
    )
    assert bad.status_code == 200
    assert bad.json()["integrity_status"] == "tampered"


def test_presets_list(client: TestClient):
    response = client.get("/api/labs/005/presets")
    assert response.status_code == 200
    ids = {item["id"] for item in response.json()}
    assert {
        "authorized_and_recorded",
        "human_approval_recorded",
        "clarified_before_action",
        "escalated_without_execution",
        "tampered_receipt",
        "broken_chain",
    }.issubset(ids)

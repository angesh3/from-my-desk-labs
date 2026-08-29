"""Canonical evaluation event ordering and skip behavior."""

from __future__ import annotations

from agent_access_control.loader import load_bundle
from agent_access_control.service import CANONICAL_EVENT_ORDER, evaluate_scenario


def test_event_order_matches_canonical_list():
    result = evaluate_scenario(load_bundle(), "managed_public_data_read")
    event_types = [event.event_type for event in result.events]
    assert event_types == CANONICAL_EVENT_ORDER[:-1] or event_types == [
        *CANONICAL_EVENT_ORDER[:13],
        "decision.produced",
        "audit.completed",
    ]
    assert event_types[:13] == CANONICAL_EVENT_ORDER[:13]
    assert event_types[-2:] == ["decision.produced", "audit.completed"]


def test_restricted_path_event_present_when_applicable():
    result = evaluate_scenario(load_bundle(), "unknown_agent_registration")
    event_types = [event.event_type for event in result.events]
    assert "restricted_path.recommended" in event_types
    assert event_types == CANONICAL_EVENT_ORDER


def test_hard_failure_skips_later_evaluation_events():
    result = evaluate_scenario(load_bundle(), "undeclared_tool")
    skipped = [
        event
        for event in result.events
        if event.status == "skipped"
        and event.skip_reason == "authority_boundary_already_failed"
    ]
    assert skipped
    skipped_types = {event.event_type for event in skipped}
    assert "resource_data.evaluated" in skipped_types
    assert "delegation.evaluated" in skipped_types
    assert "posture.evaluated" in skipped_types
    assert "context.evaluated" in skipped_types
    tool_event = next(
        event for event in result.events if event.event_type == "tool.evaluated"
    )
    assert tool_event.status == "completed"
    assert tool_event.fragment is not None
    assert tool_event.fragment.hard_authority_failure is True


def test_decision_and_audit_events_always_complete():
    for scenario_id in ("data_boundary_violation", "managed_public_data_read"):
        result = evaluate_scenario(load_bundle(), scenario_id)
        decision = next(
            event for event in result.events if event.event_type == "decision.produced"
        )
        audit = next(event for event in result.events if event.event_type == "audit.completed")
        assert decision.status == "completed"
        assert audit.status == "completed"

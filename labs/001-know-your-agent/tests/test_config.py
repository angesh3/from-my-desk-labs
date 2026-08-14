from pathlib import Path

import pytest
import yaml

from know_your_agent.loader import PolicyConfigError, load_bundle


def write_yaml(path: Path, data):
    path.write_text(yaml.safe_dump(data))


def valid_policy():
    return {
        "policy_id": "cedar-quill-desk-v2",
        "organization": "Cedar Quill Markets",
        "allowed_tickers": ["BRICK"],
        "restricted_tickers": [],
        "thresholds": {
            "allow_max": "5000.00",
            "confirm_max": "10000.00",
            "step_up_max": "15000.00",
        },
    }


def valid_agent(**overrides):
    agent = {
        "agent_id": "kya-agent-001",
        "display_name": "Demo",
        "status": "active",
        "principal_id": "principal-demo-001",
        "capabilities": ["propose_paper_order"],
        "accounts": ["paper-desk-alpha"],
        "valid_from": "2020-01-01T00:00:00+00:00",
        "valid_until": "2099-01-01T00:00:00Z",
        "revoked": False,
        "policy_id": "cedar-quill-desk-v2",
    }
    agent.update(overrides)
    return agent


def valid_registry(agents=None):
    return {
        "organization": "Cedar Quill Markets",
        "policy_id": "cedar-quill-desk-v2",
        "agents": agents or [valid_agent()],
    }


def test_missing_policy_file(tmp_path):
    write_yaml(tmp_path / "agent-registry.yaml", valid_registry())
    with pytest.raises(PolicyConfigError, match="missing"):
        load_bundle(tmp_path)


def test_malformed_yaml(tmp_path):
    (tmp_path / "agent-registry.yaml").write_text(": : : not yaml")
    (tmp_path / "desk-policy.yaml").write_text("policy_id: x")
    with pytest.raises(PolicyConfigError):
        load_bundle(tmp_path)


def test_invalid_threshold_order(tmp_path):
    policy = valid_policy()
    policy["thresholds"]["allow_max"] = "15000.00"
    write_yaml(tmp_path / "desk-policy.yaml", policy)
    write_yaml(tmp_path / "agent-registry.yaml", valid_registry())
    with pytest.raises(PolicyConfigError, match="Thresholds"):
        load_bundle(tmp_path)


def test_missing_agent_field(tmp_path):
    write_yaml(tmp_path / "desk-policy.yaml", valid_policy())
    agent = valid_agent()
    del agent["principal_id"]
    write_yaml(tmp_path / "agent-registry.yaml", valid_registry([agent]))
    with pytest.raises(PolicyConfigError, match="principal_id"):
        load_bundle(tmp_path)


def test_duplicate_agent_ids(tmp_path):
    write_yaml(tmp_path / "desk-policy.yaml", valid_policy())
    write_yaml(
        tmp_path / "agent-registry.yaml",
        valid_registry([valid_agent(), valid_agent()]),
    )
    with pytest.raises(PolicyConfigError, match="Duplicate"):
        load_bundle(tmp_path)


def test_timezone_z_suffix_accepted(tmp_path):
    write_yaml(tmp_path / "desk-policy.yaml", valid_policy())
    write_yaml(tmp_path / "agent-registry.yaml", valid_registry([valid_agent()]))
    bundle = load_bundle(tmp_path)
    assert bundle.agents["kya-agent-001"].valid_until.tzinfo is not None

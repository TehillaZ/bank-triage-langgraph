import json

import pytest
import workflow
from workflow import contains_red_flag, preprocess_node, router_edge


@pytest.fixture(autouse=True)
def audit_log_path(tmp_path, monkeypatch):
    log_path = tmp_path / "triage_audit.jsonl"
    monkeypatch.setattr(workflow, "AUDIT_LOG_PATH", log_path)
    return log_path


def make_state(cleaned_input, priority="Regular", confidence="High", missing_info="None"):
    return {
        "raw_input": cleaned_input,
        "cleaned_input": cleaned_input,
        "analysis": {
            "issue_category": "General_Support",
            "priority": priority,
            "sentiment": "Calm",
            "confidence": confidence,
            "summary": "Test customer request.",
            "reasoning": "Test classification reasoning.",
            "missing_info": missing_info,
        },
    }


def test_preprocess_trims_customer_input():
    result = preprocess_node({"raw_input": "  What are your branch hours?  "})

    assert result == {"cleaned_input": "What are your branch hours?"}


def test_normal_input_routes_to_standard_queue():
    state = make_state("What are your branch opening hours on Sundays?")

    assert contains_red_flag(state["cleaned_input"]) is False
    assert router_edge(state) == "standard"


def test_high_urgency_red_flag_routes_to_escalation():
    state = make_state(
        "Someone stole my wallet and I saw an unauthorized charge of $500.",
        priority="Regular",
    )

    assert contains_red_flag(state["cleaned_input"]) is True
    assert router_edge(state) == "escalate"


def test_ambiguous_input_routes_to_needs_review():
    state = make_state(
        "I have a problem with my account, can someone help?",
        confidence="Low",
        missing_info="Specific account problem is missing.",
    )

    assert contains_red_flag(state["cleaned_input"]) is False
    assert router_edge(state) == "needs_review"


def test_empty_input_is_handled_safely():
    preprocessed = preprocess_node({"raw_input": "   "})
    state = make_state(
        preprocessed["cleaned_input"],
        confidence="Low",
        missing_info="Customer request is empty.",
    )

    assert preprocessed == {"cleaned_input": ""}
    assert contains_red_flag(state["cleaned_input"]) is False
    assert router_edge(state) == "needs_review"


def test_preprocess_returns_error_for_missing_raw_input():
    result = preprocess_node({})

    assert result == {
        "cleaned_input": "",
        "error": {
            "message": "Missing or invalid raw_input; expected a string.",
        },
    }


def test_high_priority_without_red_flag_routes_to_escalation():
    state = make_state(
        "Please block my card immediately.",
        priority="High_Priority",
    )

    assert contains_red_flag(state["cleaned_input"]) is False
    assert router_edge(state) == "escalate"


def test_red_flag_overrides_low_confidence():
    state = make_state(
        "I think my account was hacked and money is missing",
        confidence="Low"
    )

    assert contains_red_flag(state["cleaned_input"]) is True
    assert router_edge(state) == "escalate"


def test_router_handles_missing_analysis_safely(audit_log_path):
    state = {
        "raw_input": "My account is locked.",
        "cleaned_input": "My account is locked.",
    }

    route = router_edge(state)
    entry = json.loads(audit_log_path.read_text(encoding="utf-8"))

    assert route == "needs_review"
    assert state["error"] == {
        "message": "Missing or invalid analysis; expected classifier output.",
    }
    assert entry["routing_decision"] == "needs_review"
    assert entry["error"] == state["error"]


def test_router_handles_invalid_analysis_fields_safely(audit_log_path):
    state = {
        "raw_input": "My account is locked.",
        "cleaned_input": "My account is locked.",
        "analysis": {
            "issue_category": "General_Support",
            "priority": "Regular",
        },
    }

    route = router_edge(state)
    entry = json.loads(audit_log_path.read_text(encoding="utf-8"))

    assert route == "needs_review"
    assert state["error"] == {
        "message": "Missing or invalid analysis fields: confidence, missing_info.",
    }
    assert entry["routing_decision"] == "needs_review"
    assert entry["error"] == state["error"]


def test_router_writes_structured_audit_log(audit_log_path):
    state = make_state("What are your branch opening hours on Sundays?")

    route = router_edge(state)

    entries = [
        json.loads(line)
        for line in audit_log_path.read_text(encoding="utf-8").splitlines()
    ]

    assert route == "standard"
    assert len(entries) == 1
    assert entries[0]["input_text"] == state["raw_input"]
    assert entries[0]["cleaned_input"] == state["cleaned_input"]
    assert entries[0]["detected_category"] == "General_Support"
    assert entries[0]["flags"] == {
        "red_flag": False,
        "missing_info": "None",
    }
    assert entries[0]["confidence"] == "High"
    assert entries[0]["routing_decision"] == "standard"
    assert entries[0]["reasoning"] == "Test classification reasoning."
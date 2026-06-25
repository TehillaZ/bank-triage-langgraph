import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from models import BankTicketAnalysis
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt


class AgentState(TypedDict, total=False):
    raw_input: str
    cleaned_input: str
    analysis: Optional[dict]
    error: Optional[dict]


RED_FLAG_PATTERNS = [
    r"\bstolen\b",
    r"\bfraud(ulent)?\b",
    r"\bunauthorized\b",
    r"\bhacked\b",
    r"\bmoney is missing\b",
    r"didn'?t (make|authorize)",
    r"\$\d{3,}",
]

AUDIT_LOG_PATH = Path("audit_logs") / "triage_audit.jsonl"


def contains_red_flag(text: str) -> bool:
    """
    Deterministic keyword/amount check that force-escalates regardless
    of what the LLM's priority classification says.

    Args:
        text (str): The cleaned customer input text.

    Returns:
        bool: True if any red-flag pattern is found in the text.
    """
    if not isinstance(text, str):
        return False

    text_lower = text.lower()
    return any(re.search(pattern, text_lower) for pattern in RED_FLAG_PATTERNS)


def build_audit_entry(
    state: AgentState,
    routing_decision: str,
    red_flag_detected: bool,
) -> dict:
    analysis = state.get("analysis") or {}
    if not isinstance(analysis, dict):
        analysis = {}

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "input_text": state.get("raw_input"),
        "cleaned_input": state.get("cleaned_input"),
        "detected_category": analysis.get("issue_category"),
        "flags": {
            "red_flag": red_flag_detected,
            "missing_info": analysis.get("missing_info"),
        },
        "confidence": analysis.get("confidence"),
        "routing_decision": routing_decision,
        "reasoning": analysis.get("reasoning"),
        "error": state.get("error"),
    }


def append_audit_log(entry: dict) -> None:
    try:
        AUDIT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with AUDIT_LOG_PATH.open("a", encoding="utf-8") as log_file:
            log_file.write(json.dumps(entry) + "\n")
    except OSError as exc:
        print(f"[ERROR] Failed to write audit log: {exc}")


def error_result(message: str) -> dict:
    return {"error": {"message": message}}


def preprocess_node(state: AgentState) -> dict:
    """
    Preprocesses the raw customer inbound text by removing unnecessary 
    whitespaces and padding to optimize token usage for the LLM.
    
    Args:
        state (AgentState): The current state of the conversation graph.
        
    Returns:
        dict: A dictionary updating the 'cleaned_input' key in the state.
    """
    print("[EVENT] Preprocess Node: Cleaning customer text...")
    raw_input = state.get("raw_input")

    if not isinstance(raw_input, str):
        return {
            "cleaned_input": "",
            **error_result("Missing or invalid raw_input; expected a string."),
        }

    cleaned = raw_input.strip()
    return {"cleaned_input": cleaned}


def classifier_node(state: AgentState) -> dict:
    """
    Agent node that invokes the LLM to analyze and classify the customer request.
    Uses structured output to guarantee the response matches the required schema.
    
    Args:
        state (AgentState): The current state containing the cleaned input text.
        
    Returns:
        dict: A dictionary updating the 'analysis' key with the structured data.
    """
    print("[EVENT] Agent Classifier Node: Invoking LLM for analysis...")

    llm = ChatGroq(model="llama-3.3-70b-versatile")
    structured_llm = llm.with_structured_output(BankTicketAnalysis)

    system_prompt = """
        You are a bank triage assistant.
        Analyze the customer's request and classify it.
        Return category, priority, sentiment, confidence, summary,
        reasoning, and missing_info.
        The reasoning field should briefly explain WHY you chose this
        category, priority, and confidence level.
        """
    
    response = structured_llm.invoke([
        ("system", system_prompt),
        ("user", state["cleaned_input"])
    ])

    print(f"[REASONING] {response.dict()['reasoning']}")
    
    return {"analysis": response.dict()}


def escalate_to_human_node(state: AgentState) -> dict:
    """
    A Human-in-the-loop node that pauses graph execution for high-risk tickets.
    Utilizes LangGraph's native interrupt mechanism to wait for manual approval.
    
    Args:
        state (AgentState): The current state containing the LLM analysis.
        
    Returns:
        dict: An empty dictionary as it logs actions but doesn't mutate state data directly.
    """
    
    human_approval = interrupt(
        {
            "question": "Approve immediate escalation?",
            "ticket_summary": state['analysis']['summary'],
            "reasoning": state['analysis']['reasoning']
        }
    )
    
    if not human_approval:
        print("\n🚨 [PAUSED FOR HUMAN APPROVAL] 🚨")
        print(f"CRITICAL RISK DETECTED: {state['analysis']['summary']}")
        return {}
        
    if human_approval.get("approved") == True:
        print("[HUMAN ACTION]: Escalated to Security Team.")
    else:
        print("[HUMAN ACTION]: Ticket returned to normal queue.")
        
    return {}

def route_to_standard_queue_node(state: AgentState) -> dict:
    """
    Standard routing node that processes safe/low-priority tickets 
    and assigns them to the appropriate department queue.
    
    Args:
        state (AgentState): The current state containing the classification results.
        
    Returns:
        dict: An empty dictionary representing completion of routing.
    """
    category = state["analysis"]["issue_category"]
    print(f"[ROUTE] Assigned standard ticket for department: {category}.")
    return {}
    
def flag_for_review_node(state: AgentState) -> dict:
    """
    Routes ambiguous or low-confidence tickets to a manual review queue
    instead of silently processing them as standard tickets.
    """
    print(f"[ROUTE] Flagged for manual review: {state['analysis']['summary']}")
    return {}


def router_edge(state: AgentState) -> str:
    """
    A conditional edge (router) that first checks a deterministic red-flag
    layer, then falls back to the LLM's priority/confidence assessment to
    determine the next node execution path.

    Args:
        state (AgentState): The current state containing the priority key.

    Returns:
        str: The target route name.
    """
    print("[EVENT] Router Node: Checking priority...")

    cleaned_input = state.get("cleaned_input")

    if not isinstance(cleaned_input, str):
        route = "needs_review"
        state["error"] = error_result(
            "Missing or invalid cleaned_input; expected a string."
        )["error"]
        print(f"[ERROR] {state['error']['message']}")
        append_audit_log(build_audit_entry(state, route, False))
        return route

    red_flag_detected = contains_red_flag(cleaned_input)

    if red_flag_detected:
        print("[RED FLAG] Deterministic rule triggered escalation.")
        route = "escalate"
        append_audit_log(build_audit_entry(state, route, red_flag_detected))
        return route

    analysis = state.get("analysis")

    if not isinstance(analysis, dict):
        route = "needs_review"
        state["error"] = error_result(
            "Missing or invalid analysis; expected classifier output."
        )["error"]
        print(f"[ERROR] {state['error']['message']}")
        append_audit_log(build_audit_entry(state, route, red_flag_detected))
        return route

    required_fields = ["priority", "confidence", "missing_info"]
    missing_fields = [
        field
        for field in required_fields
        if not isinstance(analysis.get(field), str)
    ]

    if missing_fields:
        route = "needs_review"
        state["error"] = error_result(
            f"Missing or invalid analysis fields: {', '.join(missing_fields)}."
        )["error"]
        print(f"[ERROR] {state['error']['message']}")
        append_audit_log(build_audit_entry(state, route, red_flag_detected))
        return route

    priority = analysis["priority"]
    confidence = analysis["confidence"]
    missing_info = analysis["missing_info"]

    if priority == "High_Priority":
        route = "escalate"
    elif confidence == "Low" or (missing_info and missing_info.lower() != "none"):
        route = "needs_review"
    elif priority == "Regular" and confidence in {"High", "Medium"}:
        route = "standard"
    else:
        route = "needs_review"
        state["error"] = error_result(
            "Invalid analysis values; routing to manual review."
        )["error"]
        print(f"[ERROR] {state['error']['message']}")

    append_audit_log(build_audit_entry(state, route, red_flag_detected))
    return route


def build_workflow():
    """
    Constructs and compiles the StateGraph workflow, integrating nodes,
    conditional edges, and state persistence (memory checkpointer).
    
    Returns:
        CompiledGraph: The ready-to-run LangGraph workflow.
    """
    workflow = StateGraph(AgentState)

    workflow.add_node("preprocess", preprocess_node)
    workflow.add_node("classifier", classifier_node)
    workflow.add_node("escalate_human", escalate_to_human_node)
    workflow.add_node("standard_queue", route_to_standard_queue_node)
    workflow.add_node("needs_review", flag_for_review_node)  

    workflow.set_entry_point("preprocess")
    workflow.add_edge("preprocess", "classifier")

    workflow.add_conditional_edges(                      
        "classifier",
        router_edge,
        {
            "escalate": "escalate_human",
            "needs_review": "needs_review",
            "standard": "standard_queue"
        }
    )

    workflow.add_edge("escalate_human", END)
    workflow.add_edge("standard_queue", END)
    workflow.add_edge("needs_review", END)                      

    memory = MemorySaver()

    return workflow.compile(checkpointer=memory)

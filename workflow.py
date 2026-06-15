from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from models import BankTicketAnalysis


class AgentState(TypedDict):
    raw_input: str
    cleaned_input: str
    analysis: Optional[dict]


def preprocess_node(state: AgentState) -> dict:
    print("[EVENT] Preprocess Node: Cleaning customer text...")
    cleaned = state["raw_input"].strip()
    return {"cleaned_input": cleaned}


def classifier_node(state: AgentState) -> dict:
    print("[EVENT] Agent Classifier Node: Invoking LLM for analysis...")

    llm = ChatGroq(model="llama-3.3-70b-versatile")
    //ensure structured output by Pydantic
    structured_llm = llm.with_structured_output(BankTicketAnalysis)

    system_prompt = """
        You are a bank triage assistant.
        Analyze the customer's request and classify it.
        Return category, priority, summary, and missing_info.
        """

    response = structured_llm.invoke([
        ("system", system_prompt),
        ("user", state["cleaned_input"])
    ])

    return {"analysis": response.dict()}


def escalate_to_human_node(state: AgentState) -> dict:
    print("\n🚨 [PAUSED FOR HUMAN APPROVAL] 🚨")
    print(f"CRITICAL RISK DETECTED: {state['analysis']['summary']}")
    
    human_approval = interrupt(
        {
            "question": "Approve immediate escalation?",
            "ticket_summary": state['analysis']['summary']
        }
    )
    
    if human_approval.get("approved") == True:
        print("[HUMAN ACTION]: Escalated to Security Team.")
    else:
        print("[HUMAN ACTION]: Ticket returned to normal queue.")
        
    return {}

def route_to_standard_queue_node(state: AgentState) -> dict:
    category = state["analysis"]["issue_category"]
    print(f"[ROUTE] Assigned standard ticket for department: {category}.")
    return {}


def router_edge(state: AgentState) -> str:
    print("[EVENT] Router Node: Checking priority...")

    priority = state["analysis"]["priority"]

    if priority == "High_Priority":
        return "escalate"

    return "standard"


def build_workflow():
    workflow = StateGraph(AgentState)

    workflow.add_node("preprocess", preprocess_node)
    workflow.add_node("classifier", classifier_node)
    workflow.add_node("escalate_human", escalate_to_human_node)
    workflow.add_node("standard_queue", route_to_standard_queue_node)

    workflow.set_entry_point("preprocess")
    workflow.add_edge("preprocess", "classifier")

    workflow.add_conditional_edges(
        "classifier",
        router_edge,
        {
            "escalate": "escalate_human",
            "standard": "standard_queue"
        }
    )

    workflow.add_edge("escalate_human", END)
    workflow.add_edge("standard_queue", END)
    memory = MemorySaver()

   return workflow.compile(checkpointer=memory)

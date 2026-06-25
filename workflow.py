from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from models import BankTicketAnalysis
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt


class AgentState(TypedDict):
    raw_input: str
    cleaned_input: str
    analysis: Optional[dict]


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
    cleaned = state["raw_input"].strip()
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
        Return category, priority, summary, and missing_info.
        """
    
    response = structured_llm.invoke([
        ("system", system_prompt),
        ("user", state["cleaned_input"])
    ])

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
            "ticket_summary": state['analysis']['summary']
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
    A conditional edge (router) that inspects the LLM's priority assessment
    and determines the next node execution path.
    
    Args:
        state (AgentState): The current state containing the priority key.
        
    Returns:
        str: The target route name ('escalate' or 'standard').
    """
    print("[EVENT] Router Node: Checking priority...")

    priority = state["analysis"]["priority"]
    confidence = state["analysis"]["confidence"]
    missing_info = state["analysis"]["missing_info"]

    if priority == "High_Priority":
        return "escalate"

    if confidence == "Low" or (missing_info and missing_info.lower() != "none"):
        return "needs_review"

    return "standard"


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

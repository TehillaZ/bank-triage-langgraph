from dotenv import load_dotenv
load_dotenv()  


from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from models import BankTicketAnalysis

import os
import ssl
ssl._create_default_https_context = ssl._create_unverified_context

class AgentState(TypedDict):
    raw_input: str
    cleaned_input: str
    analysis: Optional[dict]

def preprocess_node(state: AgentState) -> dict:
    print("[EVENT]  Preprocess Node: Cleaning customer text...")
    cleaned = state["raw_input"].strip()
    return {"cleaned_input": cleaned}

def classifier_node(state: AgentState) -> dict:
    print("[EVENT]  Agent Classifier Node: Invoking LLM for analysis...")
    
    llm = ChatGroq(model="llama-3.3-70b-versatile") 
    structured_llm = llm.with_structured_output(BankTicketAnalysis)
    
    system_prompt = "You are a bank triage assistant. Analyze the customer's request and classify it."
    
    response = structured_llm.invoke([
        ("system", system_prompt),
        ("user", state["cleaned_input"])
    ])
    
    return {"analysis": response.dict()}

def escalate_to_human_node(state: AgentState) -> dict:
    print("\n🚨 [PAUSED FOR HUMAN APPROVAL / ESCALATION] 🚨")
    print(f"CRITICAL RISK DETECTED: {state['analysis']['summary']}")
    print("[HUMAN ACTION]: Notification sent to Security Team. Customer bypassed the queue.")
    return {}

def route_to_standard_queue_node(state: AgentState) -> dict:
    category = state["analysis"]["issue_category"]
    print(f" [ROUTE] Assigned standard ticket for department: {category}.")
    return {}

def router_edge(state: AgentState) -> str:
    print("[EVENT]  Router Node: Checking priority...")
    priority = state["analysis"]["priority"]
    
    if priority == "High_Priority":
        return "escalate"
    else:
        return "standard"

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

app = workflow.compile()

if __name__ == "__main__":
    mock_input = "OMG! Someone stole my wallet and I just saw a charge of $500 that I didn't make! Please block my card immediately!!!"
    
    print("=== Starting LangGraph Bank Triage Workflow ===")
    initial_state = {"raw_input": mock_input}
    app.invoke(initial_state)
    print("=== Workflow Finished Successfully ===")
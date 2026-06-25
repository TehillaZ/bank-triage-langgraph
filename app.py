from dotenv import load_dotenv
load_dotenv()
import ssl
ssl._create_default_https_context = ssl._create_unverified_context
from workflow import build_workflow
from langgraph.types import Command

# Eval set: labeled examples covering high-risk, ambiguous, and standard cases
TEST_TICKETS = [
    {
        "label": "fraud_high_risk",
        "text": "OMG! Someone stole my wallet and I just saw a charge of $500 that I didn't make! Please block my card immediately!!!"
    },
    {
        "label": "ambiguous_missing_info",
        "text": "I have a problem with my account, can someone help?"
    },
    {
        "label": "standard_low_priority",
        "text": "What are your branch opening hours on Sundays?"
    },
]

def run_ticket(app, ticket: dict, thread_id: str):
    print(f"\n=== Running ticket: {ticket['label']} ===")
    config = {"configurable": {"thread_id": thread_id}}
    initial_state = {"raw_input": ticket["text"]}
    result = app.invoke(initial_state, config)

    # If the graph paused for human approval, auto-approve for the demo run
    if app.get_state(config).next:
        human_response = {"approved": True}
        result = app.invoke(Command(resume=human_response), config)

    return result


if __name__ == "__main__":
    app = build_workflow()
    print("=== Starting LangGraph Bank Triage Workflow ===")

    for i, ticket in enumerate(TEST_TICKETS):
        run_ticket(app, ticket, thread_id=f"bank_session_{i}")

    print("\n=== Workflow Finished Successfully ===")

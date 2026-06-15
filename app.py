from dotenv import load_dotenv
load_dotenv()

import ssl
ssl._create_default_https_context = ssl._create_unverified_context

from workflow import build_workflow


if __name__ == "__main__":
    app = build_workflow()

    mock_input = "OMG! Someone stole my wallet and I just saw a charge of $500 that I didn't make! Please block my card immediately!!!"

    print("=== Starting LangGraph Bank Triage Workflow ===")

    config = {"configurable": {"thread_id": "bank_session_123"}}
    initial_state = {"raw_input": mock_input}

    app.invoke(initial_state, config)

    human_response = {"approved": True}

    app.invoke(Command(resume=human_response), config)
    print("\n=== Workflow Finished Successfully ===")

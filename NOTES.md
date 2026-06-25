# Bank Triage System Notes

## Main Entry Point

The main executable entry point is `app.py`.

When run directly, it:

1. Loads environment variables with `load_dotenv()`.
2. Builds the LangGraph workflow by calling `build_workflow()` from `workflow.py`.
3. Runs three demo tickets from `TEST_TICKETS`.
4. Invokes the graph once per ticket through `run_ticket()`.
5. If the graph pauses for human approval, it automatically resumes the run with `{"approved": True}` for demo purposes.

## Core Files

- `app.py` contains the demo runner and sample input tickets.
- `workflow.py` contains the LangGraph state, nodes, routing logic, and graph construction.
- `models.py` contains the Pydantic schema used for structured LLM classification output.
- `README.md` documents the intended architecture and example behavior.

## Core Functions and Components

### `build_workflow()`

Defined in `workflow.py`.

This function constructs the LangGraph `StateGraph`, registers all workflow nodes, wires the edges, attaches a memory checkpointer, and returns the compiled graph.

The graph entry point is:

```text
preprocess
```

### `AgentState`

Defined in `workflow.py`.

This is the shared graph state. It contains:

- `raw_input`: the original customer message.
- `cleaned_input`: the preprocessed customer message.
- `analysis`: the structured classifier result.

### `preprocess_node()`

Defined in `workflow.py`.

This is the first workflow node. It trims whitespace from `raw_input` and stores the result in `cleaned_input`.

### `classifier_node()`

Defined in `workflow.py`.

This node calls Groq through `ChatGroq(model="llama-3.3-70b-versatile")`.

It wraps the LLM with `with_structured_output(BankTicketAnalysis)`, so the model response should match the schema in `models.py`.

The classifier is expected to produce:

- issue category
- priority
- sentiment
- confidence
- summary
- missing information
- reasoning

Important note: `workflow.py` reads `response.dict()["reasoning"]`, but `models.py` does not currently define a `reasoning` field on `BankTicketAnalysis`. As written, this can cause a runtime `KeyError` after classification unless the schema is updated.

### `BankTicketAnalysis`

Defined in `models.py`.

This Pydantic model defines the structured classifier output:

- `issue_category`: one of `Lost_Card`, `Fraud_Alert`, `Loan_Inquiry`, or `General_Support`.
- `priority`: either `Regular` or `High_Priority`.
- `sentiment`: one of `Calm`, `Frustrated`, or `Distressed`.
- `confidence`: one of `High`, `Medium`, or `Low`.
- `summary`: a short summary of the customer request.
- `missing_info`: missing details, or `"None"`.

### `contains_red_flag()`

Defined in `workflow.py`.

This is a deterministic safety check that scans the cleaned customer text for risky patterns such as:

- stolen
- fraud or fraudulent
- unauthorized
- did not make or did not authorize
- dollar amounts of three or more digits

If any pattern matches, the ticket is escalated regardless of the LLM's classification.

### `router_edge()`

Defined in `workflow.py`.

This is the conditional router after classification.

Routing order:

1. First, check deterministic red flags with `contains_red_flag()`.
2. If a red flag is found, route to human escalation.
3. Otherwise, if the classifier returned `High_Priority`, route to human escalation.
4. Otherwise, if confidence is `Low`, or `missing_info` is not `"None"`, route to manual review.
5. Otherwise, route to the standard queue.

### `escalate_to_human_node()`

Defined in `workflow.py`.

This node uses LangGraph's `interrupt()` mechanism to pause execution and ask for approval before immediate escalation.

In the demo runner, `app.py` automatically resumes this pause with approval.

### `route_to_standard_queue_node()`

Defined in `workflow.py`.

This handles normal tickets by printing the department queue based on the classifier's `issue_category`.

### `flag_for_review_node()`

Defined in `workflow.py`.

This handles ambiguous or incomplete tickets by printing that the ticket was flagged for manual review.

## Data Flow

The intended flow is:

```text
Customer ticket text
  -> app.py creates initial state: {"raw_input": ticket["text"]}
  -> preprocess_node trims the text into cleaned_input
  -> classifier_node sends cleaned_input to the LLM
  -> LLM returns structured BankTicketAnalysis data
  -> router_edge chooses the next path
  -> one terminal route runs
  -> workflow ends
```

The three possible terminal paths are:

```text
High risk or red flag
  -> escalate_human
  -> END

Low confidence or missing information
  -> needs_review
  -> END

Normal ticket
  -> standard_queue
  -> END
```

## Input and Output

### Input

The graph receives an initial state like:

```python
{"raw_input": "Customer message here"}
```

### Output

The graph returns the final LangGraph state, including:

- the original `raw_input`
- the derived `cleaned_input`
- the classifier `analysis`

The route result itself is mainly shown through printed logs. The routing nodes do not currently add a final route label or queue name back into the state.

## Demo Tickets

`app.py` includes three test tickets:

- `fraud_high_risk`: should trigger escalation.
- `ambiguous_missing_info`: should be flagged for manual review.
- `standard_low_priority`: should go to the standard queue.

## Observations

- The architecture is intentionally small and readable.
- The deterministic red-flag layer makes routing safer because escalation does not depend only on the LLM.
- The human-in-the-loop path uses LangGraph interrupts and requires a checkpointer, which is provided by `MemorySaver`.
- The workflow currently logs routing decisions, but does not persist the selected route in the returned state.
- There is a likely schema mismatch: `workflow.py` expects `reasoning`, but `models.py` does not define it.


# 🚀 Project Name

> **Interviewer:** "Welcome! Let's dive straight in. Can you tell me a bit about this project?"

**Candidate (The App):** "Absolutely. [Insert a 1-2 sentence high-level, human-readable description of what the app does. Keep it punchy and clear!]"

---

## 🎙️ The Tech Stack Interview

> **Interviewer:** "Before we look under the hood, what technologies did you choose to build this with and why?"

**Candidate:** "I wanted a robust, scalable, and modern stack. Here is what I used to bring this project to life:"

*   **Frontend:** React (with TypeScript) / [Other UI tools]
*   **Backend:** Node.js / C# .NET / [Other backend tools]
*   **Database:** SQL Server / PostgreSQL / MongoDB
*   **State Management / Tools:** [e.g., Redux, Axios, Tailwind]

---

## 🧠 Architectural & Engineering Decisions

> **Interviewer:** "Every project faces trade-offs. What major engineering decisions did you make along the way?"

**Candidate:** "That's a great question. I focused heavily on [e.g., Separation of Concerns / Clean Architecture / Performance]. Here is how the system is structured:"

### System Architecture
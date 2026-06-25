# 🏦 Bank Ticket Triage Workflow

## Overview
This project implements an intelligent bank support ticket triage system using **LangGraph** and **LLMs**. The workflow automatically analyzes incoming customer requests, classifies them, determines their urgency, and routes them to the appropriate handling path.

The system simulates a real-world banking support process where high-risk requests receive immediate attention and can be escalated for human approval. It also includes a deterministic safety layer that does not rely solely on the LLM's judgment, and a review path for ambiguous or low-confidence tickets.

---

## Personal Notes
This project was my first hands-on experience with LangGraph and AI workflow orchestration.
Since the topic was completely new to me,
I spent additional time learning the fundamentals through online courses (YouTube).
I intentionally focused on creating a simple and readable architecture rather than a highly complex implementation, in order to build
a clear and maintainable workflow while understanding the core concepts of graph-based AI agents.

After receiving feedback on the initial version, I extended the project with a deterministic rule-based safety layer, additional classification dimensions (confidence and sentiment), a dedicated review path for ambiguous tickets, and a small evaluation set covering multiple ticket types instead of a single hardcoded example.

This project was a valuable learning experience that helped me better understand how AI workflows are designed,
routed, monitored, and made more robust in real-world applications.

---

## Features
* **Preprocessing stage**
  * Cleans and normalizes incoming customer messages.
* **AI-powered classification**
  * Uses an LLM with structured output to analyze requests.
  * Extracts:
    * Issue category
    * Priority level
    * Confidence level
    * Customer sentiment
    * Request summary
    * Missing information
* **Deterministic red-flag layer**
  * A keyword/amount-based regex check (e.g. "stolen", "fraud", large dollar amounts) that can force escalation regardless of the LLM's own priority classification.
* **Intelligent routing**
  * Standard requests are assigned to the appropriate department.
  * High-priority or red-flagged requests are escalated for immediate attention.
  * Ambiguous or low-confidence requests are flagged for manual review instead of being silently treated as standard.
* **Human approval path**
  * Critical cases can pause the workflow and require human confirmation before taking action.
* **Event streaming**
  * Each step prints status messages, providing full visibility into the execution process.
* **Evaluation set**
  * Multiple labeled example tickets (high-risk, ambiguous, and standard) are run through the workflow to demonstrate routing behavior across different scenarios.

---

## Architecture
```
Customer Request
       ↓
Preprocess Node
       ↓
AI Classifier Node
       ↓
Priority Router (red-flag check → priority → confidence/missing info)
   ↙            ↓            ↘
Standard      Needs Review    Human Escalation
Queue
   ↓              ↓                ↓
  END            END              END
```

---

## Technologies
* Python
* LangGraph
* LangChain
* Groq API
* Pydantic
* dotenv

---

## Example Request
```
OMG! Someone stole my wallet and I just saw a charge of $500 that I didn't make! Please block my card immediately!!!
```

## Example Classification
```json
{
  "issue_category": "Fraud_Alert",
  "priority": "High_Priority",
  "confidence": "High",
  "sentiment": "Distressed",
  "summary": "Customer reports unauthorized charges and requests an immediate card block.",
  "missing_info": "Card number or account identification."
}
```

---

## Running Example
```
=== Starting LangGraph Bank Triage Workflow ===

=== Running ticket: fraud_high_risk ===
[EVENT] Preprocess Node: Cleaning customer text...
[EVENT] Agent Classifier Node: Invoking LLM for analysis...
[REASONING] The customer explicitly states that their wallet was stolen and they have seen an unauthorized charge, which clearly indicates a fraud alert and requires immediate attention
[EVENT] Router Node: Checking priority...
[RED FLAG] Deterministic rule triggered escalation.
[HUMAN ACTION]: Escalated to Security Team.

=== Running ticket: ambiguous_missing_info ===
[EVENT] Preprocess Node: Cleaning customer text...
[EVENT] Agent Classifier Node: Invoking LLM for analysis...
[REASONING] The customer's request is vague, but it appears to be a general inquiry, so I chose the General_Support category with a Regular priority and Medium confidence level.
[EVENT] Router Node: Checking priority...
[ROUTE] Flagged for manual review: The customer needs help with their account

=== Running ticket: standard_low_priority ===
[EVENT] Preprocess Node: Cleaning customer text...
[EVENT] Agent Classifier Node: Invoking LLM for analysis...
[REASONING] The customer is asking a general question about branch hours, which is a common inquiry and does not indicate any urgency or distress, so I have chosen the General_Support category and Regular priority.
[EVENT] Router Node: Checking priority...
[ROUTE] Assigned standard ticket for department: General_Support.

=== Workflow Finished Successfully ===
```

---

## Learning Objectives
This project demonstrates:
* Graph-based workflow orchestration with LangGraph.
* Structured LLM outputs using Pydantic models.
* Conditional routing and switch-case edges.
* Combining deterministic rule-based logic with LLM-driven decisions for safer automation.
* Human-in-the-loop workflows.
* Real-time event tracing and transparency.
* Building AI-powered support automation systems with a small evaluation set instead of a single hardcoded example.

---

### Author
Tehila – AI Workflow Engineering Homework Project

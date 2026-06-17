# 🏦 Bank Ticket Triage Workflow

## Overview

This project implements an intelligent bank support ticket triage system using **LangGraph** and **LLMs**. The workflow automatically analyzes incoming customer requests, classifies them, determines their urgency, and routes them to the appropriate handling path.

The system simulates a real-world banking support process where high-risk requests receive immediate attention and can be escalated for human approval.

---
## Personal Notes
This project was my first hands-on experience with LangGraph and AI workflow orchestration.
Since the topic was completely new to me,   
I spent additional time learning the fundamentals through online courses (YouTube)
I intentionally focused on creating a simple and readable architecture rather than a highly complex implementation In order to build
clear and maintainable workflow while understanding the core concepts of graph-based AI agents,
This project was a valuable learning experience that helped me better understand how AI workflows are designed, 
routed, and monitored in real-world applications.

---

## Features

* **Preprocessing stage**

  * Cleans and normalizes incoming customer messages.

* **AI-powered classification**

  * Uses an LLM with structured output to analyze requests.
  * Extracts:

    * Issue category
    * Priority level
    * Request summary
    * Missing information

* **Intelligent routing**

  * Standard requests are assigned to the appropriate department.
  * High-priority requests are escalated for immediate attention.

* **Human approval path**

  * Critical cases can pause the workflow and require human confirmation before taking action.

* **Event streaming**

  * Each step prints status messages, providing full visibility into the execution process.

---

## Architecture

```
Customer Request
       ↓
Preprocess Node
       ↓
AI Classifier Node
       ↓
Priority Router
   ↙             ↘
Standard Queue    Human Escalation
       ↓               ↓
      END             END
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
  "summary": "Customer reports unauthorized charges and requests an immediate card block.",
  "missing_info": "Card number or account identification."
}
```

---
## Running Example
```
=== Starting LangGraph Bank Triage Workflow ===
[EVENT] Preprocess Node: Cleaning customer text...
[EVENT] Agent Classifier Node: Invoking LLM for analysis...
[EVENT] Router Node: Checking priority...

🚨 [PAUSED FOR HUMAN APPROVAL] 🚨
CRITICAL RISK DETECTED: Customer requests to block their card due to a stolen wallet and a fraudulent charge of $500.

[HUMAN ACTION]: Escalated to Security Team.
=== Workflow Finished Successfully ===
```
## Learning Objectives

This project demonstrates:

* Graph-based workflow orchestration with LangGraph.
* Structured LLM outputs using Pydantic models.
* Conditional routing and switch-case edges.
* Human-in-the-loop workflows.
* Real-time event tracing and transparency.
* Building AI-powered support automation systems.

---

### Author

Tehila – AI Workflow Engineering Homework Project

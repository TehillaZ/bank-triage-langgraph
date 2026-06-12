# 🏦 Bank Ticket Triage Workflow

## Overview

This project implements an intelligent bank support ticket triage system using **LangGraph** and **LLMs**. The workflow automatically analyzes incoming customer requests, classifies them, determines their urgency, and routes them to the appropriate handling path.

The system simulates a real-world banking support process where high-risk requests receive immediate attention and can be escalated for human approval.

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

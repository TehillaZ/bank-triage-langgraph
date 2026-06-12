from typing import Literal
from pydantic import BaseModel, Field

class BankTicketAnalysis(BaseModel):
    issue_category: Literal[
        "Lost_Card",
        "Fraud_Alert",
        "Loan_Inquiry",
        "General_Support"
    ]

    priority: Literal["Regular", "High_Priority"]

    summary: str = Field(
        description="A brief 1-sentence summary of what the customer wants."
    )

    missing_info: str = Field(
        description="Important missing information from the customer request, or 'None'."
    )
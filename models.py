from pydantic import BaseModel, Field

class BankTicketAnalysis(BaseModel):
    issue_category: str = Field(
        description="The category of the issue. Must be one of: Lost_Card, Fraud_Alert, Loan_Inquiry, General_Support"
    )
    priority: str = Field(
        description="The urgency level. Must be one of: Regular, High_Priority"
    )
    summary: str = Field(
        description="A brief 1-sentence summary of what the customer wants."
    )
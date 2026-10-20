from enum import Enum
from typing import List
from pydantic import BaseModel, Field


class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Category(str, Enum):
    CRASH = "crash"
    PERFORMANCE = "performance"
    SECURITY = "security"
    DATA_LOSS = "data_loss"
    UI_UX = "ui_ux"
    NETWORK = "network"
    AUTH = "authentication"
    DATABASE = "database"
    CONFIGURATION = "configuration"
    OTHER = "other"


class BugAnalysis(BaseModel):
    summary: str = Field(description="One-line summary of the bug")
    category: Category
    severity: Severity
    severity_reason: str
    likely_root_causes: List[str]
    troubleshooting_steps: List[str]
    suggested_labels: List[str]
    confidence: float = Field(ge=0.0, le=1.0)
    engine: str = Field(description="'llm' or 'rule-based'")

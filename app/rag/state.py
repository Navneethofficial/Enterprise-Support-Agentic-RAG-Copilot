
from typing import List, Literal
from typing_extensions import TypedDict
from pydantic import BaseModel, Field
from langchain_core.documents import Document


# -----------------------------
# Agent Routing Decision
# -----------------------------

class RouteDecision(BaseModel):
    route: Literal["kb", "direct"] = Field(
        description=(
            "Use kb for IT support and company knowledge questions; "
            "use direct for greetings and simple conversations."
        )
    )


# -----------------------------
# Evidence Evaluation
# -----------------------------

class EvidenceGrade(BaseModel):
    grade: Literal["good", "weak"] = Field(
        description=(
            "Return good if the available evidence is sufficient "
            "and relevant; otherwise return weak."
        )
    )


# -----------------------------
# LangGraph Agent State
# -----------------------------

class AgentState(TypedDict):
    question: str
    current_query: str

    kb_docs: List[Document]
    web_results: str

    kb_grade: str
    web_grade: str

    answer: str
    source_used: str

    retry_count: int

    trace: List[str]
    citations: List[dict]

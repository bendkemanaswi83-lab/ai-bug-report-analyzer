import logging
from typing import Iterable, List, Optional

from pydantic import ValidationError

from .llm_client import LLMClient, LLMError
from .models import BugAnalysis
from .preprocess import clean_report
from .rule_based import analyze_rule_based

log = logging.getLogger(__name__)


class BugReportAnalyzer:
    """Classifies bug reports, rates severity and suggests troubleshooting steps.

    Uses an LLM when an API key is configured; otherwise (or on any failure)
    falls back to a deterministic rule-based engine.
    """

    def __init__(self, llm: Optional[LLMClient] = None, use_llm: bool = True):
        self.llm = llm or LLMClient()
        self.use_llm = use_llm and self.llm.available

    def analyze(self, report: str) -> BugAnalysis:
        if not report or not report.strip():
            raise ValueError("Bug report is empty")
        cleaned = clean_report(report)

        if self.use_llm:
            try:
                data = self.llm.analyze(cleaned)
                data["engine"] = "llm"
                return BugAnalysis(**data)
            except (LLMError, ValidationError, TypeError) as e:
                log.warning("LLM analysis failed (%s); using rule-based fallback", e)

        return analyze_rule_based(cleaned)

    def analyze_many(self, reports: Iterable[str]) -> List[BugAnalysis]:
        return [self.analyze(r) for r in reports]

import json
from pathlib import Path

import pytest

from bug_analyzer import BugReportAnalyzer
from bug_analyzer.llm_client import LLMClient, LLMError
from bug_analyzer.models import Category, Severity
from bug_analyzer.preprocess import clean_report

A = BugReportAnalyzer(use_llm=False)


def test_crash_is_high():
    r = A.analyze("App crashes on checkout with NullPointerException every time")
    assert r.category == Category.CRASH
    assert r.severity in (Severity.HIGH, Severity.CRITICAL)
    assert len(r.troubleshooting_steps) >= 3


def test_data_loss_is_critical():
    r = A.analyze("Migration caused data loss, records deleted in production")
    assert r.category == Category.DATA_LOSS
    assert r.severity == Severity.CRITICAL


def test_cosmetic_is_low():
    r = A.analyze("Minor typo and alignment issue on button, cosmetic")
    assert r.severity == Severity.LOW


def test_empty_report_raises():
    with pytest.raises(ValueError):
        A.analyze("   ")


def test_pii_redacted():
    out = clean_report("Contact bob@example.com from 192.168.1.10 token sk-abcdef1234567890xyz")
    assert "bob@example.com" not in out and "192.168.1.10" not in out and "sk-abcdef" not in out


def test_llm_json_parsing_with_fences():
    raw = '```json\n{"a": 1}\n```'
    assert LLMClient.parse_json(raw) == {"a": 1}
    with pytest.raises(LLMError):
        LLMClient.parse_json("not json")


def test_llm_failure_falls_back():
    class Broken:
        available = True
        def analyze(self, _): raise LLMError("boom")
    r = BugReportAnalyzer(llm=Broken()).analyze("App crashes with exception")
    assert r.engine == "rule-based"


def test_llm_path_used_when_valid():
    class Fake:
        available = True
        def analyze(self, _):
            return {"summary": "s", "category": "crash", "severity": "high", "severity_reason": "r",
                    "likely_root_causes": ["a"], "troubleshooting_steps": ["b"],
                    "suggested_labels": ["c"], "confidence": 0.9}
    r = BugReportAnalyzer(llm=Fake()).analyze("anything")
    assert r.engine == "llm" and r.severity == Severity.HIGH


def test_sample_data():
    reports = json.loads((Path(__file__).parent.parent / "data/sample_reports.json").read_text())
    assert len(A.analyze_many(reports)) == len(reports)

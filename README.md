# AI Bug Report Analyzer

**Python | LLM | Generative AI**

An AI-powered triage tool that reads unstructured bug reports, classifies the issue,
rates its severity, and generates troubleshooting suggestions.

## Features
- **LLM-based analysis** (Anthropic Claude) returning strict, validated JSON
- **Issue classification** into 10 categories (crash, security, data loss, auth, DB, network, ...)
- **Severity detection** (critical / high / medium / low) with a written justification
- **Automated troubleshooting**: likely root causes, ordered fix steps, suggested labels
- **Privacy-aware**: emails, IPs and API-key-like tokens are redacted before any LLM call
- **Resilient**: falls back to an offline rule-based engine if no API key is set or the LLM fails
- **CLI + REST API (FastAPI)**, batch mode, unit tests

## Architecture
```
bug report -> preprocess (clean + redact) -> LLM (JSON) -> pydantic validation -> BugAnalysis
                                                 |  (no key / error / bad JSON)
                                                 +--> rule-based fallback
```

## Setup
```bash
pip install -r requirements.txt
cp .env.example .env        # optional: add ANTHROPIC_API_KEY for LLM mode
export ANTHROPIC_API_KEY=your_key_here
```

## Usage
```bash
# CLI
python -m bug_analyzer.cli "App crashes on checkout with NullPointerException on Android 14"
python -m bug_analyzer.cli -f data/sample_reports.json
python -m bug_analyzer.cli --json --no-llm "Dashboard is very slow and times out"

# API
uvicorn bug_analyzer.api:app --reload
curl -X POST localhost:8000/analyze -H "Content-Type: application/json" \
     -d '{"report": "Users get 401 right after SSO login"}'
```

## Tests
```bash
pytest -q
```

## Example output
```json
{
  "summary": "App crashes immediately after I tap Checkout on Android 14",
  "category": "crash",
  "severity": "high",
  "severity_reason": "Core purchase flow fails every time with a NullPointerException.",
  "likely_root_causes": ["Unhandled exception or null reference", "..."],
  "troubleshooting_steps": ["Collect the full stack trace and crash logs", "..."],
  "suggested_labels": ["crash", "severity:high", "android"],
  "confidence": 0.95,
  "engine": "llm"
}
```

## Project structure
```
bug_analyzer/  analyzer.py  llm_client.py  prompts.py  preprocess.py  rule_based.py  models.py  cli.py  api.py
tests/         test_analyzer.py
data/          sample_reports.json
```

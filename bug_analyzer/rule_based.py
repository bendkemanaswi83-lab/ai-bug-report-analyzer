"""Offline fallback so the tool works (and tests run) without an API key."""
import re
from typing import Dict, List, Tuple

from .models import BugAnalysis, Category, Severity

CATEGORY_KEYWORDS: Dict[Category, List[str]] = {
    Category.SECURITY: ["xss", "sql injection", "csrf", "vulnerab", "exploit", "leak", "unauthorized", "privilege"],
    Category.DATA_LOSS: ["data loss", "lost data", "deleted", "corrupt", "overwritten", "missing records"],
    Category.CRASH: ["crash", "segfault", "nullpointer", "null pointer", "exception", "stack trace", "traceback", "fatal", "force close", "oom", "out of memory"],
    Category.AUTH: ["login", "log in", "password", "token expired", "401", "403", "sso", "oauth", "session"],
    Category.DATABASE: ["database", "sql", "query", "deadlock", "migration", "constraint", "postgres", "mysql", "mongodb"],
    Category.NETWORK: ["timeout", "timed out", "connection refused", "dns", "502", "503", "504", "socket", "ssl", "certificate"],
    Category.PERFORMANCE: ["slow", "lag", "latency", "high cpu", "memory leak", "takes forever", "performance", "freezes", "times out", "to load", "seconds"],
    Category.CONFIGURATION: ["config", "env var", "environment variable", "settings", "misconfigur", ".env"],
    Category.UI_UX: ["button", "layout", "alignment", "css", "typo", "display", "overlap", "dark mode", "responsive", "ui"],
}

SEVERITY_SIGNALS: List[Tuple[Severity, List[str]]] = [
    (Severity.CRITICAL, ["data loss", "production down", "outage", "security", "breach", "corrupt", "all users", "cannot recover"]),
    (Severity.HIGH, ["crash", "cannot login", "can't login", "unable to", "blocker", "payment", "fails every", "500", "401", "403"]),
    (Severity.MEDIUM, ["slow", "intermittent", "sometimes", "workaround", "timeout", "error"]),
    (Severity.LOW, ["typo", "cosmetic", "minor", "alignment", "color", "nice to have"]),
]

PLAYBOOK: Dict[Category, Dict[str, List[str]]] = {
    Category.CRASH: {
        "causes": ["Unhandled exception or null reference", "Memory exhaustion / resource leak", "Incompatible dependency or OS version"],
        "steps": ["Collect the full stack trace and crash logs", "Reproduce on the reported version/platform", "Bisect recent commits or dependency upgrades", "Add null/exception guards around the failing call site", "Add a regression test and monitor crash-free rate after the fix"],
    },
    Category.SECURITY: {
        "causes": ["Missing input validation or output encoding", "Broken access control", "Secrets or PII exposed in logs/responses"],
        "steps": ["Treat as confidential; restrict ticket visibility", "Reproduce in an isolated environment", "Assess exposure scope and affected users", "Patch, rotate any exposed credentials", "Run a security regression scan and notify stakeholders"],
    },
    Category.DATA_LOSS: {
        "causes": ["Faulty write/delete logic or missing transaction", "Failed migration or race condition", "Missing backup/soft-delete safeguards"],
        "steps": ["Stop further writes to affected data if possible", "Identify the affected records and time window", "Restore from the latest backup", "Review recent migrations and delete/update code paths", "Add transactions, soft deletes and audit logging"],
    },
    Category.AUTH: {
        "causes": ["Expired or invalid token/session handling", "Misconfigured identity provider or redirect URI", "Clock skew or cookie policy issue"],
        "steps": ["Check auth service logs for the failing request", "Verify token expiry, issuer and clock sync", "Test in a clean browser/session", "Validate SSO/OAuth config and redirect URIs", "Confirm password-reset and lockout flows"],
    },
    Category.DATABASE: {
        "causes": ["Slow or unindexed query", "Lock contention / deadlock", "Schema mismatch after migration"],
        "steps": ["Capture the failing query and error code", "Run EXPLAIN / query plan analysis", "Inspect locks and connection pool usage", "Verify migrations were applied in order", "Add indexes or retry logic as needed"],
    },
    Category.NETWORK: {
        "causes": ["Upstream service unavailable or overloaded", "DNS / TLS certificate problem", "Timeouts too aggressive or firewall rules"],
        "steps": ["Check service health dashboards and recent deploys", "Test connectivity with curl/ping/traceroute", "Verify DNS and TLS certificate validity", "Review timeout and retry settings", "Inspect load balancer / gateway logs"],
    },
    Category.PERFORMANCE: {
        "causes": ["Inefficient algorithm or N+1 queries", "Memory leak or unbounded cache", "Resource contention under load"],
        "steps": ["Profile CPU and memory during the slow scenario", "Review slow-query and APM traces", "Check for N+1 queries and missing caching", "Load-test before/after the fix", "Set up latency alerts"],
    },
    Category.CONFIGURATION: {
        "causes": ["Missing or wrong environment variable", "Config drift between environments", "Bad default value"],
        "steps": ["Diff config between working and failing environments", "Verify required env vars are set", "Check recent config or deployment changes", "Add startup validation for required settings"],
    },
    Category.UI_UX: {
        "causes": ["CSS/layout regression", "Browser or viewport-specific rendering issue", "State not updated after interaction"],
        "steps": ["Capture a screenshot and browser/device details", "Reproduce across browsers and viewport sizes", "Inspect element styles and console errors", "Fix and add a visual regression test"],
    },
    Category.OTHER: {
        "causes": ["Insufficient information to determine cause"],
        "steps": ["Ask the reporter for exact reproduction steps", "Request app version, OS and environment", "Collect logs and screenshots", "Try to reproduce locally"],
    },
}

_PLATFORM = re.compile(r"\b(ios|android|windows|macos|linux)\b")


def _score_category(text: str) -> Tuple[Category, int]:
    best, best_score = Category.OTHER, 0
    for cat, kws in CATEGORY_KEYWORDS.items():
        score = sum(1 for k in kws if k in text)
        if score > best_score:
            best, best_score = cat, score
    return best, best_score


def _pick_severity(text: str, category: Category) -> Tuple[Severity, str]:
    for sev, kws in SEVERITY_SIGNALS:
        hits = [k for k in kws if k in text]
        if hits:
            return sev, f"Report contains signals such as: {', '.join(hits[:3])}."
    if category in (Category.SECURITY, Category.DATA_LOSS):
        return Severity.CRITICAL, f"Category '{category.value}' is treated as critical by default."
    return Severity.MEDIUM, "No strong severity signals; defaulting to medium."


def analyze_rule_based(report: str) -> BugAnalysis:
    text = report.lower()
    category, score = _score_category(text)
    severity, reason = _pick_severity(text, category)
    play = PLAYBOOK[category]

    first_line = re.split(r"[.\n]", report.strip(), maxsplit=1)[0][:120] or "Bug report"
    labels = [category.value, f"severity:{severity.value}"]
    m = _PLATFORM.search(text)
    if m:
        labels.append(m.group(1))

    return BugAnalysis(
        summary=first_line,
        category=category,
        severity=severity,
        severity_reason=reason,
        likely_root_causes=play["causes"],
        troubleshooting_steps=play["steps"],
        suggested_labels=labels,
        confidence=round(min(0.35 + 0.1 * score, 0.7), 2),
        engine="rule-based",
    )

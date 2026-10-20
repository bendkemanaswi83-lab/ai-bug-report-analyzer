from typing import List

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .analyzer import BugReportAnalyzer
from .models import BugAnalysis

app = FastAPI(title="AI Bug Report Analyzer", version="1.0.0")
analyzer = BugReportAnalyzer()


class ReportIn(BaseModel):
    report: str = Field(min_length=5, description="Raw, unstructured bug report text")


class BatchIn(BaseModel):
    reports: List[str] = Field(min_length=1, max_length=50)


@app.get("/health")
def health():
    return {"status": "ok", "llm_enabled": analyzer.use_llm}


@app.post("/analyze", response_model=BugAnalysis)
def analyze(body: ReportIn):
    try:
        return analyzer.analyze(body.report)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@app.post("/analyze/batch", response_model=List[BugAnalysis])
def analyze_batch(body: BatchIn):
    return analyzer.analyze_many(body.reports)

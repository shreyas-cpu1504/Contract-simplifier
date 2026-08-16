from pydantic import BaseModel, Field


class ClauseAnalysis(BaseModel):
    clause_id: str
    clause_number: str | None = None
    clause_type: str | None = None

    meaning: str | None = None

    parties: list[str] = Field(default_factory=list)
    obligations: list[str] = Field(default_factory=list)
    rights: list[str] = Field(default_factory=list)
    deadlines: list[str] = Field(default_factory=list)
    conditions: list[str] = Field(default_factory=list)
    monetary_terms: list[str] = Field(default_factory=list)

    risk_level: str | None = None
    risk_score: int = 0
    risk_reasons: list[str] = Field(default_factory=list)
    user_impact: str | None = None

    recommendations: list[str] = Field(default_factory=list)


class ClauseAnalysisResponse(BaseModel):
    file_id: str
    analysis_count: int
    analyses: list[ClauseAnalysis]

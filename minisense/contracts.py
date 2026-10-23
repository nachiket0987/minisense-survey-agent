from datetime import date
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator

THEMES = (
    "food_quality",
    "wait_time",
    "staff_service",
    "order_accuracy",
    "cleanliness",
    "value",
    "satisfaction",
)
Theme = Literal[
    "food_quality",
    "wait_time",
    "staff_service",
    "order_accuracy",
    "cleanliness",
    "value",
    "satisfaction",
]


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid")


class SurveyResponse(Contract):
    response_id: str = Field(min_length=1)
    date: date
    business_id: str = Field(min_length=1)
    business_name: str = Field(min_length=1)
    survey_id: str = Field(min_length=1)
    survey_name: str = Field(min_length=1)
    rating: int = Field(ge=1, le=5, strict=True)
    response_channel: Literal["mobile", "web", "in_store"]
    free_text: str = Field(min_length=1)
    sentiment: Literal["positive", "negative", "neutral", "mixed"]
    themes: list[Theme] = Field(min_length=1)
    complaint_themes: list[Theme]

    @model_validator(mode="after")
    def annotations(self):
        if len(set(self.themes)) != len(self.themes) or len(
            set(self.complaint_themes)
        ) != len(self.complaint_themes):
            raise ValueError("Theme annotations must be unique")
        if not set(self.complaint_themes) <= set(self.themes):
            raise ValueError("Complaint themes must be mentioned themes")
        return self


class Period(Contract):
    start: date
    end: date

    @model_validator(mode="after")
    def chronological(self):
        if self.start > self.end:
            raise ValueError("Period start must precede end")
        return self


class Task(Contract):
    id: str = Field(min_length=1)
    agent: Literal["data", "comparison", "rag", "summary"]
    operation: Literal["metrics", "compare", "retrieve", "synthesize"]
    depends_on: list[str] = Field(default_factory=list)
    period: Period | None = None
    business_id: str = "b01"
    theme: Theme | None = None
    top_n: int = Field(default=3, ge=1, le=7)
    query: str | None = None

    @model_validator(mode="after")
    def task_shape(self):
        expected = {
            "data": "metrics",
            "comparison": "compare",
            "rag": "retrieve",
            "summary": "synthesize",
        }
        if self.operation != expected[self.agent]:
            raise ValueError("Agent and operation disagree")
        if self.agent == "data" and self.period is None:
            raise ValueError("Data tasks require a period")
        if self.agent == "rag" and not self.query:
            raise ValueError("Retrieval tasks require a query")
        return self


class Plan(Contract):
    question: str = Field(min_length=1, max_length=2000)
    tasks: list[Task] = Field(min_length=1, max_length=12)

    @model_validator(mode="after")
    def valid_graph(self):
        ids = {t.id for t in self.tasks}
        if len(ids) != len(self.tasks):
            raise ValueError("Task IDs must be unique")
        by_id = {t.id: t for t in self.tasks}
        if sum(t.agent == "summary" for t in self.tasks) != 1:
            raise ValueError("Exactly one summary is required")
        pending = list(self.tasks)
        done = set()
        while pending:
            ready = [t for t in pending if set(t.depends_on) <= done]
            if not ready:
                raise ValueError("Unknown dependencies or cycle")
            for t in ready:
                if len(t.depends_on) != len(set(t.depends_on)):
                    raise ValueError("Duplicate dependencies")
                if t.agent == "comparison" and (
                    len(t.depends_on) != 2
                    or any(by_id[d].agent != "data" for d in t.depends_on)
                ):
                    raise ValueError(
                        "Comparison requires two ordered data dependencies"
                    )
                if t.agent == "summary" and set(t.depends_on) != ids - {t.id}:
                    raise ValueError("Summary must depend on every evidence task")
                done.add(t.id)
                pending.remove(t)
        return self


class Metrics(Contract):
    period: Period
    business_id: str
    count: int = Field(ge=0)
    mean_rating: float | None
    satisfied_pct: float | None
    themes: dict[str, int]
    complaints: dict[str, int]
    complaint_rates: dict[str, float | None]
    top_complaints: list[tuple[str, int]]


class Comparison(Contract):
    earlier: Period
    later: Period
    count_delta: int
    count_change_pct: float | None
    mean_delta: float | None
    complaints: dict[str, dict[str, float | int | None]]
    warnings: list[str]


class Chunk(Contract):
    id: str
    source: str
    content: str
    score: float | None = None


class Retrieval(Contract):
    query: str
    chunks: list[Chunk]
    limitation: str | None = None


class ToolCall(Contract):
    agent: str
    name: str
    arguments: dict
    result: dict


class Summary(Contract):
    answer: str
    evidence: list[str]
    recommendation: str | None = None
    mode: Literal["demo", "llm"]


class Answer(Contract):
    plan: Plan
    agents_invoked: list[str]
    tool_calls: list[ToolCall]
    results: dict[str, dict]
    summary: Summary

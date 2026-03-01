from pydantic import BaseModel, Field, field_validator
from typing import Optional, Union, Literal, Annotated

# Max lengths for security (prevent DoS / prompt injection)
MAX_CITY_LENGTH = 200
MAX_TTS_TEXT_LENGTH = 5000
MAX_SOURCE_URL_LENGTH = 2048


def _validate_https_url(v: str) -> str:
    """Validate source_url to prevent XSS via javascript:, data:, etc."""
    if not isinstance(v, str) or len(v) > MAX_SOURCE_URL_LENGTH:
        raise ValueError("source_url must be a valid https URL")
    v = v.strip()
    if not v.lower().startswith("https://"):
        raise ValueError("source_url must be an https URL")
    return v


class DataPoint(BaseModel):
    label: str
    value: float


class MetricKPI(BaseModel):
    id: str
    title: str
    type: Literal["kpi"]
    unit: str
    source_dataset: str
    source_url: str
    value: Union[float, str]
    delta: Optional[float] = None
    delta_label: Optional[str] = None

    @field_validator("source_url")
    @classmethod
    def validate_source_url(cls, v: str) -> str:
        return _validate_https_url(v)


class MetricChart(BaseModel):
    id: str
    title: str
    type: Literal["line_chart", "bar_chart"]
    unit: str
    source_dataset: str
    source_url: str
    data: list[DataPoint]

    @field_validator("source_url")
    @classmethod
    def validate_source_url(cls, v: str) -> str:
        return _validate_https_url(v)


Metric = Annotated[Union[MetricKPI, MetricChart], Field(discriminator="type")]


class DashboardData(BaseModel):
    city: str
    summary: str
    metrics: list[Metric]


class DashboardRequest(BaseModel):
    city: str = Field(min_length=1, max_length=MAX_CITY_LENGTH)


class TTSRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=MAX_TTS_TEXT_LENGTH)

class DashboardResponse(BaseModel):
    data: DashboardData
    duration_seconds: float
    iterations: int

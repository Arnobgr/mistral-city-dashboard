from pydantic import BaseModel, Field
from typing import Optional, Union, Literal, Annotated

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

class MetricChart(BaseModel):
    id: str
    title: str
    type: Literal["line_chart", "bar_chart"]
    unit: str
    source_dataset: str
    source_url: str
    data: list[DataPoint]

Metric = Annotated[Union[MetricKPI, MetricChart], Field(discriminator="type")]

class DashboardData(BaseModel):
    city: str
    summary: str
    metrics: list[Metric]

class DashboardRequest(BaseModel):
    city: str


class TTSRequest(BaseModel):
    text: str = Field(..., min_length=1)

class DashboardResponse(BaseModel):
    data: DashboardData
    duration_seconds: float
    iterations: int

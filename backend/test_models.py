import pytest
from pydantic import ValidationError
from models import DashboardData, MetricKPI, MetricChart, DataPoint, DashboardRequest, TTSRequest

def test_datapoint_model():
    data = DataPoint(label="2020", value=100.0)
    assert data.label == "2020"
    assert data.value == 100.0

def test_metric_kpi_model():
    kpi = MetricKPI(
        id="population",
        title="Population",
        type="kpi",
        unit="inhabitants",
        source_dataset="Population Data",
        source_url="https://example.com",
        value=1000000,
        delta=10000,
        delta_label="vs 2019"
    )
    assert kpi.id == "population"
    assert kpi.value == 1000000
    assert kpi.delta == 10000

def test_metric_chart_model():
    chart = MetricChart(
        id="population_trend",
        title="Population Trend",
        type="line_chart",
        unit="inhabitants",
        source_dataset="Population Data",
        source_url="https://example.com",
        data=[DataPoint(label="2020", value=1000000), DataPoint(label="2021", value=1010000)]
    )
    assert chart.id == "population_trend"
    assert len(chart.data) == 2

def test_dashboard_data_model():
    dashboard = DashboardData(
        city="Lyon",
        summary="Test summary",
        metrics=[]
    )
    assert dashboard.city == "Lyon"
    assert dashboard.summary == "Test summary"

def test_dashboard_data_with_metrics():
    dashboard = DashboardData(
        city="Lyon",
        summary="Test summary",
        metrics=[
            MetricKPI(
                id="population",
                title="Population",
                type="kpi",
                unit="inhabitants",
                source_dataset="Population Data",
                source_url="https://example.com",
                value=1000000
            )
        ]
    )
    assert len(dashboard.metrics) == 1
    assert dashboard.metrics[0].id == "population"


def test_source_url_rejects_javascript():
    """source_url must be https, not javascript: (XSS prevention)."""
    with pytest.raises(ValidationError):
        MetricKPI(
            id="x",
            title="X",
            type="kpi",
            unit="",
            source_dataset="",
            source_url="javascript:alert(1)",
            value=1,
        )


def test_source_url_rejects_http():
    """source_url must be https, not http."""
    with pytest.raises(ValidationError):
        MetricKPI(
            id="x",
            title="X",
            type="kpi",
            unit="",
            source_dataset="",
            source_url="http://example.com",
            value=1,
        )


def test_source_url_accepts_https():
    """source_url accepts valid https URLs."""
    kpi = MetricKPI(
        id="x",
        title="X",
        type="kpi",
        unit="",
        source_dataset="",
        source_url="https://www.data.gouv.fr/fr/datasets/example/",
        value=1,
    )
    assert kpi.source_url == "https://www.data.gouv.fr/fr/datasets/example/"


def test_dashboard_request_max_length():
    """City input has max length to prevent DoS."""
    DashboardRequest(city="Lyon")
    DashboardRequest(city="A" * 200)
    with pytest.raises(ValidationError):
        DashboardRequest(city="A" * 201)


def test_tts_request_max_length():
    """TTS text has max length to prevent DoS."""
    TTSRequest(text="Hello")
    TTSRequest(text="A" * 5000)
    with pytest.raises(ValidationError):
        TTSRequest(text="A" * 5001)

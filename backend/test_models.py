import pytest
from models import DashboardData, MetricKPI, MetricChart, DataPoint

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

export type MetricType = "kpi" | "line_chart" | "bar_chart";

export interface DataPoint {
  label: string;
  value: number;
}

export interface MetricBase {
  id: string;
  title: string;
  type: MetricType;
  unit: string;
  source_dataset: string;
  source_url: string;
}

export interface MetricKPI extends MetricBase {
  type: "kpi";
  value: number | string;
  delta: number | null;
  delta_label: string | null;
}

export interface MetricChart extends MetricBase {
  type: "line_chart" | "bar_chart";
  data: DataPoint[];
}

export type Metric = MetricKPI | MetricChart;

export interface DashboardData {
  city: string;
  summary: string;
  metrics: Metric[];
}

export interface DashboardResponse {
  data: DashboardData;
  duration_seconds: number;
  iterations: number;
}
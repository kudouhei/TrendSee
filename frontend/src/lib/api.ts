import axios from "axios";

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1",
  timeout: 60000,
});

// ── Types ─────────────────────────────────────────────────────────────────────

export interface DashboardStats {
  total_items: number;
  total_reports: number;
  total_content: number;
  total_jobs: number;
  platform_distribution: Record<string, number>;
  recent_reports: ReportSummary[];
}

export interface ReportSummary {
  id: number;
  module: string;
  title: string;
  period_label: string;
  total_items: number;
  top_topics: string[];
  created_at: string;
}

export interface Report extends ReportSummary {
  platforms: string[];
  trend_chart_data: Record<string, unknown>;
  executive_summary: string;
  deep_insights: DeepInsight[] | string[];
}

export interface DeepInsight {
  title?: string;
  body?: string;
  implication?: string;
}

export interface GeneratedContent {
  id: number;
  output_platform: string;
  content_type: string;
  title: string;
  body: string;
  hashtags: string[];
  cover_prompt: string;
  meta: Record<string, unknown>;
  created_at: string;
}

export interface RawItem {
  id: number;
  platform: string;
  title: string;
  author: string;
  url: string;
  likes: number;
  comments: number;
  collects: number;
  shares: number;
  tags: string[];
  collected_at: string;
}

export interface CollectionJob {
  id: number;
  job_type: string;
  status: string;
  params: Record<string, unknown>;
  result_summary: Record<string, unknown> | null;
  error_message: string | null;
  started_at: string | null;
  finished_at: string | null;
  created_at: string;
}

// ── API calls ─────────────────────────────────────────────────────────────────

export const getDashboardStats = () =>
  api.get<DashboardStats>("/dashboard/stats").then((r) => r.data);

export const getReports = (module?: string) =>
  api.get<ReportSummary[]>("/reports", { params: { module, limit: 50 } }).then((r) => r.data);

export const getReport = (id: number) =>
  api.get<Report>(`/reports/${id}`).then((r) => r.data);

export const getReportContent = (id: number) =>
  api.get<GeneratedContent[]>(`/reports/${id}/content`).then((r) => r.data);

export const getRawItems = (platform?: string, limit = 50) =>
  api.get<RawItem[]>("/items", { params: { platform, limit } }).then((r) => r.data);

export const getJobs = () =>
  api.get<CollectionJob[]>("/jobs").then((r) => r.data);

export const runTrendRadar = (payload: {
  keywords: string[];
  platforms: string[];
  period: string;
  limit_per_source: number;
  date_from?: string;
  date_to?: string;
}) => api.post<Report>("/modules/trend-radar/run-now", payload).then((r) => r.data);

export const runCommentMining = (payload: {
  topic: string;
  platforms: string[];
  limit_per_source: number;
}) => api.post("/modules/comment-mining/run-now", payload).then((r) => r.data);

export const runViralAnatomy = (payload: {
  topic: string;
  platforms: string[];
  limit_per_source: number;
}) => api.post("/modules/viral-anatomy/run-now", payload).then((r) => r.data);

export const runVerticalDeep = (payload: {
  vertical: string;
  sub_topics: string[];
  platforms: string[];
  output_types: string[];
  limit_per_source: number;
}) => api.post("/modules/vertical-deep/run-now", payload).then((r) => r.data);

export const generateContent = (reportId: number, outputPlatforms: string[]) =>
  api.post("/content/generate", { report_id: reportId, output_platforms: outputPlatforms }, { timeout: 180000 }).then((r) => r.data);

export const regenerateNarrative = (reportId: number) =>
  api.post(`/reports/${reportId}/regenerate-narrative`, {}, { timeout: 120000 }).then((r) => r.data);

export const triggerCollect = (platform: string, keyword = "", limit = 50) =>
  api.post("/collect", { platform, keyword, limit }).then((r) => r.data);

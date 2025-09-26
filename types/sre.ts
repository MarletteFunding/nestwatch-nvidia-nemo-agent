export type SREEvent = {
  id: string;
  slack_id: string;
  summary: string;
  status: "Open" | "In Progress" | "Resolved";
  priority: "P1" | "P2" | "P3";
  source: "jira" | "datadog" | "jams";
  timestamp: string;
};

export type Action = {
  provider: "slack" | "jira" | "datadog" | "jams" | "confluence";
  operation: string;
  params: Record<string, any>;
  why: string;
  risk: string;
  rollback: string;
  requires_approval: boolean;
  dry_run: boolean;
  idempotency_key: string;
};

export type EventAnalysis = {
  window: string;
  totals: number;
  by_priority: { P1: number; P2: number; P3: number };
  by_source: { jira?: number; datadog?: number; jams?: number };
  clusters: {
    theme: string;
    count: number;
    representatives: string[];
    suggested_owner: string;
  }[];
  top_events: {
    id: string;
    priority: "P1" | "P2" | "P3";
    source: "jira" | "datadog" | "jams";
    why_top: string;
  }[];
  recommendations: string[];
  actions: Action[];
  next_data_to_fetch: string[];
};

export type EnhancedSummaryResponse = {
  json: EventAnalysis;
  summary: string;
};

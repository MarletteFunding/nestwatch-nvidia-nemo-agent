# Event Analysis V1

Task: Event Analysis for a batch of SRE events.

Input context (provided by caller):

- A compact rollup of counts by priority/source, time window, and up to 12 representative event snippets (id, source, priority, short summary).

Output profile: profile=json or profile=chat.

Return format (in this order):
1) JSON conforming to schema event_analysis_v1.json
2) (only if profile=chat) A brief human summary (≤8 lines).

Behavior:

- Prioritize P1/P2 open events. For P3, cluster by theme and recommend batch actions.
- Limit the "top_events" list to ≤10 items, sorted by business impact heuristic.
- Produce actionable, integration-ready Actions (Slack/Jira/Datadog/JAMS) for triage and follow-ups.
- Keep text short; prefer lists over paragraphs.

Heuristics:

- Severity order: P1>P2>P3; Open > In Progress > Resolved; Newer > Older.
- Impact hints in summary raise weight: ["payment","checkout","auth","login","api-gw","db","kafka","timeout","5xx"].
- Source weighting (tunable): jira=1.0, datadog=0.9, jams=0.7 unless keywords increase impact.

Do not include prose outside the required outputs.

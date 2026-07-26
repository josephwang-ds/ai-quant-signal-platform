/** Phase 5 reproducibility metadata attached to research evidence artifacts. */

export type ReproducibilityManifest = {
  data_source: string;
  symbol: string | string[] | Record<string, unknown>;
  universe: string | string[] | Record<string, unknown> | null;
  requested_start_date: string;
  requested_end_date: string;
  actual_start_date: string;
  actual_end_date: string;
  retrieval_timestamp: string;
  row_count: number | string;
  adjustment_mode: string;
  protocol_version: string;
  protocol_hash: string;
  data_hash: string;
  engine_version: string;
  git_commit_sha: string;
  runtime_version: string;
  created_at: string;
};

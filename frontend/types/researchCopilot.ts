export type GroundingStatus = "grounded" | "partially_grounded" | "unavailable";

export type EvidenceCitation = {
  source_type: string;
  source_id: string;
  label: string;
  excerpt: string;
};

export type CopilotWarning = {
  code: string;
  message: string;
};

export type ResearchCopilotResult = {
  research_id: string;
  answer: string;
  citations: EvidenceCitation[];
  warnings: CopilotWarning[];
  grounding_status: GroundingStatus;
  model: string;
  generated_at: string;
};

export type ResearchCopilotRequestStatus =
  | "idle"
  | "awaiting_validation"
  | "loading"
  | "ready"
  | "error";

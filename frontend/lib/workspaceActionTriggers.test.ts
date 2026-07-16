import { describe, expect, it } from "vitest";
import {
  canRequestEvaluation,
  shouldReloadEvaluationOnAction,
  shouldReloadValidationOnAction,
} from "@/lib/workspaceActionTriggers";

describe("workspace action triggers", () => {
  it("lets the Validation tab hook own the first request after navigation", () => {
    expect(shouldReloadValidationOnAction(false)).toBe(false);
  });

  it("reloads Validation exactly when evidence fetch is already active", () => {
    expect(shouldReloadValidationOnAction(true)).toBe(true);
  });

  it("blocks Evaluation without validation_run_id", () => {
    expect(canRequestEvaluation(null)).toBe(false);
    expect(shouldReloadEvaluationOnAction(null, "evaluation")).toBe(false);
  });

  it("navigates to Evaluation without reload on first open", () => {
    expect(canRequestEvaluation("val-1")).toBe(true);
    expect(shouldReloadEvaluationOnAction("val-1", "validation")).toBe(false);
  });

  it("reloads Evaluation only when already on the Evaluation tab", () => {
    expect(shouldReloadEvaluationOnAction("val-1", "evaluation")).toBe(true);
  });
});

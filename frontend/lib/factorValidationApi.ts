/**
 * Client for POST /api/v1/research/factor-validation.
 * Browser never calculates RankIC or quantile metrics.
 */

import { CANONICAL_FACTOR_RESEARCH_ID } from "@/lib/canonicalCrossSectionalFactor";
import {
  API_REQUEST_TIMEOUT_MS,
  ApiRequestError,
  requestJson,
} from "@/lib/apiRequest";
import type { FactorValidationResult } from "@/types/factorValidation";
import type { FactorRunConfiguration } from "@/types/research";

export { ApiRequestError as FactorValidationApiError };

const DEFAULT_CONFIGURATION: FactorRunConfiguration = {
  templateId: "cross_sectional_factor",
  universeId: "us_sector_etfs",
  factorId: "momentum",
  rebalanceFrequency: "monthly",
  holdingPeriodMonths: 1,
  startDate: "2018-01-01",
  endDate: null,
  transactionCost: 0.001,
};

export async function fetchFactorValidation(options?: {
  signal?: AbortSignal;
  researchId?: string;
  configuration?: FactorRunConfiguration;
}): Promise<FactorValidationResult> {
  const configuration = options?.configuration ?? DEFAULT_CONFIGURATION;
  return requestJson<FactorValidationResult>(
    "/api/v1/research/factor-validation",
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      signal: options?.signal,
      body: JSON.stringify({
        research_id: options?.researchId ?? CANONICAL_FACTOR_RESEARCH_ID,
        universe_id: configuration.universeId,
        factor_id: configuration.factorId,
        rebalance_frequency: configuration.rebalanceFrequency,
        holding_period_months: configuration.holdingPeriodMonths,
        start_date: configuration.startDate,
        end_date: configuration.endDate,
        transaction_cost: configuration.transactionCost,
      }),
    },
    { timeoutMs: Math.max(API_REQUEST_TIMEOUT_MS, 120_000) }
  );
}

/**
 * Research List mock 数据源。
 *
 * TODO(backend): 替换为 GET /api/research（list）响应映射。
 * TODO(database): 当前无持久化；仅内存演示。
 */

import type { ResearchListItem } from "@/types/research";

export const MOCK_RESEARCH_PROJECTS: ResearchListItem[] = [
  {
    id: "rs-momentum-001",
    name: "Momentum Strategy",
    researchQuestion:
      "Does 12–1 month cross-sectional momentum remain significant after costs on liquid US equities?",
    status: "Running",
    confidenceScore: 62,
    owner: "A. Chen",
    tags: ["momentum", "equities", "cross-sectional"],
    createdAt: "2026-03-12T09:20:00.000Z",
    updatedAt: "2026-07-10T14:05:00.000Z",
    experimentCount: 14,
    lastValidation: "Walk-forward fold 3/5 in progress",
    currentRecommendation: "Continue; freeze universe before next OOS fold",
  },
  {
    id: "rs-rsi-002",
    name: "RSI Mean Reversion",
    researchQuestion:
      "Can RSI(14) oversold entries on large-cap names deliver positive expectancy with a 5-day exit?",
    status: "Review",
    confidenceScore: 48,
    owner: "M. Okonkwo",
    tags: ["mean-reversion", "RSI", "short-horizon"],
    createdAt: "2026-02-04T11:00:00.000Z",
    updatedAt: "2026-07-08T16:40:00.000Z",
    experimentCount: 9,
    lastValidation: "OOS Sharpe 0.41; sample thin in 2022 regime",
    currentRecommendation: "Request risk review before paper allocation",
  },
  {
    id: "rs-pairs-003",
    name: "Pairs Trading",
    researchQuestion:
      "Do cointegrated sector ETF pairs sustain half-life and z-score edges after 2020 microstructure shifts?",
    status: "Validated",
    confidenceScore: 71,
    owner: "S. Patel",
    tags: ["pairs", "cointegration", "ETF"],
    createdAt: "2025-11-18T08:15:00.000Z",
    updatedAt: "2026-06-28T10:12:00.000Z",
    experimentCount: 22,
    lastValidation: "Passed holdout + cost stress at 8 bps",
    currentRecommendation: "Approve for limited paper trading book",
  },
  {
    id: "rs-vol-004",
    name: "Volatility Breakout",
    researchQuestion:
      "Does a 20-day realized-vol breakout on SPX futures improve risk-adjusted returns versus buy-and-hold?",
    status: "Paper Trading",
    confidenceScore: 58,
    owner: "J. Morales",
    tags: ["volatility", "breakout", "futures"],
    createdAt: "2025-09-02T13:45:00.000Z",
    updatedAt: "2026-07-09T09:30:00.000Z",
    experimentCount: 17,
    lastValidation: "Paper day 47; max DD within gate",
    currentRecommendation: "Keep paper; review after 90 trading days",
  },
  {
    id: "rs-etf-005",
    name: "ETF Rotation",
    researchQuestion:
      "Can dual-momentum rotation across sector ETFs beat a 60/40 benchmark on a monthly rebalance?",
    status: "Monitoring",
    confidenceScore: 66,
    owner: "L. Bergström",
    tags: ["rotation", "ETF", "allocation"],
    createdAt: "2025-06-21T10:00:00.000Z",
    updatedAt: "2026-07-07T18:22:00.000Z",
    experimentCount: 31,
    lastValidation: "Live monitor healthy; regime flag amber",
    currentRecommendation: "Maintain; escalate if correlation cluster rises",
  },
  {
    id: "rs-factor-006",
    name: "Factor Timing",
    researchQuestion:
      "Can value–momentum relative strength time factor tilts without excessive turnover?",
    status: "Draft",
    confidenceScore: 28,
    owner: "A. Chen",
    tags: ["factors", "timing", "value"],
    createdAt: "2026-07-01T07:50:00.000Z",
    updatedAt: "2026-07-06T12:10:00.000Z",
    experimentCount: 2,
    lastValidation: "No formal validation yet",
    currentRecommendation: "Define falsification criteria before scoping experiments",
  },
  {
    id: "rs-macro-007",
    name: "Macro Allocation",
    researchQuestion:
      "Do simple growth/inflation regime maps improve multi-asset risk parity overlays?",
    status: "Running",
    confidenceScore: 44,
    owner: "H. Nakamura",
    tags: ["macro", "multi-asset", "regimes"],
    createdAt: "2026-01-15T15:20:00.000Z",
    updatedAt: "2026-07-11T08:05:00.000Z",
    experimentCount: 11,
    lastValidation: "Sensitivity to CPI revision lag unfinished",
    currentRecommendation: "Complete lag robustness before synthesis",
  },
  {
    id: "rs-sector-008",
    name: "Sector Momentum",
    researchQuestion:
      "Is industry-level momentum robust after excluding the top liquidity quintile?",
    status: "Archived",
    confidenceScore: 35,
    owner: "M. Okonkwo",
    tags: ["sector", "momentum", "liquidity"],
    createdAt: "2025-04-09T09:00:00.000Z",
    updatedAt: "2026-05-19T11:45:00.000Z",
    experimentCount: 18,
    lastValidation: "Rejected: edge disappears under realistic capacity",
    currentRecommendation: "Archive; reopen only with new capacity model",
  },
];

/** 返回可变更的列表副本，避免页面状态污染模块常量。 */
export function getMockResearchProjects(): ResearchListItem[] {
  return MOCK_RESEARCH_PROJECTS.map((item) => ({
    ...item,
    tags: [...item.tags],
  }));
}

export class MockResearchListError extends Error {
  constructor(message = "Unable to load the research workspace.") {
    super(message);
    this.name = "MockResearchListError";
  }
}

function delay(ms: number): Promise<void> {
  return new Promise((resolve) => {
    setTimeout(resolve, ms);
  });
}

/**
 * 模拟异步列表加载（无网络、无后端）。
 *
 * - 默认成功返回 8 个项目
 * - URL `?mockError=1` 用于演示 Error 态（截图 / QA）
 *
 * TODO(backend): 替换为 listResearch() API 客户端。
 */
export async function loadMockResearchProjects(options?: {
  delayMs?: number;
}): Promise<ResearchListItem[]> {
  await delay(options?.delayMs ?? 480);

  if (typeof window !== "undefined") {
    const params = new URLSearchParams(window.location.search);
    if (params.get("mockError") === "1") {
      throw new MockResearchListError(
        "Mock load failed. Remove mockError=1 from the URL or retry."
      );
    }
  }

  return getMockResearchProjects();
}

import { expect, test } from "@playwright/test";

const FORBIDDEN = [
  "SUPABASE_DB_URL",
  "traceback",
  "Traceback",
  "No module named",
  "stack trace",
];

async function assertSafePage(page: import("@playwright/test").Page) {
  const body = await page.locator("body").innerText();
  for (const bad of FORBIDDEN) {
    expect(body).not.toContain(bad);
  }
  await expect(page.locator("h1")).toHaveCount(1);
}

test.describe("Demo navigation smoke", () => {
  test("primary nav exposes Intelligence and Research Engine destinations", async ({
    page,
  }) => {
    await page.goto("/");
    const nav = page.getByRole("navigation", { name: /primary|主导航/i });
    const links = nav.locator("a.workspace-sidenav__item");
    await expect(links.first()).toBeVisible();
    const count = await links.count();
    expect(count).toBeGreaterThanOrEqual(8);

    const routes = [
      "/",
      "/platform",
      "/intelligence/research",
      "/engine",
      "/engine/portfolio",
      "/data-center",
    ];
    for (const route of routes) {
      await page.goto(route);
      await assertSafePage(page);
    }
  });

  test("retired routes redirect into the research spine", async ({ page }) => {
    await page.goto("/overview");
    await expect(page).toHaveURL(/\/platform$/);

    await page.goto("/legacy");
    await expect(page).toHaveURL(/\/platform$/);

    await page.goto("/risk-gate-review");
    await expect(page).toHaveURL(/engine\/research\/ma-crossover-spy.*tab=robustness/);
  });

  test("Strategy Studio keeps backtest enabled when archive is optional", async ({
    page,
  }) => {
    await page.goto("/strategy-lab");
    await expect(page.getByTestId("strategy-lab-run-backtest")).toBeEnabled();
    const save = page.getByTestId("strategy-lab-save-run");
    await expect(save).toBeDisabled();
    await assertSafePage(page);
  });

  test("/experiments redirects into the Backtesting engine stage", async ({
    page,
  }) => {
    await page.goto("/experiments");
    await expect(page).toHaveURL(/\/engine\/backtest/);
    await expect(page.getByTestId("engine-stage-page")).toHaveAttribute(
      "data-stage",
      "backtest"
    );
    await assertSafePage(page);
  });

  test("Chinese chrome stays readable on Research Library", async ({ page }) => {
    await page.goto("/");
    await page.getByRole("button", { name: /中文|中/ }).first().click();
    await expect(page.locator("h1")).toBeVisible();
    const body = await page.locator("body").innerText();
    expect(body).toMatch(/研究资料库|已发布|证据/);
  });
});

test.describe("Research Library → Workspace spine", () => {
  test("Research Library surfaces empty or list state without layout crash", async ({
    page,
  }) => {
    await page.goto("/");
    await expect(page.getByTestId("research-library")).toBeVisible();
    await expect(page.locator("h1")).toHaveText(/Research Library|研究资料库/);
    await expect(
      page.getByTestId("research-library-empty").or(page.getByTestId("published-runs-section")).or(page.getByTestId("research-library-error")).or(page.getByTestId("research-library-loading"))
    ).toBeVisible({ timeout: 15_000 });
    await assertSafePage(page);

    const libraryNav = page.locator('a.workspace-sidenav__item[href="/"]');
    await expect(libraryNav).toHaveAttribute("aria-current", "page");
  });

  test("Platform Overview → Research Engine → Active Workspace Trend demo", async ({
    page,
  }) => {
    await page.goto("/platform");
    await expect(page.getByTestId("platform-home-hero")).toBeVisible();
    await page.getByTestId("open-research-engine").click();
    await expect(page).toHaveURL(/\/engine$/);
    await expect(page.getByTestId("guided-workflow")).toBeVisible();
    await expect(page.getByTestId("workflow-continue")).toBeVisible();

    await page.getByTestId("open-trend-demo").click();
    await expect(page).toHaveURL(/\/engine\/research\/ma-crossover-spy/);
    await assertSafePage(page);

    for (const tab of ["overview", "validation", "robustness", "decision"] as const) {
      await page.goto(`/engine/research/ma-crossover-spy?tab=${tab}`);
      await expect(page.locator("h1")).toHaveCount(1);
      await assertSafePage(page);
    }

    await page.goto("/engine/research/ma-crossover-spy?tab=robustness");
    await expect(page.locator("h1")).toHaveCount(1);
    await expect(
      page.getByText(/stress test|robustness|walk-forward|challenge|稳健|压力|挑战/i).first()
    ).toBeVisible({ timeout: 15_000 });
    await assertSafePage(page);
  });

  test("legacy /research/catalog-id redirects into Active Workspace", async ({
    page,
  }) => {
    await page.goto("/research/ma-crossover-spy");
    await expect(page).toHaveURL(/\/engine\/research\/ma-crossover-spy/);
    await assertSafePage(page);
  });

  test("Agent execution trace stays collapsed by default when present", async ({
    page,
  }) => {
    await page.goto("/engine/research/ma-crossover-spy?tab=decision");
    const trace = page.locator("details.agent-execution-trace");
    if (await trace.count()) {
      await expect(trace.first()).not.toHaveAttribute("open", "");
    }
    await assertSafePage(page);
  });
});

test.describe("Mobile shell", () => {
  test.use({ viewport: { width: 390, height: 844 } });

  test("drawer opens without horizontal overflow", async ({ page }) => {
    await page.goto("/");
    const overflow = await page.evaluate(
      () =>
        document.documentElement.scrollWidth >
        document.documentElement.clientWidth + 1
    );
    expect(overflow).toBe(false);
    const menu = page.getByRole("button", {
      name: /menu|菜单|Open menu|打开菜单/i,
    });
    if (await menu.count()) {
      await menu.first().click();
      await expect(page.getByRole("navigation").first()).toBeVisible();
      await menu.first().click();
    }
    const h1Box = await page.locator("h1").boundingBox();
    expect(h1Box).toBeTruthy();
    if (h1Box) {
      expect(h1Box.width).toBeLessThanOrEqual(390);
    }
  });
});

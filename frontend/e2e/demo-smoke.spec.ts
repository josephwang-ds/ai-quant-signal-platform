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
  test("primary nav has five destinations and pages expose one h1", async ({
    page,
  }) => {
    await page.goto("/");
    const nav = page.getByRole("navigation", { name: /primary|主导航/i });
    const links = nav.locator("a.workspace-sidenav__item");
    await expect(links).toHaveCount(5);

    const routes = [
      "/",
      "/compare-models",
      "/strategy-lab",
      "/ai-insights",
      "/data-center",
    ];
    for (const route of routes) {
      await page.goto(route);
      await assertSafePage(page);
    }
  });

  test("retired routes redirect into the research spine", async ({ page }) => {
    await page.goto("/overview");
    await expect(page).toHaveURL(/\/$/);

    await page.goto("/legacy");
    await expect(page).toHaveURL(/\/$/);

    await page.goto("/risk-gate-review");
    await expect(page).toHaveURL(/research\/ma-crossover-spy.*tab=robustness/);
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

  test("Saved Runs optional state stays quiet without DB", async ({ page }) => {
    await page.route("**/health", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ status: "ok", service: "ai-quant-signal-backend" }),
      });
    });
    await page.route("**/api/database/status", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          configured: false,
          connected: false,
          message: "Database is not configured.",
          database: "supabase_postgres",
          persistence_mode: "browser-local",
        }),
      });
    });
    await page.route("**/api/experiments/**", async (route) => {
      await route.fulfill({
        status: 503,
        contentType: "application/json",
        body: JSON.stringify({ detail: "Persistent storage is not enabled." }),
      });
    });
    await page.goto("/experiments");
    await expect(
      page.getByText(/Saved-run storage is optional|可选数据库持久化/i)
    ).toBeVisible({ timeout: 15_000 });
    await assertSafePage(page);
    const body = await page.locator("body").innerText();
    expect(body).not.toContain("SUPABASE_DB_URL");
  });

  test("Chinese chrome stays readable on Research Home", async ({ page }) => {
    await page.goto("/");
    await page.getByRole("button", { name: /中文|中/ }).first().click();
    await expect(page.locator("h1")).toBeVisible();
    const body = await page.locator("body").innerText();
    expect(body).toMatch(/研究|证据|决策/);
  });
});

test.describe("Research workspace spine", () => {
  test("Research Home → Trend Following Study → Question/Evidence/Challenge/Decision", async ({
    page,
  }) => {
    await page.goto("/");
    await expect(page.getByTestId("research-persistence-mode")).toBeVisible();
    await expect(page.getByTestId("research-persistence-mode")).toHaveAttribute(
      "data-mode",
      /browser-local|persisted|persistence-unavailable/
    );

    const study = page.getByRole("link", {
      name: /Trend Following Study|趋势跟踪研究/i,
    });
    if (await study.count()) {
      await study.first().click();
    } else {
      await page.goto("/research/ma-crossover-spy");
    }
    await expect(page).toHaveURL(/\/research\/ma-crossover-spy/);
    await assertSafePage(page);

    // Research Home remains the active primary nav item while inside workspace.
    const homeNav = page.locator('a.workspace-sidenav__item[href="/"]');
    await expect(homeNav).toHaveAttribute("aria-current", "page");

    const tabs = page.getByRole("group", { name: /Research lifecycle/i });
    await expect(tabs).toBeVisible();

    for (const tab of ["overview", "validation", "robustness", "decision"] as const) {
      await page.goto(`/research/ma-crossover-spy?tab=${tab}`);
      await expect(page.locator("h1")).toHaveCount(1);
      await assertSafePage(page);
    }

    // Pressure-test / robustness is the Challenge step.
    await page.goto("/research/ma-crossover-spy?tab=robustness");
    await expect(page.locator("h1")).toHaveCount(1);
    await expect(
      page.getByText(/stress test|robustness|walk-forward|challenge|稳健|压力|挑战/i).first()
    ).toBeVisible({ timeout: 15_000 });
    await assertSafePage(page);
  });

  test("Agent execution trace stays collapsed by default when present", async ({
    page,
  }) => {
    await page.goto("/research/ma-crossover-spy?tab=decision");
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

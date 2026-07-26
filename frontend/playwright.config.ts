import { defineConfig, devices } from "@playwright/test";

/**
 * Minimal deterministic e2e suite for portfolio demo clarity.
 * Does not call live Yahoo/AkShare or real LLMs — UI structure + redirects only.
 */
const PORT = Number(process.env.PLAYWRIGHT_PORT || 3010);
const BASE_URL =
  process.env.PLAYWRIGHT_BASE_URL || `http://127.0.0.1:${PORT}`;

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: "list",
  use: {
    baseURL: BASE_URL,
    trace: "on-first-retry",
    screenshot: "only-on-failure",
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
    {
      name: "mobile",
      use: { ...devices["iPhone 12"] },
    },
  ],
  webServer: process.env.PLAYWRIGHT_SKIP_WEBSERVER
    ? undefined
    : {
        // Prefer production server — avoids Watchpack EMFILE on crowded CI/dev hosts.
        // Dedicated port so we never accidentally reuse an unrelated process on :3000.
        command: `npx next start --port ${PORT} --hostname 127.0.0.1`,
        url: BASE_URL,
        reuseExistingServer: false,
        timeout: 120_000,
      },
});

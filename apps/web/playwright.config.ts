import { defineConfig, devices } from "@playwright/test";

const externalServer = process.env.PLAYWRIGHT_EXTERNAL_SERVER === "1";

export default defineConfig({
  testDir: "./tests/e2e",
  timeout: 30_000,
  use: {
    baseURL: "http://127.0.0.1:3000",
    trace: "on-first-retry",
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
  ...(externalServer
    ? {}
    : {
        webServer: {
          command: "npx next dev -H 127.0.0.1",
          url: "http://127.0.0.1:3000",
          reuseExistingServer: true,
        },
      }),
});
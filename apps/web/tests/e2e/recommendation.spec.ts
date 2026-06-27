import path from "node:path";

import { test, expect, type Page } from "@playwright/test";

async function submitRecommendation(page: Page, options: { firstSubject: "physics" | "history"; score: string; rank: string; acceptSino?: boolean }) {
  await page.goto("/input");
  await page.locator('select').first().selectOption(options.firstSubject);
  await page.locator('input[name="score"]').fill(options.score);
  await page.locator('input[name="rank"]').fill(options.rank);
  if (options.acceptSino === false) {
    await page.getByLabel("\u63a5\u53d7\u4e2d\u5916\u5408\u4f5c").uncheck();
  }
  await page.getByRole("button", { name: /\u751f\u6210\u63a8\u8350/ }).click();
  await page.waitForURL(/\/result\//, { timeout: 20_000 });
  await expect(page.getByRole("heading", { name: "\u63a8\u8350\u7ed3\u679c" })).toBeVisible();
}

test("input page renders privacy-safe Hubei form", async ({ page }) => {
  await page.goto("/input");
  await expect(page.getByText("\u8f93\u5165\u8003\u751f\u4fe1\u606f")).toBeVisible();
  await expect(page.getByText("\u4e0d\u4f1a\u6536\u96c6\u59d3\u540d")).toBeVisible();
});

test("physics candidate can submit and see major-group results", async ({ page }) => {
  await submitRecommendation(page, { firstSubject: "physics", score: "610", rank: "26000" });
  await expect(page.getByText("Doctor.Peak").first()).toBeVisible();
  await expect(page.getByRole("heading", { name: "Doctor.Peak \u603b\u8bc4" })).toBeVisible();
  await expect(page.getByText("\u4e0b\u4e00\u6b65\u6838\u9a8c")).toBeVisible();
  await expect(page.getByText(/HBA\d{3}-P\d{2}/).first()).toBeVisible();
  await expect(page.getByText("\u9662\u6821\u4e13\u4e1a\u7ec4").first()).toBeVisible();
  await expect(page.getByText("\u6ce2\u52a8\u7cfb\u6570").first()).toBeVisible();
  await expect(page.getByText("\u4e13\u4e1a\u7ec4\u53d8\u5316").first()).toBeVisible();
  await expect(page.getByText("\u6765\u6e90\u8ffd\u6eaf").first()).toBeVisible();
});

test("history candidate results do not mix physics major groups", async ({ page }) => {
  await submitRecommendation(page, { firstSubject: "history", score: "585", rank: "18000" });
  await expect(page.getByText(/HBA\d{3}-H\d{2}/).first()).toBeVisible();
  await expect(page.getByText(/HBA\d{3}-P\d{2}/)).toHaveCount(0);
});

test("rejecting sino-foreign cooperation removes those projects", async ({ page }) => {
  await submitRecommendation(page, { firstSubject: "physics", score: "610", rank: "26000", acceptSino: false });
  await expect(page.getByText("\u4e2d\u5916\u5408\u4f5c\u9879\u76ee")).toHaveCount(0);
});

test("compare page generates five strategy recommendation plans", async ({ page }) => {
  await page.goto("/compare");
  await expect(page.getByRole("heading", { name: "\u65b9\u6848\u5bf9\u6bd4" })).toBeVisible();
  await page.getByRole("button", { name: "\u751f\u6210\u4e94\u7c7b\u65b9\u6848" }).click();

  await expect(page.getByText("\u5b66\u6821\u4f18\u5148").first()).toBeVisible({ timeout: 20_000 });
  await expect(page.getByText("\u4e13\u4e1a\u4f18\u5148").first()).toBeVisible();
  await expect(page.getByText("\u57ce\u5e02\u4f18\u5148").first()).toBeVisible();
  await expect(page.getByText("\u5c31\u4e1a\u4f18\u5148").first()).toBeVisible();
  await expect(page.getByText("\u5747\u8861\u65b9\u6848").first()).toBeVisible();
  await expect(page.getByRole("link", { name: "\u67e5\u770b\u7ed3\u679c" })).toHaveCount(5);
  await expect(page.getByText(/HBA\d{3}-P\d{2}/).first()).toBeVisible();
});

test("admin can upload a 2026 plan fixture, queue parse job, and run data quality checks", async ({ page }) => {
  const fixturePath = path.resolve(process.cwd(), "../../data/fixtures/hubei/hubei_sample_admission_plans_2026.csv");

  await page.goto("/admin");
  await expect(page.getByRole("heading", { name: "\u6570\u636e\u540e\u53f0" })).toBeVisible();
  await page.locator('input[name="hubei-plan-upload"]').setInputFiles(fixturePath);
  await page.getByRole("button", { name: "\u4e0a\u4f20\u62db\u751f\u8ba1\u5212" }).click();

  await expect(page.getByText("accepted_for_manual_review")).toBeVisible({ timeout: 10_000 });
  await expect(page.getByRole("cell", { name: "hubei_sample_admission_plans_2026.csv" })).toBeVisible();
  await expect(page.getByText("\u6709\u6548\u5019\u9009 108")).toBeVisible();

  await page.getByRole("button", { name: "\u6392\u961f\u89e3\u6790\u4efb\u52a1" }).click();
  await expect(page.getByRole("cell", { name: "hubei_plan_parse" }).first()).toBeVisible({ timeout: 10_000 });
  await expect(page.getByText("queued").first()).toBeVisible();

  await page.getByRole("button", { name: "\u8fd0\u884c\u6570\u636e\u8d28\u91cf\u68c0\u67e5" }).click();
  await expect(page.getByText(/\u8d28\u91cf\u68c0\u67e5\u5b8c\u6210/)).toBeVisible({ timeout: 10_000 });
  await expect(page.getByText(/\u53d1\u73b0 \d+ \u9879/)).toBeVisible();
});
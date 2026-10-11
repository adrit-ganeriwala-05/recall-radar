// Owner: D. F8 one-page check (PRD_v2 §4 F8.5): for 4 fixtures (long names, long recall text, empty data,
// many campaigns) the US Letter PDF printed by Chromium has exactly one page, and the report's text and
// links are present. /api/report is intercepted with the fixture; everything else is the real build.
// Needs C's mount: /vehicle/report?make&model&year.
import { readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { expect, test } from "@playwright/test";

const HERE = dirname(fileURLToPath(import.meta.url));
const FIXTURES = ["long-names", "long-recall-text", "empty", "many-campaigns"] as const;

function pdfPageCount(pdf: Buffer): number {
  return (pdf.toString("latin1").match(/\/Type\s*\/Page(?![s\w])/g) ?? []).length;
}

for (const name of FIXTURES) {
  test(`buyer report fits one Letter page: ${name}`, async ({ page }, info) => {
    test.skip(info.project.name !== "desktop", "PDF printing is checked once, in desktop Chromium");
    const data = JSON.parse(readFileSync(join(HERE, "fixtures", `report-${name}.json`), "utf8"));
    await page.route("**/api/report?*", (r) => r.fulfill({ json: data }));
    const v = data.vehicle;
    await page.goto(`/vehicle/report?${new URLSearchParams({ make: v.make, model: v.model, year: String(v.model_year) })}`);
    const report = page.getByTestId("buyer-report");
    const mounted = await report.waitFor({ timeout: 8_000 }).then(() => true, () => false);
    test.skip(!mounted && process.env.RR_RELEASE !== "1", "/vehicle/report is not mounted yet (C)");

    await expect(page.getByRole("button", { name: "Print / Save as PDF" })).toBeVisible();
    await expect(page.getByText("Download PDF")).toHaveCount(0);
    await page.emulateMedia({ media: "print" });
    await expect(report.getByRole("heading", { name: "Used-car complaint and recall summary" })).toBeVisible();
    await expect(report.getByText(`${v.model_year} ${v.make} ${v.model}`)).toBeVisible();
    await expect(report.getByText(/distinct NHTSA complaint IDs/)).toBeVisible();
    await expect(report.getByText(data.selection_rule, { exact: false })).toBeVisible();
    await expect(report.locator('a[href="https://www.nhtsa.gov/recalls"]').first()).toBeVisible();
    await expect(report.locator('a[href*="/vehicle?"]').first()).toBeVisible();
    for (const c of data.campaigns) await expect(report.getByRole("link", { name: c.campno })).toBeVisible();
    for (const g of data.top_groups) await expect(report.getByRole("link", { name: g.group.comp_system })).toBeVisible();
    await expect(page.getByRole("button", { name: "Print / Save as PDF" })).toBeHidden();
    const text = (await report.innerText()).toLowerCase();
    for (const banned of [/\bsafe\b/, /\bvin:/, /\bscore\b/, /failure rate/, /safer|less safe|more reliable/]) {
      expect(text).not.toMatch(banned);
    }

    const pdf = await page.pdf({ format: "Letter", printBackground: true });
    if (process.env.BR_PDF_DIR) writeFileSync(join(process.env.BR_PDF_DIR, `report-${name}.pdf`), pdf);
    expect(pdfPageCount(pdf)).toBe(1);
    const raw = pdf.toString("latin1");
    expect(raw).toContain("https://www.nhtsa.gov/recalls"); // link annotations survive printing
    for (const c of data.campaigns) if (c.source_url) expect(raw).toContain(c.source_url);
  });
}

// Owner: D. F5 browser check (PRD_v2 §4 F5.6–F5.8): fill → review → copy → link attributes, and the
// synthetic marker never appears in any network request, storage, cookie or the URL. Never submits to NHTSA.
// Needs C's mount: route /report (header link) and /report?make&model&year (vehicle page button).
import { expect, test } from "@playwright/test";

const SYNTH = "ZZQ-SYNTH-7741";

test("report a problem: draft, copy, NHTSA link; nothing leaves the page", async ({ page, context, browserName }) => {
  const seen: string[] = [];
  page.on("request", (r) => seen.push(`${r.method()} ${r.url()} ${r.postData() ?? ""}`));
  const logs: string[] = [];
  page.on("console", (m) => logs.push(m.text()));
  if (browserName === "chromium") await context.grantPermissions(["clipboard-read", "clipboard-write"]);

  await page.goto("/report?make=VOLKSWAGEN&model=JETTA&year=2019");
  const heading = page.getByRole("heading", { name: "Report a problem to NHTSA" });
  // Before C mounts /report the route does not exist; a release run (RR_RELEASE=1) must fail instead.
  const mounted = await heading.waitFor({ timeout: 5_000 }).then(() => true, () => false);
  test.skip(!mounted && process.env.RR_RELEASE !== "1", "/report is not mounted yet (C)");
  await expect(heading).toBeVisible();
  await expect(page.getByLabel("Make")).toHaveValue("VOLKSWAGEN");
  await expect(page.getByText("This draft is not saved if you close or refresh the page.")).toBeVisible();

  await page.getByLabel(/What happened\?/).fill(`Brakes made a grinding noise near ${SYNTH}.`);
  await page.getByRole("group", { name: /crash/ }).getByLabel("Unknown").check();
  await page.getByRole("button", { name: "Review the draft" }).click();
  const draft = page.getByLabel("Review and edit the draft");
  await expect(draft).toHaveValue(/Crash: unknown/);
  await draft.fill(`${await draft.inputValue()}\nEdited ${SYNTH}`);
  await page.getByRole("button", { name: "Continue" }).click();

  await expect(page.getByRole("heading", { name: "Draft ready" })).toBeVisible();
  await expect(page.getByText("Your complaint is submitted only after you complete NHTSA's form.")).toBeVisible();
  const link = page.getByRole("link", { name: "Continue to NHTSA" });
  await expect(link).toHaveAttribute("href", "https://www.nhtsa.gov/report-a-safety-problem");
  await expect(link).toHaveAttribute("target", "_blank");
  await expect(link).toHaveAttribute("rel", "noopener noreferrer");

  await page.getByRole("button", { name: "Copy draft" }).click();
  if (browserName === "chromium") {
    await expect(page.getByText("Copied", { exact: true })).toBeVisible();
    expect(await page.evaluate(() => navigator.clipboard.readText())).toContain(SYNTH);
  } else {
    // other engines may refuse clipboard access in automation: the fallback must appear instead
    await expect(page.getByText("Copied", { exact: true }).or(page.getByLabel("Draft text to copy"))).toBeVisible();
  }

  // the link is not followed (nothing is ever submitted); only its attributes are checked above
  const state = await page.evaluate(() => ({
    url: location.href,
    cookies: document.cookie,
    storage: JSON.stringify({ ...localStorage }) + JSON.stringify({ ...sessionStorage }),
  }));
  expect(state.url).not.toContain(SYNTH);
  expect(state.cookies).not.toContain(SYNTH);
  expect(state.storage).not.toContain(SYNTH);
  expect(seen.filter((s) => s.includes(SYNTH))).toEqual([]);
  expect(logs.filter((s) => s.includes(SYNTH))).toEqual([]);
});

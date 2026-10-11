// Owner: D. F5 (PRD_v2 §4 F5.4): the complaint draft is built only from the answers the person gave.
// No causes, no defect links, no recall or investigation text. Their own words are copied verbatim.

export type Answer3 = "" | "yes" | "no" | "unknown"; // "" = not answered (no default)
export type Frequency = "" | "once" | "repeatedly" | "unknown";
export type DateMode = "" | "exact" | "approximate" | "unknown";
export type MileageMode = "" | "number" | "unknown";

export interface ReportAnswers {
  make: string;
  model: string;
  year: string;
  dateMode: DateMode;
  exactDate: string; // YYYY-MM-DD from <input type="date">
  approxMonth: string; // "" or "1".."12"
  approxYear: string;
  mileageMode: MileageMode;
  mileage: string; // digits only
  description: string;
  frequency: Frequency;
  crash: Answer3;
  fire: Answer3;
  injury: Answer3;
}

export const EMPTY_ANSWERS: ReportAnswers = {
  make: "",
  model: "",
  year: "",
  dateMode: "",
  exactDate: "",
  approxMonth: "",
  approxYear: "",
  mileageMode: "",
  mileage: "",
  description: "",
  frequency: "",
  crash: "",
  fire: "",
  injury: "",
};

export const MONTHS = [
  "January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December",
] as const;

export function incidentDateText(a: ReportAnswers): string | null {
  if (a.dateMode === "unknown") return "unknown";
  if (a.dateMode === "exact") return a.exactDate.trim() || null;
  if (a.dateMode === "approximate") {
    const y = a.approxYear.trim();
    if (!y) return null;
    const m = Number(a.approxMonth);
    return m >= 1 && m <= 12 ? `approximately ${MONTHS[m - 1]} ${y}` : `approximately ${y}`;
  }
  return null;
}

export function mileageText(a: ReportAnswers): string | null {
  if (a.mileageMode === "unknown") return "unknown";
  if (a.mileageMode === "number" && /^\d+$/.test(a.mileage.trim())) return `${a.mileage.trim()} miles`;
  return null;
}

const ANSWER_TEXT: Record<Exclude<Answer3, "">, string> = { yes: "yes", no: "no", unknown: "unknown" };

/** The draft text. Lines for unanswered questions are left out; "unknown" is written only when chosen. */
export function buildDraft(a: ReportAnswers): string {
  const lines: string[] = [];
  const vehicle = [a.year.trim(), a.make.trim(), a.model.trim()].filter(Boolean).join(" ");
  if (vehicle) lines.push(`Vehicle: ${vehicle}`);
  const date = incidentDateText(a);
  if (date) lines.push(`Date of the incident: ${date}`);
  const miles = mileageText(a);
  if (miles) lines.push(`Mileage at the time: ${miles}`);
  if (a.frequency) lines.push(`How often it happened: ${a.frequency}`);
  if (a.crash) lines.push(`Crash: ${ANSWER_TEXT[a.crash]}`);
  if (a.fire) lines.push(`Fire: ${ANSWER_TEXT[a.fire]}`);
  if (a.injury) lines.push(`Injury: ${ANSWER_TEXT[a.injury]}`);
  if (a.description.trim()) {
    lines.push("", "What happened, in my words:", a.description);
  }
  return lines.join("\n");
}

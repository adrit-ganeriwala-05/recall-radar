// Owner: D. F5 Report a problem → NHTSA (PRD_v2 §4 F5). C mounts <ReportProblem/> in the header
// (no vehicle) and on the vehicle page (prefilled). Everything lives in React state only: nothing is
// written to storage, cookies, the URL, the network or the console, and nothing is sent to NHTSA.
import { useId, useRef, useState, type ReactNode } from "react";
import type { VehicleKey } from "../../contracts.gen";
import "./report.css";
import {
  buildDraft,
  EMPTY_ANSWERS,
  MONTHS,
  type Answer3,
  type DateMode,
  type Frequency,
  type MileageMode,
  type ReportAnswers,
} from "./template";

export const NHTSA_REPORT_URL = "https://www.nhtsa.gov/report-a-safety-problem";
export const NOT_SAVED_TEXT = "This draft is not saved if you close or refresh the page.";
export const SUBMIT_NOTE = "Your complaint is submitted only after you complete NHTSA's form.";

type Step = 1 | 2 | 3;
type CopyState = "idle" | "copied" | "failed";

function initial(v?: VehicleKey): ReportAnswers {
  return v ? { ...EMPTY_ANSWERS, make: v.make, model: v.model, year: String(v.model_year) } : { ...EMPTY_ANSWERS };
}

function Choice<T extends string>(props: {
  legend: string;
  name: string;
  value: T;
  options: { value: T; label: string }[];
  onChange: (v: T) => void;
  optional?: boolean;
}) {
  return (
    <fieldset className="rp-choice">
      <legend>
        {props.legend}
        {props.optional && <span className="small"> (optional)</span>}
      </legend>
      {props.options.map((o) => (
        <label key={o.value}>
          <input
            type="radio"
            name={props.name}
            value={o.value}
            checked={props.value === o.value}
            onChange={() => props.onChange(o.value)}
          />{" "}
          {o.label}
        </label>
      ))}
    </fieldset>
  );
}

const YES_NO_UNKNOWN: { value: Answer3; label: string }[] = [
  { value: "yes", label: "Yes" },
  { value: "no", label: "No" },
  { value: "unknown", label: "Unknown" },
];

export function ReportProblem({ initialVehicle }: { initialVehicle?: VehicleKey }) {
  const [step, setStep] = useState<Step>(1);
  const [a, setA] = useState<ReportAnswers>(() => initial(initialVehicle));
  const [draft, setDraft] = useState("");
  const [generated, setGenerated] = useState(""); // the text last produced by the template
  const [confirmRegen, setConfirmRegen] = useState(false);
  const [copy, setCopy] = useState<CopyState>("idle");
  const fallbackRef = useRef<HTMLTextAreaElement>(null);
  const uid = useId(); // two instances (header + vehicle page) must not share radio names or ids

  const edited = draft !== generated;
  const set = <K extends keyof ReportAnswers>(k: K, v: ReportAnswers[K]) => setA((p) => ({ ...p, [k]: v }));
  const mileageInvalid = a.mileageMode === "number" && a.mileage.trim() !== "" && !/^\d+$/.test(a.mileage.trim());
  const canReview = a.description.trim() !== "" && !mileageInvalid;

  function toReview() {
    // A manual edit is never overwritten by navigation; only an explicit, confirmed regenerate replaces it.
    if (!edited) {
      const text = buildDraft(a);
      setDraft(text);
      setGenerated(text);
    }
    setConfirmRegen(false);
    setStep(2);
  }

  function regenerate() {
    const text = buildDraft(a);
    setDraft(text);
    setGenerated(text);
    setConfirmRegen(false);
  }

  function clearAll() {
    setA(initial(initialVehicle));
    setDraft("");
    setGenerated("");
    setConfirmRegen(false);
    setCopy("idle");
    setStep(1);
  }

  async function copyDraft() {
    setCopy("idle");
    try {
      if (!navigator.clipboard?.writeText) throw new Error("clipboard unavailable");
      await navigator.clipboard.writeText(draft);
      setCopy("copied");
    } catch {
      setCopy("failed");
    }
  }

  let body: ReactNode;
  if (step === 1) {
    body = (
      <form
        className="rp-form"
        onSubmit={(e) => {
          e.preventDefault();
          if (canReview) toReview();
        }}
      >
        <div className="rp-vehicle">
          <label>
            Make <input value={a.make} onChange={(e) => set("make", e.target.value)} autoComplete="off" />
          </label>
          <label>
            Model <input value={a.model} onChange={(e) => set("model", e.target.value)} autoComplete="off" />
          </label>
          <label>
            Year{" "}
            <input value={a.year} inputMode="numeric" onChange={(e) => set("year", e.target.value)} autoComplete="off" />
          </label>
        </div>

        <Choice<DateMode>
          legend="When did it happen?"
          name={`${uid}-date`}
          optional
          value={a.dateMode}
          onChange={(v) => set("dateMode", v)}
          options={[
            { value: "exact", label: "Exact date" },
            { value: "approximate", label: "Approximate month and year" },
            { value: "unknown", label: "Unknown" },
          ]}
        />
        {a.dateMode === "exact" && (
          <label>
            Date <input type="date" value={a.exactDate} onChange={(e) => set("exactDate", e.target.value)} />
          </label>
        )}
        {a.dateMode === "approximate" && (
          <div className="rp-row">
            <label>
              Month{" "}
              <select value={a.approxMonth} onChange={(e) => set("approxMonth", e.target.value)}>
                <option value="">Not sure</option>
                {MONTHS.map((m, i) => (
                  <option key={m} value={String(i + 1)}>
                    {m}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Year{" "}
              <input
                value={a.approxYear}
                inputMode="numeric"
                onChange={(e) => set("approxYear", e.target.value)}
                autoComplete="off"
              />
            </label>
          </div>
        )}

        <Choice<MileageMode>
          legend="Mileage when it happened"
          name={`${uid}-miles`}
          optional
          value={a.mileageMode}
          onChange={(v) => set("mileageMode", v)}
          options={[
            { value: "number", label: "I know the mileage" },
            { value: "unknown", label: "Unknown" },
          ]}
        />
        {a.mileageMode === "number" && (
          <label>
            Miles{" "}
            <input
              value={a.mileage}
              inputMode="numeric"
              aria-invalid={mileageInvalid}
              onChange={(e) => set("mileage", e.target.value)}
              autoComplete="off"
            />
            {mileageInvalid && <span className="rp-error"> Use digits only, for example 42000.</span>}
          </label>
        )}

        <label className="rp-desc">
          What happened?
          <span className="small rp-help" id={`${uid}-help`}>
            Don&apos;t include your name, phone, email, address or VIN.
          </span>
          <textarea
            rows={6}
            value={a.description}
            aria-describedby={`${uid}-help`}
            onChange={(e) => set("description", e.target.value)}
          />
        </label>

        <Choice<Frequency>
          legend="Did it happen once or repeatedly?"
          name={`${uid}-freq`}
          optional
          value={a.frequency}
          onChange={(v) => set("frequency", v)}
          options={[
            { value: "once", label: "Once" },
            { value: "repeatedly", label: "Repeatedly" },
            { value: "unknown", label: "Unknown" },
          ]}
        />
        <Choice<Answer3> legend="Was there a crash?" name={`${uid}-crash`} optional value={a.crash} onChange={(v) => set("crash", v)} options={YES_NO_UNKNOWN} />
        <Choice<Answer3> legend="Was there a fire?" name={`${uid}-fire`} optional value={a.fire} onChange={(v) => set("fire", v)} options={YES_NO_UNKNOWN} />
        <Choice<Answer3> legend="Was anyone injured?" name={`${uid}-injury`} optional value={a.injury} onChange={(v) => set("injury", v)} options={YES_NO_UNKNOWN} />

        <button type="submit" disabled={!canReview}>
          Review the draft
        </button>
        {!a.description.trim() && <p className="small">Describe what happened to continue.</p>}
      </form>
    );
  } else if (step === 2) {
    body = (
      <div className="rp-form">
        <label className="rp-desc">
          Review and edit the draft
          <textarea rows={12} value={draft} onChange={(e) => setDraft(e.target.value)} />
        </label>
        {edited && !confirmRegen && (
          <p className="small">You edited this draft. Going back to your answers keeps your edits.</p>
        )}
        <div className="rp-row">
          <button type="button" onClick={() => setStep(1)}>
            Back to my answers
          </button>
          <button type="button" onClick={() => (edited ? setConfirmRegen(true) : regenerate())}>
            Regenerate from my answers
          </button>
          <button
            type="button"
            disabled={!draft.trim()}
            onClick={() => {
              setCopy("idle");
              setStep(3);
            }}
          >
            Continue
          </button>
        </div>
        {confirmRegen && (
          <div className="notice" role="alertdialog" aria-label="Replace your edits?">
            <p>Regenerating replaces your edits with a new draft from your answers.</p>
            <div className="rp-row">
              <button type="button" onClick={regenerate}>
                Replace my edits
              </button>
              <button type="button" onClick={() => setConfirmRegen(false)}>
                Keep my edits
              </button>
            </div>
          </div>
        )}
      </div>
    );
  } else {
    body = (
      <div className="rp-form">
        <h3>Draft ready</h3>
        <p>{SUBMIT_NOTE}</p>
        <pre className="rp-draft" data-testid="rp-draft">
          {draft}
        </pre>
        <div className="rp-row">
          <button type="button" onClick={copyDraft}>
            Copy draft
          </button>
          <a className="button" href={NHTSA_REPORT_URL} target="_blank" rel="noopener noreferrer">
            Continue to NHTSA
          </a>
          <button type="button" onClick={() => setStep(2)}>
            Back to the draft
          </button>
        </div>
        <p aria-live="polite" className="small">
          {copy === "copied" ? "Copied" : ""}
        </p>
        {copy === "failed" && (
          <div className="rp-fallback">
            <p>Copying didn&apos;t work in this browser. Select all the text below and copy it yourself.</p>
            <textarea ref={fallbackRef} readOnly rows={10} value={draft} aria-label="Draft text to copy" />
            <button type="button" onClick={() => fallbackRef.current?.select()}>
              Select all and copy
            </button>
          </div>
        )}
      </div>
    );
  }

  return (
    <section className="rp" aria-labelledby={`${uid}-title`}>
      <h2 id={`${uid}-title`}>Report a problem to NHTSA</h2>
      <ol className="rp-steps" aria-label="Steps">
        <li aria-current={step === 1 ? "step" : undefined}>Describe</li>
        <li aria-current={step === 2 ? "step" : undefined}>Review and edit</li>
        <li aria-current={step === 3 ? "step" : undefined}>Copy and continue</li>
      </ol>
      <p className="small">{NOT_SAVED_TEXT}</p>
      {body}
      <p>
        <button type="button" className="rp-clear" onClick={clearAll}>
          Clear draft
        </button>
      </p>
    </section>
  );
}

export default ReportProblem;

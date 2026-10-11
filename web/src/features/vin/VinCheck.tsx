// Owner: A (C mounts it). PRD v2 F6: identify a vehicle from a VIN, then hand off to NHTSA's official lookup.
// Recall Radar never says whether a VIN has open recalls (no documented, authorized interface for that).
import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { checkVin, decodeVin, NHTSA_RECALLS_URL, type DecodeState } from "./vin";

export const DECODE_NOTICE = "Decoding sends this VIN to NHTSA's vPIC service.";
export const HANDOFF_TEXT = "NHTSA's lookup shows unrepaired recalls for this VIN. Recall Radar does not check it.";

type Selected = { make: string; model: string; model_year: number };

export function VinCheck({ selected, decodeEnabled = true }: { selected?: Selected; decodeEnabled?: boolean }) {
  const navigate = useNavigate();
  const [input, setInput] = useState("");
  const [state, setState] = useState<DecodeState | "decoding" | null>(null);
  const [copied, setCopied] = useState<"copied" | "manual" | null>(null);
  const check = checkVin(input);
  const vin = check.ok ? check.vin : null;

  const decode = async (e: FormEvent) => {
    e.preventDefault();
    if (!vin) return;
    setState("decoding");
    setState(await decodeVin(vin));
  };
  const copy = async () => {
    if (!vin) return;
    try {
      await navigator.clipboard.writeText(vin);
      setCopied("copied");
    } catch {
      setCopied("manual"); // show a selectable field instead
    }
  };
  const goTo = (make: string, model: string, year: number) =>
    navigate(`/vehicle?${new URLSearchParams({ make: make.toUpperCase(), model: model.toUpperCase(), year: String(year) })}`);

  const mismatch =
    selected && state && state !== "decoding" && state.kind === "success" &&
    (state.make.toUpperCase() !== selected.make || state.model.toUpperCase() !== selected.model || state.year !== selected.model_year);

  return (
    <section className="vin-check" aria-labelledby="vin-check-h" data-testid="vin-check">
      <h2 id="vin-check-h">Check by VIN</h2>
      <form onSubmit={decode} noValidate>
        <label htmlFor="vin-input">Vehicle identification number (17 characters)</label>
        <input
          id="vin-input"
          name="vin"
          autoComplete="off"
          spellCheck={false}
          inputMode="text"
          maxLength={40}
          value={input}
          onChange={(e) => {
            setInput(e.target.value);
            setState(null);
            setCopied(null);
          }}
          aria-describedby="vin-msg"
        />
        <p id="vin-msg" className="small" role="status" aria-live="polite" data-testid="vin-message">
          {input && !check.ok ? check.message : check.ok && check.checkDigitWarning ? `Warning: ${check.checkDigitWarning}` : ""}
        </p>
        {decodeEnabled && (
          <>
            <p className="small" data-testid="vin-notice">
              {DECODE_NOTICE}
            </p>
            <button type="submit" disabled={!vin || state === "decoding"}>
              Decode with NHTSA
            </button>
          </>
        )}
      </form>

      {state === "decoding" && <p className="state">Asking NHTSA's vPIC service…</p>}
      {state && state !== "decoding" && (
        <div className="vin-result" data-testid={`vin-${state.kind}`}>
          {state.kind === "success" && (
            <>
              <p>
                NHTSA's vPIC decodes this VIN as a <strong>{state.year} {state.make} {state.model}</strong>.
              </p>
              {mismatch && (
                <p data-testid="vin-mismatch">
                  That is not the {selected!.model_year} {selected!.make} {selected!.model} you selected.
                </p>
              )}
              <p>Is this your vehicle?</p>
              <button type="button" onClick={() => goTo(state.make, state.model, state.year)}>
                Yes, show this vehicle
              </button>{" "}
              <button type="button" className="link-button" onClick={() => setState(null)}>
                No
              </button>
            </>
          )}
          {state.kind === "partial" && (
            <>
              <p>
                NHTSA's vPIC decoded only part of this VIN ({[state.year, state.make, state.model].filter(Boolean).join(" ") || "no vehicle fields"}). {state.errorText}
              </p>
              {state.make && state.model && state.year && (
                <>
                  {/* the warning stays visible; the user decides (PRD v2 F6.4: confirm before navigating) */}
                  <p>Is this your vehicle?</p>
                  <button type="button" onClick={() => goTo(state.make!, state.model!, state.year!)}>
                    Yes, show this vehicle
                  </button>{" "}
                  <button type="button" className="link-button" onClick={() => setState(null)}>
                    No
                  </button>
                </>
              )}
            </>
          )}
          {state.kind === "error" && (
            <p>
              NHTSA's vPIC could not decode this VIN (error {state.errorCode}): {state.errorText}
            </p>
          )}
          {state.kind === "unsupported" && <p>NHTSA's vPIC does not support this VIN: {state.errorText}</p>}
          {state.kind === "unavailable" && <p>NHTSA's vPIC service is unavailable right now. {state.detail}</p>}
        </div>
      )}

      <div className="vin-handoff" data-testid="vin-handoff">
        <p>{HANDOFF_TEXT}</p>
        <button type="button" onClick={copy} disabled={!vin}>
          Copy VIN
        </button>{" "}
        <a href={NHTSA_RECALLS_URL} target="_blank" rel="noopener noreferrer">
          Check open recalls on NHTSA
        </a>
        <span role="status" aria-live="polite" className="small">
          {copied === "copied" && " Copied"}
        </span>
        {copied === "manual" && vin && (
          <p className="small">
            Copy it from here: <input readOnly value={vin} aria-label="VIN to copy" onFocus={(e) => e.target.select()} />
          </p>
        )}
      </div>
    </section>
  );
}

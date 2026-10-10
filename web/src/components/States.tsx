// Owner: C. Loading, empty and error states shared by every screen.
import type { ReactNode } from "react";
import type { ErrorResponse } from "../contracts.gen";

export function Loading({ what }: { what: string }) {
  return (
    <p className="state state-loading" role="status" aria-live="polite">
      Loading {what}…
    </p>
  );
}

export function Empty({ children }: { children: ReactNode }) {
  return (
    <p className="state state-empty" role="status">
      {children}
    </p>
  );
}

const HINT: Record<ErrorResponse["error"]["code"], string> = {
  invalid_parameter: "Check the selection and try again.",
  not_found: "Try another selection.",
  unavailable: "The data for this page has not been built yet, or the data service is offline.",
  internal: "Something went wrong on our side. Try again in a moment.",
};

/** Retrying helps only when the service is down or failed; not for a bad or unknown selection. */
const RETRYABLE: ErrorResponse["error"]["code"][] = ["unavailable", "internal"];

export function ErrorState({ error, retry }: { error: ErrorResponse; retry?: () => void }) {
  const canRetry = retry && RETRYABLE.includes(error.error.code);
  return (
    <div className="state state-error" role="alert">
      <p>
        <strong>{error.error.message}</strong>
      </p>
      <p>{HINT[error.error.code]}</p>
      {canRetry && (
        <button type="button" onClick={retry}>
          Try again
        </button>
      )}
    </div>
  );
}

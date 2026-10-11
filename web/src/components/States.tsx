// Owner: C. Loading, empty and error states shared by every screen.
import { motion } from "motion/react";
import type { ReactNode } from "react";
import { stateFade, useMotionPresets } from "../ui/motion";
import type { ErrorResponse } from "../contracts.gen";

export function Loading({ what }: { what: string }) {
  return (
    <motion.p className="state state-loading" role="status" aria-live="polite" {...stateFade}>
      Loading {what}…
    </motion.p>
  );
}

export function Empty({ children }: { children: ReactNode }) {
  return (
    <motion.p className="state state-empty" role="status" {...stateFade}>
      {children}
    </motion.p>
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
  const mp = useMotionPresets();
  const canRetry = retry && RETRYABLE.includes(error.error.code);
  return (
    <motion.div className="state state-error" role="alert" {...stateFade}>
      <p>
        <strong>{error.error.message}</strong>
      </p>
      <p>{HINT[error.error.code]}</p>
      {canRetry && (
        <motion.button type="button" onClick={retry} {...mp.buttonTap}>
          Try again
        </motion.button>
      )}
    </motion.div>
  );
}

// Owner: C. Runs one client call per dependency change; ignores stale responses.
// Pass `null` as the call while its inputs are not chosen yet (state "idle").
import { useCallback, useEffect, useState } from "react";
import type { ApiResult } from "./client";

export type Loadable<T> = { state: "idle" } | { state: "loading" } | ({ state: "done" } & ApiResult<T>);

export function useApi<T>(call: (() => Promise<ApiResult<T>>) | null, deps: unknown[]): [Loadable<T>, () => void] {
  const [value, setValue] = useState<Loadable<T>>({ state: call ? "loading" : "idle" });
  const [attempt, setAttempt] = useState(0);
  const reload = useCallback(() => setAttempt((a) => a + 1), []);
  useEffect(() => {
    if (!call) {
      setValue({ state: "idle" });
      return;
    }
    let live = true;
    setValue({ state: "loading" });
    call().then((r) => {
      if (live) setValue({ state: "done", ...r });
    });
    return () => {
      live = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, attempt]);
  return [value, reload];
}

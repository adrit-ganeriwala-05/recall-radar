// Owner: C. Chart modules (Bklit + visx + d3) load only when a page with a chart renders one, so the
// homepage never downloads chart code. `preload()` fetches the module ahead of time (tests call it so
// charts render synchronously; pages may call it on idle).
import { lazy, Suspense, type ComponentType, type ReactNode } from "react";

export type Preloadable<P> = ComponentType<P> & { preload: () => Promise<void> };

export function lazyWithPreload<P extends object>(
  factory: () => Promise<{ default: ComponentType<P> }>,
  fallback: ReactNode,
): Preloadable<P> {
  let loaded: ComponentType<P> | null = null;
  const load = () =>
    factory().then((m) => {
      loaded = m.default;
      return m;
    });
  const Lazy = lazy(load);
  const Component = ((props: P) => {
    if (loaded) {
      const Loaded = loaded;
      return <Loaded {...props} />;
    }
    return (
      <Suspense fallback={fallback}>
        <Lazy {...props} />
      </Suspense>
    );
  }) as Preloadable<P>;
  Component.preload = () => load().then(() => undefined);
  return Component;
}

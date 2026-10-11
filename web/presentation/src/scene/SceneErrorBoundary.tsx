"use client";
// Owner: C. Catches model download/parse errors and renderer crashes inside the scene so the
// static illustrative fallback replaces the canvas; the HTML page is never affected.
import { Component, type ReactNode } from "react";

type Props = { fallback: ReactNode; onError: (error: Error) => void; children: ReactNode };
type State = { failed: boolean };

export class SceneErrorBoundary extends Component<Props, State> {
  state: State = { failed: false };

  static getDerivedStateFromError(): State {
    return { failed: true };
  }

  componentDidCatch(error: Error) {
    this.props.onError(error);
  }

  render() {
    return this.state.failed ? this.props.fallback : this.props.children;
  }
}

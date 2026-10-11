// Owner: C. Server-rendered root layout. Geist (SIL Open Font License, npm package `geist`) is
// bundled at build time by next/font, so there is no remote font request; the CSS stack falls back
// to system fonts.
import type { Metadata, Viewport } from "next";
import { GeistSans } from "geist/font/sans";
import type { ReactNode } from "react";
import "./globals.css";

export const metadata: Metadata = {
  title: "Recall Radar — The Automotive Observatory",
  description: "Explore reported problems, official recalls, and the records behind them.",
};

export const viewport: Viewport = {
  themeColor: "#111315",
  colorScheme: "dark",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" className={GeistSans.variable}>
      <body>{children}</body>
    </html>
  );
}

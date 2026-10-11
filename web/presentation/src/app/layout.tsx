// Owner: C. Server-rendered root layout. Two typefaces, both SIL OFL variable fonts from npm
// (@fontsource-variable/*) bundled at build time by next/font — no remote font request, preloaded, and
// each with a metric-adjusted fallback face so the swap from fallback to web font barely moves text:
//   Space Grotesk — headings, navigation, buttons, labels, important numbers (--font-space-grotesk)
//   Manrope       — body copy, forms, tables, cards, longer explanations   (--font-manrope)
// The typography tokens built on these live in globals.css (@theme).
import type { Metadata, Viewport } from "next";
import localFont from "next/font/local";
import type { ReactNode } from "react";
import "./globals.css";

const spaceGrotesk = localFont({
  src: [{ path: "../../node_modules/@fontsource-variable/space-grotesk/files/space-grotesk-latin-wght-normal.woff2", weight: "300 700", style: "normal" }],
  variable: "--font-space-grotesk",
  display: "swap",
  fallback: ["ui-sans-serif", "sans-serif"],
});

const manrope = localFont({
  src: [{ path: "../../node_modules/@fontsource-variable/manrope/files/manrope-latin-wght-normal.woff2", weight: "200 800", style: "normal" }],
  variable: "--font-manrope",
  display: "swap",
  fallback: ["ui-sans-serif", "sans-serif"],
});

export const metadata: Metadata = {
  title: "Recall Radar — The Automotive Observatory",
  description: "Explore reported problems, official recalls, and the records behind them.",
};

export const viewport: Viewport = {
  themeColor: "#0c0e11",
  colorScheme: "dark",
  // Edge-to-edge on devices with display cutouts; gutters use env(safe-area-inset-*) (globals.css).
  viewportFit: "cover",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" className={`${spaceGrotesk.variable} ${manrope.variable}`}>
      <body>{children}</body>
    </html>
  );
}

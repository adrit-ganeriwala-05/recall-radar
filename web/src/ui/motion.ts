// Owner: C. The interface motion values (Framer Motion via the `motion` package). One MotionConfig with
// reducedMotion="user" wraps the app (App.tsx), so under prefers-reduced-motion every transform below
// is dropped and only opacity changes remain. Chart marks are animated by Bklit, never by these.
import { useReducedMotionConfig, type Transition, type Variants } from "motion/react";
import { useMemo } from "react";

export const EASE: [number, number, number, number] = [0.22, 1, 0.36, 1];

/** Page (route) entrance: fades in without delaying navigation; the header is outside it. */
export const pageEntrance = {
  initial: { opacity: 0, y: 12 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.35, ease: EASE } satisfies Transition,
};

/** Section entrance: once, when 25% visible; children stagger by 0.06 s. */
export const sectionVariants: Variants = {
  hidden: { opacity: 0, y: 16 },
  shown: { opacity: 1, y: 0, transition: { duration: 0.4, ease: EASE, staggerChildren: 0.06 } },
};
export const sectionChildVariants: Variants = {
  hidden: { opacity: 0, y: 16 },
  shown: { opacity: 1, y: 0, transition: { duration: 0.4, ease: EASE } },
};
export const sectionViewport = { once: true, amount: 0.25 } as const;

/** Card hover: lift 2 px, never scale. */
export const cardHover = { whileHover: { y: -2 }, transition: { duration: 0.15, ease: EASE } satisfies Transition };

/** Buttons: brightness on hover is CSS (styles.css); motion does the tap. */
export const buttonTap = { whileTap: { scale: 0.98 }, transition: { duration: 0.12, ease: EASE } satisfies Transition };

/** Drawer: slides in 24 px from the right, and back out. */
export const drawerMotion = {
  initial: { opacity: 0, x: 24 },
  animate: { opacity: 1, x: 0 },
  exit: { opacity: 0, x: 24 },
  transition: { duration: 0.25, ease: EASE } satisfies Transition,
};

/** Modal backdrop fade. */
export const backdropMotion = {
  initial: { opacity: 0 },
  animate: { opacity: 1 },
  exit: { opacity: 0 },
  transition: { duration: 0.18 } satisfies Transition,
};

/** Loading / empty / error and other state swaps: a short opacity change only. */
export const stateFade = {
  initial: { opacity: 0 },
  animate: { opacity: 1 },
  transition: { duration: 0.2 } satisfies Transition,
};

// ---- Reduced motion -------------------------------------------------------------------------------

const fadeSection: Variants = { hidden: { opacity: 0 }, shown: { opacity: 1, transition: { duration: 0.2, staggerChildren: 0.03 } } };
const fadeChild: Variants = { hidden: { opacity: 0 }, shown: { opacity: 1, transition: { duration: 0.2 } } };

/**
 * The presets components use. Under reduced motion (MotionConfig reducedMotion="user" follows the OS
 * setting) every movement is removed, not just its animation: no initial offsets, no hover lift, no tap
 * scale, no drawer slide; only short opacity changes remain.
 */
export function useMotionPresets() {
  const reduce = useReducedMotionConfig() ?? false;
  return useMemo(
    () =>
      reduce
        ? {
            page: { initial: { opacity: 0 }, animate: { opacity: 1 }, transition: { duration: 0.2 } },
            section: fadeSection,
            sectionChild: fadeChild,
            cardHover: {},
            buttonTap: {},
            drawer: { initial: { opacity: 0 }, animate: { opacity: 1 }, exit: { opacity: 0 }, transition: { duration: 0.15 } },
          }
        : { page: pageEntrance, section: sectionVariants, sectionChild: sectionChildVariants, cardHover, buttonTap, drawer: drawerMotion },
    [reduce],
  );
}

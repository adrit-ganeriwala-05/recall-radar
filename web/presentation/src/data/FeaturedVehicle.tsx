"use client";
// Owner: C. The presentation's data sections all describe one real example: the vehicle and component
// of the published hero replay (exports/demo/hero.json, chosen by the frozen hero rule). Loaded once
// (hero → replay → vehicle) and shared through context. If any step fails the sections show that
// state; they never fall back to invented records.
import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import type { HeroPointer, Replay, VehicleResponse } from "@/contracts.gen";
import { api, type ApiFailure } from "./api";

export type FeaturedState =
  | { status: "loading" }
  | { status: "error"; step: "hero" | "replay" | "vehicle"; error: ApiFailure }
  | { status: "ready"; hero: HeroPointer; replay: Replay; vehicle: VehicleResponse };

const FeaturedContext = createContext<FeaturedState>({ status: "loading" });

export function useFeatured(): FeaturedState {
  return useContext(FeaturedContext);
}

export function FeaturedVehicleProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<FeaturedState>({ status: "loading" });

  useEffect(() => {
    const controller = new AbortController();
    (async () => {
      const hero = await api.hero(controller.signal);
      if (controller.signal.aborted) return;
      if (!hero.ok) return setState({ status: "error", step: "hero", error: hero.error });
      const replay = await api.replay(hero.data.episode_id, controller.signal);
      if (controller.signal.aborted) return;
      if (!replay.ok) return setState({ status: "error", step: "replay", error: replay.error });
      const v = replay.data.vehicle;
      const vehicle = await api.vehicle(v.make, v.model, v.model_year, controller.signal);
      if (controller.signal.aborted) return;
      if (!vehicle.ok) return setState({ status: "error", step: "vehicle", error: vehicle.error });
      setState({ status: "ready", hero: hero.data, replay: replay.data, vehicle: vehicle.data });
    })();
    return () => controller.abort();
  }, []);

  return <FeaturedContext.Provider value={state}>{children}</FeaturedContext.Provider>;
}

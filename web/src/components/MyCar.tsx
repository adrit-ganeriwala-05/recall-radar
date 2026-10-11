// Owner: C. PRD v2 F4 controls on the vehicle page: Remember / Change / Forget.
import { useState } from "react";
import { Link } from "react-router-dom";
import type { VehicleKey } from "../contracts.gen";
import { forgetMyCar, readMyCar, sameCar, saveMyCar } from "../mycar";

export function MyCarControls({ vehicle }: { vehicle: VehicleKey }) {
  const [car, setCar] = useState(() => readMyCar().car);
  const [msg, setMsg] = useState<string | null>(null);
  const mine = sameCar(car, vehicle.make, vehicle.model, vehicle.model_year);

  const remember = () => {
    const r = saveMyCar(vehicle.make, vehicle.model, vehicle.model_year);
    if (r === "saved") {
      setCar({ v: 1, make: vehicle.make, model: vehicle.model, year: vehicle.model_year });
      setMsg("Saved");
    } else {
      setMsg("Couldn't save in this browser");
    }
  };
  const forget = () => {
    setMsg(forgetMyCar() ? "Forgotten" : "Couldn't change this browser's storage");
    setCar(null);
  };

  return (
    <div className="mycar" data-testid="mycar">
      {mine ? (
        <>
          <span className="small">This is your saved car.</span>{" "}
          <Link to="/?change=1">Change car</Link>{" "}
          <button type="button" className="link-button" onClick={forget}>
            Forget my car
          </button>
        </>
      ) : (
        <button type="button" onClick={remember}>
          Remember this car
        </button>
      )}{" "}
      <span role="status" aria-live="polite" className="small" data-testid="mycar-status">
        {msg}
      </span>
    </div>
  );
}

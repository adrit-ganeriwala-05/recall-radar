# HANDOFF D→B: F2 review sheet (PRD F2.6) — 72 accepted explanations
- From: D · To: B (verdicts), A (review of the verdict PR) · Contract 1.1.0 · Generated 03:00–03:08 ET
- Run: `recall_explain --generate --only <300 bounded campnos: 123 demo-vehicle campaigns first, then top vehicles by complaints>` on A's v2 DB (sha256 c3a40246…, content-identical to the serving DB), model **gemini-3.1-flash-lite** (3.8/3.5-flash returned 503 "high demand"; key on the free tier, 15 RPM → paced 12/min), prompt f2-v1.
- Result: **accepted 72** (51 of them in the 123 demo-vehicle campaigns), rejected by validate or model errors → fallback. Tables file stays on D's machine; D assembles the v2 DB after `--finalize` with your verdict file.
- **B: please write `review/explanation_verdicts.csv` (your file) from the lines below — `accept` only when you have no doubt (F2.6) — PR to A, needed merged by 03:45.** Then D runs `--finalize --verdicts review/explanation_verdicts.csv`, assembles, re-runs protect.

# F2 review sheet: 72 accepted explanations to read (PRD F2.6)

Verdict file: review/explanation_verdicts.csv with the header `campno,cache_key,verdict,reviewer,note`.

## 10V070000  (model gemini-3.1-flash-lite, prompt f2-v1)

1. **Certain model year 2011 Sonata vehicles have a defect where the front inside door lock switch may remain in the unlatched position.**
   - cites summary: "CERTAIN MODEL YEAR 2011 SONATA VEHICLES" | "THE FRONT INSIDE DOOR LOCK SWITCH CAN REMAIN IN THE UNLATCHED POSITION"
2. **The door may not be in the locked position and may open while the vehicle is in motion, possibly resulting in injury to the driver or passenger.**
   - cites consequence: "THE DOOR MAY NOT BE IN THE LOCKED POSITION AND MAY OPEN WHILE THE VEHICLE IS IN MOTION, POSSIBLY RESULTING IN INJURY TO THE DRIVER OR PASSENGER."

Official NHTSA text:
- summary: HYUNDAI-KIA HAS NOTIFIED NHTSA ABOUT A DEFECT IN CERTAIN MODEL YEAR 2011 SONATA VEHICLES MANUFACTURED FROM DECEMBER 11, 2009 THROUGH FEBRUARY 15, 2010.  THE FRONT INSIDE DOOR LOCK SWITCH CAN REMAIN IN THE UNLATCHED POSITION.
- consequence: THE DOOR MAY NOT BE IN THE LOCKED POSITION AND MAY OPEN WHILE THE VEHICLE IS IN MOTION, POSSIBLY RESULTING IN INJURY TO THE DRIVER OR PASSENGER.
- remedy: HYUNDAI-KIA WILL NOTIFY OWNERS AND DEALERS WILL REPAIR THE VEHICLES BY REPLACING LATCHES AFFECTED BY THIS RECALL CAMPAIGN FREE OF CHARGE.  THE SAFETY RECALL BEGAN ON MARCH 12, 2010.  OWNERS MAY CONTACT HYUNDAI CUSTOMER ASSISTANCE CENTER AT 1-800-633-5151.

`10V070000,10V070000|73aa56685fc201cb939878fe223bd869898dcd590433dc3a7680f920ad02b7b0|gemini-3.1-flash-lite|f2-v1,,B,`

## 10V222000  (model gemini-3.1-flash-lite, prompt f2-v1)

1. **Ford is recalling certain 2010 Fusion, Milan, and Escape vehicles because the park rod guide retention pin may not have been properly installed.**
   - cites summary: "FORD IS RECALLING CERTAIN MODEL YEAR 2010 FUSION, MILAN, AND ESCAPE VEHICLES" | "THE PARK ROD GUIDE RETENTION PIN MAY NOT HAVE BEEN PROPERLY INSTALLED"
2. **If parked without the parking brake, a vehicle may have unintended movement which may cause a crash.**
   - cites consequence: "A VEHICLE PARKED WITHOUT AN ENGAGED PARK PAWL AND WITHOUT AN APPLIED PARKING BRAKE MAY HAVE UNINTENDED MOVEMENT WHICH MAY CAUSE A CRASH."

Official NHTSA text:
- summary: FORD IS RECALLING CERTAIN MODEL YEAR 2010 FUSION, MILAN, AND ESCAPE VEHICLES MANUFACTURED FROM FEBRUARY 27, THROUGH MARCH 26, 2010.  THE PARK ROD GUIDE RETENTION PIN MAY NOT HAVE BEEN PROPERLY INSTALLED WHICH FAILS TO CONFORM TO THE REQUIREMENT OF FEDERAL MOTOR VEHICLE SAFETY STANDARD NO. 114, "THEFT PROTECTION AND ROLLAWAY PREVENTION".
- consequence: A VEHICLE PARKED WITHOUT AN ENGAGED PARK PAWL AND WITHOUT AN APPLIED PARKING BRAKE MAY HAVE UNINTENDED MOVEMENT WHICH MAY CAUSE A CRASH.
- remedy: FORD WILL NOTIFY OWNERS AND DEALERS WILL REPAIR THE VEHICLES FREE OF CHARGE.  THE SAFETY RECALL BEGAN ON MAY 28, 2010.  OWNERS MAY CONTACT FORD MOTOR COMPANY CUSTOMER RELATIONSHIP CENTER AT 1-866-436-7332 AND FOR THE HEARING IMPAIRED CALL 1-800-232-5952 (TDD).  REPRESENTATIVES ARE AVAILABLE MONDAY THROUGH FRIDAY:  8:00AM - 5:00PM.

`10V222000,10V222000|20d47c4b1c7ce3a8db2c866eebef1b035c74fdcd39b2f685de91a772c7d16b01|gemini-3.1-flash-lite|f2-v1,,B,`

## 10V401000  (model gemini-3.1-flash-lite, prompt f2-v1)

1. **Nissan is recalling certain vehicles that were equipped with a Garmin Nuvi model 750 navigation system because the batteries may overheat.**
   - cites summary: "NISSAN IS RECALLING CERTAIN VEHICLES THAT WERE EQUIPPED WITH A GARMIN NUVI MODEL 750 NAVIGATION SYSTEM. THE BATTERIES CONTAINED IN THE AFFECTED GPS UNITS CAN OVERHEAT."
2. **Overheated batteries could result in a fire.**
   - cites consequence: "OVERHEATED BATTERIES COULD RESULT IN A FIRE."

Official NHTSA text:
- summary: NISSAN IS RECALLING CERTAIN VEHICLES THAT WERE EQUIPPED WITH A GARMIN NUVI MODEL 750 NAVIGATION SYSTEM.  THE BATTERIES CONTAINED IN THE AFFECTED GPS UNITS CAN OVERHEAT.
- consequence: OVERHEATED BATTERIES COULD RESULT IN A FIRE.
- remedy: NISSAN WILL NOTIFY OWNERS AND THE REPAIRS WILL BE PERFORMED BY GARMIN TECHNICIANS BY REPLACING THE BATTERY AND INSERTING A SPACER ON TOP OF THE BATTERY FREE OF CHARGE.   THE SAFETY RECALL BEGAN ON SEPTEMBER 16, 2010.  OWNERS MAY CONTACT GARMIN DIRECTLY AT 1-866-957-1981 OR NISSAN AT 1-800-647-7261.

`10V401000,10V401000|627144652e66545652f85e27404f93d6362a88030631f2a40920a77681d667dd|gemini-3.1-flash-lite|f2-v1,,B,`

## 10V426000  (model gemini-3.1-flash-lite, prompt f2-v1)

1. **Hyundai is recalling certain 2011 Sonata vehicles where some steering column intermediate shaft universal joint connections may have been improperly assembled or insufficiently tightened.**
   - cites summary: "HYUNDAI IS RECALLING CERTAIN MODEL YEAR 2011 SONATA VEHICLES" | "ON SOME OF THESE VEHICLES THE STEERING COLUMN INTERMEDIATE SHAFT UNIVERSAL JOINT CONNECTIONS MAY HAVE BEEN EITHER IMPROPERLY ASSEMBLED OR INSUFFICIENTLY TIGHTENED."
2. **This could cause a loss of or reduction in steering capability, and dealers will inspect the connections and update software.**
   - cites consequence, remedy: "LOSS OF, OR REDUCTION IN, STEERING CAPABILITY" | "DEALERS WILL INSPECT THE STEERING COLUMN INTERMEDIATE SHAFT UNIVERSAL JOINT CONNECTIONS FOR PROPER ASSEMBLY AND TORQUE. IN ADDITION DEALERS WILL UPDATE THE POWER STEERING SOFTWARE"

Official NHTSA text:
- summary: HYUNDAI IS RECALLING CERTAIN MODEL YEAR 2011 SONATA VEHICLES MANUFACTURED FROM DECEMBER 11, 2009, THROUGH SEPTEMBER 10, 2010.  ON SOME OF THESE VEHICLES THE STEERING COLUMN INTERMEDIATE SHAFT UNIVERSAL JOINT CONNECTIONS MAY HAVE BEEN EITHER IMPROPERLY ASSEMBLED OR INSUFFICIENTLY TIGHTENED.
- consequence: IMPROPER ASSEMBLY OR INSUFFICIENT TIGHTENING OF THE CONNECTIONS COULD RESULT IN A COMPLETE SEPARATION OR COMPROMISED ATTACHMENT OF THE CONNECTIONS, SUCH THAT THE DRIVER COULD EXPERIENCE A LOSS OF, OR REDUCTION IN, STEERING CAPABILITY INCREASING THE RISK OF A CRASH.
- remedy: DEALERS WILL INSPECT THE STEERING COLUMN INTERMEDIATE SHAFT UNIVERSAL JOINT CONNECTIONS FOR PROPER ASSEMBLY AND TORQUE.  IN ADDITION DEALERS WILL UPDATE THE POWER STEERING SOFTWARE FREE OF CHARGE.  THE SAFETY RECALL IS EXPECTED TO BEGIN DURING OCTOBER 2010.  OWNERS MAY CONTACT HYUNDAI CUSTOMER ASSISTANCE CENTER AT 1-800-633-5151.

`10V426000,10V426000|01c975f3887aa7f8558a62303c8b290244949e8102da8a42baa99cbf525aa9ab|gemini-3.1-flash-lite|f2-v1,,B,`

## 10V516000  (model gemini-3.1-flash-lite, prompt f2-v1)

1. **Ford is recalling certain 2011 Edge and Lincoln MKX vehicles because incorrect electronic module settings may disable the liftgate locking function.**
   - cites summary: "FORD IS RECALLING CERTAIN MODEL YEAR 2011 EDGE AND LINCOLN MKX VEHICLES" | "INCORRECTLY CONFIGURED ELECTRONIC MODULE SETTINGS THAT DISABLE THE LOCKING FUNCTION OF THE LIFTGATE"
2. **The liftgate lock may be disabled, and the driver may not be able to lock it using interior switches or remote key fob buttons.**
   - cites consequence: "THE LIFTGATE LOCK MAY BE DISABLED AND THE DRIVER MAY NOT BE ABLE TO LOCK THE LIFTGATE USING INTERIOR LOCK SWITCHES OR REMOTE KEY FOB BUTTONS."

Official NHTSA text:
- summary: FORD IS RECALLING CERTAIN MODEL YEAR 2011 EDGE AND LINCOLN MKX VEHICLES MANUFACTURED FROM JULY 1, 2010, THROUGH OCTOBER 8, 2010.  THESE VEHICLES WERE SHIPPED WITH INCORRECTLY CONFIGURED ELECTRONIC MODULE SETTINGS THAT DISABLE THE LOCKING FUNCTION OF THE LIFTGATE.  ACCORDINGLY, THE VEHICLES FAIL TO CONFORM TO THE REQUIREMENTS OF FEDERAL MOTOR VEHICLE SAFETY STANDARD NO. 206, "DOOR LOCKS AND DOOR RETENTION COMPONENTS."
- consequence: THE LIFTGATE LOCK MAY BE DISABLED AND THE DRIVER MAY NOT BE ABLE TO LOCK THE LIFTGATE USING INTERIOR LOCK SWITCHES OR REMOTE KEY FOB BUTTONS.
- remedy: FORD WILL NOTIFY OWNERS AND DEALERS WILL HAVE THE AFFECTED CONTROL MODULES UPDATED FREE OF CHARGE.  THE SAFETY RECALL BEGAN ON NOVEMBER 1, 2010.  OWNERS MAY CONTACT FORD AT 1-866-436-7332.

`10V516000,10V516000|b1cbe72eecaa655d0d6cf494c7be367546fa4a93930784d5b6d8622316a78a42|gemini-3.1-flash-lite|f2-v1,,B,`

## 10V611000  (model gemini-3.1-flash-lite, prompt f2-v1)

1. **Chrysler is recalling certain model year 2008 Chrysler Town and Country and Dodge Grand Caravan vehicles that may experience a water leak which can lead to illumination of airbag warning light and a potential inadvertent airbag deployment.**
   - cites summary: "CHRYSLER IS RECALLING CERTAIN MODEL YEAR 2008 CHRYSLER TOWN AND COUNTRY AND DODGE GRAND CARAVAN VEHICLES." | "THESE VEHICLES MAY EXPERIENCE A WATER LEAK At THE HEATING AND AIR CONDITIONER (HVAC) DRAIN GROMMET WHICH CAN LEAD TO ILLUMINATION OF AIRBAG WARNING LIGHT AND A POTENTIAL INADVERTENT AIRBAG DEPLOYMENT."
2. **An inadvertent airbag deployment could result in injury to the seat occupant or a vehicle crash.**
   - cites consequence: "AN INADVERTENT AIRBAG DEPLOYMENT COULD RESULT IN INJURY TO THE SEAT OCCUPANT IN FRONT OF THE DEPLOYING AIRBAG AND/OR A VEHICLE CRASH."

Official NHTSA text:
- summary: CHRYSLER IS RECALLING CERTAIN MODEL YEAR 2008 CHRYSLER TOWN AND COUNTRY AND DODGE GRAND CARAVAN VEHICLES.  THESE VEHICLES MAY EXPERIENCE A WATER LEAK At THE HEATING AND AIR CONDITIONER (HVAC) DRAIN GROMMET WHICH CAN LEAD TO ILLUMINATION OF AIRBAG WARNING LIGHT AND A POTENTIAL INADVERTENT AIRBAG DEPLOYMENT.
- consequence: AN INADVERTENT AIRBAG DEPLOYMENT COULD RESULT IN INJURY TO THE SEAT OCCUPANT IN FRONT OF THE DEPLOYING AIRBAG AND/OR A VEHICLE CRASH.
- remedy: DEALERS WILL REPLACE THE HVAC DRAIN GROMMET FREE OF CHARGE.    THE SAFETY RECALL BEGAN ON JANUARY 14, 2011.  OWNERS MAY CONTACT CHRYSLER AT 1-800-853-1403.

`10V611000,10V611000|8397396757be47b9c17017ddfe0e461a738a991c622c2898c87e483b8a05c6f2|gemini-3.1-flash-lite|f2-v1,,B,`

## 10V659000  (model gemini-3.1-flash-lite, prompt f2-v1)

1. **Ford is recalling certain model year vehicles because the body control module may have the potential for an internal short.**
   - cites summary: "FORD IS RECALLING CERTAIN MODEL YEAR 2011 F-150, F-250, F-350, F-450, F-550, EDGE AND LINCOLN MKX VEHICLES" | "MAY HAVE THE POTENTIAL FOR AN INTERNAL SHORT"
2. **If an electrical short develops, an overheating condition may occur which can result in an unattended vehicle fire.**
   - cites consequence: "IF AN ELECTRICAL SHORT DEVELOPS, AN OVERHEATING CONDITION MAY OCCUR WHICH CAN RESULT IN AN UNATTENDED VEHICLE FIRE."

Official NHTSA text:
- summary: FORD IS RECALLING CERTAIN MODEL YEAR 2011 F-150, F-250, F-350, F-450, F-550, EDGE AND LINCOLN MKX VEHICLES.  DURING A SIX-DAY PRODUCTION PERIOD, THE SUPPLIER OF THE BODY CONTROL MODULE MANUFACTURED MODULES THAT MAY HAVE THE POTENTIAL FOR AN INTERNAL SHORT.
- consequence: IF AN ELECTRICAL SHORT DEVELOPS, AN OVERHEATING CONDITION MAY OCCUR WHICH CAN RESULT IN AN UNATTENDED VEHICLE FIRE.
- remedy: DEALER WILL REPLACE THE BODY CONTROL MODULE IF NECESSARY FREE OF CHARGE.  THE SAFETY RECALL BEGAN ON JANUARY 11, 2011.  OWNERS MAY CONTACT FORD AT 1-866-436-7332.

`10V659000,10V659000|3e407f707c89f46cc07c00926fdbb023ab189032e947c5581da82440262a11c8|gemini-3.1-flash-lite|f2-v1,,B,`

## 11V113000  (model gemini-3.1-flash-lite, prompt f2-v1)

1. **Toyota is recalling certain vehicles where the accelerator pedal may get stuck if trapped by an unsecured or incompatible driver's floor mat.**
   - cites summary: "TOYOTA IS RECALLING CERTAIN" | "THE ACCELERATOR PEDAL CAN GET STUCK IN THE WIDE OPEN POSITION DUE TO ITS BEING TRAPPED BY AN UNSECURED OR INCOMPATIBLE DRIVER'S FLOOR MAT."
2. **A stuck accelerator pedal may make it difficult to stop, which could cause a crash.**
   - cites consequence: "A STUCK OPEN ACCELERATOR PEDAL MAY RESULT IN" | "MAKE IT DIFFICULT TO STOP THE VEHICLE, WHICH COULD CAUSE A CRASH"

Official NHTSA text:
- summary: TOYOTA IS RECALLING CERTAIN MODEL YEAR 2008 THROUGH 2011 LEXUS LX570, 2003 THROUGH 2009 TOYOTA 4RUNNER, AND 2006 THROUGH 2010 RAV4 VEHICLES.  THE ACCELERATOR PEDAL CAN GET STUCK IN THE WIDE OPEN POSITION DUE TO ITS BEING TRAPPED BY AN UNSECURED OR INCOMPATIBLE DRIVER'S FLOOR MAT.
- consequence: A STUCK OPEN ACCELERATOR PEDAL MAY RESULT IN VERY HIGH VEHICLE SPEEDS AND MAKE IT DIFFICULT TO STOP THE VEHICLE, WHICH COULD CAUSE A CRASH, SERIOUS INJURY OR DEATH.
- remedy: THE REMEDY IS NOW AVAILABLE.  THE SAFETY RECALL BEGAN EARLY APRIL 2011. THE REMEDY WILL INVOLVE MODIFICATION OR REPLACEMENT OF THE ACCELERATOR PEDAL AND REPLACEMENT OF ANY TOYOTA ALL-WEATHER FLOOR MAT.  OWNERS MAY CONTACT TOYOTA AT 1-800-331-4331 OR LEXUS AT 1-800-255-3987.

`11V113000,11V113000|8c2f663b770ef8dcda47ee69445faccdf83d1eb4c2b4fc15bfc548e2113bd1b8|gemini-3.1-flash-lite|f2-v1,,B,`

## 11V139000  (model gemini-3.1-flash-lite, prompt f2-v1)

1. **Chrysler is recalling certain model year 2010 Dodge Journey, Grand Caravan, and Chrysler Town & Country vehicles because some vehicles may experience inadvertent ignition key displacement from the run to accessory position while driving.**
   - cites summary: "CHRYSLER IS RECALLING CERTAIN MODEL YEAR 2010 DODGE JOURNEY, GRAND CARAVAN, AND CHRYSLER TOWN & COUNTRY VEHICLES" | "SOME VEHICLES MAY EXPERIENCE INADVERTENT IGNITION KEY DISPLACEMENT FROM THE RUN TO ACCESSORY POSITION WHILE DRIVING"
2. **Engine shut off while driving could increase the risk of a crash.**
   - cites consequence: "ENGINE SHUT OFF WHILE DRIVING COULD INCREASE THE RISK OF A CRASH."

Official NHTSA text:
- summary: CHRYSLER IS RECALLING CERTAIN MODEL YEAR 2010 DODGE JOURNEY, GRAND CARAVAN, AND CHRYSLER TOWN & COUNTRY VEHICLES MANUFACTURER FROM AUGUST 3, 2009, THROUGH JUNE 17, 2010. SOME VEHICLES MAY EXPERIENCE INADVERTENT IGNITION KEY DISPLACEMENT FROM THE RUN TO ACCESSORY POSITION WHILE DRIVING CAUSING THE ENGINE TO SHUT OFF.
- consequence: ENGINE SHUT OFF WHILE DRIVING COULD INCREASE THE RISK OF A CRASH.
- remedy: DEALERS WILL REPLACE THE WIN MODULES FREE OF CHARGE.  THE SAFETY RECALL IS EXPECTED TO BEGIN DURING JULY 2011.  OWNERS MAY CONTACT CHRYSLER AT 1-800-853-1403.

`11V139000,11V139000|9a4f0ff7117fd7c06641448f68c080ff72d8bb4d959ab8035bedd8117cf55025|gemini-3.1-flash-lite|f2-v1,,B,`

## 11V487000  (model gemini-3.1-flash-lite, prompt f2-v1)

1. **Chrysler is recalling certain 2012 vehicles equipped with 3.6L engines because they may experience connecting rod bearing failure due to debris inside the engine block.**
   - cites summary: "CHRYSLER IS RECALLING CERTAIN MODEL YEAR 2012 CHRYSLER VEHICLES" | "EQUIPPED WITH 3.6L ENGINES" | "THESE ENGINES MAY EXPERIENCE CONNECTING ROD BEARING FAILURE DUE TO DEBRIS INSIDE THE ENGINE BLOCK."
2. **Connecting rod failure may lead to engine seizure which may increase the risk of a crash.**
   - cites consequence: "CONNECTING ROD FAILURE MAY LEAD TO ENGINE SEIZURE WHICH MAY INCREASE THE RISK OF A CRASH."

Official NHTSA text:
- summary: CHRYSLER IS RECALLING CERTAIN MODEL YEAR 2012 CHRYSLER VEHICLES, INCLUDING 200 AND TOWN AND COUNTRY MODELS, DODGE VEHICLES, INCLUDING CHARGER, DURANGO, GRAND CARAVAN AND JOURNEY MODELS AND JEEP GRAND CHEROKEE VEHICLES MANUFACTURED FROM AUGUST 31, 2011, THROUGH SEPTEMBER 13, 2011, THAT ARE EQUIPPED WITH 3.6L ENGINES.   THESE ENGINES MAY EXPERIENCE CONNECTING ROD BEARING FAILURE DUE TO DEBRIS INSIDE THE ENGINE BLOCK.
- consequence: CONNECTING ROD FAILURE MAY LEAD TO ENGINE SEIZURE WHICH MAY INCREASE THE RISK OF A CRASH.
- remedy: CHRYSLER WILL NOTIFY OWNERS AND REPLACE THE ENGINE FREE OF CHARGE.  THE SAFETY RECALL IS EXPECTED TO BEGIN ON OR ABOUT NOVEMBER 18, 2011.  OWNERS MAY CONTACT CHRYSLER AT 1-800-853-1403.

`11V487000,11V487000|75826aff37d331d4c9f09b757ef6cc1b08302d81966353628ae1ffc89e8c096e|gemini-3.1-flash-lite|f2-v1,,B,`

## 12V149000  (model gemini-3.1-flash-lite, prompt f2-v1)

1. **Ford is recalling certain model year 2012 Focus vehicles because a seal in the wiring harness connector to the passenger side wiper motor may be missing.**
   - cites summary: "FORD IS RECALLING CERTAIN MODEL YEAR 2012 FOCUS VEHICLES" | "A SEAL IN THE WIRING HARNESS CONNECTOR TO THE PASSENGER SIDE WIPER MOTOR MAY BE MISSING."
2. **Water or other contaminants may accumulate in the connector, resulting in an inoperative passenger side wiper motor.**
   - cites consequence: "WATER OR OTHER CONTAMINANTS MAY ACCUMULATE IN THE CONNECTOR, RESULTING IN AN INTERMITTENT OR INOPERATIVE PASSENGER SIDE WIPER MOTOR"

Official NHTSA text:
- summary: FORD IS RECALLING CERTAIN MODEL YEAR 2012 FOCUS VEHICLES MANUFACTURED FROM AUGUST 1, 2010, THROUGH OCTOBER 18, 2011.  A SEAL IN THE WIRING HARNESS CONNECTOR TO THE PASSENGER SIDE WIPER MOTOR MAY BE MISSING.
- consequence: WATER OR OTHER CONTAMINANTS MAY ACCUMULATE IN THE CONNECTOR, RESULTING IN AN INTERMITTENT OR INOPERATIVE PASSENGER SIDE WIPER MOTOR, REDUCING VISIBILITY AND INCREASING THE RISK OF A CRASH.
- remedy: FORD WILL NOTIFY OWNERS, AND DEALERS WILL INSPECT AND AS NECESSARY, CLEAN AND PROPERLY SEAL THE PASSENGER SIDE WIPER MOTOR CONNECTOR.  ANY INOPERATIVE WIPER MOTORS WILL BE REPLACED.  THIS SERVICE WILL BE PROVIDED FREE OF CHARGE.   THE SAFETY RECALL BEGAN ON MAY 21, 2012.  OWNERS MAY CONTACT THE FORD MOTOR COMPANY CUSTOMER RELATIONSHIP CENTER AT 1-866-436-7332.

`12V149000,12V149000|201efe85f1746224d4a4b6860c358dc36ba2f31637c788d7e28db91a045d3cd2|gemini-3.1-flash-lite|f2-v1,,B,`

## 12V431000  (model gemini-3.1-flash-lite, prompt f2-v1)

1. **Ford is recalling certain model year 2013 Escape vehicles equipped with 1.6L engines where the cylinder head cup plug may become dislodged.**
   - cites summary: "Ford is recalling certain model year 2013 Escape vehicles" | "equipped with 1.6L engines" | "The cylinder head cup plug (freeze plug) may become dislodged"
2. **As leaking engine coolant evaporates on the hot engine, the glycol may ignite causing an engine compartment fire.**
   - cites consequence: "As leaking engine coolant evaporates on the hot engine, the glycol may ignite causing an engine compartment fire."

Official NHTSA text:
- summary: Ford is recalling certain model year 2013 Escape vehicles manufactured from October 5, 2011, through August 31, 2012, equipped with 1.6L engines.  The cylinder head cup plug (freeze plug) may become dislodged resulting in significant loss of engine coolant.
- consequence: As leaking engine coolant evaporates on the hot engine, the glycol may ignite causing an engine compartment fire.
- remedy: Ford will notify owners, and dealers will seal the existing plug and add a secondary plug cover, free of charge.  The safety recall began on September 11, 2012.  Owners may contact Ford at 1-866-436-7332.

`12V431000,12V431000|b8ee9e9ff85498fa579f6aff0144a1c11761a76e09cd525714cc401a429a107d|gemini-3.1-flash-lite|f2-v1,,B,`

## 13V085000  (model gemini-3.1-flash-lite, prompt f2-v1)

1. **Ford is recalling certain model year 2013 Focus, C-Max, and Escape vehicles because the left rear door child lock may not engage.**
   - cites summary: "Ford is recalling certain model year 2013 Focus and C-Max" | "Escape vehicles" | "the child lock may not engage"
2. **The operator may incorrectly believe the child lock is engaged, but the door may be opened from the inside, increasing the risk of injury to an unrestrained child.**
   - cites consequence: "The operator may incorrectly believe the child lock is engaged. However, the door may be opened from the inside, increasing the risk of injury to an unrestrained child."

Official NHTSA text:
- summary: Ford is recalling certain model year 2013 Focus and C-Max vehicles built from November 16, 2012, through November 21, 2012; and model year 2013 Escape vehicles manufactured from November 14, 2012, through November 21, 2012.  The left rear door child lock was built incorrectly.  As a result, the child lock may not engage when the operator uses normal force to activate the child lock.
- consequence: The operator may incorrectly believe the child lock is engaged.  However, the door may be opened from the inside, increasing the risk of injury to an unrestrained child.
- remedy: Ford will notify owners, and dealers will inspect the affected rear door latches, and replace them as necessary, free of charge.  The recall began on March 27, 2013.  Owners may contact Ford Motor Company Customer Relationship Center at 1-866-436-7332.

`13V085000,13V085000|db7f98bc6c4c9472f2e346b5d36864733c5ff183b3405f9f278b070df45c5c30|gemini-3.1-flash-lite|f2-v1,,B,`

## 13V158000  (model gemini-3.1-flash-lite, prompt f2-v1)

1. **Nissan is recalling certain model year 2013 Altima vehicles because the spare tires may have been significantly over- or under-inflated.**
   - cites summary: "Nissan North America is recalling certain model year 2013 Altima vehicles" | "The spare tires may have been significantly over- or under-inflated."
2. **Tires that are significantly over- or under-inflated may fail without warning, increasing the risk of a crash.**
   - cites consequence: "Tires that are significantly over- or under-inflated may fail without warning, increasing the risk of a crash."

Official NHTSA text:
- summary: Nissan North America is recalling certain model year 2013 Altima vehicles manufactured March 21, 2012, through March 26, 2013.  The spare tires may have been significantly over- or under-inflated.
- consequence: Tires that are significantly over- or under-inflated may fail without warning, increasing the risk of a crash.
- remedy: Nissan will notify owners, and dealers will inspect and adjust the spare tire pressure, as necessary, free of charge.  The recall began on April 29, 2013.  Owners may contact Nissan at 1-800-647-7261.

`13V158000,13V158000|401c2b9efb30a2a909abbac3883db779564341d79b69104036ef6db1837fce0e|gemini-3.1-flash-lite|f2-v1,,B,`

## 13V289000  (model gemini-3.1-flash-lite, prompt f2-v1)

1. **Chrysler is recalling certain 2014 Grand Cherokee vehicles equipped with premium headlamps because electrical spikes may cause the parking lamps to turn off.**
   - cites summary: "Chrysler is recalling certain" | "2014, non-SRT trimmed, Grand Cherokee vehicles" | "equipped with premium headlamps." | "electrical spikes may cause the parking lamps to turn off"
2. **Without parking lamps, the vehicle may not be as visible to other vehicles, increasing the risk of a crash.**
   - cites consequence: "Without parking lamps, the vehicle may not be as visible to other vehicles, increasing the risk of a crash."

Official NHTSA text:
- summary: Chrysler is recalling certain model year 2014, non-SRT trimmed, Grand Cherokee vehicles manufactured January 14, 2013, through March 20, 2013 equipped with premium headlamps.  In the affected vehicles, when switching between daytime running lights and parking lights, electrical spikes may cause the parking lamps to turn off.  Without properly functioning parking lamps these vehicles fail to conform to the requirements of Federal Motor Vehicle Safety Standard (FMVSS) No. 108, "Lamps, reflective devices, and associated equipment."
- consequence: Without parking lamps, the vehicle may not be as visible to other vehicles, increasing the risk of a crash.
- remedy: Chrysler will notify owners, and dealers will update the Central Body Controller software, free of charge.  The recall BEGAN ON September 12, 2013.  Owners may contact Chrysler at 1-800-247-9753.  Chrysler's recall campaign number is N42.

`13V289000,13V289000|7d3c404dd77a8416e1873d868b2018c21ed95b2211d79335336ad5ec43fdf56d|gemini-3.1-flash-lite|f2-v1,,B,`

## 13V624000  (model gemini-3.1-flash-lite, prompt f2-v1)

1. **Hyundai is recalling certain 2014 Santa Fe vehicles equipped with P235/65R17 103T Continental Crosscontact LX tires that may have a damaged sidewall.**
   - cites summary: "Hyundai is recalling certain model year 2014 Santa Fe vehicles" | "equipped with P235/65R17 103T Continental Crosscontact LX tires. The tires may have a damaged sidewall."
2. **The damaged sidewall may result in a separation between the belt edges which could cause tread detachment or rapid air loss, increasing the risk of a crash.**
   - cites consequence: "The damaged sidewall may result in a separation between the belt edges which could cause tread detachment or rapid air loss, increasing the risk of a crash."

Official NHTSA text:
- summary: Hyundai is recalling certain model year 2014 Santa Fe vehicles manufactured November 5, 2013, through November 15, 2013, and equipped with P235/65R17 103T Continental Crosscontact LX tires. The tires may have a damaged sidewall.
- consequence: The damaged sidewall may result in a separation between the belt edges which could cause tread detachment or rapid air loss, increasing the risk of a crash.
- remedy: Hyundai notified dealers to suspend sales of affected Santa Fe Sport vehicles equipped with the P235/65R17 103T tires, and replace them with alternative tires.  All affected vehicles were remedied prior to retail sale.  Owners may contact Hyundai Customer Care Center at 1-800-633-5151.

`13V624000,13V624000|ef38ddb001ee716f512e04828bd16f7bc08fdf0c819df3af2e6efaab264bd497|gemini-3.1-flash-lite|f2-v1,,B,`

## 14V154000  (model gemini-3.1-flash-lite, prompt f2-v1)

1. **Certain vehicles may have a brake booster with a center shell that may corrode and allow water to get inside.**
   - cites summary: "certain model year 2011-2014 Jeep Grand Cherokee and Dodge Durango vehicles" | "brake booster with a center shell that may corrode and allow water to get inside"
2. **Water inside could freeze and limit the braking ability of the vehicle, increasing the risk of a crash.**
   - cites consequence: "The water inside could freeze and limit the braking ability of the vehicle, increasing the risk of a crash."

Official NHTSA text:
- summary: Chrysler Group LLC (Chrysler) is recalling certain model year 2011-2014 Jeep Grand Cherokee and Dodge Durango vehicles manufactured from January 5, 2010, through September 8, 2013.  The subject vehicles have a brake booster with a center shell that may corrode and allow water to get inside.
- consequence: The water inside could freeze and limit the braking ability of the vehicle, increasing the risk of a crash.
- remedy: Chrysler will notify owners, and dealers will add a water diverter shield to the booster after the booster has been tested to confirm it can hold an acceptable amount of vacuum pressure.  If the booster inspection confirms an unacceptable loss of vacuum pressure, the booster will be replaced.  Repairs will be made free of charge.  The recall began on May 30, 2014.  Owners may contact Chrysler at 1-800-853-1403.  Chrysler's recall campaign number is P14.

`14V154000,14V154000|b9308e4c9cfc276a1f326df4f3bfa392bbff5c4682e645d44ff39808394ca717|gemini-3.1-flash-lite|f2-v1,,B,`

## 14V164000  (model gemini-3.1-flash-lite, prompt f2-v1)

1. **Ford is recalling certain vehicles because the driver and passenger seatback assemblies may have been produced with sub-standard weld joints.**
   - cites summary: "Ford Motor Company (Ford) is recalling certain" | "The driver and passenger seatback assemblies may have been produced with sub-standard weld joints"
2. **These seat backs may have insufficient strength, which may cause them to become loose or lean while driving and potentially increase the risk of injury in certain crashes.**
   - cites summary, consequence: "The affected seat backs may have insufficient strength" | "The back of the subject seats may become loose or lean while driving and potentially increase the risk of injury in certain crashes."

Official NHTSA text:
- summary: Ford Motor Company (Ford) is recalling certain model year 2013-2014 Ford Fusion and Lincoln MKZ vehicles manufactured August 15, 2012, through September 10, 2013, 2013-2014 Ford Escape vehicles manufactured June 5, 2012, through August 12, 2013, and 2013-2014 Ford C-Max vehicles manufactured from July 23, 2012, through May 28, 2013.  The driver and passenger seatback assemblies may have been produced with sub-standard weld joints used to attach the seat back recliner mechanism to the seat frame. The affected seat backs may have insufficient strength to meet the requirements of Federal Motor Vehicle Safety Standard (FMVSS) number 207, "Seating Systems."
- consequence: The back of the subject seats may become loose or lean while driving and potentially increase the risk of injury in certain crashes.
- remedy: Ford will notify owners, and dealers will replace the seatback, free of charge.  The recall began on May 30, 2014.  Owners may contact Ford at 1-800-392-3673.  Ford's number for this recall is 14C03.

`14V164000,14V164000|8c20a13e17bffaff4d07cf7cdb27c05a3b615e932e1759ac82e288829cd1cc33|gemini-3.1-flash-lite|f2-v1,,B,`

## 14V237000  (model gemini-3.1-flash-lite, prompt f2-v1)

1. **Ford is recalling certain 2013-2014 C-MAX and Escape vehicles because the restraint control module may have programming errors that result in a delayed side-curtain rollover air bag deployment.**
   - cites summary: "certain model year 2013-2014 C-MAX, and Escape vehicles" | "restraint control module (RCM) may have errors in the programming software which may result in a delayed deployment of the side-curtain rollover air bag"
2. **If the side-curtain rollover air bag is delayed in certain rollover circumstances, the risk of injury to the passengers is increased.**
   - cites consequence: "If the side-curtain rollover air bag is delayed in deploying in certain rollover circumstances, the risk of injury to the passengers is increased."

Official NHTSA text:
- summary: Ford Motor Company (Ford) is recalling certain model year 2013-2014 C-MAX, and Escape vehicles.  In the affected vehicles, the restraint control module (RCM) may have errors in the programming software which may result in a delayed deployment of the side-curtain rollover air bag.
- consequence: If the side-curtain rollover air bag is delayed in deploying in certain rollover circumstances, the risk of injury to the passengers is increased.
- remedy: Ford will notify owners, and dealers will reprogram the RCM, free of charge.  The recall began on May 30, 2014.  Owners may contact Ford customer service at 1-800-392-3673.  Ford's number for this recall is 14S04.

`14V237000,14V237000|f90468c6889ae1d0d1eb7d8e2edb9e156b92cfaaabf9dcf04cc20dc5df2ac59b|gemini-3.1-flash-lite|f2-v1,,B,`

## 14V239000  (model gemini-3.1-flash-lite, prompt f2-v1)

1. **Certain Escape vehicles have doors that may be difficult to close or may possibly open while driving due to an assembly misalignment.**
   - cites summary: "certain model year 2013-2014 Escape vehicles" | "doors that may be difficult to close or may possibly open while driving"
2. **A door that opens unexpectedly may result in an unrestrained occupant falling from the vehicle, increasing the risk of injury.**
   - cites consequence: "A door that opens unexpectedly may result in an unrestrained occupant falling from the vehicle, increasing the risk of injury."

Official NHTSA text:
- summary: Ford Motor Company (Ford) is recalling certain model year 2013-2014 Escape vehicles manufactured October 5, 2011, through April 10, 2014.  Due to an assembly misalignment between the exterior door handle and the door outer panel, the affected vehicles have doors that may be difficult to close or may possibly open while driving.
- consequence: A door that opens unexpectedly may result in an unrestrained occupant falling from the vehicle, increasing the risk of injury.
- remedy: Ford will notify owners, and dealers will inspect and correct the mounting of the door handles, as necessary, free of charge.  The recall began on May 30, 2014.  Owners may contact Ford customer service at 1-800-392-3673. Ford's number for this recall is 14S03.

`14V239000,14V239000|e32d6bfcb93ea8f3df99b45c83e5f1c728ccc06ce40a2ea287c5d6d344c56495|gemini-3.1-flash-lite|f2-v1,,B,`

## 14V246000  (model gemini-3.1-flash-lite, prompt f2-v1)

1. **General Motors is recalling certain vehicles because the tie rod threaded attachment may not be properly tightened to the steering gear rack.**
   - cites summary: "General Motors LLC (GM) is recalling certain" | "the tie rod threaded attachment may not be properly tightened to the steering gear rack."
2. **An improperly tightened tie rod attachment may allow the tie rod to separate from the steering rack, resulting in a loss of steering and increasing the risk of a crash.**
   - cites consequence: "An improperly tightened tie rod attachment may allow the tie rod to separate from the steering rack, resulting in a loss of steering, increasing the risk of a vehicle crash."

Official NHTSA text:
- summary: General Motors LLC (GM) is recalling certain model year 2014 Chevrolet Silverado vehicles manufactured May 23, 2013, through March 25, 2014, 2014 GMC Sierra vehicles manufactured May 25, 2013, through March 31, 2014, and 2015 Chevrolet Tahoe vehicles manufactured January 29, 2014, through March 27, 2014.  In the affected vehicles, the tie rod threaded attachment may not be properly tightened to the steering gear rack.
- consequence: An improperly tightened tie rod attachment may allow the tie rod to separate from the steering rack, resulting in a loss of steering, increasing the risk of a vehicle crash.
- remedy: GM notified all owners, and dealers will inspect the inner tie rods to make sure that they are correctly tightened, replacing the steering gear, as necessary, free of charge.  The recall began on May 14, 2014.  Owners may contact General Motors customer service at 1-800-222-1020 (Chevrolet), or 1-800-462-8782 (GMC). GM's number for this recall is 14204.  NOTE: Owners are advised not to drive their vehicles until they have been inspected and repaired.  Owners should contact GM to have their vehicles towed to the dealership.

`14V246000,14V246000|6c94987437c9386a9017b9d4ebd187c43da5c3c5df1bc25e2791e0f5e1a10deb|gemini-3.1-flash-lite|f2-v1,,B,`

## 14V374000  (model gemini-3.1-flash-lite, prompt f2-v1)

1. **General Motors is recalling certain Chevrolet, GMC, and Suburban vehicles because an electrical signal short may cause the transfer case to shift to neutral without input.**
   - cites summary: "General Motors LLC (GM) is recalling certain model year 2014-2015 Chevrolet Silverado and GMC Sierra vehicles, and model year 2015 GMC Yukon and Chevrolet Suburban and Tahoe vehicles. In the affected vehicles, an electrical signal short may cause the transfer case to shift to neutral without the driver's input."
2. **If the transfer case switches to neutral, the vehicle may roll away if parked or lose drive power if being driven.**
   - cites consequence: "If the transfer case switches to neutral while the vehicle is parked and the parking brake is not in use, the vehicle may roll away" | "If the transfer case switches to neutral while the vehicle is being driven, the vehicle would lose drive power"

Official NHTSA text:
- summary: General Motors LLC (GM) is recalling certain model year 2014-2015 Chevrolet Silverado and GMC Sierra vehicles, and model year 2015 GMC Yukon and Chevrolet Suburban and Tahoe vehicles.  In the affected vehicles, an electrical signal short may cause the transfer case to shift to neutral without the driver's input.
- consequence: If the transfer case switches to neutral while the vehicle is parked and the parking brake is not in use, the vehicle may roll away increasing the risk of injury to bystanders.  If the transfer case switches to neutral while the vehicle is being driven, the vehicle would lose drive power, increasing the risk of a crash.
- remedy: GM will notify owners, and dealers will re-program the software in the transfer case control module, free of charge.  The recall began in early August 2014.  Owners may contact General Motors customer service at 1-800-222-1020 (Chevrolet), or 1-800-462-8782 (GMC).  GM's number for this recall is 14192.

`14V374000,14V374000|080968c9847fbe948bc4d0399ed9730e9995712b2c1aeba4fe7dd159ee7c39e2|gemini-3.1-flash-lite|f2-v1,,B,`

## 14V403000  (model gemini-3.1-flash-lite, prompt f2-v1)

1. **Certain model year 2014 Ford Escape vehicles may have a panorama roof glass that is not properly bonded to the bracket.**
   - cites summary: "certain model year 2014 Ford Escape vehicles" | "panorama roof glass may not be properly bonded to the attaching bracket"
2. **If the glass panel is improperly bonded, the glass may separate from the vehicle.**
   - cites consequence: "If the glass panel is improperly bonded, the glass may separate from the vehicle"

Official NHTSA text:
- summary: Ford Motor Company (Ford) is recalling certain model year 2014 Ford Escape vehicles manufactured October 15, 2013, through October 22, 2013.  The panorama roof glass may not be properly bonded to the attaching bracket.
- consequence: If the glass panel is improperly bonded, the glass may separate from the vehicle, increasing the risk of a crash or injury.
- remedy: Ford has notified owners.  Dealers will inspect each vehicle and replace the front roof glass if its production date and sequence number falls within the affected range, free of charge.  The recall is began on July 14, 2014.  Owners may contact Ford customer service at 1-800-392-3673.  Ford's number for this recall is 14S13.

`14V403000,14V403000|419189abcfb7028e95fa50279bb7e45fa26fa3a8a7f7feb185b44457056ef938|gemini-3.1-flash-lite|f2-v1,,B,`

## 14V434000  (model gemini-3.1-flash-lite, prompt f2-v1)

1. **Hyundai is recalling certain 2011-2014 Sonata vehicles because the transmission shift cable may detach from the shift lever pin.**
   - cites summary: "Hyundai Motor Company (Hyundai) is recalling certain model year 2011-2014 Sonata vehicles" | "the transmission shift cable may detach from from the shift lever pin"
2. **If the cable detaches, the gear selection may not match the indicated gear, which may cause the vehicle to move in an unexpected direction or roll away if not in park.**
   - cites consequence: "the transmission gear selection may not match the indicated gear and the vehicle may move in an unintended or unexpected direction" | "the transmission may not be in 'PARK.'"

Official NHTSA text:
- summary: Hyundai Motor Company (Hyundai) is recalling certain model year 2011-2014 Sonata vehicles manufactured December 11, 2009, through May 29, 2014.  In the affected vehicles, the transmission shift cable may detach from from the shift lever pin.
- consequence: If the transmission shift cable detaches, the transmission gear selection may not match the indicated gear and the vehicle may move in an unintended or unexpected direction, increasing the risk of a crash.  Furthermore, when the driver parks the vehicle, despite selecting the 'PARK' position, the transmission may not be in 'PARK.'  If the vehicle is not in the 'PARK' position and the parking brake is not applied, there is a risk the vehicle will roll away as the driver and other occupants exit the vehicle or anytime thereafter.  A vehicle rollaway increases the risk of injury to exiting occupants and bystanders.
- remedy: Hyundai will notify owners, and dealers will inspect and, as necessary, repair the connection between the shift cable and shift lever, free of charge.  The recall began in September 2014.  Owners may contact Hyundai customer service at 1-800-633-5151.  Hyundai's number for this recall is 123.

`14V434000,14V434000|a213263685e9f123e0dc5666cfa685248c75713239ca28f87535c6f8b24ee050|gemini-3.1-flash-lite|f2-v1,,B,`

## 14V514000  (model gemini-3.1-flash-lite, prompt f2-v1)

1. **Ford Motor Company is recalling certain model year 2014 Focus and C-Max vehicles that may have steering gears that were incorrectly assembled.**
   - cites summary: "Ford Motor Company (Ford) is recalling certain model year 2014 Focus and C-Max vehicles" | "may have steering gears that were incorrectly assembled."
2. **These incorrectly manufactured steering gears may cause impaired steering, including the loss of steering control, increasing the risk of a crash.**
   - cites consequence: "The incorrectly manufactured steering gears may cause impaired steering, including the loss of steering control, increasing the risk of a crash."

Official NHTSA text:
- summary: Ford Motor Company (Ford) is recalling certain model year 2014 Focus and C-Max vehicles manufactured August 8, 2014, to August 15, 2014.  The affected vehicles may have steering gears that were incorrectly assembled.
- consequence: The incorrectly manufactured steering gears may cause impaired steering, including the loss of steering control, increasing the risk of a crash.
- remedy: Ford will notify owners, and dealers will replace the steering gears, free of charge.  The recall began on November 11, 2014.  Owners may contact Ford customer service at 1-800-392-3673.  Ford's number for this recall is 14S18.

`14V514000,14V514000|1b199a767ee2d5a2929c77dc31bb1283bbeae16616c90ead79e73720653b1456|gemini-3.1-flash-lite|f2-v1,,B,`

## 14V565000  (model gemini-3.1-flash-lite, prompt f2-v1)

1. **Nissan is recalling certain model year 2013 Nissan Altima vehicles because interference may cause the secondary hood latch to bind and remain in the unlatched position.**
   - cites summary: "Nissan North America, Inc. (Nissan) is recalling certain model year 2013 Nissan Altima vehicles" | "interference" | "may cause the secondary hood latch to bind and remain in the unlatched position"
2. **If the primary latch is released and the secondary latch is not engaged, the hood could unexpectedly open while driving, increasing the risk of a crash.**
   - cites consequence: "If the primary latch is inadvertently released and the secondary latch is not engaged, the hood could unexpectedly open while driving, increasing the risk of a vehicle crash."

Official NHTSA text:
- summary: Nissan North America, Inc. (Nissan) is recalling certain model year 2013 Nissan Altima vehicles manufactured March 6, 2012, to February 28, 2013.  In the affected vehicles, interference between the hood inner panel and the secondary latch lever, in combination with debris and corrosion, may cause the secondary hood latch to bind and remain in the unlatched position when the hood is closed.
- consequence: If the primary latch is inadvertently released and the secondary latch is not engaged, the hood could unexpectedly open while driving, increasing the risk of a vehicle crash.
- remedy: Nissan will notify owners, and dealers will be instructed to modify the bend angle of the hood actuation lever to eliminate potential interference with the hood inner panel.  In addition, dealers will clean and lubricate the latch joint as needed.  If significant corrosion is observed, the latch assembly will be replaced. This repairs will be performed free of charge.  The recall began on October 20, 2014.  Owners may contact Nissan customer service at 1-800-647-7261.

`14V565000,14V565000|f829acb0134ecb7c5f08a6b5461c5fae7cb524c2dc0aae06e119cc2cda133a4a|gemini-3.1-flash-lite|f2-v1,,B,`

## 14V597000  (model gemini-3.1-flash-lite, prompt f2-v1)

1. **Ford is recalling certain vehicles because the coating on the Restraint Control Module may crack, which can cause circuits to short when exposed to humidity.**
   - cites summary: "Ford Motor Company (Ford) is recalling certain" | "The coating on portions of the Restraint Control Module (RCM) may crack, and when exposed to humidity, circuits on the printed circuit board may short."
2. **These short circuits could cause air bags and seat belt pretensioners to not function as intended, increasing the risk of injury during a crash.**
   - cites consequence: "The short circuits could cause the frontal air bags, side curtain air bags and the seat belt pretensioners to not function as intended when needed, increasing the risk of occupant injury in the event of a crash."

Official NHTSA text:
- summary: Ford Motor Company (Ford) is recalling certain model year 2013-2014 Ford C-Max vehicles manufactured January 19, 2012, to November 21, 2013; Ford Fusion vehicles manufactured February 3, 2012, to August 24, 2013; Ford Escape vehicles manufactured October 5, 2011, to November 1, 2013; and Lincoln MKZ vehicles manufactured April 25, 2012, to September 30, 2013.  The coating on portions of the Restraint Control Module (RCM) may crack, and when exposed to humidity, circuits on the printed circuit board may short.
- consequence: The short circuits could cause the frontal air bags, side curtain air bags and the seat belt pretensioners to not function as intended when needed, increasing the risk of occupant injury in the event of a crash.
- remedy: Ford will notify owners, and dealers will replace the RCM, free of charge.  Parts are not currently available. The recall began on May 26,2015.  Owners may contact Ford customer service at 1-866-436-7332.  Ford's number for this recall is 14S21.

`14V597000,14V597000|f7e9bdd81144eba9dfffca013b00bb04f853762e03a36c42c06712a24c0dd583|gemini-3.1-flash-lite|f2-v1,,B,`

## 14V719000  (model gemini-3.1-flash-lite, prompt f2-v1)

1. **General Motors is recalling certain vehicles equipped with electric power steering that may experience a sudden loss of power steering assist while in operation.**
   - cites summary: "certain model year 2015 Chevrolet Silverado, Suburban, Tahoe, GMC Sierra, and Yukon XL vehicles, equipped with electric power steering (EPS)" | "may experience a sudden loss of power steering assist during vehicle operation"
2. **An unexpected loss of power steering increases the risk of a crash.**
   - cites consequence: "An unexpected loss of power steering increases the risk of a crash."

Official NHTSA text:
- summary: General Motors LLC (GM) is recalling certain model year 2015 Chevrolet Silverado, Suburban, Tahoe, GMC Sierra, and Yukon XL vehicles, equipped with electric power steering (EPS).  Due to a problem with the EPS module, the affected vehicles may experience a sudden loss of power steering assist during vehicle operation.
- consequence: An unexpected loss of power steering increases the risk of a crash.
- remedy: GM will notify owners, and dealers will replace the power steering assist motor kit, free of charge.  The recall began on November 17, 2014.  Owners may contact GM customer service at 1-800-222-1020 (Chevrolet), or 1-800-462-8782 (GMC).  GM's number for this recall is 14743.

`14V719000,14V719000|1c6e6c681f1c84c6ab87f384b2221e10006d2cbb66f548475190ba1a1a995883|gemini-3.1-flash-lite|f2-v1,,B,`

## 15V041000  (model gemini-3.1-flash-lite, prompt f2-v1)

1. **Certain model year 2014-2015 Jeep Cherokee vehicles may experience unintended side curtain and seat air bag deployment during vehicle operation.**
   - cites summary: "certain model year 2014-2015 Jeep Cherokee vehicles" | "may experience unintended side curtain and seat air bag deployment during vehicle operation"
2. **If the air bags deploy unexpectedly during vehicle operation, it can increase the risk of personal injury and increase the risk of a crash.**
   - cites consequence: "If the air bags deploy unexpectedly during vehicle operation, it can increase the risk of personal injury and increase the risk of a crash."

Official NHTSA text:
- summary: Chrysler is recalling certain model year 2014-2015 Jeep Cherokee vehicles manufactured January 1, 2013, to November 19, 2014.  The affected vehicles may experience unintended side curtain and seat air bag deployment during vehicle operation.
- consequence: If the air bags deploy unexpectedly during vehicle operation, it can increase the risk of personal injury and increase the risk of a crash.
- remedy: Chrysler will notify owners, and dealers will re-flash the occupant restraint control module software, free of charge. The recall began on March 4, 2015. Owners may contact Chrysler customer service at 1-800-853-1403. Chrysler's number for this recall is R05.

`15V041000,15V041000|1ce70a611837d07ab3e065cd7443c377b57ec2d024520dcf4c55b6ff87c5e6f8|gemini-3.1-flash-lite|f2-v1,,B,`

## 15V145000  (model gemini-3.1-flash-lite, prompt f2-v1)

1. **General Motors is recalling certain vehicles where the battery may drain and the engine could start automatically if the system is not turned off.**
   - cites summary: "certain model year 2011-2013 Volt vehicles" | "battery may drain" | "the gasoline engine will automatically start itself"
2. **If the engine runs in an enclosed space, there may be a build up of carbon monoxide, increasing the risk of personal injury.**
   - cites consequence: "there may be a build up of carbon monoxide, increasing the risk of personal injury"

Official NHTSA text:
- summary: General Motors LLC (GM) is recalling certain model year 2011-2013 Volt vehicles manufactured August 25, 2010, to June 26, 2013.  If the driver exits the vehicle without turning off the electrical system, the battery may drain low enough that the gasoline engine will automatically start itself to recharge the electric battery.
- consequence: If the engine runs for an extended period of time in an enclosed space, there may be a build up of carbon monoxide, increasing the risk of personal injury.
- remedy: GM will notify owners, and dealers will update the engine management software to limit the time that the stationary vehicle can be left in the ON position, free of charge. The recall began April 15, 2015. Owners may contact Chevrolet customer service at 1-800-222-1020. GM's number for this recall is 14617.

`15V145000,15V145000|db0a39a7283ea8bd9a8c1b3934fae69e3a0bd07bd2bc1d16c3149b431f809247|gemini-3.1-flash-lite|f2-v1,,B,`

## 15V406000  (model gemini-3.1-flash-lite, prompt f2-v1)

1. **Ford Motor Company is recalling certain model year 2014-2015 Ford Escape and Transit Connect vehicles because a software issue may cause the instrument panel cluster to be inoperative.**
   - cites summary: "Ford Motor Company (Ford) is recalling certain model year 2014-2015 Ford Escape vehicles" | "Transit Connect vehicles" | "software incompatibility issue, the instrument panel cluster be inoperative"
2. **If the instrument cluster is inoperative, the driver may not be warned of safety related issues, increasing the risk of personal injury or a crash.**
   - cites consequence: "If the instrument cluster is inoperative, the driver of may not be warned of safety related issues" | "increasing the risk of personal injury or a crash."

Official NHTSA text:
- summary: Ford Motor Company (Ford) is recalling certain model year 2014-2015 Ford Escape vehicles manufactured May 19, 2014, to February 6, 2015, and Transit Connect vehicles manufactured May 11, 2014, to July 2, 2015.  Due to a software incompatibility issue, the instrument panel cluster be inoperative including a blank multiple functional display (MFD), and non-functional warning chimes, messages and warning lights.  Specific warning chimes, messages and warning lights.  As such, these vehicles fail to comply with the requirements of Federal Motor Vehicle Safety Standard (FMVSS) number 101, "Control and Displays."
- consequence: If the instrument cluster is inoperative, the driver of may not be warned of safety related issues such as low tire pressures or disabled air bags, increasing the risk of personal injury or a crash.
- remedy: Ford will notify owners, and dealers will update the instrument panel software, free of charge.  The recall began on August 4, 2015.  Owners may contact Ford customer service at 1-866-436-7332.  Ford's number for this recall is 15C03.

`15V406000,15V406000|519a3245a682c2ef756c21c317a2ec1d67e0eb2f618b38028b06e5ea09eeded8|gemini-3.1-flash-lite|f2-v1,,B,`

## 15V629000  (model gemini-3.1-flash-lite, prompt f2-v1)

1. **Hyundai is recalling certain model year 2011 Elantra and Sonata vehicles because road salt may corrode the front coil springs, possibly resulting in the coil springs fracturing.**
   - cites summary: "Hyundai Motor America (Hyundai) is recalling certain model year 2011 Elantra vehicles" | "and Sonata vehicles" | "Road salt may corrode the front coil springs, possibly resulting in the coil springs fracturing."
2. **If a front coil spring fractures, it may contact the tire, possibly puncturing it, increasing the risk of a crash.**
   - cites consequence: "If a front coil spring fractures, it may contact the tire, possibly puncturing it, increasing the risk of a crash."

Official NHTSA text:
- summary: Hyundai Motor America (Hyundai) is recalling certain model year 2011 Elantra vehicles manufactured November 12, 2010, to March 31, 2011, and Sonata vehicles manufactured December 11, 2009, to February 28, 2010, originally sold in, or currently registered in, Connecticut, Delaware, Illinois, Indiana, Iowa, Maine, Maryland, Massachusetts, Michigan, Minnesota, Missouri, New Hampshire, New Jersey, New York, Ohio, Pennsylvania, Rhode Island, Vermont, West Virginia, Wisconsin and the District of Columbia.  Road salt may corrode the front coil springs, possibly resulting in the coil springs fracturing.
- consequence: If a front coil spring fractures, it may contact the tire, possibly puncturing it, increasing the risk of a crash.
- remedy: Hyundai will notify owners, and dealers will replace the front coil springs, free of charge.  Interim notifications were mailed on November 17, 2015.  The recall began on January 6, 2016.  Owners may contact Hyundai customer service at 1-855-671-3059.  Hyundai's number for this recall is 133.  Note: Vehicles that were previously registered in salt belt states but are currently registered elsewhere are eligible to be inspected and repaired.

`15V629000,15V629000|4034de31e69efcd59881fdadc4ccbb2ce8ac46cdc2aae8d6639f479b675b2078|gemini-3.1-flash-lite|f2-v1,,B,`

## 15V759000  (model gemini-3.1-flash-lite, prompt f2-v1)

1. **Hyundai is recalling certain 2011-2012 Sonata vehicles because the brake pedal stopper pad may deteriorate.**
   - cites summary: "Hyundai Motor America (Hyundai) is recalling certain model 2011-2012 Sonata vehicles. The brake pedal stopper pad can deteriorate"
2. **This may cause brake lights to stay illuminated or allow the transmission to be shifted out of PARK, increasing the risk of a crash.**
   - cites consequence: "the brake lights may stay illuminated" | "the transmission can be shifted out of PARK" | "increases the risk of a crash"

Official NHTSA text:
- summary: Hyundai Motor America (Hyundai) is recalling certain model 2011-2012 Sonata vehicles.  The brake pedal stopper pad can deteriorate allowing the brake light switch plunger to remain extended when the brake pedal is released.
- consequence: If the brake light switch plunger does not retract as it should when the brake pedal is not being pressed, the brake lights may stay illuminated preventing accurate communication to rearward following vehicles that the vehicle is slowing or stopping. Additionally, if the brake switch plunger is not retracted, then the transmission can be shifted out of PARK without depressing the brake pedal. Either condition increases the risk of a crash.
- remedy: Hyundai will notify owners, and dealers will replace the brake pedal stopper pad with an improved part, free of charge.  The recall began on January 6, 2016.  Owners may contact Hyundai customer service at 1-855-671-3059.  Hyundai's number for this recall is 136.

`15V759000,15V759000|6fdebba8cbab1e97cd3478b486f94c3926d35632c8dec134c2b91aca9dad0feb|gemini-3.1-flash-lite|f2-v1,,B,`

## 15V813000  (model gemini-3.1-flash-lite, prompt f2-v1)

1. **Ford is recalling certain 2013 Escape and 2013-2014 Focus ST vehicles because insufficient compression in engine wiring harness splices may provide incorrect signals.**
   - cites summary: "Ford Motor Company (Ford) is recalling certain model year 2013 Escape vehicles" | "2013-2014 Focus ST vehicles" | "Insufficient compression in the engine wiring harness splices to the Manifold Absolute Pressure (MAP) sensor may provide incorrect signals"
2. **These incorrect signals could cause the vehicle to hesitate or the engine to stall, increasing the risk of a crash.**
   - cites consequence: "The incorrect signals could cause the vehicle to hesitate or the engine to stall, increasing the risk of a crash."

Official NHTSA text:
- summary: Ford Motor Company (Ford) is recalling certain model year 2013 Escape vehicles manufactured January 11, 2012, to April 1, 2013, and 2013-2014 Focus ST vehicles manufactured May 03, 2012, to October 14, 2013.  Insufficient compression in the engine wiring harness splices to the Manifold Absolute Pressure (MAP) sensor may provide incorrect signals to the powertrain control module (PCM).
- consequence: The incorrect signals could cause the vehicle to hesitate or the engine to stall, increasing the risk of a crash.
- remedy: Ford will notify owners, and dealers will replace the current crimped splices with new splices, free of charge.  The recall began on January 7, 2016.  Owners may contact Ford customer service 1-866-436-7332.  Ford's number for this recall is 14S17-S1.

`15V813000,15V813000|bacf699ea4c3811eb242b8a484f6dc381d030eb9cb6bfee84a85fd6ab93fca9c|gemini-3.1-flash-lite|f2-v1,,B,`

## 16V065000  (model gemini-3.1-flash-lite, prompt f2-v1)

1. **Certain vehicles equipped with side curtain-shield-air bags have an air bag control module that may be improperly programmed, causing the bags to deploy inadvertently.**
   - cites summary: "certain model year 2003-2006 Toyota Land Cruiser and Lexus LX470, 2005-2006 Toyota Tundra and Sequoia, 2004-2006 Toyota 4Runner and Lexus GX470 vehicles equipped with side curtain-shield-air bags" | "may be improperly programmed, causing the side curtain-shield-air bags to deploy inadvertently"
2. **If the side curtain-shield-air bags deploy unexpectedly, it can increase the risk of occupant injury.**
   - cites consequence: "If the side curtain-shield-air bags deploy unexpectedly, it can increase the risk of occupant injury."

Official NHTSA text:
- summary: Toyota Motor Engineering & Manufacturing (Toyota) is recalling certain model year 2003-2006 Toyota Land Cruiser and Lexus LX470, 2005-2006 Toyota Tundra and Sequoia, 2004-2006 Toyota 4Runner and Lexus GX470 vehicles equipped with side curtain-shield-air bags.  The affected vehicles have an air bag control module that may be improperly programmed, causing the side curtain-shield-air bags to deploy inadvertently.
- consequence: If the side curtain-shield-air bags deploy unexpectedly, it can increase the risk of occupant injury.
- remedy: Toyota will notify owners, and dealers will replace the air bag control module with one that has improved programming, free of charge.  The recall began on December 1, 2016.  Owners may contact Toyota customer service at 1-888-271-9371.  Toyota's number for this recall is G0C and GLB.

`16V065000,16V065000|f26df37c72be60b2171093afe8305907df0de1815553cc33e768703c74e9d898|gemini-3.1-flash-lite|f2-v1,,B,`

## 16V911000  (model gemini-3.1-flash-lite, prompt f2-v1)

1. **Nissan is recalling certain vehicles where an incorrect Occupant Classification System Electronic Control Unit may have been installed.**
   - cites summary: "Nissan North America, Inc. (Nissan) is recalling certain" | "incorrect Occupant Classification System (OCS) Electronic Control Unit (ECU) may have been installed"
2. **If the occupant is misclassified, the air bag may deploy incorrectly in the event of a crash.**
   - cites consequence: "If the front passenger seat occupant is misclassified, the air bag may deploy incorrectly in the event of a crash"

Official NHTSA text:
- summary: Nissan North America, Inc. (Nissan) is recalling certain model year 2013-2015 Altima vehicles manufactured January 3, 2013, to July 29, 2013, 2015-2016 Rogue vehicles manufactured October 14, 2014, to August 12, 2016, and 2016 Maxima vehicles manufactured June 4, 2015, to August 19, 2015.  An incorrect Occupant Classification System (OCS) Electronic Control Unit (ECU) may have been installed in the front passenger seat.  The incorrect ECU and seat combination may misclassify the front passenger seat occupant.
- consequence: If the front passenger seat occupant is misclassified, the air bag may deploy incorrectly in the event of a crash, increasing the risk of injury.
- remedy: Nissan will notify owners, and dealers will replace the ECU and update the OCS software free of charge.  The recall began February 13, 2017.  Owners may contact Nissan customer service at 1-800-647-7261.

`16V911000,16V911000|7d84d3b455e802f732a46abb789cb8623425b554284f52c1b6a4c6fb25e16c30|gemini-3.1-flash-lite|f2-v1,,B,`

## 17V152000  (model gemini-3.1-flash-lite, prompt f2-v1)

1. **Hyundai is recalling certain 2011-2014 Sonata and 2011-2015 Sonata Hybrid vehicles where the seat belt linkages may detach from the seat belt anchor pretensioners.**
   - cites summary: "certain 2011-2014 Sonata and 2011-2015 Sonata Hybrid vehicles" | "seat belt linkages for both front seat belts may detach from the seat belt anchor pretensioners"
2. **In the event of a crash, if the seat belts detach from the anchor pretensioners, it can increase the risk of injury.**
   - cites consequence: "In the event of a crash, if the seat belts detach from the anchor pretensioners, it can increase the risk of injury."

Official NHTSA text:
- summary: Hyundai Motor America (Hyundai) is recalling certain 2011-2014 Sonata and 2011-2015 Sonata Hybrid vehicles.  In the affected vehicles, the seat belt linkages for both front seat belts may detach from the seat belt anchor pretensioners.
- consequence: In the event of a crash, if the seat belts detach from the anchor pretensioners, it can increase the risk of injury.
- remedy: Hyundai will notify owners and dealers will inspect the connection between the seat belt linkages and the seat belt anchor pretensioners, repairing them as necessary, free of charge.  The recall is expected to begin April 7, 2017.  Owner's may contact Hyundai customer service at 1-855-371-9460.  Hyundai's number for the recall is 160.

`17V152000,17V152000|173f90dc1b104869b58882f63c7867232e68d216222934e927e9d64ff9a9290d|gemini-3.1-flash-lite|f2-v1,,B,`

## 17V224000  (model gemini-3.1-flash-lite, prompt f2-v1)

1. **Kia is recalling certain vehicles because machining errors may cause premature bearing wear within the engine.**
   - cites summary: "Kia Motor Company (Kia) is recalling certain" | "Machining errors during the engine manufacturing process may cause premature bearing wear within the engine."
2. **This bearing wear may result in the engine seizing, and dealers will inspect the engine assembly and replace it if necessary.**
   - cites consequence, remedy: "Bearing wear may result in the engine seizing" | "dealers will inspect the engine assembly, and replace the engine if necessary"

Official NHTSA text:
- summary: Kia Motor Company (Kia) is recalling certain 2011-2014 Optima, 2012-2014 Sorento and 2011-2013 Sportage vehicles.  Machining errors during the engine manufacturing process may cause premature bearing wear within the engine.
- consequence: Bearing wear may result in the engine seizing, increasing the risk of a crash.
- remedy: Kia will notify owners, and dealers will inspect the engine assembly, and replace the engine if necessary, free of charge.  The recall began June 20, 2017.  Owners may contact Kia customer service at 1-800-333-4542.  Kia's number for this recall is SC147.

`17V224000,17V224000|2789d0ac7825e5f324bd2d12ddd7ccb0305e7fdb987c09af154fe6c1c578e058|gemini-3.1-flash-lite|f2-v1,,B,`

## 17V342000  (model gemini-3.1-flash-lite, prompt f2-v1)

1. **Vantage Mobility is recalling certain Chrysler Pacifica vans modified for wheelchair accessibility because the rear brake lines may have been crossed.**
   - cites summary: "Vantage Mobility International, LLC (Vantage Mobility) is recalling certain 2017 Chrysler Pacifica lowered floor vans modified by Vantage Mobility for wheelchair accessibility." | "The affected vans have rear brake lines that might have been crossed"
2. **These crossed rear brake lines will cause the rear anti-lock brake system to be ineffective, increasing the risk of a crash.**
   - cites consequence: "The crossed rear brake lines will cause the rear anti-lock brake system to be ineffective, increasing the risk of a crash."

Official NHTSA text:
- summary: Vantage Mobility International, LLC (Vantage Mobility) is recalling certain 2017 Chrysler Pacifica lowered floor vans modified by Vantage Mobility for wheelchair accessibility.  The affected vans have rear brake lines that might have been crossed during the modification.  As such, these vehicles fail to comply with the requirements of Federal Motor Vehicle Safety Standard number 135, "Light Vehicle Brake Systems."
- consequence: The crossed rear brake lines will cause the rear anti-lock brake system to be ineffective, increasing the risk of a crash.
- remedy: Vantage Mobility will notify owners, and dealers will correct the rear brake line attachments, free of charge.  The recall began on July 3, 2017.  Owners may contact Vantage Mobility customer service at 1-800-488-9082.  Vantage Mobility's number for this recall is Pac-20170525.

`17V342000,17V342000|22627a27075df618c302c62439fa23a47c88a116007702c2e632f7b98a3d4eec|gemini-3.1-flash-lite|f2-v1,,B,`

## 17V617000  (model gemini-3.1-flash-lite, prompt f2-v1)

1. **For certain vehicles, the seat belt linkages may detach from the seat belt anchor pretensioners.**
   - cites summary: "certain 2011-2014 Sonata and 2011-2015 Sonata Hybrid vehicles" | "The seat belt linkages for both front seat belts may detach from the seat belt anchor pretensioners."
2. **If the seat belt linkage detaches, it may not properly restrain the occupant in a crash, increasing the risk of injury.**
   - cites consequence: "If the seat belt linkage detaches from the seat belt anchorage, it can not properly restrain the occupant in the event of a crash, increasing the risk of injury."

Official NHTSA text:
- summary: Hyundai Motor America (Hyundai) is recalling certain 2011-2014 Sonata and 2011-2015 Sonata Hybrid vehicles previously repaired under recall campaign 17V-152.  The seat belt linkages for both front seat belts may detach from the seat belt anchor pretensioners.
- consequence: If the seat belt linkage detaches from the seat belt anchorage, it can not properly restrain the occupant in the event of a crash, increasing the risk of injury.
- remedy: Hyundai will notify owners, and dealers will again verify the connection between the seat belt linkage and the pretensioner and additionally install a warning label to prevent future seat belt linkage detachment, free of charge.  The recall began November 6, 2017.  Owners may contact Hyundai customer service at 1-855-371-9460.  Hyundai's number for this recall is 169.

`17V617000,17V617000|1018ef9be8e373a582d250b581b8b0eb13b396d831271cba54ba71133b7d477e|gemini-3.1-flash-lite|f2-v1,,B,`

## 17V824000  (model gemini-3.1-flash-lite, prompt f2-v1)

1. **Certain Chrysler, Dodge, and RAM vehicles may be equipped with fire extinguishers that can become clogged or have a nozzle that may detach.**
   - cites summary: "Chrysler (FCA US LLC) is recalling various Dodge, Chrysler, and RAM vehicles equipped with Kidde Plastic-Handle or Push Button 'Pindicator' Fire Extinguishers." | "These extinguishers may become clogged" | "in certain models, the nozzle may detach"

Official NHTSA text:
- summary: Chrysler (FCA US LLC) is recalling various Dodge, Chrysler, and RAM vehicles equipped with Kidde Plastic-Handle or Push Button 'Pindicator' Fire Extinguishers.  A list of the affected trailer models is available at: https://static.nhtsa.gov/odi/rcl/2017/RMISC-17V824-0103.pdf.  These extinguishers may become clogged, preventing the extinguisher from discharging as expected or requiring excessive force to activate the extinguisher.  Additionally, in certain models, the nozzle may detach from the valve assembly with enough force that it could cause injury and also render the product inoperable.  For a full list of the affected fire extinguisher models visit: https://static.nhtsa.gov/odi/rcl/2017/RMISC-17E062-5427.pdf
- consequence: If the fire extinguisher does not function properly, it can increase the risk of injury in the event of a fire.
- remedy: Chrysler will notify owners instructing them to contact Kidde for a replacement fire extinguisher, free of charge.  The recall began February 14, 2018.  Owners may contact Chrysler customer service at 1-800-853-1403 or Kidde customer service service toll-free at 1-855-262-3540, or online at www.kidde.com and click on "Product Safety Recall" for more information. Chrysler's number for this recall is T82.

`17V824000,17V824000|95cff692dbc8fac2a162ddcaeba0830dc27c02dc2b78e4a1e30b8d7b48fc54ba|gemini-3.1-flash-lite|f2-v1,,B,`

## 18V049000  (model gemini-3.1-flash-lite, prompt f2-v1)

1. **Chrysler is recalling certain 2017 Chrysler Pacifica vehicles equipped with a 3.6l engine because the engine control software may become out of sync with the crankshaft position sensor, possibly resulting in an engine stall.**
   - cites summary: "Chrysler (FCA US LLC) is recalling certain 2017 Chrysler Pacifica vehicles equipped with a 3.6l engine. The engine control software may become out of sync with the crankshaft position sensor, possibly resulting in an engine stall."
2. **An engine stall may increase the risk of a crash, so dealers will update the engine control software.**
   - cites consequence, remedy: "An engine stall can increase the risk of a crash." | "dealers will update the engine control software"

Official NHTSA text:
- summary: Chrysler (FCA US LLC) is recalling certain 2017 Chrysler Pacifica vehicles equipped with a 3.6l engine.  The engine control software may become out of sync with the crankshaft position sensor, possibly resulting in an engine stall.
- consequence: An engine stall can increase the risk of a crash.
- remedy: Chrysler will notify owners, and dealers will update the engine control software, free of charge.  The recall began March 7, 2018.  Owners may contact Chrysler customer service at 1-800-853-1403.  Chrysler's number for this recall is U01.

`18V049000,18V049000|a5ed391fd627fbd6aaf33179902f2e219d94928082dfd39900ad1531eb1e40d0|gemini-3.1-flash-lite|f2-v1,,B,`

## 18V280000  (model gemini-3.1-flash-lite, prompt f2-v1)

1. **Chrysler is recalling certain Dodge, Jeep, Chrysler, and RAM vehicles because an incorrect transmission park lock rod may have been installed.**
   - cites summary: "Chrysler (FCA US LLC) is recalling certain 2018 Dodge Charger, Durango and Challenger, Jeep Grand Cherokee and Wrangler, Chrysler 300, and RAM 1500 vehicles. An incorrect transmission park lock rod may have been installed in the transmission."
2. **If the incorrect park lock rod is installed, the transmission may not shift into park, which increases the risk of unintended vehicle movement.**
   - cites consequence: "If the incorrect park lock rod is installed, the transmission may not shift into 'PARK' and keep the vehicle from moving, increasing the risk of unintended vehicle movement"

Official NHTSA text:
- summary: Chrysler (FCA US LLC) is recalling certain 2018 Dodge Charger, Durango and Challenger, Jeep Grand Cherokee and Wrangler, Chrysler 300, and RAM 1500 vehicles.  An incorrect transmission park lock rod may have been installed in the transmission.
- consequence: If the incorrect park lock rod is installed, the transmission may not shift into 'PARK' and keep the vehicle from moving, increasing the risk of unintended vehicle movement and the risk of a crash.
- remedy: Chrysler will notify owners, and dealers will install the correct park lock rod, free of charge.  The recall began June 28, 2018.  Owners may contact Chrysler customer service at 1-800-853-1403.  Chrysler's number for this recall is U43.

`18V280000,18V280000|7d0e4482bd3ba86ec3b64ced44e70131f28634e8eef137cae1ecd9fb6de6ab95|gemini-3.1-flash-lite|f2-v1,,B,`

## 18V291000  (model gemini-3.1-flash-lite, prompt f2-v1)

1. **General Motors LLC is recalling certain Chevrolet Silverado 1500 and Tahoe Police Pursuit and Special-Service vehicles because the flexible steel cable connecting the driver's seat belt may be repeatedly bent and separate.**
   - cites summary: "General Motors LLC (GM) is recalling certain 2015-2016 Chevrolet Silverado 1500 and Tahoe Police Pursuit and Special-Service vehicles." | "The flexible steel cable connecting the driver's seat belt to the outboard side of the seat may be repeatedly bent over the seat side shield as the driver enters and exits the vehicle causing the cable to fatigue and separate."
2. **If the pretensioner cable becomes fatigued or breaks, the driver may not be properly restrained in the event of a crash, increasing their risk of injury.**
   - cites consequence: "If the pretensioner cable becomes fatigued or breaks, the driver may not be properly restrained in the event of a crash, increasing their risk of injury."

Official NHTSA text:
- summary: General Motors LLC (GM) is recalling certain 2015-2016 Chevrolet Silverado 1500 and Tahoe Police Pursuit and Special-Service vehicles.  The flexible steel cable connecting the driver's seat belt to the outboard side of the seat may be repeatedly bent over the seat side shield as the driver enters and exits the vehicle causing the cable to fatigue and separate.
- consequence: If the pretensioner cable becomes fatigued or breaks, the driver may not be properly restrained in the event of a crash, increasing their risk of injury.
- remedy: GM will notify owners, and dealers will replace the pretensioner cable and seat side-shield, free of charge.  The recall began June 19, 2018.  Owners may contact Chevrolet customer service at 1-800-222-1020.  GM's number for this recall is 18156.

`18V291000,18V291000|8e6accbb2c71355cd8489c74db9a4291ba19d5592bf5e45a387b9bd55cb996aa|gemini-3.1-flash-lite|f2-v1,,B,`

## 18V343000  (model gemini-3.1-flash-lite, prompt f2-v1)

1. **Chrysler is recalling certain 2018 Jeep Wrangler vehicles because the intermediate steering shaft may not have been properly welded.**
   - cites summary: "Chrysler (FCA US LLC) is recalling certain 2018 Jeep Wrangler vehicles. The intermediate steering shaft may not have been properly welded"
2. **If the weld seam splits, the steering wheel may lose center positioning causing a loss of steering responsiveness.**
   - cites consequence: "If the weld seam splits, the steering wheel may lose center positioning causing a loss of steering responsiveness"

Official NHTSA text:
- summary: Chrysler (FCA US LLC) is recalling certain 2018 Jeep Wrangler vehicles.  The intermediate steering shaft may not have been properly welded causing a split where the external spline is formed.
- consequence: If the weld seam splits, the steering wheel may lose center positioning causing a loss of steering responsiveness and increasing the risk of a crash.
- remedy: Chrysler will notify owners, and dealers will inspect and, as necessary, replace the intermediate steering shaft, free of charge.  The recall began June 21, 2018.  Owners may contact Chrysler customer service at 1-800-853-1403.  Chrysler's number for this recall is U48.

`18V343000,18V343000|83378680e3a2832b6330f094fb970227585f6b31c34e9eb99d66314452ac5c36|gemini-3.1-flash-lite|f2-v1,,B,`

## 18V397000  (model gemini-3.1-flash-lite, prompt f2-v1)

1. **General Motors is recalling certain 2013 Chevrolet Volt vehicles because an update may have disabled a function causing a low-voltage condition.**
   - cites summary: "General Motors LLC (GM) is recalling certain 2013 Chevrolet Volt vehicles. An update to the Hybrid Powertrain Control Module 2 (HPCM2) may have disabled the cell balancing function causing a low-voltage condition."
2. **If the voltage drops, the vehicle may lose propulsion, which increases the risk of a crash.**
   - cites consequence: "If the voltage drops, the vehicle may lose propulsion, increasing the risk of crash."

Official NHTSA text:
- summary: General Motors LLC (GM) is recalling certain 2013 Chevrolet Volt vehicles.  An update to the Hybrid Powertrain Control Module 2 (HPCM2) may have disabled the cell balancing function causing a low-voltage condition.
- consequence: If the voltage drops, the vehicle may lose propulsion, increasing the risk of crash.
- remedy: GM will notify owners, and dealers will reprogram the HPCM2, free of charge.  The recall began July 24, 2018.  Owners may contact Chevrolet customer service at 1-800-222-1020.  GM's number for this recall is 18215.

`18V397000,18V397000|4a715c64e0f896581d2cb9bd71c534b9cc7d1893f21c9ee7d44599802d33241a|gemini-3.1-flash-lite|f2-v1,,B,`

## 18V471000  (model gemini-3.1-flash-lite, prompt f2-v1)

1. **Certain Ford vehicles equipped with six-speed automatic transmissions may have a shifter cable bushing that can degrade and detach.**
   - cites summary: "certain 2013-2014 Ford Escape, and 2013-2016 Ford Fusion vehicles, equipped with six-speed automatic transmissions" | "The bushing that attaches the transmission shifter cable to the transmission may degrade over time and cause the bushing to detach from the transmission"
2. **If the transmission is not in Park, the vehicle may unexpectedly move, increasing the risk of a crash.**
   - cites consequence: "the vehicle may unexpectedly move, increasing the risk of a crash"

Official NHTSA text:
- summary: Ford Motor Company (Ford) is recalling certain 2013-2014 Ford Escape, and 2013-2016 Ford Fusion vehicles, equipped with six-speed automatic transmissions.  The bushing that attaches the transmission shifter cable to the transmission may degrade over time and cause the bushing to detach from the transmission.  The condition could allow the driver to move the shift lever to Park and remove the ignition key, while the transmission may not be in Park, with no warning message or audible chime.
- consequence: If the vehicle is exited without the transmission being in Park and without the parking brake being applied, the vehicle may unexpectedly move, increasing the risk of a crash.
- remedy: Ford will notify owners, and dealers will replace the shifter cable bushing, free of charge.  The recall began September 20, 2018.  Owners may contact Ford customer service at 1-866-436-7332.  Ford's number for this recall is 18S20.  Note: Owners are directed to use the parking brake until the recall remedy repairs can be made.

`18V471000,18V471000|2a9a64c7fca433b116b2219f28d821161be1a641fa952f7f73a72a1431d383d4|gemini-3.1-flash-lite|f2-v1,,B,`

## 18V675000  (model gemini-3.1-flash-lite, prompt f2-v1)

1. **Certain 2018-2019 Jeep Wrangler vehicles may have front track bar brackets that are improperly welded, potentially causing the bracket to separate from the frame and reducing steering capability.**
   - cites summary: "certain 2018-2019 Jeep Wrangler vehicles" | "The front track bar brackets may be improperly welded, which can cause the bracket to separate from the frame, reducing steering capability."
2. **An unexpected reduction in steering ability can increase the risk of a crash, and dealers will inspect and repair the track bar bracket welds as necessary.**
   - cites consequence, remedy: "An unexpected reduction in steering ability, can increase the risk of a crash." | "dealers will inspect and repair the track bar bracket welds, as necessary"

Official NHTSA text:
- summary: Chrysler (FCA US LLC) is recalling certain 2018-2019 Jeep Wrangler vehicles.  The front track bar brackets may be improperly welded, which can cause the bracket to separate from the frame, reducing steering capability.
- consequence: An unexpected reduction in steering ability, can increase the risk of a crash.
- remedy: Chrysler will notify owners, and dealers will inspect and repair the track bar bracket welds, as necessary, free of charge.  The recall is expected to begin November 17, 2018.  Owners may contact Chrysler customer service at 1-800-853-1403.  Chrysler's number for this recall is UA5.

`18V675000,18V675000|7266ee46fed72189065c9363dc9a6947cb7abb6c025391ede7e195e27b08ff8d|gemini-3.1-flash-lite|f2-v1,,B,`

## 18V775000  (model gemini-3.1-flash-lite, prompt f2-v1)

1. **For certain vehicles that received a replacement passenger air bag, the bracket that secures the air bag inflator may deform during a crash, allowing the gas to leak.**
   - cites summary: "certain 2010 Ford Fusion, Mercury Milan and 2010-2012 Lincoln MKZ vehicles that previously received a replacement passenger air bag" | "the bracket that secures the air bag inflator to the module housing may deform, allowing the gas that inflates the air bag to leak out."
2. **If the air bag does not inflate as intended, there is an increased risk of injury.**
   - cites consequence: "If the air bag does not inflate as intended, there is an increased risk of injury"

Official NHTSA text:
- summary: Ford Motor Company (Ford) is recalling certain 2010 Ford Fusion, Mercury Milan and 2010-2012 Lincoln MKZ vehicles that previously received a replacement passenger air bag under recall 16V-384, 17V-024 or 18V-046.  In the event of a crash requiring deployment of the passenger air bag, the bracket that secures the air bag inflator to the module housing may deform, allowing the gas that inflates the air bag to leak out.
- consequence: If the air bag does not inflate as intended, there is an increased risk of injury in the event of a crash.
- remedy: Ford will notify owners, and dealers will replace the passenger air bag module, free of charge.  The recall began November 21, 2018.  Owners may contact Ford customer service at 1-866-436-7332.  Ford's number for this recall is 18S34.

`18V775000,18V775000|5249827a9639b3b88bc677634d25073639f29c5628287d9c2e9728b23b91cf54|gemini-3.1-flash-lite|f2-v1,,B,`

## 18V786000  (model gemini-3.1-flash-lite, prompt f2-v1)

1. **Chrysler is recalling certain 2018 Jeep Wrangler four-door vehicles because the right rear passenger door latch may not be in the correct location.**
   - cites summary: "Chrysler (FCA US LLC) is recalling certain 2018 Jeep Wrangler four-door vehicles. The right rear passenger door latch may not be in the correct location"
2. **If the right rear passenger door opens unexpectedly, it can increase the risk of injury.**
   - cites consequence: "If the right rear passenger door opens unexpectedly, it can increase the risk of injury."

Official NHTSA text:
- summary: Chrysler (FCA US LLC) is recalling certain 2018 Jeep Wrangler four-door vehicles.  The right rear passenger door latch may not be in the correct location, possibly preventing the door from latching properly.
- consequence: If the right rear passenger door opens unexpectedly, it can increase the risk of injury.
- remedy: Chrysler will notify owners, and dealers will repair the right rear door latch reinforcement, free of charge.  The recall begin December 6, 2018.  Owners may contact Chrysler customer service at 1-800-853-1403.  Chrysler's number for this recall is UB6.

`18V786000,18V786000|5bb7b4eb20f3e35b87d9f63062e433ca2993c9dc5e243eaafb5ea33d3f1b728f|gemini-3.1-flash-lite|f2-v1,,B,`

## 18V824000  (model gemini-3.1-flash-lite, prompt f2-v1)

1. **Certain Volkswagen vehicles that do not have keyless entry may not provide an audible warning if the key is still in the ignition when the door is open.**
   - cites summary: "certain 2018-2019 Volkswagen Atlas and Tiguan and 2019 Volkswagen Jetta vehicles that do not have keyless entry. The instrument cluster may not provide an audible warning to let the driver know that the key is still in the ignition when the door is open."
2. **If the driver is not notified by an audible noise that the key is left in the ignition, it can increase the risk of vehicle theft or crash.**
   - cites consequence: "If the driver is not notified by an audible noise that the key is left in the ignition, it can increase the risk of vehicle theft or crash."

Official NHTSA text:
- summary: Volkswagen Group of America, Inc. (Volkswagen) is recalling certain 2018-2019 Volkswagen Atlas and Tiguan and 2019 Volkswagen Jetta vehicles that do not have keyless entry.  The instrument cluster may not provide an audible warning to let the driver know that the key is still in the ignition when the door is open.  As such, these vehicles fail to comply with the requirements of Federal Motor Vehicle Safety Standard (FMVSS) number 114, "Theft Protection."
- consequence: If the driver is not notified by an audible noise that the key is left in the ignition, it can increase the risk of vehicle theft or crash.
- remedy: Volkswagen will notify owners, and dealers will reprogram the instrument cluster, free of charge.  The recall began December 13, 2018.  Owners may contact Volkswagen customer service at 1-800-893-5298.  Volkswagen's numbers for this recall are 90L3 and 90L4.

`18V824000,18V824000|2d642138d8d20011187daefb074e74b624e64de6c3c3ced9422db19e7d5c4daf|gemini-3.1-flash-lite|f2-v1,,B,`

## 18V904000  (model gemini-3.1-flash-lite, prompt f2-v1)

1. **Volkswagen is recalling certain vehicles because the rear coil springs may prematurely fracture.**
   - cites summary: "Volkswagen Group of America, Inc. (Volkswagen) is recalling certain 2018-2019 Volkswagen Atlas, 2015 Volkswagen Golf SportWagen, and 2019 Volkswagen Jetta vehicles. The rear coil springs may prematurely fracture."
2. **If a coil spring fractures while driving, it may damage a rear tire, which increases the risk of a crash.**
   - cites consequence: "If a coil spring fractures while driving, it may damage a rear tire causing a loss of vehicle control, increasing the risk of a crash."

Official NHTSA text:
- summary: Volkswagen Group of America, Inc. (Volkswagen) is recalling certain 2018-2019 Volkswagen Atlas, 2015 Volkswagen Golf SportWagen, and 2019 Volkswagen Jetta vehicles.  The rear coil springs may prematurely fracture.
- consequence: If a coil spring fractures while driving, it may damage a rear tire causing a loss of vehicle control, increasing the risk of a crash.
- remedy: Volkswagen has notified owners, and dealers will replace the rear axle coil springs, free of charge.  The recall began January 31, 2019.  Owners may contact Volkswagen customer service at 1-800-893-5298.  Volkswagen's number for this recall is 42J2/42J3.

`18V904000,18V904000|53e1ea7838770229db65f2321b6ddb43c8abde291974d0afb5b112db513b39f4|gemini-3.1-flash-lite|f2-v1,,B,`

## 18V907000  (model gemini-3.1-flash-lite, prompt f2-v1)

1. **Kia is recalling certain vehicles that received an engine replacement, as the high pressure fuel pipe may have been damaged, misaligned or improperly torqued, possibly causing a fuel leak.**
   - cites summary: "certain 2011-2017 Optima, 2012-2017 Sorento and 2011-2018 Sportage vehicles that previously received an engine replacement" | "The high pressure fuel pipe that connects to the fuel pump outlet may have been damaged, misaligned or improperly torqued during the engine replacement procedure, possibly causing a fuel leak."
2. **A fuel leak in the presence of an ignition source can increase the risk of a fire.**
   - cites consequence: "A fuel leak in the presence of an ignition source can increase the risk of a fire."

Official NHTSA text:
- summary: Kia Motors America (Kia) is recalling certain 2011-2017 Optima, 2012-2017 Sorento and 2011-2018 Sportage vehicles that previously received an engine replacement under recall number 17V-224, warranty, or the Knock Sensor Detection System (KSDS) Product Improvement Campaign.  The high pressure fuel pipe that connects to the fuel pump outlet may have been damaged, misaligned or improperly torqued during the engine replacement procedure, possibly causing a fuel leak.
- consequence: A fuel leak in the presence of an ignition source can increase the risk of a fire.
- remedy: Kia has notified owners, and dealers will inspect and replace the fuel pipe, as necessary, free of charge.  The recall began January 17, 2019.  Owners may contact Kia customer service at 1-800-333-4542.  Kia's number for this recall is SC172.

`18V907000,18V907000|105254f63fc73dd4356da9ed62236990237699ac492317fe86507c79841b5f52|gemini-3.1-flash-lite|f2-v1,,B,`

## 18V934000  (model gemini-3.1-flash-lite, prompt f2-v1)

1. **Certain Hyundai vehicles may have a high pressure fuel pipe that was damaged, misaligned, or improperly torqued, potentially allowing fuel to leak.**
   - cites summary: "certain 2011-2014 Sonata and 2013-2014 Santa Fe Sport vehicles" | "The high pressure fuel pipe that connects to the fuel pump outlet may have been damaged, misaligned, or improperly torqued" | "allowing fuel to leak from the pipe"
2. **A fuel leak in the presence of an ignition source can increase the risk of a fire.**
   - cites consequence: "A fuel leak in the presence of an ignition source can increase the risk of a fire."

Official NHTSA text:
- summary: Hyundai Motor America (Hyundai) is recalling certain 2011-2014 Sonata and 2013-2014 Santa Fe Sport vehicles previously repaired under recall numbers 15V-568 and 17V-226.  The high pressure fuel pipe that connects to the fuel pump outlet  may have been damaged, misaligned, or improperly torqued during the engine replacement procedure, allowing fuel to leak from the pipe.
- consequence: A fuel leak in the presence of an ignition source can increase the risk of a fire.
- remedy: Hyundai will notify owners, and dealers will inspect and replace the fuel pipe, as necessary, free of charge. The recall began March 1, 2019.  Owners may contact Hyundai customer service at 1-855-371-9460.  Hyundai's recall number for this recall is 180.

`18V934000,18V934000|9f2d5efe6fb2093f3395787031ed0dbaaabffef1cd3b2d2b141d2efab2f63262|gemini-3.1-flash-lite|f2-v1,,B,`

## 19V348000  (model gemini-3.1-flash-lite, prompt f2-v1)

1. **Certain Pacifica vehicles equipped with engine stop/start systems may have a loose battery ground connection that can cause a loss of power steering assist or a stall.**
   - cites summary: "certain 2017-2019 Pacifica vehicles equipped with engine stop/start systems" | "A loose battery ground connection may result in an intermittent loss of power steering assist and/or a stall"
2. **A loss of power steering assist or a stall may increase the risk of a crash.**
   - cites consequence: "A loss of power steering assist or a stall can increase the risk of crash"

Official NHTSA text:
- summary: Chrysler (FCA US LLC) is recalling certain 2017-2019 Pacifica vehicles equipped with engine stop/start systems.  A loose battery ground connection may result in an intermittent loss of power steering assist and/or a stall.
- consequence: A loss of power steering assist or a stall can increase the risk of crash.
- remedy: Chrysler will notify owners, and dealers will inspect the battery ground surfaces, clean the contact surfaces as needed, and properly reassemble the ground connection, free of charge.  The recall began May 24, 2019.  Owners may contact Chrysler customer service at 1-800-853-1403.  FCA US' number for this recall is V53.

`19V348000,19V348000|701f813d82232758b309185e7d2a90553873e6ca81e2519e9d557a11a17bf915|gemini-3.1-flash-lite|f2-v1,,B,`

## 19V615000  (model gemini-3.1-flash-lite, prompt f2-v1)

1. **Volkswagen is recalling certain vehicles equipped with an automatic transmission, manual handbrake and keyless entry because a build-up of silicate on the shift lever micro switch contacts may enable the key to be removed when the transmission is not in Park.**
   - cites summary: "Volkswagen Group of America, Inc. (Volkswagen) is recalling certain" | "vehicles equipped with an automatic transmission, manual handbrake and keyless entry" | "A build-up of silicate on the shift lever micro switch contacts may enable the key to be removed from the ignition when the transmission shift lever is not in "Park.""
2. **Removing the key while the shift lever is not in Park increases the risk of an unintended vehicle rollaway that may result in personal injury or a crash.**
   - cites consequence: "Removing the key while the shift lever is in a position other than "Park" increases the risk of an unintended vehicle rollaway that may result in personal injury or a crash."

Official NHTSA text:
- summary: Volkswagen Group of America, Inc. (Volkswagen) is recalling certain 2015-2019 GTI, 2015-2016 and 2018-2019 Golf, 2012-2019 Beetle and Beetle Convertible, 2017-2019 Golf SportWagen and 2011-2018 Jetta vehicles equipped with an automatic transmission, manual handbrake and keyless entry.  A build-up of silicate on the shift lever micro switch contacts may enable the key to be removed from the ignition when the transmission shift lever is not in "Park."
- consequence: Removing the key while the shift lever is in a position other than "Park" increases the risk of an unintended vehicle rollaway that may result in personal injury or a crash.
- remedy: Volkswagen will notify owners, and dealers will install an additional switch and circuit board, free of charge.  The recall began November 19, 2019. Owners may contact Volkswagen customer service at 1-800-893-5298.  Volkswagen's number for this recall is 37M2.

`19V615000,19V615000|b6daa15b6021f32a9ea15f0c1fa0d7285f3f82c4f98ac01a12ef8f73909497e5|gemini-3.1-flash-lite|f2-v1,,B,`

## 19V680000  (model gemini-3.1-flash-lite, prompt f2-v1)

1. **Certain Jeep Wrangler vehicles are being recalled because the driver's seat belt buckle mounting strap may fracture and separate from the seat frame.**
   - cites summary: "certain 2011-2018 Jeep Wrangler right hand drive vehicles. The driver's seat belt buckle mounting strap may fracture and separate from the seat frame."
2. **A separated or severed seat belt buckle strap will result in an inoperable seat belt, increasing the risk of injury in the event of a crash.**
   - cites consequence: "A separated or severed seat belt buckle strap will result in an inoperable seat belt, increasing the risk of injury in the event of a crash."

Official NHTSA text:
- summary: Chrysler (FCA US LLC) is recalling certain 2011-2018 Jeep Wrangler right hand drive vehicles.  The driver's seat belt buckle mounting strap may fracture and separate from the seat frame.
- consequence: A separated or severed seat belt buckle strap will result in an inoperable seat belt, increasing the risk of injury in the event of a crash.
- remedy: FCA US will notify owners, and dealers will replace the driver's seat belt buckle, free of charge.  Interim notices informing owners of the safety risk were mailed November 19, 2019.  Owners will received a second letter and the recall began March 26, 2020.  Owners may contact FCA customer service at 1-800-853-1403.  FCA's number for this recall is VA6.

`19V680000,19V680000|da3dcb16c7e706fc9aa04830c0c84eab0f99db96fdbfad59230ede6874e01d13|gemini-3.1-flash-lite|f2-v1,,B,`

## 20V124000  (model gemini-3.1-flash-lite, prompt f2-v1)

1. **Chrysler is recalling certain Jeep Wrangler and Gladiator vehicles equipped with manual transmissions because the clutch pressure plate may overheat and fracture.**
   - cites summary: "Chrysler (FCA US LLC) is recalling certain 2018-2020 Jeep Wrangler and 2020 Gladiator vehicles equipped with manual transmissions. The clutch pressure plate may overheat and fracture."
2. **These overheated clutch components may increase the risk of a fire or cause a loss of drive.**
   - cites consequence: "The overheated clutch components may increase the risk of a fire." | "loss of drive"

Official NHTSA text:
- summary: Chrysler (FCA US LLC) is recalling certain 2018-2020 Jeep Wrangler and 2020 Gladiator vehicles equipped with manual transmissions.  The clutch pressure plate may overheat and fracture.
- consequence: The overheated clutch components may increase the risk of a fire.  Additionally, damage to other nearby components can result in debris falling onto the road or a loss of drive, increasing the risk of a crash.
- remedy: Chrysler will notify owners, and dealers will reroute a wire harness and inspect the clutch system, and replace components as needed.  The recall began April 30, 2020.  Owners may contact Chrysler customer service at 1-800-853-1403.  Chrysler's number for this recall is W12.

`20V124000,20V124000|d52b9de1e3cf206df06c64d2ad46ecec53a642ef2d095cbae3790f3267b3a240|gemini-3.1-flash-lite|f2-v1,,B,`

## 20V315000  (model gemini-3.1-flash-lite, prompt f2-v1)

1. **Nissan is recalling certain vehicles where the secondary hood latch may corrode over time if the primary hood latch is inadvertently released.**
   - cites summary: "Nissan North America, Inc. (Nissan) is recalling certain model year 2013-2018 Nissan Altima vehicles. If the primary hood latch is inadvertently released, there is an increased likelihood that the secondary hood latch may corrode over time."
2. **Corrosion may cause the secondary latch to bind, and the hood could unexpectedly open while driving, increasing the risk of a vehicle crash.**
   - cites consequence: "Corrosion to the secondary latch may cause it to bind and remain in the unlatched position when the hood is closed. If the primary latch is inadvertently released again and the secondary latch is not engaged, the hood could unexpectedly open while driving, increasing the risk of a vehicle crash."

Official NHTSA text:
- summary: Nissan North America, Inc. (Nissan) is recalling certain model year 2013-2018 Nissan Altima vehicles.  If the primary hood latch is inadvertently released, there is an increased likelihood that the secondary hood latch may corrode over time.
- consequence: Corrosion to the secondary latch may cause it to bind and remain in the unlatched position when the hood is closed.  If the primary latch is inadvertently released again and the secondary latch is not engaged, the hood could unexpectedly open while driving, increasing the risk of a vehicle crash.
- remedy: Nissan will notify owners, and dealers will install a stronger release spring in the hood release lever, a warning label near the secondary hood latch, and an Owners Manual addendum card with instructions on how to lubricate and maintain the secondary hood latch mechanism, free of charge.  Owner notification letters were mailed June 30, 2021.  Owners may contact Nissan customer service at 1-800-867-7669.  Note: Recall 16V-029 remains open for any unremedied 2013-2015 Altimas and this recall applies to all vehicles covered by 16V-029 even if those repairs have already been performed.

`20V315000,20V315000|9fa6f024b1d2e98f3857e2040a3e0fee9467f42b4520bbe877df4bbd7e31ee88|gemini-3.1-flash-lite|f2-v1,,B,`

## 20V331000  (model gemini-3.1-flash-lite, prompt f2-v1)

1. **Ford is recalling certain vehicles because a component within the door latches may break, which could lead a passenger to believe a door is securely closed when it is not.**
   - cites summary: "Ford Motor Company (Ford) is recalling certain" | "A component within the door latches may break" | "leading the driver or a passenger to believe a door is securely closed when, in fact, it is not."
2. **A door that is not securely latched could open while the vehicle is in motion, increasing the risk of injury to a vehicle occupant.**
   - cites consequence: "A door that is not securely latched could open while the vehicle is in motion, increasing the risk of injury to a vehicle occupant."

Official NHTSA text:
- summary: Ford Motor Company (Ford) is recalling certain 2011-2014 Fiesta, 2013-2014 Fusion, 2015 Mustang, 2013-2015 Escape and C-Max, 2012-2015 Focus, 2014-2016 Transit Connect, 2013-2014 Lincoln MKZ, and 2015 MKC vehicles.  These vehicles were previously recalled and repaired under recalls 15V-246, 16V-643 or 17V-210, however the repair may not have been completed properly.  A component within the door latches may break making the doors difficult to latch and/or leading the driver or a passenger to believe a door is securely closed when, in fact, it is not.
- consequence: A door that is not securely latched could open while the vehicle is in motion, increasing the risk of injury to a vehicle occupant.
- remedy: Ford will notify owners, and dealers will inspect the latch date codes to confirm if the repair was done correctly, and replace the side door latches if necessary, free of charge.  Owners will also have the option to inspect their own vehicle's door latches and enter the date codes into a website to determine if the latches are correct.  Owner notification letters were mailed on July 27, 2020.  Owners may contact Ford customer service at 1-866-436-7332.  Ford's number for this recall is 20S30.

`20V331000,20V331000|f94a6e0ecbd0a0290efafb082e4433612714a7dfd38d4ed111c3cc67a5bee299|gemini-3.1-flash-lite|f2-v1,,B,`

## 20V519000  (model gemini-3.1-flash-lite, prompt f2-v1)

1. **Kia is recalling certain vehicles because brake fluid may leak inside the Hydraulic Electronic Control Unit (HECU), possibly resulting in an electrical short.**
   - cites summary: "certain 2013-2015 Optima and 2014-2015 Sorento vehicles" | "Brake fluid may leak inside the Hydraulic Electronic Control Unit (HECU), possibly resulting in an electrical short"
2. **If the HECU short circuits, there is an increased risk of an engine compartment fire.**
   - cites consequence: "If the HECU short circuits, there is an increased risk of an engine compartment fire."

Official NHTSA text:
- summary: Kia Motors America (Kia) is recalling certain 2013-2015 Optima and 2014-2015 Sorento vehicles.  Brake fluid may leak inside the Hydraulic Electronic Control Unit (HECU), possibly resulting in an electrical short.
- consequence: If the HECU short circuits, there is an increased risk of an engine compartment fire.
- remedy: Kia will notify owners, and dealers will inspect the HECU for leaking brake fluid and replace the HECU if necessary, free of charge. Owners are advised to park outside and away from other vehicles and structures until the recall repair is completed.  The recall began October 20, 2020.  Owners may contact Kia customer service at 1-800-333-4542.  Kia's number for this recall is SC197.

`20V519000,20V519000|fcd21ddabbf06b2a34ab00b6a755abc20fab5be5569d9d145bedf790fb7f7b64|gemini-3.1-flash-lite|f2-v1,,B,`

## 20V520000  (model gemini-3.1-flash-lite, prompt f2-v1)

1. **Hyundai is recalling certain 2013-2015 Santa Fe Sport vehicles because brake fluid may leak inside the ABS module, potentially causing an electrical short.**
   - cites summary: "Hyundai Motor America (Hyundai) is recalling certain 2013-2015 Santa Fe Sport vehicles. Brake fluid may leak inside the Anti-lock Brake System (ABS) module, possibly resulting in an electrical short."
2. **If the ABS module short circuits, there is an increased risk of an engine compartment fire.**
   - cites consequence: "If the ABS module short circuits, there is an increased risk of an engine compartment fire."

Official NHTSA text:
- summary: Hyundai Motor America (Hyundai) is recalling certain 2013-2015 Santa Fe Sport vehicles.  Brake fluid may leak inside the Anti-lock Brake System (ABS) module, possibly resulting in an electrical short.
- consequence: If the ABS module short circuits, there is an increased risk of an engine compartment fire.
- remedy: Hyundai will notify owners, and dealers will inspect the ABS module and replace it if necessary, free of charge.  Owners are advised to park outside as a precaution until the recall repair is complete.  The recall began December 22, 2020.  Note: This recall has been superseded by NHTSA Recall 21V-303 and all affected vehicles will now be repaired under 21V-303.  Owners may contact Hyundai customer service at 1-855-371-9460.  Hyundai's number for this recall is 194.

`20V520000,20V520000|b01f1dc69e15332809af1acceebc6bb4562c2ae664e9b9b68b9a6be6bb41318f|gemini-3.1-flash-lite|f2-v1,,B,`

## 20V750000  (model gemini-3.1-flash-lite, prompt f2-v1)

1. **Kia is recalling certain vehicles because an engine compartment fire may occur while driving.**
   - cites summary: "Kia Motors America (Kia) is recalling certain" | "An engine compartment fire can occur while driving."
2. **An engine compartment fire increases the risk of injury.**
   - cites consequence: "An engine compartment fire increases the risk of injury."

Official NHTSA text:
- summary: Kia Motors America (Kia) is recalling certain 2012-2013 Sorento, 2012-2015 Forte and Forte Koup, 2011-2013 Optima Hybrid, 2014-2015 Soul, and 2012 Sportage vehicles.  An engine compartment fire can occur while driving.
- consequence: An engine compartment fire increases the risk of injury.
- remedy: Kia will notify owners, and dealers will inspect the engine compartment for fuel and/or engine oil leaks, perform an engine test and make any repairs, including engine replacement, as necessary, free of charge.  In addition, Kia dealers will update the Knock Sensor Detection System (KSDS) software, free of charge.  The recall began January 27, 2021.  Owners may contact Kia customer service at 1-800-333-4542.  Kia's number for this recall is SC200.

`20V750000,20V750000|9776e3dc1f81c6b7d3ce73e32940e8f6b8d0f9f4106deb643fc11fb39b36694d|gemini-3.1-flash-lite|f2-v1,,B,`

## 21V028000  (model gemini-3.1-flash-lite, prompt f2-v1)

1. **Certain Jeep Wrangler and Gladiator vehicles equipped with manual transmissions have a clutch pressure plate that may overheat and fracture.**
   - cites summary: "certain 2018-2021 Jeep Wrangler and 2020-2021 Jeep Gladiator vehicles equipped with manual transmissions" | "clutch pressure plate may overheat and fracture"
2. **Overheated clutch components may increase the risk of a fire, debris falling onto the road, or a loss of drive.**
   - cites consequence: "Overheated clutch components may increase the risk of a fire" | "debris falling onto the road or a loss of drive"

Official NHTSA text:
- summary: Chrysler (FCA US, LLC) is recalling certain 2018-2021 Jeep Wrangler and 2020-2021 Jeep Gladiator vehicles equipped with manual transmissions.  The clutch pressure plate may overheat and fracture.
- consequence: Overheated clutch components may increase the risk of a fire.  Additionally, damage to other nearby components can result in debris falling onto the road or a loss of drive, increasing the risk of a crash.
- remedy: FCA US LLC will notify owners, and dealers will add software to reduce engine torque capability when clutch assembly temperatures rise to a level that may damage the inner pressure plate, free of charge."  FCA has ordered a stop sale for the affected vehicles as of February 25, 2021.  Owner notification letters were mailed on March 4, 2021.

`21V028000,21V028000|03018c917e34ac273a62cb108ede4fdf932cc5921e8edf96f33ad30f91421aaf|gemini-3.1-flash-lite|f2-v1,,B,`

## 21V158000  (model gemini-3.1-flash-lite, prompt f2-v1)

1. **Ford is recalling certain vehicles because the driver's side air bag inflator may explode.**
   - cites summary: "Ford Motor Company (Ford) is recalling certain" | "The driver's side air bag inflator may explode"
2. **An inflator explosion may result in sharp metal fragments striking occupants.**
   - cites consequence: "An inflator explosion may result in sharp metal fragments striking the driver or other occupants"

Official NHTSA text:
- summary: Ford Motor Company (Ford) is recalling certain 2007-2011 Ranger, 2006-2012 Fusion, Lincoln Zephyr, Lincoln MKZ, 2006-2011 Mercury Milan, 2007-2010 Ford Edge, and Lincoln MKX vehicles.  The driver's side air bag inflator may explode due to propellant degradation occurring after long-term exposure to high absolute humidity, high temperatures, and high temperature cycling.
- consequence: An inflator explosion may result in sharp metal fragments striking the driver or other occupants, resulting in serious injury or death.
- remedy: Ford will notify owners, and dealers will replace the driver-side airbag inflator or module with an alternate one, free of charge.  Owner notification letters were mailed on April 9, 2021 for the passenger side, and November 14, 2022 for the driver side.  Owners may contact Ford customer service at 1-866-436-7332.  Ford's number for this recall is 21S12.

`21V158000,21V158000|e1edb4e7b12cec8b58171afc10f249c1199e4ed7e49a47f50dd6d58b7af0a497|gemini-3.1-flash-lite|f2-v1,,B,`

## 21V245000  (model gemini-3.1-flash-lite, prompt f2-v1)

1. **General Motors is recalling certain Chevrolet and GMC vehicles that may have received an incorrect replacement tensioner cable assembly.**
   - cites summary: "General Motors, LLC (GM) is recalling certain 2014-2016 Chevrolet Silverado 1500, 2015-2016 Chevrolet Tahoe, and 2014-2015 GMC Sierra 1500 vehicles that may have received an incorrect replacement tensioner cable assembly"
2. **A broken pretensioner cable reduces the effectiveness of the driver's seat belt, increasing the risk of injury.**
   - cites consequence: "A broken pretensioner cable reduces the effectiveness of the driver's seat belt, increasing the risk of injury."

Official NHTSA text:
- summary: General Motors, LLC (GM) is recalling certain 2014-2016 Chevrolet Silverado 1500, 2015-2016 Chevrolet Tahoe, and 2014-2015 GMC Sierra 1500 vehicles that may have received an incorrect replacement tensioner cable assembly as part of a previous recall remedy or a subsequent repair.  The flexible steel cable connecting the driver's seat belt to the outboard side of the seat may be repeatedly bent over the seat side shield as the driver enters and exits the vehicle causing the cable to fatigue and separate.
- consequence: A broken pretensioner cable reduces the effectiveness of the driver's seat belt, increasing the risk of injury.
- remedy: GM will notify owners, and dealers will replace the driver seat belt lap pretensioner, free of charge.  The recall began on May 5, 2021.  Owners may contact Chevrolet customer service at 1-800-222-1020, and GMC customer service at 1-800-462-8782.  GM's number for this recall is N212330040.

`21V245000,21V245000|0c97ec24a2b77b4b06045ea3595a7459c2cc5d6eb1c88410a7d566cce81e68ff|gemini-3.1-flash-lite|f2-v1,,B,`

## 21V303000  (model gemini-3.1-flash-lite, prompt f2-v1)

1. **Hyundai is recalling certain 2013-2015 Santa Fe Sport vehicles because brake fluid may leak inside the ABS module, potentially causing an electrical short.**
   - cites summary: "Hyundai Motor America (Hyundai) is recalling certain 2013-2015 Santa Fe Sport vehicles. Brake fluid may leak inside the Anti-lock Brake System (ABS) module, possibly resulting in an electrical short."
2. **An electrical short in the ABS module can increase the risk of an engine compartment fire while parked or driving.**
   - cites consequence: "An electrical short in the ABS module can increase the risk of an engine compartment fire while parked or driving."

Official NHTSA text:
- summary: Hyundai Motor America (Hyundai) is recalling certain 2013-2015 Santa Fe Sport vehicles.  Brake fluid may leak inside the Anti-lock Brake System (ABS) module, possibly resulting in an electrical short.
- consequence: An electrical short in the ABS module can increase the risk of an engine compartment fire while parked or driving.
- remedy: Owners are advised to park outside and away from structures as a precaution until the recall repair is complete.  Dealers will replace the ABS multi-fuse, and inspect and replace the ABS module, as necessary, free of charge.  Owner notification letters were mailed on August 25, 2021.  Note: This recall includes all vehicles previously recalled under NHTSA recall number 20V-520.  Owners may contact Hyundai customer service at 1-855-371-9460.  Hyundai's number for this recall is 205.

`21V303000,21V303000|ee5fd45eb0047b6ff254bbb8bdc40c1b60887eca260a35861cce5dac855a5ea9|gemini-3.1-flash-lite|f2-v1,,B,`

## 22V406000  (model gemini-3.1-flash-lite, prompt f2-v1)

1. **Chrysler is recalling certain Jeep Grand Cherokee and Ram 1500 vehicles equipped with 3.0L diesel engines because a high pressure fuel pump failure may introduce debris into the fuel system.**
   - cites summary: "Chrysler (FCA US, LLC) is recalling certain 2014-2020 Jeep Grand Cherokee, and 2014-2019 Ram 1500 vehicles equipped with 3.0L diesel engines. A high pressure fuel pump (HPFP) failure may introduce internal debris into the fuel system"
2. **Fuel starvation may result in an unexpected loss of drive power, increasing the risk of a crash.**
   - cites consequence: "Fuel starvation may result in an unexpected loss of drive power, increasing the risk of a crash."

Official NHTSA text:
- summary: Chrysler (FCA US, LLC) is recalling certain 2014-2020 Jeep Grand Cherokee, and 2014-2019 Ram 1500 vehicles equipped with 3.0L diesel engines.  A high pressure fuel pump (HPFP) failure may introduce internal debris into the fuel system, potentially resulting in fuel starvation.
- consequence: Fuel starvation may result in an unexpected loss of drive power, increasing the risk of a crash.
- remedy: Dealers will replace the HPFP, and inspect and replace, if necessary, additional fuel system components, free of charge.  Interim notification letters informing owners of the safety risk were mailed July 21, 2022.  Owner notification letters for were mailed for Jeep Grand Cherokee owners starting January 11, 2024.  Owner notification letters for Ram 1500 owners were mailed March 7, 2024.  Owners may contact FCA US, LLC customer service at 1-800-853-1403.  FCA US, LLS's number for this recall is Z46.

`22V406000,22V406000|59a4d819f173031565f20e66dcb89a2352a38a744c51869d2a99b236e5eddd87|gemini-3.1-flash-lite|f2-v1,,B,`

## 23V116000  (model gemini-3.1-flash-lite, prompt f2-v1)

1. **Chrysler is recalling certain Jeep Wrangler and Jeep Gladiator vehicles equipped with manual transmissions because the clutch pressure plate may overheat and fracture.**
   - cites summary: "Chrysler (FCA US, LLC) is recalling certain 2018-2023 Jeep Wrangler, and 2020-2023 Jeep Gladiator vehicles equipped with manual transmissions. The clutch pressure plate may overheat and fracture."
2. **Overheated clutch components may increase the risk of a fire, and damage to other components can result in debris on the road or a loss of drive.**
   - cites consequence: "Overheated clutch components may increase the risk of a fire. Additionally, damage to other nearby components can result in debris falling onto the road or a loss of drive"

Official NHTSA text:
- summary: Chrysler (FCA US, LLC) is recalling certain 2018-2023 Jeep Wrangler, and 2020-2023 Jeep Gladiator vehicles equipped with manual transmissions.  The clutch pressure plate may overheat and fracture.
- consequence: Overheated clutch components may increase the risk of a fire.  Additionally, damage to other nearby components can result in debris falling onto the road or a loss of drive, increasing the risk of a crash.
- remedy: Dealers will replace the clutch assembly and update the software, free of charge.  Owner notification letters were mailed from November 16, 2023 through July 25, 2024.  Owners may contact (FCA US, LLC) customer service at 1-800-853-1403.  FCA US LLC's number for this recall is 19A.  This recall expands and replaces previous recall 21V-028.  Vehicles previously repaired under recall 21V-028 will need to have the new remedy completed.

`23V116000,23V116000|b8f03495651eb9b85ea96ccf9dffbd674e19a1292dfc4993b7c809e2b3a87d78|gemini-3.1-flash-lite|f2-v1,,B,`

## 23V652000  (model gemini-3.1-flash-lite, prompt f2-v1)

1. **Kia America, Inc. is recalling certain vehicles because the Hydraulic Electronic Control Unit may experience an electrical short, which can result in an engine compartment fire while parked or driving.**
   - cites summary: "Kia America, Inc. (Kia) is recalling certain" | "Hydraulic Electronic Control Unit (HECU) may experience an electrical short, which can result in an engine compartment fire while parked or driving."
2. **An engine compartment fire while parked or driving can increase the risk of injury.**
   - cites consequence: "An engine compartment fire while parked or driving can increase the risk of injury."

Official NHTSA text:
- summary: Kia America, Inc. (Kia) is recalling certain 2010-2019 Borrego, 2014-2016 Cadenza, 2010-2013 Forte, Forte Koup, Sportage, 2015-2018 K900, 2011-2015 Optima, 2011-2013 Optima Hybrid, Soul, 2012-2017 Rio, 2011-2014 Sorento, and 2010-2011 Rondo vehicles.  The Hydraulic Electronic Control Unit (HECU) may experience an electrical short, which can result in an engine compartment fire while parked or driving.
- consequence: An engine compartment fire while parked or driving can increase the risk of injury.
- remedy: Owners are advised to park outside and away from structures until the recall repair is complete.  Dealers will replace the HECU fuse, free of charge.  Interim notification letters, notifying owners of the safety risk, were mailed November 14, 2023.  Owner notification letters were mailed March 29, 2024 through June 18, 2024.  Owners may contact Kia customer service at 1-800-333-4542.  Kia's number for this recall is SC284.

`23V652000,23V652000|f5fb5baa656fae87e85e6bba6e5596b49962dd7aac2a302d8a795e8c6bbe8db9|gemini-3.1-flash-lite|f2-v1,,B,`

## 24V652000  (model gemini-3.1-flash-lite, prompt f2-v1)

1. **Certain Jeep Gladiator and Wrangler vehicles may experience an internal short circuit that causes the instrument panel cluster to fail.**
   - cites summary: "certain 2020-2024 Jeep Gladiator and 2018-2024 Jeep Wrangler vehicles" | "The instrument panel cluster may experience an internal short circuit and fail"
2. **An instrument panel that fails to display critical safety information can increase the risk of a crash.**
   - cites consequence: "An instrument panel that fails to display critical safety information, such as the speedometer or warning lights, can increase the risk of a crash."

Official NHTSA text:
- summary: Chrysler (FCA US, LLC) is recalling certain 2020-2024 Jeep Gladiator and 2018-2024 Jeep Wrangler vehicles.  The instrument panel cluster may experience an internal short circuit and fail.  As such, these vehicles fail to comply with the requirements of Federal Motor Vehicle Safety Standard number 101, "Controls and Displays."
- consequence: An instrument panel that fails to display critical safety information, such as the speedometer or warning lights, can increase the risk of a crash.
- remedy: Dealers will replace the instrument panel cluster, free of charge.  Owner notification letters were mailed between October 3, 2024, and January 23, 2025.  Owners may contact FCA customer service at 1-800-853-1403.  FCA's number for this recall is 30B.

`24V652000,24V652000|d4be76af1078b82d5ec556d7f1b9ab3df992652fb7f51c96f22e677f6485506f|gemini-3.1-flash-lite|f2-v1,,B,`

## 26V369000  (model gemini-3.1-flash-lite, prompt f2-v1)

1. **Ford is recalling certain Focus vehicles because the Canister Purge Valve may malfunction, causing the engine to stall unexpectedly while driving.**
   - cites summary: "Ford Motor Company (Ford) is recalling certain 2012-2018 Focus vehicles" | "The Canister Purge Valve (CPV) may malfunction, causing the engine to stall unexpectedly while driving."
2. **An engine that stalls while driving increases the risk of a crash.**
   - cites consequence: "An engine that stalls while driving increases the risk of a crash."

Official NHTSA text:
- summary: Ford Motor Company (Ford) is recalling certain 2012-2018 Focus vehicles previously repaired incorrectly under recall number 18V735. The Canister Purge Valve (CPV) may malfunction, causing the engine to stall unexpectedly while driving.
- consequence: An engine that stalls while driving increases the risk of a crash.
- remedy: Dealers will update the powertrain control module (PCM) software, free of charge. Owner notification letters were mailed July 29, 2026. Owners may contact Ford customer service at 1-866-436-7332. Ford's number for this recall is 26S40. Vehicle Identification Numbers (VINs) involved in this recall will become searchable on NHTSA.gov on July 6,2026.

`26V369000,26V369000|bf6635265df079acf33fd7a275aae20cb72b22b1d40a9a267c726e5ec049e5f5|gemini-3.1-flash-lite|f2-v1,,B,`


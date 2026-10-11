<!-- Owner: D. Reviewer: C. Paste everything below this comment into Devpost's "About the project".
Numbers are period.metric placeholders in square brackets, filled ONLY by `make submission` from
exports/demo/results.csv into submission/out/DEVPOST.md. Paste from out/, never from this template. -->

## Inspiration
Every complaint a driver files with NHTSA ends up in a public file. There are millions of them. When something starts going wrong with a particular model, the first signs are often already in there: people describing the same stall, the same warning light, the same noise, long before anything official happens.

The files aren't made to be read that way. You get one row per complaint and no sense of whether a problem is growing. We wanted to answer two things. Could a simple detector, using only what was public at each point in time, have pointed at those patterns before NHTSA opened an investigation? And could we make the same records easy to read for someone looking at a used car or trying to make sense of a recall?

## What it does
Pick a year, make and model, or decode a VIN, and Recall Radar shows that vehicle's complaint history by component and month, its recall campaigns with NHTSA's official text, and the investigations NHTSA opened.

For each component, it compares the last two months of complaints with that vehicle's own history and flags a pattern when the count is well above what the history predicts. The replay page walks through one case month by month. The detector only sees complaints that were public by each date (we count a complaint as public seven days after NHTSA received it), and the investigation shows up afterwards as a reveal.

The results page answers our first question, and the answer is no. On the held-out year, which we ran once after freezing every setting, the detector raised an early alert for [held_out.early_coverage_all.numerator] of the [held_out.early_coverage_all.denominator] eligible investigations. For comparison we used up to five similar vehicles per case that NHTSA never investigated for that component: same component, model year within two years, a different model, similar complaint volume beforehand. Those reached [held_out.chance_coverage]. On the development years we used to choose the settings, the detector came out level with chance ([development.early_coverage_all] against [development.chance_coverage]). We set the bar before running the held-out year and report the result as it came out.

An alert means a pattern is worth a closer look. It doesn't mean a car has a defect or that a recall is coming, and NHTSA staff see data we don't.

The app also has:
- Recall cards with NHTSA's official text. For a set of campaigns a teammate reviewed by hand, there is also a plain-language explanation written by Google Gemini, with each sentence tied to the official words it came from.
- Symptom search, so you can type something like "grinding when braking" and find the matching complaint groups.
- Check by VIN. Your browser sends the VIN to NHTSA's vPIC decoder and it never reaches our server. For a specific car's open recalls we link to NHTSA's own lookup, because there is no authorized public interface we could use for that.
- Report a problem. You draft the complaint on the page, copy it, and finish on NHTSA's form. We don't send anything.
- A one-page used-car summary that prints on a single page, and "Remember this car", which stays in your browser.

Two more pieces went in after our feature freeze, so we label them that way. One is a 3D presentation page at recall-radar.us/observatory. The other is an iMessage assistant through Photon. You can text it "what problems are reported for the 2019 Jetta?" or "any recalls on it?" Gemini works out what you're asking and which vehicle you mean, our code looks up the answer, and a reply only goes out if every number and link in it matches our data. It won't diagnose a car or say whether it's safe to drive. If you WATCH a vehicle, it sends at most one update a day when NHTSA publishes new complaints or recalls for it, and STOP and DELETE work at any time. Since it came in after the freeze, we only switch it on for supervised tests and don't count it as shipped.

## How we built it
We were four people, each working with a Claude Code agent: one on data and the API, one on detection and evaluation, one on the website, and one on integration and deployment. Before writing code we wrote the spec: what each feature had to do and how we would check it, the API contracts all four parts share (Pydantic models turned into JSON Schema and TypeScript types), and who owns which folders. Every change went through a pull request that needed green CI and a second teammate's review on that exact commit. Releases went through gates that re-ran the checks against the live site.

The pipeline is Python and DuckDB. It drops personal fields when it reads NHTSA's files, redacts complaint text, and counts each complaint once even when it lists several components. The detector is a Poisson test written with SciPy. FastAPI serves precomputed results, so browsing the site triggers no outside calls, and the whole app also runs offline on a laptop. The website is React, Vite and TypeScript, with visx and D3 for the charts and Motion for animation. The 3D page is Next.js with three.js, React Three Fiber and GSAP. Everything runs on one Vultr VM behind Caddy. The iMessage assistant is a separate service with its own off switch: Photon Spectrum delivers messages to a signed webhook, a small Node service sends the replies, and Gemini handles the language.

## Challenges we ran into
NHTSA's "added to file" date turned out to equal the received date for nearly every complaint, so it couldn't tell us when a record really became public. We count each complaint as public seven days after NHTSA received it, and every screen that depends on this says "received-date experiment".

It is easy to keep adjusting a detector until the chart looks good. We tuned only on the development years, froze the settings under a git tag, and ran the held-out year once.

In our first live iMessage test, only the first message got an answer. The webhook's ID header was the same on every delivery, so our duplicate check threw away everything after the first message. We switched to the message's own ID.

Some small bugs had big effects. Model names with digits, like F-150 or CX-5, made the number check reject every answer about those cars. A new page-transition animation pushed the printable one-page report onto a second page. A teammate's review found that DELETE left one row that still held the person's handle. We found each of these by testing against real data or through review, and each one has a test now.

## Accomplishments that we're proud of
- We published a negative result as it came out, with the bar and the settings fixed before we looked.
- A clean clone at the tag `baseline-v1` rebuilds the published result files byte for byte.
- Every result number in the app and in this write-up comes from one file, `exports/demo/results.csv`.
- The site needs no account and does no tracking, and a VIN goes from your browser straight to NHTSA, never to us.

## What we learned
Writing the spec first and making every claim checkable slowed down our first hour and saved the rest of the night. Review by a second person mattered more than we expected. One fix passed its unit tests, but when a teammate ran it against real questions for a few hundred vehicles it broke a large share of the chat answers, so we left it out.

## What's next for Recall Radar
- Test the detector at the level of NHTSA's engineering analyses, with a new freeze and a new held-out year. Most held-out investigation families were excluded ([held_out.excluded_families.numerator] of [held_out.excluded_families.denominator]), and most of those trace back to one large engineering analysis.
- Show a specific car's recall status by VIN once there is an authorized source for it.
- Finish an independent review of the iMessage assistant and then open it to everyone.

## Try it
- Live app: https://recall-radar.us
- 3D presentation: https://recall-radar.us/observatory
- Code: https://github.com/adrit-ganeriwala-05/recall-radar. The README explains how to run it, and `make serve` runs it offline.
- No login or test account is needed.

## AI use and pre-event work
Nothing we built existed before the event. We wrote the code and the documents with Claude through Claude Code during the event, and every change is in the public git history. Inside the product, Google Gemini writes the reviewed recall explanations and plans and rewords iMessage replies. The data is NHTSA's public complaint, investigation and recall files.
The car on the 3D page is "Car Concept" by Eric Chadwick (© Darmstadt Graphics Group GmbH) from the Khronos glTF Sample Assets, used under CC BY 4.0 with the licence plate and Khronos logo removed. <!-- numbers-ok -->

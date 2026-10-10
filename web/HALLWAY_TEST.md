# Hallway test (C8) — owner: C

Two people **outside the team**, one at a time, on the deployed real-data build (not fixtures). About 5 minutes
each. Goal from the C launch prompt: *find a vehicle and explain an alert in 60 seconds.*

## Setup
- Open the deployed URL on a laptop, landing page, window maximized. No one from the team touches the mouse.
- Have a stopwatch and this sheet. Write down what they *say*, not what you think they meant.

## Script (read aloud, word for word)
1. "This site looks at public car-complaint data. Please find the **<hero make> <hero model> <hero year>**."
   Start the stopwatch.
2. When they reach the vehicle page: "Is there anything here that deserves a closer look? Tell me what it is."
3. When they have answered (or after 60 s): "What does that alert mean, in your own words?"
4. "Does this tell you whether **your** car of this model has a problem? How would you check?"
5. "Open the results page. In one sentence, how well does the method work?"

## Record
| Check | Person 1 | Person 2 |
| --- | --- | --- |
| Reached the vehicle page (seconds) | | |
| Found an alert / issue page (seconds) | | |
| Explained the alert within 60 s from start (yes/no) | | |
| Said or implied "defective", "dangerous", "will be recalled" (yes/no — a yes is a copy bug) | | |
| Understood campaigns are model-level and pointed to the VIN lookup (yes/no) | | |
| Read the results as a comparison with chance, not as a promise (yes/no) | | |
| Where they hesitated or clicked the wrong thing | | |
| Exact words that confused them | | |

## After
- Fix every "no" and every repeated hesitation before feature freeze (1:00 AM); log fixes in `docs/status/C.md`.
- Never fix by adding a performance number to copy; numbers come only from exports.

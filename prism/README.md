# The ladder as a Prism prompt

`dharma-ladder.prompt.json` states the town's ladder (`Ladder` in
`dharma_nanda.py`) as a decision table in the format of Prism Creator
(`afflom/prism-devrel`, a `prism/prompt/1` prompt). From this one file the
Prism builder can generate an application whose rules are proved in Lean.

What it says: from the strikes a seller or relay holds and one event (a good
delivery, a bad one, an injection, or a council pardon of either), whether it
is trading or suspended afterwards, under the starting rule that 3 strikes
suspend.

Five properties it claims can never happen:

- a first or second plain mistake suspends;
- one injection from a clean record suspends;
- good work lifts a suspension;
- good work suspends;
- a pardon of the delivery that took a seller to exactly 3 strikes leaves it
  suspended.

Status, 18 November 2026:

- The prompt passes the Prism builder's own check (`cli.mjs check`): 42
  acceptance cases generated, the five properties accepted.
- `test_dharma.py` checks the table and the properties against the real
  `Ladder` for every event and 0 to 59 strikes.
- **Not done:** the application has not been generated or published, and
  nothing has been proved in Lean yet.

Limits of the table: the limit of 3 is fixed, though the council can change
it in the town. Strikes can keep rising after a suspension (deliveries
already under way, and a relay that is the only route), so one pardon does
not always lift a suspension; the table covers that, which is why it counts
strikes instead of naming a fixed set of standings.

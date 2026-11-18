# The demo

Five steps, one screen each. The demo towns use sums you can do in your head
(two lines of small round numbers). Steps 1 to 4 take about five minutes;
step 5 adds about three.

A person is in the loop at three levels:

| Level | What the person does | Step |
| --- | --- | --- |
| Cases | Decides a delivery the judges could not settle | 3 |
| Rules | Votes, as a council member, on changing a rule | 5 |
| Second looks | Reviews strikes given before the rule changed | 5 |

Every one of those decisions is a record with parents, like the agents'.

## Before you present

From the `dharma-nanda` folder, with the virtual environment from the README:

```
git pull
python demo.py attack
```

The second command is only a check that everything runs. Make the terminal
font large and the window wide (about 110 columns).

## Step 1: same data, different bytes (1 minute)

```
python demo.py bytes
```

One delivery record three ways: as published, re-encoded by a gateway, and
with its answer changed. Under NandaTown's fingerprint the re-encoded record
gets a new identity, so it cannot be told from a tampered one. Under the
canonical record it keeps its identity, and only the changed one differs.

What that does to a market, over 20 seeds (from `RESULTS.md`): with the
fingerprint, an honest relay that only re-encodes is suspended as a tamperer
in every run, and if it is the only route the market delivers nothing. With
canonical records nothing is lost, and a relay that really changes answers is
caught before any changed delivery reaches a judge.

Identity says what a record contains, not who wrote it. A relay that
publishes its changed record under the seller's name passes the identity
check; the seller's signature stops it. And the signature has to be over the
canonical identity: over the bytes, it breaks on re-encoding like the
fingerprint does.

## Step 2: what the blue team alone does (1 minute)

```
python demo.py attack
```

The blue team (three judges a job, planted test jobs, three strikes and out)
removes every red-team seller. But two of the five judges are dishonest and
flag two honest sellers' work as manipulation, and the same rule removes
them: 3 of 6 honest sellers end up suspended.

## Step 3: a person in the watchtower (1 to 2 minutes)

```
python demo.py seat
```

The same town, but flagged deliveries and split panels go to a person. You
decide the first three cases. Add up the invoice: if the answer is right,
type `a`, whatever the judges claimed. If it is wrong, read the note: `i` if
it tells the judges what to do, otherwise `r`.

| Case | What it is | Right choice |
| --- | --- | --- |
| 1 | Answer 700; the sum is 600. The note tells the judges to accept. | `i` |
| 2 | Answer 2,400, which is right. No note. Two judges flagged it. | `a` |
| 3 | Answer 0, with a thank-you note. Junk. | `r` |

The other six cases are decided by the stand-in policy, or by a person's
saved answers if `demo/decisions-watch-seed7.jsonl` exists. It ends with the
comparison: 3 of 6 honest sellers suspended with the blue team alone, 0 of 6
with the watchtower.

## Step 4: trace the decision (1 minute)

```
python demo.py trace
```

Works after step 3 or step 5, on whichever was run last. Takes the first
case where the person paid a seller the judges had flagged, and
prints the settlement with every record it rests on: the person's decision,
the escalation, the three verdicts including the two false flags, the
delivery, the job, and the rule in force. Then it recomputes every record of
the run and checks every parent link.

Anyone can replay the run without that person and get the same events:

```
python verify.py demo-runs/demo_watch/demo_watch/seed-7
```

## Step 5: a person on the council too (about 3 minutes)

```
python demo.py council
```

This town starts with the blue team's rule: a delivery most judges flag is
refused with two strikes, and no person sees it. You sit in the watchtower
and on the council. Nine prompts, in this order if you answer as shown:

| Prompt | What it is | Right choice |
| --- | --- | --- |
| Case 1 | Answer 0. Junk. | `r` |
| Case 2 | Answer 0. Junk. | `r` |
| Council vote | The chair has found two deliveries refused on flags though all three judges accepted the answer, and proposes sending flagged deliveries to the watchtower. | `y` |
| Case 3 | Second look: answer 1,200, which is right. | `a` |
| Case 4 | Second look: answer 1,200, which is right. | `a` |
| Case 5 | Answer 0. Junk. | `r` |
| Case 6 | Answer 1,100, which is right. Flagged by two judges. | `a` |
| Case 7 | Answer 3,200; the sum is 2,300. No note. | `r` |
| Case 8 | Answer 1,200, which is right. Flagged by two judges. | `a` |

It ends with the comparison (3 of 6 honest sellers suspended with the blue
team alone, 1 of 6 here, two strikes taken back) and the new rule traced to
the proposal, the earlier rule and the three ballots, yours marked
`"by": "person"`.

## Optional: watch the town (1 minute)

```
python demo.py show
```

Opens the run you just decided in NandaTown's own visualizer: the agents on
a map, messages moving between them as the timeline plays, the event log,
and the verdict with this project's checks (`records_recompute`,
`records_signed`, `lineage_resolves`) alongside NandaTown's. Press Play.

## If something goes wrong

- A wrong letter is not fatal: the run continues, later cases may differ
  from the tables above, and the summary shows what it cost.
- Every step can simply be run again.

## A timed run

`demo/decisions-seed3.jsonl` holds the 13 answers a person gave to a whole
run of the `watch_flags` town with the harder three-line sums: 13 of 13
right, 34 seconds a case at the median, about seven minutes in all.
Replay it with:

```
python run.py --only watch_flags --seeds 3 --watch replay --decisions demo/decisions-seed3.jsonl
```

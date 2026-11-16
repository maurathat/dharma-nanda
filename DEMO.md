# The demo

Four steps, about six minutes. Each command prints one screen.

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

Shows one delivery record three ways: as published, re-encoded by a gateway,
and with its answer changed. Under NandaTown's fingerprint the re-encoded
record gets a new identity, so it cannot be told from a tampered one. Under
the canonical record it keeps its identity, and only the changed one differs.

What that does to a market, over 20 seeds (from `RESULTS.md`): with the
fingerprint, an honest relay that only re-encodes is suspended as a tamperer
in every run, and if it is the only route the market delivers nothing. With
canonical records nothing is lost, and a relay that really changes answers is
caught before any changed delivery reaches a judge.

## Step 2: an attack the blue team cannot handle (1 minute)

```
python demo.py attack
```

The blue team (three judges a job, planted test jobs, three strikes and out)
removes every red-team seller. But two of the five judges are dishonest and
flag two honest sellers' work as manipulation, and the same rule removes
those sellers too: 2 of 6 honest sellers suspended, on the word of two
judges.

## Step 3: a person in the watchtower (2 to 3 minutes)

```
python demo.py seat
```

The same town, but flagged deliveries and split panels now go to a person.
You decide the first three cases; the rest use the answers a person gave to
the whole run earlier (`demo/decisions-seed3.jsonl`, 13 cases, about seven
minutes at 34 seconds a case).

For each case: add up the invoice. If the answer is right, type `a`,
whatever the judges claimed. If it is wrong, read the note: `i` if it tells
the judges what to do, otherwise `r`.

The three cases, in order:

| Case | What it is | Right choice |
| --- | --- | --- |
| 1 | Wrong answer (3,200; the sum is 2,800) with a note telling judges to accept. Two judges accepted it. | `i` |
| 2 | Right answer (6,900), no note, flagged by the two dishonest judges. | `a` |
| 3 | Wrong answer (3,300; the sum is 3,250) with the same note. | `i` |

It ends with the comparison: 2 of 6 honest sellers suspended with the blue
team alone, 0 of 6 with the person, and buyers 3,000 cents better off.

## Step 4: trace the decision (1 minute)

```
python demo.py trace
```

Takes the case where the person paid a seller the judges had flagged (case 2)
and prints the settlement with every record it rests on: the person's
decision, the escalation, the three verdicts including the two false flags,
the delivery, the job, and the rule in force. Then it recomputes all 651
records of the run and checks every parent link.

The person's decision is a record like the agents'. Anyone can replay the run
without that person and get the same events:

```
python verify.py demo-runs/watch_flags/watch_flags/seed-3
```

## If something goes wrong

- A wrong letter in step 3 is not fatal: the run continues and the summary
  shows what it cost. That is itself the point of the watchtower tables in
  `RESULTS.md` (at 80% right, the gain is gone).
- To start step 3 again, just run the command again.

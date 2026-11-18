# Dharma Nanda

A market town for [NandaTown](https://github.com/projnanda/nandatown) in which
the four actors of human-agent oversight are all present, and **every action
any of them takes is a canonical record that names the records it was based
on**.

- **Red team:** sellers that cheat, inject instructions into their work,
  behave only when they spot a test, or turn bad together in one round; judges
  that flag honest work or wave bad work through; a relay that changes records
  in transit.
- **Blue team:** a panel of three judges per job, a tester that plants jobs
  with known answers, a strike ladder, and a check of every record on receipt.
- **Watchtower:** a person who decides the cases the agents cannot. You can
  sit in that seat yourself (see below).
- **Council:** a chair and three members who change the town's rules mid-run,
  citing the records that are their evidence.

It is a plugin, not a fork: NandaTown is used unchanged.

A five-step walk-through is in [DEMO.md](DEMO.md). It puts a person in the loop at three levels: deciding cases, voting on a rule, and taking a second look at old strikes.

## Why records

A job, a delivery, a verdict, a person's decision, a ballot and a rule are all
`dataset.v1` records. Each one names its parents, so any outcome can be traced
back to everything it rested on:

```
rule <- job <- delivery <- verdict (x3) <- [escalation <- decision] <- settlement
rule <- proposal (citing settlements) <- ballot (x3) <- rule
```

A record's identity is computed from its canonical structure, not from the
bytes it happened to arrive in. The canonicalizer is `canon.py`, copied
unchanged from
[maurathat/canonical-dataset-lineage](https://github.com/maurathat/canonical-dataset-lineage)
(`artifact/canon.py`, commit `c62f126`) and pinned by SHA-256 in `records.py`.
Nothing here reimplements it; `records.py` refuses to load a copy that has
been edited.

The same town can be run with NandaTown's own fingerprint as the identity
rule instead (`dharma.records.town.v1`). That is the control.

## What it shows so far

Scripted agents, 20 seeds per town, the same cast in every town. Full tables
are in [RESULTS.md](RESULTS.md).

**Records.** Every delivery starts out through one relay. A relay whose
delivery does not verify takes a strike; at three strikes sellers switch to a
second relay.

| Relay | Check on receipt | Value delivered (cents) | Honest sellers suspended (of 6) | Relay suspended |
| --- | --- | ---: | ---: | --- |
| Re-encodes every record (same data, different bytes) | NandaTown fingerprint | 114,800 | 2.7 | The honest relay, every run |
| Re-encodes every record | Canonical record | 115,760 | 2.7 | None |
| Re-encodes every record and is the only route | NandaTown fingerprint | 0 | 0.0 | The honest relay, every run |
| Re-encodes every record and is the only route | Canonical record | 115,760 | 2.7 | None |
| Changes the answer in 30% of deliveries | No check | 54,720 | 6.0 | None |
| Changes the answer in 30% of deliveries | Canonical record | 114,960 | 2.6 | The altering relay, every run |
| Changes the answer and publishes the result in the seller's name | Canonical record | 54,720 | 6.0 | None |
| Changes the answer and publishes the result in the seller's name | Canonical record, seller's signature over the identity | 114,960 | 2.6 | The forging relay, every run |
| Re-encodes every record | Canonical record, seller's signature over the bytes | 114,800 | 2.7 | The honest relay, every run |
| Re-encodes every record | Canonical record, seller's signature over the identity | 115,760 | 2.7 | None |

- A relay that only re-encodes, as any gateway written in another language
  may, is convicted as a tamperer in every run when identity is a
  fingerprint of the parsed JSON. If it is the only route, the market stops:
  every honest delivery is refused as unknown. With canonical records nothing
  is lost and nobody is blamed.
- A relay that changes answers gets every honest seller suspended when
  records are not checked: the judges see the changed answer and the seller
  takes the strike. Checked on receipt, no changed delivery reached a judge,
  the relay was suspended after 3.4 changed deliveries on average, and the
  town delivered what it delivers with an honest relay.
- Even with no check on receipt, an audit afterwards finds the damage: the
  verdicts name a delivery nobody published (57 unresolved parent links per
  run).
- Identity alone does not say who wrote a record. A relay that changes the
  answer and then publishes the changed record under the seller's name
  passes the identity check, every honest seller is suspended, and the
  lineage audit finds nothing wrong. Each author therefore signs with an
  Ed25519 key that the town's registry binds to its name. With the seller's
  signature required, no forged delivery reached a judge.
- What is signed matters. A signature over the bytes fails when an honest
  relay re-encodes the record, and convicts that relay in every run, exactly
  as the fingerprint does. A signature over the canonical identity survives
  re-encoding.

**Oversight.**

| Town | Buyers' net (cents) | Honest sellers suspended (of 6) | Red sellers still trading (of 5) |
| --- | ---: | ---: | ---: |
| Red team, no oversight | −4,000 | 0.0 | 5.0 |
| Blue team | 31,690 | 2.7 ± 0.5 | 0.0 |
| Blue team and watchtower | 31,850 | 2.8 ± 0.5 | 0.0 |
| ... and a slow council (reviews every 4 rounds, acts on 5 cases) | 31,850 | 2.8 ± 0.5 | 0.0 |
| ... and a council (every 2 rounds, 3 cases) | 31,760 | 1.8 ± 0.7 | 0.0 |
| ... and a fast council (every round, 2 cases) | 32,300 | 0.8 ± 0.5 | 0.0 |

- The blue team removes every red seller and turns a loss into a gain, but
  suspends nearly half the honest sellers: two judges who flag honest work
  are enough, and so are an honest seller's own occasional mistakes.
- A watchtower that only sees what the rules send it (split panels) changes
  nothing measurable.
- The council notices from the public records that deliveries are being
  refused on flags alone, sends flags to the watchtower instead, and has the
  earlier strikes looked at again. How soon it acts decides what it is
  worth: a slow council never acts within the run, and a fast one cuts
  wrongly suspended honest sellers from 2.7 to 0.8. Buyers' net barely
  moves, because other honest sellers were filling the gap.

**What the watchtower is sent, and how good and how busy it is.** No
council; the watchtower is a stand-in policy, not a person.

| Sent to the watchtower | Right | Cases a round | Buyers' net (cents) | Good work refused | Honest sellers suspended (of 6) |
| --- | ---: | ---: | ---: | ---: | ---: |
| Nothing (no watchtower) | | | 31,690 | 3.0 | 2.7 |
| Split panels only | 98% | 4 | 31,850 | 3.0 | 2.8 |
| Split panels and flagged deliveries | 98% | 4 | 33,200 | 0.1 | 0.8 |
| Split panels and flagged deliveries | 98% | 1 | 31,690 | 1.4 | 0.7 |
| Split panels and flagged deliveries | 80% | 4 | 31,680 | 1.2 | 1.3 |
| Split panels and flagged deliveries | 60% | 4 | 30,220 | 2.1 | 1.1 |

- What is sent matters most. Sent only split panels, the watchtower changes
  nothing. Sent flagged deliveries too, it nearly ends the refusal of good
  work and cuts wrongly suspended honest sellers from 2.7 to 0.8.
- The gain in buyers' net needs a watchtower that is both accurate and has
  time: at 80% right, or at one case a round, net is back where it was
  without one. Fewer honest sellers are suspended even then.
- None of this says how accurate or how fast a real person is. Sit in the
  seat (`--watch live`): each answer is saved with the seconds it took.

**More red-team pressure.** Each attack is added to the usual red team.
"Watchtower" is sent split panels and flagged deliveries from the start.

| Attack | Oversight | Buyers' net (cents) | Honest sellers suspended (of 6) | Notes |
| --- | --- | ---: | ---: | --- |
| Two judges accept whatever red sellers deliver | Blue team | 23,350 | 0.5 | 7,400 paid for bad work |
| | Watchtower | 32,620 | 0.8 | 650 paid for bad work |
| A buyer rewrites each job until its two judges are on the panel, to get good work refunded | Blue team | 25,468 | 6.0 | 14,560 of work taken without paying |
| | Watchtower | 34,290 | 1.4 | 240 taken |
| | Fast council | 34,140 | 1.9 | 4,240 taken before the rule changed |
| Three of five judges flag every honest seller from round 6 | Blue team | 12,128 | 6.0 | Value falls by more than half |
| | Watchtower | 30,810 | 1.1 | 43 cases a run; 3.8 held for lack of time |
| | Fast council | 28,910 | 1.9 | 39 cases; 3.9 held |

- Each attack breaks the blue team on its own: two of them end with every
  honest seller suspended.
- A watchtower that is sent the flagged and split cases holds against all
  three, at a cost in the person's time: 43 cases a run in the flood,
  against 11 normally, and some go undecided.
- The panel for a job is fixed by the job's identity, which the buyer
  chooses. That is what the grinding buyer exploits; the town does not fix
  it, it only catches the result.

## Limits

- The agents are scripted: fixed chances of a mistake, of catching one, of
  following an injection. The watchtower in the tables is a stand-in policy
  that is right 98% of the time, not a person.
- One small town, one kind of job (totalling an invoice) with one right
  answer.
- The ladder is deliberately plain: strikes only rise, and a mistake counts
  the same as a cheat.
- A relay is struck on any delivery that does not verify, so a relay that
  merely re-encodes is treated as a tamperer under the fingerprint check.
  That is the point of the comparison, not a model of how relays are policed.
- Each record is signed by its author, but the link from a name to a key is
  simply given: the registry holds one key per registered agent from the
  start. How a real registry earns that trust is outside this town. Keys
  come from the scenario seed so that runs repeat; nothing protects them.
- Nothing fixes the order of records or shows that one was withheld. That
  needs an append-only log, which the town does not have.

## Run it

Python 3.11 or later.

```
git clone https://github.com/maurathat/dharma-nanda
git clone https://github.com/projnanda/nandatown
git -C nandatown checkout 6f9a7c064486c4a0ae9242f1ff341b8a4aad0244
python3 -m venv venv
venv/bin/pip install -e nandatown -r dharma-nanda/requirements.txt
cd dharma-nanda
../venv/bin/python -m pytest -q
```

Then, from `dharma-nanda` with the virtual environment active:

| Command | What it does |
| --- | --- |
| `python run.py` | Every town over seeds 1 to 20 (under a minute). Measures go to `runs/`. |
| `python report.py > RESULTS.md` | Rebuild the tables. |
| `python run.py --only council --seeds 1 --watch live` | **Sit in the watchtower.** Each case is shown with the task, the answer, the judges' verdicts and the chain of records behind it. Seller names are hidden. Your answers, and the seconds each took, are saved to `decisions.jsonl`. |
| `python run.py --only council --seeds 1 --watch replay` | Run it again from your saved answers. |
| `python run.py --only watch_flags --seeds 1 --watch live --first 3` | Decide only the first three cases; the stand-in policy takes the rest. |
| `python audit.py runs/council/seed-1` | Recompute every record's identity and classify every parent link. |
| `python audit.py runs/council/seed-1 --why seller-3` | Trace a seller's last strike back to the job, the verdicts, the rule in force, and the ballots and evidence behind that rule. |
| `python verify.py runs/council/seed-1` | NandaTown's own bundle check, then a second run that must give the same events. |
| `python make_scenarios.py` | Rewrite the scenario files. |

`evidence/` holds the seed 1 bundle of seventeen towns; a test checks that every one still verifies. Unpack one and verify it:

```
tar -xzf evidence/council-seed1.tar.gz -C /tmp
python verify.py /tmp/council-seed1
python audit.py /tmp/council-seed1
```

`rec_alter_none` is expected to fail the `lineage_resolves` stage, and the
`rec_forge_*` towns the `records_signed` stage, with the audit failing to
match: those failures are the findings.

## Files

| File | What it is |
| --- | --- |
| `canon.py` | The canonicalizer, unchanged. Do not edit. |
| `records.py` | Builds, stores and audits records; the two identity plugins. |
| `dharma_nanda.py` | The roles, the ladder, and the measures. |
| `make_scenarios.py`, `scenarios/` | The towns. |
| `run.py`, `report.py`, `audit.py`, `verify.py` | Run, tabulate, audit, verify. |
| `test_dharma.py` | Checks to run before and after a change. |
| `demo.py`, `DEMO.md`, `demo/` | The demo, and the answers a person gave to one whole run. |

## Licence

Apache-2.0. `canon.py` is from maurathat/canonical-dataset-lineage under the
same licence.

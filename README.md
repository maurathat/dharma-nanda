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
- Records are not signed. Identity and lineage are checked; who published a
  record rests on the town's own message layer.

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
| `python run.py --only council --seeds 1 --watch live` | **Sit in the watchtower.** Each case is shown with the task, the answer, the judges' verdicts and the chain of records behind it. Your answers are saved to `decisions.jsonl`. |
| `python run.py --only council --seeds 1 --watch replay` | Run it again from your saved answers. |
| `python audit.py runs/council/seed-1` | Recompute every record's identity and classify every parent link. |
| `python audit.py runs/council/seed-1 --why seller-3` | Trace a seller's last strike back to the job, the verdicts, the rule in force, and the ballots and evidence behind that rule. |
| `python verify.py runs/council/seed-1` | NandaTown's own bundle check, then a second run that must give the same events. |
| `python make_scenarios.py` | Rewrite the scenario files. |

`evidence/` holds the seed 1 bundle of nine towns. Unpack one and verify it:

```
tar -xzf evidence/council-seed1.tar.gz -C /tmp
python verify.py /tmp/council-seed1
python audit.py /tmp/council-seed1
```

`rec_alter_none` is expected to fail the `lineage_resolves` stage and the
audit: that failure is the finding.

## Files

| File | What it is |
| --- | --- |
| `canon.py` | The canonicalizer, unchanged. Do not edit. |
| `records.py` | Builds, stores and audits records; the two identity plugins. |
| `dharma_nanda.py` | The roles, the ladder, and the measures. |
| `make_scenarios.py`, `scenarios/` | The towns. |
| `run.py`, `report.py`, `audit.py`, `verify.py` | Run, tabulate, audit, verify. |
| `test_dharma.py` | Checks to run before and after a change. |

## Licence

Apache-2.0. `canon.py` is from maurathat/canonical-dataset-lineage under the
same licence.

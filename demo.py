"""The demo, one step at a time. Each step fits on one screen.

  python demo.py bytes    the same record in different bytes, two identities
  python demo.py attack   the blue team alone, with two dishonest judges
  python demo.py seat     you in the watchtower for the first three cases
  python demo.py trace    one of those decisions, back through its records

`seat` puts the first three cases to you and takes the rest from
demo/decisions-seed3.jsonl, the answers a person gave to the whole run.
"""

import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import records  # noqa: E402

OUT, SEED = os.path.join(HERE, "demo-runs"), "3"
SAVED = os.path.join(HERE, "demo", "decisions-seed3.jsonl")
RULE = "-" * 68


def run(name, *more):
    done = subprocess.run([sys.executable, os.path.join(HERE, "run.py"),
                           "--only", name, "--seeds", SEED, "--keep", SEED,
                           "--out", os.path.join(OUT, name.split(",")[0]), "--quiet",
                           *more], stdout=subprocess.PIPE if not more
                          else None, text=True)
    if done.returncode:
        sys.exit(done.returncode)


def measures(folder, name):
    with open(os.path.join(OUT, folder, name, f"seed-{SEED}.json")) as fh:
        return json.load(fh)


def events(folder, name):
    with open(os.path.join(OUT, folder, name, f"seed-{SEED}",
                           "events.jsonl"), encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if '"dn_' in line]


def line(label, m):
    print(f"  {label:<34} buyers' net {m['net']:>7,} cents   honest sellers"
          f" suspended {len(m['honest_suspended'])} of {m['honest']}")


def bytes_step():
    raw = records.build("Zoë's Ledgers", {
        "kind": "delivery", "answer": 1600, "note": "",
        "signed": "Zoë's Ledgers"}, ["ab" * 32])
    again = records.reencode(raw)
    changed = records.alter(raw, {"answer": 1700})
    print(RULE + "\nA seller's delivery record, as published:\n\n  " + raw)
    print("\nThe same record after a gateway re-encodes it (member order,"
          "\naccents, number form and spacing all differ):\n")
    print("  " + again.replace("\n", "\n  "))
    print("\nAnd with the answer changed from 1600 to 1700 in transit.\n")
    print(f"  {'':<17}{'NandaTown fingerprint':<24}Canonical record"
          " (dataset.v1)")
    for label, text in (("published", raw), ("re-encoded", again),
                        ("answer changed", changed)):
        print(f"  {label:<17}{records.town_id(text)[:16]:<24}"
              f"{records.canonical_id(text)[:16]}")
    print("\nThe fingerprint cannot tell re-encoding from tampering. The"
          "\ncanonical record keeps its identity when re-encoded and loses it"
          "\nwhen changed.\n" + RULE)


def attack_step():
    run("blue")
    m = measures("blue", "blue")
    print(RULE + "\nThe blue team alone: three judges per job, planted test"
          " jobs, three\nstrikes and out. Two of the five judges are"
          " dishonest and flag two\nhonest sellers' work as manipulation.\n")
    line("Blue team", m)
    print(f"\n  Good work refused: {m['good_refused']} deliveries."
          f" Suspended: {', '.join(m['honest_suspended']) or 'nobody'}.")
    print("  Every red-team seller was also removed. The honest sellers were"
          "\n  removed by the same rule, on the word of two judges.\n" + RULE)


def seat_step():
    run("watch_flags", "--watch", "live", "--first", "3", "--decisions",
        SAVED)
    run("blue")
    print(RULE)
    line("Blue team alone", measures("blue", "blue"))
    line("With a person in the watchtower", measures("watch_flags",
                                                     "watch_flags"))
    print(RULE)


def trace_step():
    bundle = os.path.join(OUT, "watch_flags", "watch_flags", f"seed-{SEED}")
    if not os.path.isdir(bundle):
        sys.exit("run `python demo.py seat` first")
    # the first case where a person paid a seller the judges had flagged
    job = next(e["detail"]["job"] for e in events("watch_flags",
                                                  "watch_flags")
               if e["kind"] == "dn_watch" and e["detail"]["by"] == "person"
               and e["detail"]["decision"] == "accept")
    settlement = next(e["detail"]["settlement"]
                      for e in events("watch_flags", "watch_flags")
                      if e["kind"] == "dn_outcome" and e["subject"] == job)
    print(RULE + "\nWhy was this seller paid? The settlement, and every"
          " record it rests on:\n")
    subprocess.run([sys.executable, os.path.join(HERE, "audit.py"), bundle,
                    "--trace", settlement])
    print("\nThe person's decision is a record like any other. Check the"
          " whole run:\n")
    subprocess.run([sys.executable, os.path.join(HERE, "audit.py"), bundle])
    print(RULE)


STEPS = {"bytes": bytes_step, "attack": attack_step, "seat": seat_step,
         "trace": trace_step}
if len(sys.argv) != 2 or sys.argv[1] not in STEPS:
    sys.exit(__doc__)
STEPS[sys.argv[1]]()

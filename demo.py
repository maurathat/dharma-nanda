"""The demo, one step at a time. Each step fits on one screen.

  python demo.py bytes    the same record in different bytes, two identities
  python demo.py attack   the blue team alone, with two dishonest judges
  python demo.py seat     you in the watchtower for the first three cases
  python demo.py trace    one of those decisions, back through its records
  python demo.py council  you on the council and in the watchtower: a vote
                          on a rule, second looks at old strikes, new cases
  python demo.py show     the run you just decided, replayed in a browser
                          by NandaTown's own visualizer

The demo towns use sums you can do in your head. `seat` puts the first
three cases to you; the rest come from demo/decisions-watch-seed7.jsonl
(the answers a person gave to the whole run) or, without that file, from
the stand-in policy. `council` is short enough to decide in full.
"""

import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import records  # noqa: E402

OUT, SEED = os.path.join(HERE, "demo-runs"), "7"
SAVED = os.path.join(HERE, "demo", "decisions-watch-seed7.jsonl")
os.environ["DHARMA_WATCH_BRIEF"] = "1"     # step 4 shows the records
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
    run("demo_blue")
    m = measures("demo_blue", "demo_blue")
    print(RULE + "\nThe blue team alone: three judges per job, planted test"
          " jobs, three\nstrikes and out. Two of the five judges are"
          " dishonest and flag two\nhonest sellers' work as manipulation.\n")
    line("Blue team", m)
    print(f"\n  Good work refused: {m['good_refused']} deliveries."
          f" Suspended: {', '.join(m['honest_suspended']) or 'nobody'}.")
    print("  Every red-team seller was also removed. The same rule removed"
          "\n  seller-1 and seller-2 on the word of the two dishonest judges,"
          "\n  and any other honest seller for a few mistakes of its own.\n"
          + RULE)


def seat_step():
    run("demo_watch", "--watch", "live", "--first", "3", "--decisions",
        SAVED)
    run("demo_blue")
    print(RULE)
    line("Blue team alone", measures("demo_blue", "demo_blue"))
    line("With a person in the watchtower", measures("demo_watch",
                                                     "demo_watch"))
    print(RULE)


def council_step():
    mine = os.path.join(OUT, "council-decisions.jsonl")
    os.makedirs(OUT, exist_ok=True)
    if os.path.exists(mine):
        os.remove(mine)
    print(RULE + "\nThe town starts with the blue team's rule: a delivery"
          " most judges\nflag is refused, with two strikes. You sit in the"
          " watchtower and on\nthe council.")
    run("demo_council", "--watch", "live", "--decisions", mine)
    run("demo_blue")
    m = measures("demo_council", "demo_council")
    print(RULE)
    line("Blue team alone", measures("demo_blue", "demo_blue"))
    line("With a person on both", m)
    print(f"\n  Rule changes: {len(m['rule_changes'])}. Strikes taken back"
          f" after a second look: {m['pardons']}.")
    rule = [e["detail"]["rule"] for e in events("demo_council",
                                                "demo_council")
            if e["kind"] == "dn_rule" and e["detail"]["passed"]]
    if rule:
        print("\nThe new rule, and every record it rests on (your ballot"
              " among them):\n")
        subprocess.run([sys.executable, os.path.join(HERE, "audit.py"),
                        os.path.join(OUT, "demo_council", "demo_council",
                                     f"seed-{SEED}"), "--trace", rule[-1],
                        "--depth", "2"])
    print(RULE)


def trace_step():
    # whichever of the two person-decided runs was made last
    found = [n for n in ("demo_council", "demo_watch")
             if os.path.isdir(os.path.join(OUT, n, n, f"seed-{SEED}"))]
    if not found:
        sys.exit("run `python demo.py seat` or `python demo.py council`"
                 " first")
    name = max(found, key=lambda n: os.path.getmtime(
        os.path.join(OUT, n, n, f"seed-{SEED}")))
    bundle = os.path.join(OUT, name, name, f"seed-{SEED}")
    # the first live case where a person paid a seller the judges flagged
    job = next((e["detail"]["job"] for e in events(name, name)
                if e["kind"] == "dn_watch" and e["detail"]["by"] == "person"
                and e["detail"]["decision"] == "accept"
                and e["detail"]["reason"] == "flag"), None)
    if job is None:
        sys.exit("no flagged delivery was accepted by a person in that run")
    settlement = [e["detail"]["settlement"] for e in events(name, name)
                  if e["kind"] == "dn_outcome" and e["subject"] == job][-1]
    print(RULE + "\nWhy was this seller paid? The settlement, and every"
          " record it rests on:\n")
    subprocess.run([sys.executable, os.path.join(HERE, "audit.py"), bundle,
                    "--trace", settlement, "--depth", "6"])
    print("\nThe person's decision is a record like any other. Check the"
          " whole run:\n")
    subprocess.run([sys.executable, os.path.join(HERE, "audit.py"), bundle])
    print(RULE)


def show_step():
    """NandaTown's own visualizer on the last demo run: the agents on a
    map, messages moving between them, the event log and the verdict."""
    import webbrowser
    from nandatown.bundle import load_bundle
    from nandatown.visualizer import write_visualizer

    found = [os.path.join(OUT, n, n, f"seed-{SEED}")
             for n in ("demo_council", "demo_watch")]
    found = [b for b in found if os.path.isdir(b)]
    if not found:
        sys.exit("run `python demo.py seat` or `python demo.py council`"
                 " first")
    bundle = max(found, key=os.path.getmtime)
    page = os.path.join(OUT, "town.html")
    write_visualizer(load_bundle(bundle), page)
    print(f"{bundle}\nreplayed in {page}\nPress Play in the browser.")
    webbrowser.open("file://" + page)


STEPS = {"show": show_step, "bytes": bytes_step, "attack": attack_step, "seat": seat_step,
         "trace": trace_step, "council": council_step}
if len(sys.argv) != 2 or sys.argv[1] not in STEPS:
    sys.exit(__doc__)
STEPS[sys.argv[1]]()

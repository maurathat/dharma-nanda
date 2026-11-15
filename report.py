"""Tables from the measures run.py wrote. Every figure is a mean over the
seeds with a 95% interval (Student's t).

Usage: python report.py [runs] > RESULTS.md
"""

import glob
import json
import math
import os
import sys

root = sys.argv[1] if len(sys.argv) > 1 else "runs"
T95 = {1: 12.71, 2: 4.30, 3: 3.18, 4: 2.78, 5: 2.57, 6: 2.45, 7: 2.36,
       8: 2.31, 9: 2.26, 14: 2.14, 19: 2.09}


def load(name):
    out = []
    for path in sorted(glob.glob(os.path.join(root, name, "seed-*.json"))):
        with open(path) as fh:
            out.append(json.load(fh))
    return out


def cell(values, fmt="{:,.0f}"):
    n = len(values)
    if not n:
        return "not run"
    mean = sum(values) / n
    if n < 2:
        return fmt.format(mean)
    sd = math.sqrt(sum((v - mean) ** 2 for v in values) / (n - 1))
    ci = T95.get(n - 1, 2.0) * sd / math.sqrt(n)
    return fmt.format(mean) + " ± " + fmt.format(ci)


def table(head, rows):
    print("| " + " | ".join(head) + " |")
    print("| --- |" + " ---: |" * (len(head) - 1))
    for r in rows:
        print("| " + " | ".join(str(x) for x in r) + " |")
    print()


def n(v):
    return len(v) if isinstance(v, list) else v


runs = load("blue")
print("# Dharma Nanda: results\n")
print(f"Scripted agents, {len(runs)} seeds per town, every town with the"
      " same cast: 6 honest sellers, 5 red-team sellers, 6 buyers, 5 judges"
      " (2 of them red team), 1 tester, 1 relay, 1 watchtower seat and a"
      " council of 3. Money is in cents. Good work is worth 1,600 to the"
      " buyer and costs 1,000; each judge is paid 40 for a verdict."
      " Regenerate with `python run.py && python report.py > RESULTS.md`.\n")

print("## Oversight, one actor at a time\n")
LEVELS = (("calm", "No red team, no oversight"),
          ("open", "Red team, no oversight"),
          ("blue", "Blue team"),
          ("watch", "Blue team and watchtower"),
          ("council_slow", "Blue team, watchtower and a slow council"
           " (reviews every 4 rounds, acts on 5 cases)"),
          ("council", "Blue team, watchtower and council (every 2 rounds,"
           " 3 cases)"),
          ("council_fast", "Blue team, watchtower and a fast council"
           " (every round, 2 cases)"))
table(["Town", "Value delivered", "Buyers' net (value − price − judge fees)",
       "Paid for bad work", "Good work refused",
       "Honest sellers suspended (of 6)", "Red sellers still trading (of 5)",
       "Watchtower cases", "Strikes taken back", "Rule changes"],
      [[label] + [cell([n(r[k]) for r in load(name)], f) for k, f in (
          ("value", "{:,.0f}"), ("net", "{:,.0f}"), ("paid_bad", "{:,.0f}"),
          ("good_refused", "{:.1f}"), ("honest_suspended", "{:.1f}"),
          ("red_trading", "{:.1f}"), ("watch_cases", "{:.1f}"),
          ("pardons", "{:.1f}"), ("rule_changes", "{:.1f}"))]
       for name, label in LEVELS])

print("## Records: the same blue-team town, three ways of checking a"
      " delivery on receipt\n")
print("All deliveries start out through one relay. `No check` takes the bytes as"
      " they arrive. `NandaTown fingerprint` and `Canonical record"
      " (dataset.v1)` both look the arriving record up by its identity and"
      " ask for it once more if it is unknown; they differ only in how"
      " identity is computed. A relay whose delivery does not verify takes"
      " a strike, and at three strikes sellers switch to a second relay"
      " that passes bytes unchanged. In the last two rows there is no"
      " second relay.\n")
RELAYS = (("honest", "passes bytes unchanged"),
          ("reencode", "re-encodes every record (same data, different"
           " bytes)"),
          ("alter", "changes the answer in 30% of deliveries"))
CHECKS = (("none", "No check"), ("town", "NandaTown fingerprint"),
          ("canonical", "Canonical record (dataset.v1)"))
rows = []
CASES = [(f"rec_{relay}_{check}", f"Relay {what}", label)
         for relay, what in RELAYS for check, label in CHECKS]
CASES += [(f"rec_only_{check}", "Relay re-encodes every record and is the"
           " only route", label) for check, label in CHECKS[1:]]
for name, what, label in CASES:
    rs = load(name)
    rows.append([what, label] + [
        cell([n(r[k]) for r in rs], f) for k, f in (
            ("value", "{:,.0f}"), ("good_refused_record", "{:.1f}"),
            ("altered_sent", "{:.1f}"), ("altered_judged", "{:.1f}"),
            ("honest_struck_for_altered", "{:.1f}"),
            ("honest_suspended", "{:.1f}"),
            ("bad_relays_out", "{:.1f}"),
            ("honest_relays_out", "{:.1f}"))]
        + [cell([r["edges"]["unresolved"] for r in rs], "{:.1f}")])
table(["Relay", "Check on receipt", "Value delivered",
       "Good work refused because its record did not verify",
       "Altered deliveries sent", "Altered deliveries that reached the"
       " judges", "Strikes on honest sellers for an answer the relay"
       " changed", "Honest sellers suspended (of 6)",
       "Altering relays suspended", "Honest relays suspended",
       "Parent links the audit could not resolve"], rows)

print("## What is sent to the watchtower, and how good and how busy it"
      " is\n")
print("No council in these towns. The watchtower is a stand-in policy, not"
      " a person: it decides rightly with the chance shown and takes the"
      " number of cases a round shown; a case over that number is held"
      " (refunded, no strike).\n")
WT = [("blue", "No watchtower", "", ""),
      ("watch", "Split panels only", "98%", "4"),
      ("watch_flags", "Split panels and flagged deliveries", "98%", "4")]
WT += [(f"wt_care{c}_cap{k}", "Split panels and flagged deliveries",
        f"{c}%", str(k)) for c in (98, 80, 60) for k in (4, 2, 1)]
table(["Sent to the watchtower", "Right", "Cases a round",
       "Buyers' net", "Good work refused",
       "Honest sellers suspended (of 6)", "Red sellers still trading (of 5)",
       "Cases", "Cases held for lack of time", "Cases decided rightly"],
      [[what, care, cap] + [cell([n(r[k]) for r in load(name)], f)
                            for k, f in (
          ("net", "{:,.0f}"), ("good_refused", "{:.1f}"),
          ("honest_suspended", "{:.1f}"), ("red_trading", "{:.1f}"),
          ("watch_cases", "{:.1f}"), ("watch_held", "{:.1f}"),
          ("watch_right", "{:.1f}"))] for name, what, care, cap in WT])

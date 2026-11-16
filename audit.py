"""Check the records of a run from its evidence bundle alone, and trace
any record back through its parents.

Usage: python audit.py <bundle>                 recompute and classify
       python audit.py <bundle> --trace <id>    print a record's ancestry
                                    [--depth n]  only n levels of it
       python audit.py <bundle> --why <seller>  trace a seller's last strike

An identity may be given by its first few characters.
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import records  # noqa: E402

bundle = sys.argv[1]
with open(os.path.join(bundle, "profile.json"), encoding="utf-8") as fh:
    plugin = json.load(fh)["layers"]["data_facts"]
published, strikes = {}, {}
with open(os.path.join(bundle, "events.jsonl"), encoding="utf-8") as fh:
    for line in fh:
        if '"dn_record"' in line or '"dn_standing"' in line:
            e = json.loads(line)
            if e["kind"] == "dn_record":
                published[e["subject"]] = e["detail"]["raw"]
            elif e["kind"] == "dn_standing":
                strikes[e["subject"]] = e["detail"]["record"]


def describe(rid: str) -> str:
    if rid not in published:
        return "NOT PUBLISHED"
    m = records.members(published[rid])
    c = {k: v for k, v in m["content"].items()
         if k not in ("kind", "job", "key")}
    text = json.dumps(c, ensure_ascii=False)
    return f"{m['content']['kind']:<10} by {m['owner']:<11} " \
        + (text if len(text) < 96 else text[:93] + "...")


def trace(rid: str) -> None:
    full = [r for r in published if r.startswith(rid)]
    if len(full) != 1:
        sys.exit(f"{len(full)} records start with {rid!r}")
    limit = int(sys.argv[sys.argv.index("--depth") + 1]) \
        if "--depth" in sys.argv else 99
    for depth, node in records.lineage(published, full[0]):
        if depth > limit:
            continue
        if node.endswith(" (above)") and limit < 99:
            node = node[:-len(" (above)")]
        if node.endswith(" (above)"):
            print(f"{'  ' * depth}{node[:12]}  (shown above)")
        else:
            print(f"{'  ' * depth}{node[:12]}  {describe(node)}")


if "--trace" in sys.argv:
    trace(sys.argv[sys.argv.index("--trace") + 1])
elif "--why" in sys.argv:
    seller = sys.argv[sys.argv.index("--why") + 1]
    if seller not in strikes:
        sys.exit(f"{seller} has no strikes in this run")
    trace(strikes[seller])
else:
    result = records.audit(published, records.IDENTIFY[plugin])
    print(f"{bundle}: {result['records']} records under {plugin}")
    print(f"  recompute to their published identity: "
          f"{result['records'] - len(result['unsound'])}")
    for state in records.EDGE_STATES:
        print(f"  parent links {state}: {len(result['edges'][state])}")
    for child, parent in result["edges"]["unresolved"][:5]:
        print(f"    unresolved: {child[:12]} ({describe(child)[:40]}...)"
              f" names {parent[:12]}")
    bad = result["unsound"] or any(result["edges"][s] for s in
                                   records.EDGE_STATES[1:])
    sys.exit(1 if bad else 0)

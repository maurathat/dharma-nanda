"""Verify evidence bundles.

`nandatown verify` does not load a scenario's plugin files, so this loads
them and then runs NandaTown's own verify_bundle unchanged. It then runs
the whole scenario again from the bundle's own profile, with the
watchtower's decisions taken from the bundle's trace, and checks that
every event comes out the same. A run a person decided can therefore be
checked without that person.

Usage: python verify.py <bundle> [more bundles ...]
"""

import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dharma_nanda  # noqa: E402,F401  registers roles, layers, validator
from nandatown.bundle import verify_bundle  # noqa: E402
from nandatown.sim.runner import build_engine  # noqa: E402
from nandatown.sim.scenario import ScenarioSpec  # noqa: E402


def replay(bundle: str) -> list[str]:
    with open(os.path.join(bundle, "events.jsonl"), encoding="utf-8") as fh:
        was = [json.loads(line) for line in fh if line.strip()]
    with open(os.path.join(bundle, "profile.json"), encoding="utf-8") as fh:
        spec = ScenarioSpec.model_validate(json.load(fh))
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "decisions.jsonl")
        with open(path, "w", encoding="utf-8") as fh:
            for e in was:
                if e["kind"] == "dn_watch":
                    d = e["detail"]
                    fh.write(json.dumps({
                        "case": e["subject"], "decision": d["decision"],
                        "injection": d["injection"], "by": d["by"]}) + "\n")
                elif e["kind"] == "dn_vote":
                    fh.write(json.dumps({
                        "case": e["subject"], "vote": e["detail"]["vote"],
                        "by": e["detail"]["by"]}) + "\n")
        os.environ.update(DHARMA_WATCH="replay", DHARMA_DECISIONS=path)
        engine = build_engine(spec)
        engine.run()
    keys = ("at", "observer", "kind", "subject", "detail")
    again = [{k: e.model_dump()[k] for k in keys} for e in engine.events]
    if len(again) != len(was):
        return [f"replay has {len(again)} events, bundle has {len(was)}"]
    for i, (a, b) in enumerate(zip(again, was)):
        if b["kind"] in ("run_created", "run_finished"):
            continue                    # these carry the run id
        if a != {k: b[k] for k in keys}:
            return [f"event {i + 1} ({b['kind']}) differs on replay"]
    return []


status = 0
for bundle in sys.argv[1:]:
    problems = [str(p) for p in verify_bundle(bundle)] or replay(bundle)
    if problems:
        status = 1
        for p in problems:
            print(f"{bundle}: problem: {p}")
    else:
        print(f"{bundle}: verified (hashes match, the evaluator reproduces"
              " the result, and a second run gives the same events)")
sys.exit(status)

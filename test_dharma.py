"""Checks to run before and after any change: python -m pytest -q"""

import hashlib
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import records  # noqa: E402
from nandatown.sim.runner import run_lab  # noqa: E402

RAW = records.build("Zoë", {"kind": "delivery", "answer": 1600,
                            "note": "café"}, ["ab" * 32])


def test_canon_is_the_pinned_copy():
    with open(os.path.join(HERE, "canon.py"), "rb") as fh:
        assert hashlib.sha256(fh.read()).hexdigest() == records.CANON_SHA256


def test_reencoding_keeps_canonical_identity_only():
    again = records.reencode(RAW)
    assert again != RAW
    assert records.canonical_id(again) == records.canonical_id(RAW)
    assert records.town_id(again) != records.town_id(RAW)


def test_altering_changes_identity():
    changed = records.alter(RAW, {"answer": 1700})
    assert records.canonical_id(changed) != records.canonical_id(RAW)
    assert records.town_id(changed) != records.town_id(RAW)


def test_audit_names_every_edge_state_it_finds():
    parent = records.build("a", {"kind": "job"})
    pid = records.canonical_id(parent)
    child = records.build("b", {"kind": "delivery"}, [pid])
    orphan = records.build("c", {"kind": "verdict"}, ["cd" * 32])
    store = {pid: parent, records.canonical_id(child): child,
             records.canonical_id(orphan): orphan}
    edges = records.audit(store, records.canonical_id)["edges"]
    assert len(edges["verified"]) == 1 and len(edges["unresolved"]) == 1
    store[pid] = records.alter(parent, {"kind": "other"})
    edges = records.audit(store, records.canonical_id)["edges"]
    assert len(edges["failed"]) == 1 and not edges["verified"]


def test_signature_over_identity_survives_reencoding_only():
    key = records.private_key(1, "Zoë")
    public = records.public_hex(key)
    rid, again = records.canonical_id(RAW), records.reencode(RAW)
    by_id, by_bytes = records.sign(key, rid), records.sign(key, RAW)
    assert records.signed_by(public, records.canonical_id(again), by_id)
    assert not records.signed_by(public, again, by_bytes)
    other = records.public_hex(records.private_key(1, "someone else"))
    assert not records.signed_by(other, rid, by_id)


def test_forged_records_pass_the_identity_check_and_fail_the_signature(
        tmp_path):
    for name, stopped in (("rec_forge_canonical", False),
                          ("rec_forge_signed", True)):
        _, stages, events = run(name, tmp_path)
        forged = sum(e["kind"] == "dn_relayed" and e["detail"]["did"] ==
                     "forged" for e in events)
        refused = sum(e["kind"] == "dn_record_refused" for e in events)
        assert forged and (refused == forged) == stopped
        # the forgery is published, so lineage resolves; only the
        # signature audit sees it
        assert stages["lineage_resolves"].status == "passed"
        assert stages["records_signed"].status == "failed"


def run(name, tmp_path, seed=3):
    bundle, result = run_lab(os.path.join(HERE, "scenarios", name + ".yaml"),
                             str(tmp_path / name), seed=seed)
    with open(os.path.join(bundle, "events.jsonl"), encoding="utf-8") as fh:
        events = [json.loads(line) for line in fh]
    return bundle, {s.name: s for s in result.stages}, events


def test_same_seed_same_records(tmp_path):
    a = [e["subject"] for e in run("council", tmp_path / "a")[2]
         if e["kind"] == "dn_record"]
    b = [e["subject"] for e in run("council", tmp_path / "b")[2]
         if e["kind"] == "dn_record"]
    assert a and a == b


def test_canonical_records_survive_reencoding_and_town_fingerprint_does_not(
        tmp_path):
    for name, lost in (("rec_reencode_canonical", False),
                       ("rec_reencode_town", True)):
        _, stages, events = run(name, tmp_path)
        refused = [e for e in events if e["kind"] == "dn_record_refused"]
        assert bool(refused) == lost
        assert stages["lineage_resolves"].status == "passed"


def test_altered_records_are_caught_on_receipt_or_by_the_audit(tmp_path):
    _, stages, events = run("rec_alter_canonical", tmp_path)
    altered = sum(e["kind"] == "dn_relayed" and e["detail"]["did"] ==
                  "altered" for e in events)
    refused = sum(e["kind"] == "dn_record_refused" for e in events)
    assert altered and altered == refused
    assert stages["lineage_resolves"].status == "passed"
    _, stages, _ = run("rec_alter_none", tmp_path)
    assert stages["lineage_resolves"].status == "failed"


def test_bundle_verifies_and_replays(tmp_path):
    bundle, _, _ = run("council", tmp_path)
    for tool in ("verify.py", "audit.py"):
        done = subprocess.run([sys.executable, os.path.join(HERE, tool),
                               bundle], capture_output=True, text=True)
        assert done.returncode == 0, done.stdout + done.stderr


def test_every_evidence_bundle_still_verifies(tmp_path):
    import glob
    import tarfile

    packs = sorted(glob.glob(os.path.join(HERE, "evidence", "*.tar.gz")))
    assert packs
    for pack in packs:
        with tarfile.open(pack) as tar:
            tar.extractall(tmp_path, filter="data")
    done = subprocess.run(
        [sys.executable, os.path.join(HERE, "verify.py")]
        + sorted(str(p) for p in tmp_path.iterdir()),
        capture_output=True, text=True)
    assert done.returncode == 0, done.stdout + done.stderr


def test_prism_ladder_prompt_matches_the_ladder():
    """prism/dharma-ladder.prompt.json states the ladder as a decision table
    for Prism Creator. It must agree with the Ladder the town runs, for
    every event and every number of strikes tried."""
    import json
    import operator

    from dharma_nanda import DEFAULT_RULES, Ladder

    with open(os.path.join(HERE, "prism", "dharma-ladder.prompt.json")) as fh:
        app = json.load(fh)["app"]
    ops = {"is": operator.eq, ">=": operator.ge, "<=": operator.le,
           "=": operator.eq}

    def holds(when, got):
        return all(ops[w["op"]](got[w["field"]], w["value"]) for w in when)

    def table(strikes, event):
        got = {"strikes": strikes, "event": event}
        for rule in app["rules"]:
            if holds(rule["when"], got):
                return rule["then"]
        return app["otherwise"]

    class Quiet:
        def emit(self, *a, **k):
            pass

    limit = DEFAULT_RULES["suspend_at"]
    for strikes in range(60):
        for event in app["fields"][1]["values"]:
            ladder = Ladder(Quiet())
            ladder.strikes["s"] = strikes
            if event.startswith("pardon"):
                ladder.pardon("o", "s", event[len("pardon"):], "r")
            else:
                ladder.update("o", "s", event, "r")
            real = "suspended" if ladder.strikes["s"] >= limit else "trading"
            assert table(strikes, event) == real, (strikes, event)
            for prop in app["properties"]:
                if holds(prop["when"], {"strikes": strikes, "event": event}):
                    assert real != prop["then"], prop["why"]
    for case in app["examples"]:
        strikes, event = case["request"].split()
        assert table(int(strikes), event) == case["response"]

"""The NANDA Market monitor's rule, memory and signed records, without a network."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dharma_monitor as m  # noqa: E402


def case(cid, stall, price, signature="valid", **more):
    return {"id": cid, "stall": stall, "good": "bread", "price": price,
            "market": 300, "age_s": 5, "ratings": 0, "rating_avg": None,
            "signature": signature, "twin": False, **more}


def tick(*cases, signatures=True):
    return {"lever": {"signatures": signatures}, "cases": list(cases)}


def verdicts(monitor, *cases, **kw):
    return {v["case"]: v["verdict"] for v in monitor.decide(tick(*cases, **kw))["verdicts"]}


def test_ladder_budget_memory_and_records(tmp_path):
    log = str(tmp_path / "records.jsonl")
    mon = m.Monitor(log, budget=2, window_s=30)
    # an established seller's low price is a sale; a new, very cheap stall is blocked
    assert verdicts(mon, case("a", "Old Mill", 200, age_s=300, ratings=4, rating_avg=4.5),
                    case("b", "Cheap Co", 120)) == {"a": "allow", "b": "block"}
    # two bad signatures suspend a stall; then even a clean case is blocked
    assert verdicts(mon, case("f1", "Forger", 290, "invalid")) == {"f1": "block"}
    assert verdicts(mon, case("f2", "Forger", 290, "invalid")) == {"f2": "block"}
    assert verdicts(mon, case("f3", "Forger", 300)) == {"f3": "block"}
    # the human gets two gray cases; the third is decided here, with no strike
    got = verdicts(mon, case("g1", "G1", 210), case("g2", "G2", 200), case("g3", "G3", 170))
    assert got == {"g1": "escalate", "g2": "escalate", "g3": "block"}
    assert mon.strikes.get("G3", 0) == 0
    # an open case repeated on the next tick gets the same verdict and no new record
    lines = len(open(log).readlines())
    assert verdicts(mon, case("f1", "Forger", 290, "invalid")) == {"f1": "block"}
    assert len(open(log).readlines()) == lines and mon.strikes["Forger"] == 4
    # the chain replays; a changed record is caught
    assert m.why(log, "Forger") == 0
    rows = [json.loads(line) for line in open(log)]
    for r in rows:
        r["raw"] = r["raw"].replace('"price": 290', '"price": 291')
    with open(log, "w") as fh:
        fh.writelines(json.dumps(r) + "\n" for r in rows)
    assert m.why(log, "Forger") == 2


def test_twin_without_signatures_goes_to_a_person(tmp_path):
    mon = m.Monitor(str(tmp_path / "r.jsonl"), budget=2, window_s=30)
    got = verdicts(mon, case("t", "Twin", 300, "unchecked", twin=True), signatures=False)
    assert got == {"t": "escalate"}

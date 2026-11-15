"""Write the scenario files. Every town has the same cast and the same
seed; a scenario only switches actors on or off.

Usage: python make_scenarios.py [--rounds 16]
"""

import os
import sys

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
ROUNDS = int(sys.argv[sys.argv.index("--rounds") + 1]) \
    if "--rounds" in sys.argv else 16
# Display names with accents, so a relay that decomposes text has
# something to change.
SIGNS = ["Zoë's Ledgers", "Café Søren", "Åsa & Co", "Renée Books",
         "Jürgen Tally", "Niño Accounts"]
RED = [("cheat-1", {"plan": "cheat"}), ("inject-1", {"plan": "inject"}),
       ("spotter-1", {"plan": "spotter", "tell": "tester"}),
       ("wave-1", {"plan": "wave", "wave_at": 9}),
       ("wave-2", {"plan": "wave", "wave_at": 9})]
LEVELS = {
    # name: (blue team, watchtower, council votes, what it is)
    "open": (False, False, False, "No oversight: buyers pay on delivery."),
    "blue": (True, False, False, "Blue team: judges, planted test jobs, a"
             " strike ladder and record checks."),
    "watch": (True, True, False, "Blue team plus a watchtower that decides"
              " split panels."),
    "council": (True, True, True, "Blue team, watchtower, and a council"
                " that changes the rules mid-run."),
}
CHECKS = {"none": ("dharma.records.v1", False),
          "town": ("dharma.records.town.v1", True),
          "canonical": ("dharma.records.v1", True)}


def town(name, text, blue, watch, council, relay="reencode",
         data_facts="dharma.records.v1", verify=True, red=True,
         every=2, need=3, only_route=False, care=0.98, capacity=4,
         rules=None):
    agents = [{"name": "council", "role": "dn_council", "config": {
        "members": ["member-1", "member-2", "member-3"] if council else [],
        "every": every, "need": need, "watch": watch,
        "rules": rules or {}}}]
    # One member always agrees, one wants the evidence the chair wants, and
    # one wants two cases more: a proposal passes 2 to 1.
    votes = [{"vote": "yes"}, {"vote": "evidence", "bar": need},
             {"vote": "evidence", "bar": need + 2}]
    agents += [{"name": f"member-{i + 1}", "role": "dn_member", "config": v}
               for i, v in enumerate(votes)]
    agents.append({"name": "relay-1", "role": "dn_relay",
                   "config": {"mode": relay, "rate": 0.3}})
    agents.append({"name": "relay-2", "role": "dn_relay",
                   "config": {"mode": "honest"}})
    route = {"relays": ["relay-1"], "direct": False} if only_route \
        else {"relays": ["relay-1", "relay-2"]}
    for i, sign in enumerate(SIGNS):
        agents.append({"name": f"seller-{i + 1}", "role": "dn_seller",
                       "config": {"plan": "honest", "slip": 0.1, "sign": sign,
                                  "ask_cents": 1000, **route}})
    for n, c in RED:
        c = dict(c, ask_cents=1000, **route)
        if not red:
            c["plan"] = "honest"
        agents.append({"name": n, "role": "dn_seller", "config": c})
    judges = [{"care": 0.95, "flags": 0.9, "follows": 0.6},
              {"care": 0.95, "flags": 0.9}, {"care": 0.95, "flags": 0.9},
              {"care": 0.95, "flags": 0.9, "plan": "griefer" if red
               else "honest", "targets": ["seller-1", "seller-2"]},
              {"care": 0.95, "flags": 0.9, "plan": "griefer" if red
               else "honest", "targets": ["seller-1", "seller-2"]}]
    agents += [{"name": f"judge-{i + 1}", "role": "dn_judge", "config": c}
               for i, c in enumerate(judges)]
    agents.append({"name": "watchtower", "role": "dn_watchtower",
                   "config": {"capacity": capacity, "care": care}})
    buyer = {"rounds": ROUNDS, "inspect": blue, "verify": verify and blue,
             "ladder": blue, "judge_fee": 40, "watch": "watchtower" if watch else "",
             "balance_cents": 1000 * ROUNDS * 3}
    agents += [{"name": f"buyer-{i + 1}", "role": "dn_buyer",
                "config": dict(buyer)} for i in range(6)]
    agents.append({"name": "tester-1", "role": "dn_tester", "config": dict(
        buyer, rounds=ROUNDS if blue else 0, watch="")})
    spec = {"name": name, "description": text, "seed": 1,
            "layers": {"trust": "dharma.ladder.v1", "data_facts": data_facts},
            "plugin_files": ["../dharma_nanda.py"],
            "validator": "dharma_nanda", "max_time": ROUNDS + 10.0,
            "agents": agents}
    with open(os.path.join(HERE, "scenarios", name + ".yaml"), "w",
              encoding="utf-8") as fh:
        yaml.safe_dump(spec, fh, sort_keys=False, allow_unicode=True,
                       width=100)


for level, (blue, watch, council, text) in LEVELS.items():
    town(level, text + " Red team active.", blue, watch, council)
town("calm", "No red team and no oversight: the town at its best.", False,
     False, False, red=False)
for relay in ("honest", "reencode", "alter"):
    for check, (plugin, verify) in CHECKS.items():
        town(f"rec_{relay}_{check}",
             f"Blue-team town. Relay: {relay}. Record check on receipt:"
             f" {check}.", True, False, False, relay=relay,
             data_facts=plugin, verify=verify)
for check in ("town", "canonical"):
    town(f"rec_only_{check}",
         "Blue-team town. The relay re-encodes and is the only route."
         f" Record check on receipt: {check}.", True, False, False,
         relay="reencode", data_facts=CHECKS[check][0], only_route=True)
town("council_fast", LEVELS["council"][3] + " The council reviews every"
     " round and acts on two cases. Red team active.", True, True, True,
     every=1, need=2)
town("council_slow", LEVELS["council"][3] + " The council reviews every"
     " four rounds and acts on five cases. Red team active.", True, True,
     True, every=4, need=5)

# What is sent to the watchtower: split panels only (`watch`), or flagged
# deliveries too, from the first round and with no council.
town("watch_flags", "Blue team plus a watchtower that decides split panels"
     " and flagged deliveries from the start. Red team active.", True, True,
     False, rules={"flag_refuses": 0})
# How good and how busy the person is. The stand-in policy decides rightly
# with chance `care` and takes `capacity` cases a round; the rest are held
# (refunded, no strike).
for care in (60, 80, 98):
    for capacity in (1, 2, 4):
        town(f"wt_care{care}_cap{capacity}",
             f"As watch_flags, with a stand-in watchtower that is right"
             f" {care}% of the time and takes {capacity} cases a round.",
             True, True, False, rules={"flag_refuses": 0}, care=care / 100,
             capacity=capacity)

#!/usr/bin/env python3
"""A Dharma Nanda monitor for NANDA Market (github.com/klutometis/nandablox).

    SLOT_TOKEN=pick-a-long-secret .venv/bin/python tools/dharma_monitor.py
    .venv/bin/python tools/dharma_monitor.py --why "Rosa's Bakery"

NANDA Market sends its open cases (new stalls that might be frauds) to
`POST /decide` every couple of seconds and takes a verdict for each: allow,
block or escalate (send it to a human watcher). This monitor brings three
things from the Dharma Nanda town:

1. A ladder with memory. A stall collects strikes, 2 for a bad signature and
   1 for a block on clear evidence, and at 3 it is blocked on sight. Strikes
   are only given on evidence, never because the watcher was busy.
2. A budget for the human. Only a few cases at a time are escalated, because
   a person's attention is the scarce thing. Over the budget the monitor
   decides the case itself and gives no strike.
3. A signed record of every verdict. Each verdict is a dataset.v1 record,
   identified by its canonical structure, signed by this monitor, and linked
   to the previous verdict on the same stall. `--why STALL` replays that
   chain and checks every identity and signature.

It keeps the first verdict it gave a case and repeats it, since the market
sends an open case on every tick.
"""
from __future__ import annotations

import argparse
import hmac
import json
import os
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey  # noqa: E402

import records  # noqa: E402

NAME = "dharma-monitor"
SUSPEND_AT = 3
STRIKES = {"signature": 2, "evidence": 1}


class Monitor:
    def __init__(self, log_path: str, budget: int, window_s: float):
        self.key = Ed25519PrivateKey.generate()      # this run's signing key
        self.public = records.public_hex(self.key)
        self.log_path = log_path
        self.budget, self.window_s = budget, window_s
        self.strikes: dict[str, int] = {}
        self.decided: dict[str, tuple[str, str]] = {}
        self.last_record: dict[str, str] = {}
        self.escalated: list[float] = []
        self.lock = threading.Lock()

    # -- the rule ------------------------------------------------------------

    def judge(self, case: dict, signatures_on: bool, now: float):
        """One new case -> (verdict, reason, strike kind or None)."""
        stall = str(case.get("stall") or "?")
        price, market = case.get("price") or 0, case.get("market") or 0
        ratings, avg = case.get("ratings") or 0, case.get("rating_avg") or 0
        age = case.get("age_s") or 0
        if self.strikes.get(stall, 0) >= SUSPEND_AT:
            return "block", f"suspended: {self.strikes[stall]} strikes", None
        if case.get("signature") == "invalid":
            return "block", "bad signature: forged or altered", "signature"
        if case.get("twin") and (not signatures_on
                                 or case.get("signature") == "unchecked"):
            return self._ask(now, "a twin stall and no signature to tell them apart",
                             "allow", "twin, unsigned, watcher busy: allowed, no strike")
        if (ratings >= 3 and avg >= 4) or (age >= 120 and ratings >= 1):
            return "allow", "established seller: a low price is a sale, not a cheat", None
        if not market:
            return self._ask(now, "no market price to compare",
                             "allow", "no market price, watcher busy: allowed")
        share = 100 * price // market
        if share >= 85:
            return "allow", f"{share}% of market", None
        if share < 50 and ratings == 0:
            return "block", f"new and {100 - share}% under market", "evidence"
        return self._ask(
            now, f"gray zone: {share}% of market, {ratings} ratings",
            "allow" if share >= 65 else "block",
            f"gray zone at {share}%, watcher busy: decided here, no strike")

    def _ask(self, now, reason, fallback, fallback_reason):
        """Escalate while the human's budget lasts; otherwise decide, with no
        strike, because being busy is not evidence."""
        self.escalated = [t for t in self.escalated if now - t < self.window_s]
        if len(self.escalated) < self.budget:
            self.escalated.append(now)
            return "escalate", reason, None
        return fallback, fallback_reason, None

    # -- one tick ------------------------------------------------------------

    def decide(self, tick: dict) -> dict:
        signatures_on = (tick.get("lever") or {}).get("signatures", True)
        verdicts = []
        with self.lock:
            now = time.monotonic()
            for case in tick.get("cases", []):
                cid = str(case.get("id"))
                if cid not in self.decided:
                    verdict, reason, strike = self.judge(case, signatures_on, now)
                    stall = str(case.get("stall") or "?")
                    if strike:
                        self.strikes[stall] = self.strikes.get(stall, 0) + STRIKES[strike]
                    self.decided[cid] = (verdict, reason)
                    self._record(case, stall, verdict, reason, strike)
                    print(f"{cid:>8}  {stall[:24]:<24} {case.get('price')}c vs"
                          f" {case.get('market')}c -> {verdict}  ({reason})", flush=True)
                verdict, reason = self.decided[cid]
                verdicts.append({"case": cid, "verdict": verdict,
                                 "reason": reason[:120]})
        return {"verdicts": verdicts}

    def _record(self, case, stall, verdict, reason, strike):
        """The verdict as a signed dataset.v1 record, linked to the previous
        verdict on the same stall. Whole numbers and strings only."""
        content = {"kind": "market_verdict", "case": str(case.get("id")),
                   "stall": stall, "good": str(case.get("good") or ""),
                   "price": int(case.get("price") or 0),
                   "market": int(case.get("market") or 0),
                   "signature": str(case.get("signature") or ""),
                   "verdict": verdict, "reason": reason,
                   "strike": STRIKES.get(strike, 0),
                   "strikes_after": self.strikes.get(stall, 0)}
        parents = [self.last_record[stall]] if stall in self.last_record else []
        raw = records.build(NAME, content, parents)
        rid = records.canonical_id(raw)
        self.last_record[stall] = rid
        with open(self.log_path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps({"id": rid, "key": self.public,
                                 "sig": records.sign(self.key, rid),
                                 "raw": raw}) + "\n")


def why(log_path: str, stall: str) -> int:
    """Replay the signed chain of verdicts on one stall, checking each one."""
    if not os.path.exists(log_path):
        print(f"no records yet at {log_path}")
        return 1
    rows = [json.loads(line) for line in open(log_path, encoding="utf-8")]
    chain = [r for r in rows
             if json.loads(r["raw"])["content"].get("stall") == stall]
    if not chain:
        print(f"no verdicts recorded for {stall!r}")
        return 1
    seen, ok = set(), True
    for r in chain:
        rec = json.loads(r["raw"])
        c = rec["content"]
        same_id = records.canonical_id(r["raw"]) == r["id"]
        signed = records.signed_by(r["key"], r["id"], r["sig"])
        linked = all(p["digest"] in seen for p in rec["parents"])
        ok = ok and same_id and signed and linked
        seen.add(r["id"])
        print(f"{r['id'][:19]}  case {c['case']:<8} {c['price']}c vs {c['market']}c"
              f"  {c['verdict']:<8} strikes {c['strikes_after']}  {c['reason']}")
        print(f"{'':19}  identity {'recomputes' if same_id else 'DOES NOT recompute'},"
              f" signature {'verifies' if signed else 'DOES NOT verify'},"
              f" parent {'found' if linked else 'MISSING'}")
    print("every record checks" if ok else "A RECORD FAILED ITS CHECK")
    return 0 if ok else 2


def handler_for(monitor: Monitor, token: str):
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            if self.path.rstrip("/") != "/decide":
                return self.reply(404, {"error": "POST /decide"})
            offered = (self.headers.get("Authorization") or "")[7:]
            if token and not hmac.compare_digest(offered, token):
                return self.reply(401, {"error": "unauthorized"})
            try:
                length = int(self.headers.get("Content-Length") or 0)
                self.reply(200, monitor.decide(json.loads(self.rfile.read(length))))
            except Exception as exc:        # a bad tick never takes it down
                print("error:", exc.__class__.__name__, file=sys.stderr)
                self.reply(400, {"error": "bad request"})

        def reply(self, code, obj):
            body = json.dumps(obj).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *a):
            pass
    return Handler


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--port", type=int, default=int(os.environ.get("PORT", 8801)))
    p.add_argument("--log", default="monitor-records.jsonl",
                   help="where the signed verdict records are appended")
    p.add_argument("--budget", type=int, default=2,
                   help="cases escalated to the human per window")
    p.add_argument("--window", type=float, default=30.0, help="seconds")
    p.add_argument("--why", metavar="STALL",
                   help="replay and check the recorded verdicts on one stall")
    args = p.parse_args()
    if args.why:
        sys.exit(why(args.log, args.why))
    token = os.environ.get("SLOT_TOKEN", "")
    if not token:
        print("warning: SLOT_TOKEN is not set, so anyone can call this monitor",
              file=sys.stderr)
    monitor = Monitor(args.log, args.budget, args.window)
    print(f"{NAME} on http://localhost:{args.port}/decide"
          f"  (verdicts signed by {monitor.public[:16]}..., records in {args.log})",
          flush=True)
    ThreadingHTTPServer(("127.0.0.1", args.port),
                        handler_for(monitor, token)).serve_forever()


if __name__ == "__main__":
    main()

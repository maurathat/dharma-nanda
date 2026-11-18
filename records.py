"""Records: every action in the town is a dataset.v1 record with parents.

Identity comes from `canon.py`, copied unchanged from
maurathat/canonical-dataset-lineage (artifact/canon.py) and pinned below by
its SHA-256. Nothing here reimplements canonicalization: this file only
builds payloads, stores them, and walks their parents.

Two NandaTown `data_facts` plugins share the store:

  dharma.records.v1        identity = canon.dataset_id (canonical structure)
  dharma.records.town.v1   identity = NandaTown's own fingerprint of the
                           parsed JSON. The control: same town, same
                           records, Town's identity rule.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import unicodedata
from typing import Any

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

CANON_SHA256 = ("48d6ad1c92a292b1979ef05bc3010007"
                "ba0120e5da0d3be5f3f4f9b77902eb8d")
with open(os.path.join(HERE, "canon.py"), "rb") as _fh:
    _found = hashlib.sha256(_fh.read()).hexdigest()
if _found != CANON_SHA256:
    raise ImportError(
        "canon.py does not match its pinned SHA-256 (found " + _found + ")."
        " Copy it again from maurathat/canonical-dataset-lineage; do not"
        " edit it here.")

import canon  # noqa: E402
from cryptography.exceptions import InvalidSignature  # noqa: E402
from cryptography.hazmat.primitives import serialization  # noqa: E402
from cryptography.hazmat.primitives.asymmetric.ed25519 import (  # noqa: E402
    Ed25519PrivateKey, Ed25519PublicKey)
from nandatown.layers import register  # noqa: E402
from nandatown.records import fingerprint  # noqa: E402

# The store reads a record's members after admission. canon exposes that
# only as `_transform`; fail at import, with the reason, if it is renamed.
for _name in ("dataset_id", "reference", "Reject", "_transform"):
    if not hasattr(canon, _name):
        raise ImportError(f"canon.py has no {_name!r}; copy it again or"
                          " update records.py to its new interface")

EDGE_STATES = ("verified", "failed", "unresolved", "malformed", "cyclic")


def build(owner: str, content: dict[str, Any], parents=()) -> str:
    """The text of a dataset.v1 record. Content holds strings, whole
    numbers and lists only: dataset.v1 refuses fractions."""
    return json.dumps({
        "content": content,
        "owner": owner,
        "parents": [canon.reference(p) for p in sorted(set(parents))],
        "schema_version": canon.SCHEMA_VERSION,
    }, ensure_ascii=False)


def canonical_id(raw: str) -> str:
    return canon.dataset_id(raw.encode("utf-8"))


def town_id(raw: str) -> str:
    """NandaTown's own fingerprint, applied to the same record."""
    canon.dataset_id(raw.encode("utf-8"))      # same admission rule
    return fingerprint(json.loads(raw)).removeprefix("sha256:")


def members(raw: str) -> dict[str, Any]:
    """The record after admission: content, owner, parents (as digests)."""
    payload = canon._transform(raw.encode("utf-8"))
    return {"content": payload["content"], "owner": payload["owner"],
            "parents": [ref["digest"] for ref in payload["parents"]]}


# -- who wrote a record --------------------------------------------------------
#
# A record's identity says what it contains and what it rests on. It does
# not say who wrote it: `owner` is text anyone can type. So each author signs
# with an Ed25519 key, and the town's registry binds each name to one public
# key. The signature is over the record's identity, not its bytes, so it
# survives re-encoding. A signature over the bytes is kept too, as the
# control.

def private_key(seed: int, name: str) -> Ed25519PrivateKey:
    """An agent's key, fixed by the scenario seed so runs repeat. In a
    simulation every key is derivable; the agents only use their own."""
    return Ed25519PrivateKey.from_private_bytes(
        hashlib.sha256(f"{seed}|key|{name}".encode()).digest())


def public_hex(key: Ed25519PrivateKey) -> str:
    return key.public_key().public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw).hex()


def sign(key: Ed25519PrivateKey, text: str) -> str:
    return key.sign(text.encode("utf-8")).hex()


def signed_by(public: str, text: str, signature: str) -> bool:
    try:
        Ed25519PublicKey.from_public_bytes(bytes.fromhex(public)).verify(
            bytes.fromhex(signature), text.encode("utf-8"))
        return True
    except (InvalidSignature, ValueError):
        return False


# -- what a relay can do to a record in transit ----------------------------

def _respell(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return float(value)                     # 1600 -> 1600.0
    if isinstance(value, str):
        return unicodedata.normalize("NFD", value)
    if isinstance(value, list):
        return [_respell(v) for v in value]
    if isinstance(value, dict):
        return {k: _respell(v) for k, v in reversed(list(value.items()))}
    return value


def reencode(raw: str) -> str:
    """The same record in different bytes: member order reversed, text
    decomposed (NFD), non-ASCII escaped, whole numbers written with a
    decimal point, and indented. What any gateway written in another
    language may do without meaning harm."""
    data = json.loads(raw)
    data["content"] = _respell(data["content"])
    data = {k: data[k] for k in reversed(list(data))}
    data["owner"] = unicodedata.normalize("NFD", data["owner"])
    return json.dumps(data, indent=2, ensure_ascii=True)


def alter(raw: str, change: dict[str, Any]) -> str:
    """A different record: some content members replaced."""
    data = json.loads(raw)
    data["content"].update(change)
    return json.dumps(data, ensure_ascii=False)


# -- the store --------------------------------------------------------------

class _Ledger:
    """One in-process store of every record published in a run."""

    def __init__(self, engine):
        self.engine = engine
        self.store: dict[str, str] = {}
        self.log: list[str] = []
        self.rule_id: str | None = None
        # The registry: one public key per registered name, fixed before
        # anything runs, so nobody can enrol a key under another's name.
        self.keys = {a.name: public_hex(private_key(engine.spec.seed, a.name))
                     for a in engine.spec.agents}
        self.sigs: dict[str, dict[str, str]] = {}
        self._mine: dict[str, Ed25519PrivateKey] = {}

    def key_of(self, agent) -> Ed25519PrivateKey:
        """The agent's own private key; its public half goes in the trace
        the first time it is used."""
        if agent.name not in self._mine:
            self._mine[agent.name] = private_key(self.engine.spec.seed,
                                                 agent.name)
            self.engine.emit(agent.name, "dn_key", agent.name,
                             {"public": self.keys[agent.name]})
        return self._mine[agent.name]

    def identify(self, raw: str) -> str:
        raise NotImplementedError

    def publish(self, owner, content: dict[str, Any], parents=(),
                key: Ed25519PrivateKey | None = None) -> tuple[str, str]:
        """Publish a record. `owner` is an agent, which signs with its own
        key, or a name, in which case the record is signed with `key` if
        one is given and is otherwise unsigned. Nothing stops a name being
        someone else's: that is what the signature check is for."""
        if not isinstance(owner, str):
            key, owner = self.key_of(owner), owner.name
        raw = build(owner, content, parents)
        rid = self.identify(raw)
        if rid not in self.store:
            self.store[rid] = raw
            self.log.append(rid)
            detail = {"kind": content.get("kind", ""), "raw": raw}
            if key is not None:
                self.sigs[rid] = {"id": sign(key, rid),
                                  "bytes": sign(key, raw)}
                detail["sig"] = self.sigs[rid]
            self.engine.emit(owner, "dn_record", rid, detail)
        return rid, raw

    def signed(self, rid: str, received: str, how: str = "id") -> bool:
        """Did the record's named owner sign it? `how` is "id" (the
        signature over the record's identity) or "bytes" (the signature
        over the bytes it was published in, checked against the bytes that
        arrived)."""
        if rid not in self.store or rid not in self.sigs:
            return False
        public = self.keys.get(members(self.store[rid])["owner"])
        return public is not None and signed_by(
            public, rid if how == "id" else received, self.sigs[rid][how])

    def admit(self, raw: str) -> tuple[str | None, dict[str, Any] | None]:
        """Identify bytes that arrived in a message. Returns (None, None)
        if they are not a record, and (id, None) if they are a record
        nobody published."""
        try:
            rid = self.identify(raw)
        except (canon.Reject, ValueError):
            return None, None
        if rid not in self.store:
            return rid, None
        return rid, members(self.store[rid])

    def read(self, rid: str) -> dict[str, Any]:
        return members(self.store[rid])

    def rules(self) -> dict[str, int]:
        if self.rule_id is None:
            return {}
        return dict(self.read(self.rule_id)["content"]["rules"])

    # NandaTown's TownAPI.attest calls this on whatever data_facts plugin
    # is loaded; a receipt is one more record.
    def attest(self, observer: str, subject: str, claim: str,
               value: Any) -> str:
        return self.publish(observer, {"kind": "receipt", "subject": subject,
                                       "claim": claim,
                                       "value": str(value)})[0]


@register("data_facts", "dharma.records.v1")
class CanonicalRecords(_Ledger):
    """Records identified by canonical structure (dataset.v1)."""

    def identify(self, raw: str) -> str:
        return canonical_id(raw)


@register("data_facts", "dharma.records.town.v1")
class TownRecords(_Ledger):
    """Control: the same records identified by NandaTown's fingerprint."""

    def identify(self, raw: str) -> str:
        return town_id(raw)


IDENTIFY = {"dharma.records.v1": canonical_id,
            "dharma.records.town.v1": town_id}


# -- audit ------------------------------------------------------------------

def audit_signatures(published: dict[str, str], keys: dict[str, str],
                     sigs: dict[str, dict[str, str]]) -> dict[str, list[str]]:
    """Sort records by whether their named owner signed their identity."""
    out: dict[str, list[str]] = {"valid": [], "invalid": [], "unsigned": []}
    for rid, raw in published.items():
        try:
            owner = members(raw)["owner"]
        except (canon.Reject, ValueError):
            out["invalid"].append(rid)
            continue
        if rid not in sigs:
            out["unsigned"].append(rid)
        elif owner in keys and signed_by(keys[owner], rid, sigs[rid]["id"]):
            out["valid"].append(rid)
        else:
            out["invalid"].append(rid)
    return out


def audit(published: dict[str, str], identify) -> dict[str, Any]:
    """Recompute every record's identity and classify every parent edge.

    `published` maps the identity each record was published under to its
    text. Edge states: verified (the parent is published and recomputes to
    the identity named), failed (it is published but recomputes to
    something else), unresolved (nobody published it), malformed (the
    child itself is not a record), cyclic (a record among its own
    ancestors).
    """
    sound: dict[str, bool] = {}
    parents: dict[str, list[str]] = {}
    for rid, raw in published.items():
        try:
            sound[rid] = identify(raw) == rid
            parents[rid] = members(raw)["parents"]
        except (canon.Reject, ValueError):
            sound[rid] = False
            parents[rid] = None
    edges = {state: [] for state in EDGE_STATES}
    for rid, ps in parents.items():
        if ps is None:
            edges["malformed"].append((rid, ""))
            continue
        for p in ps:
            if p not in published:
                edges["unresolved"].append((rid, p))
            elif not sound[p]:
                edges["failed"].append((rid, p))
            else:
                edges["verified"].append((rid, p))
    # A cycle needs a record that names its own identity among its
    # ancestors, which a sound hash rules out; walk anyway and report.
    state: dict[str, int] = {}
    for start in parents:
        stack = [(start, iter(parents[start] or ()))]
        state.setdefault(start, 1)
        while stack:
            node, it = stack[-1]
            nxt = next(it, None)
            if nxt is None:
                state[node] = 2
                stack.pop()
            elif state.get(nxt) == 1:
                edges["cyclic"].append((node, nxt))
            elif nxt in parents and nxt not in state:
                state[nxt] = 1
                stack.append((nxt, iter(parents[nxt] or ())))
    return {"records": len(published),
            "unsound": sorted(r for r, ok in sound.items() if not ok),
            "edges": edges}


def lineage(published: dict[str, str], rid: str) -> list[tuple[int, str]]:
    """Every ancestor of a record, depth first, as (depth, identity)."""
    out, seen = [], set()

    def visit(node: str, depth: int) -> None:
        out.append((depth, node if node not in seen else node + " (above)"))
        if node in seen or node not in published:
            return
        seen.add(node)
        for p in members(published[node])["parents"]:
            visit(p, depth + 1)

    visit(rid, 0)
    return out

"""A local bridge between NandaTown's agent test and an A2A 1.0 endpoint
that needs an API key.

Why it exists. `nandatown test-agent --url` speaks A2A 0.3 (JSON-RPC
`message/send`, parts tagged with `kind`) and can only send credentials
written into the URL. An endpoint that speaks A2A 1.0 and wants a key in a
header stops it at the protocol-invocation stage. This bridge runs on your
own machine, answers Town in 0.3, and calls the endpoint in 1.0 with the
key.

    python tools/a2a_bridge.py --upstream https://AGENT-ENDPOINT
    nandatown test-agent --url http://127.0.0.1:8941 \\
        --path-profile a2a-capability-fulfillment@0.3

The key never appears in a URL, a command or a file. It is read when the
bridge starts, from the macOS keychain (service name `--keychain`) or, if
that is not available, from the environment variable named by `--key-env`.
It is sent only to the upstream host, and it is never printed or logged.

A result obtained through this bridge is a result for the agent plus this
bridge. Say so when you share it. Town's descriptor check sees the bridge's
card, not the agent's own.
"""
from __future__ import annotations

import argparse
import getpass
import json
import os
import subprocess
import sys
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit

import httpx

CARD_PATHS = ("/.well-known/agent-card.json", "/.well-known/agent.json")
STATES = {"TASK_STATE_SUBMITTED": "submitted", "TASK_STATE_WORKING": "working",
          "TASK_STATE_COMPLETED": "completed", "TASK_STATE_FAILED": "failed",
          "TASK_STATE_CANCELED": "canceled", "TASK_STATE_REJECTED": "rejected",
          "TASK_STATE_INPUT_REQUIRED": "input-required",
          "TASK_STATE_AUTH_REQUIRED": "auth-required"}
ROLES_UP = {"user": "ROLE_USER", "agent": "ROLE_AGENT"}
ROLES_DOWN = {v: k for k, v in ROLES_UP.items()}


class BridgeError(Exception):
    """Something the bridge could not do. The message never holds a secret."""


def read_key(service: str, env: str) -> str:
    """The API key, from the keychain or the environment. Never printed."""
    try:
        out = subprocess.run(
            ["security", "find-generic-password", "-a", getpass.getuser(),
             "-s", service, "-w"], capture_output=True, text=True, timeout=10)
        if out.returncode == 0 and out.stdout.strip():
            return out.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        pass
    key = os.environ.get(env, "").strip()
    if not key:
        raise BridgeError(
            f"no API key found: add one to the keychain as service {service!r}"
            f" or set the environment variable {env}")
    return key


# -- translation, kept free of I/O so it can be tested on its own ----------

def part_up(part: dict) -> dict:
    """A 0.3 part as a 1.0 part."""
    if part.get("kind") == "text":
        return {"text": part.get("text", ""), "mediaType": "text/plain"}
    if part.get("kind") == "data":
        return {"data": part.get("data")}
    raise BridgeError(f"cannot translate a 0.3 part of kind {part.get('kind')!r}")


def part_down(part: dict) -> dict:
    """A 1.0 part as a 0.3 part."""
    if "text" in part:
        return {"kind": "text", "text": part["text"]}
    if "data" in part:
        return {"kind": "data", "data": part["data"]}
    raise BridgeError("cannot translate a 1.0 part that is neither text nor data")


def request_up(request: dict) -> dict:
    """Town's 0.3 `message/send` as a 1.0 `SendMessage`."""
    if request.get("method") != "message/send":
        raise BridgeError(f"method {request.get('method')!r} is not bridged;"
                          " only message/send is")
    message = (request.get("params") or {}).get("message") or {}
    return {"jsonrpc": "2.0", "id": request.get("id", 1),
            "method": "SendMessage",
            "params": {"message": {
                "role": ROLES_UP.get(message.get("role"), "ROLE_USER"),
                "messageId": message.get("messageId") or "m-" + uuid.uuid4().hex[:8],
                "parts": [part_up(p) for p in message.get("parts", [])]}}}


def message_down(message: dict) -> dict:
    return {"kind": "message",
            "role": ROLES_DOWN.get(message.get("role"), "agent"),
            "messageId": message.get("messageId", ""),
            "parts": [part_down(p) for p in message.get("parts", [])]}


def result_down(result: dict) -> dict:
    """A 1.0 `SendMessage` result as a 0.3 result.

    1.0 wraps the result as {"task": ...} or {"message": ...}. A bare task
    is accepted too. A reply that is a message stays a message: the bridge
    does not dress it up as a completed task.
    """
    if isinstance(result.get("message"), dict) and "task" not in result:
        return message_down(result["message"])
    task = result.get("task") if isinstance(result.get("task"), dict) else result
    status = dict(task.get("status") or {})
    status["state"] = STATES.get(status.get("state"), status.get("state"))
    if isinstance(status.get("message"), dict):
        status["message"] = message_down(status["message"])
    out = {"kind": "task", "id": task.get("id", ""),
           "contextId": task.get("contextId", ""), "status": status,
           "artifacts": [{"artifactId": a.get("artifactId", ""),
                          **({"name": a["name"]} if "name" in a else {}),
                          "parts": [part_down(p) for p in a.get("parts", [])]}
                         for a in task.get("artifacts") or []]}
    return out


def card_down(card: dict, own_url: str) -> dict:
    """The upstream card restated as a 0.3 card that points at the bridge."""
    out = {k: card[k] for k in ("name", "description", "version", "skills",
                                "defaultInputModes", "defaultOutputModes",
                                "capabilities", "provider") if k in card}
    out.setdefault("defaultInputModes", ["text/plain"])
    out.setdefault("defaultOutputModes", ["text/plain"])
    out.update(protocolVersion="0.3.0", url=own_url, preferredTransport="JSONRPC")
    return out


def rpc_url(card: dict, upstream: str) -> str:
    """Where the upstream takes JSON-RPC: the card's 1.0 interface if it
    names one, else its 0.3 `url`, else the upstream address itself."""
    for face in card.get("supportedInterfaces") or []:
        if str(face.get("protocolBinding", "")).upper() == "JSONRPC" and face.get("url"):
            return face["url"]
    return card.get("url") or upstream


def same_host(a: str, b: str) -> bool:
    return urlsplit(a).hostname == urlsplit(b).hostname and bool(urlsplit(a).hostname)


# -- the server --------------------------------------------------------------

class Bridge:
    def __init__(self, args, key: str):
        self.upstream = args.upstream.rstrip("/")
        self.own_url = f"http://{args.host}:{args.port}"
        self.version = args.upstream_version
        value = key if args.auth_scheme == "none" else f"{args.auth_scheme} {key}"
        self.auth = {args.auth_header: value}
        self.http = httpx.Client(timeout=args.timeout, follow_redirects=False)
        self.card = None

    def upstream_card(self) -> dict:
        if self.card is None:
            for path in CARD_PATHS:
                # The card is fetched without the key first: Town could read
                # it without one, and a key is not sent where it is not needed.
                r = self.http.get(self.upstream + path)
                if r.status_code in (401, 403):
                    r = self.http.get(self.upstream + path, headers=self.auth)
                if r.status_code == 200:
                    self.card = r.json()
                    break
            else:
                raise BridgeError("the upstream served no agent card")
        return self.card

    def send(self, request: dict) -> dict:
        target = rpc_url(self.upstream_card(), self.upstream)
        if not same_host(target, self.upstream):
            raise BridgeError("the card names a different host for JSON-RPC;"
                              " the key is not sent there")
        r = self.http.post(target, json=request_up(request),
                           headers={**self.auth, "A2A-Version": self.version})
        if r.status_code in (401, 403):
            raise BridgeError(f"the upstream refused the key (HTTP {r.status_code});"
                              " check --auth-header and --auth-scheme")
        if not 200 <= r.status_code < 300:
            raise BridgeError(f"the upstream answered HTTP {r.status_code}")
        reply = r.json()
        if "error" in reply:
            err = reply["error"] if isinstance(reply["error"], dict) else {}
            return {"jsonrpc": "2.0", "id": request.get("id", 1),
                    "error": {"code": err.get("code", -32000),
                              "message": str(err.get("message", "upstream error"))}}
        return {"jsonrpc": "2.0", "id": request.get("id", 1),
                "result": result_down(reply.get("result") or {})}


def handler_for(bridge: Bridge):
    class Handler(BaseHTTPRequestHandler):
        def _json(self, status: int, body: dict) -> None:
            data = json.dumps(body).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            if self.path in CARD_PATHS:
                try:
                    self._json(200, card_down(bridge.upstream_card(), bridge.own_url))
                except (BridgeError, httpx.HTTPError, ValueError) as exc:
                    self._json(502, {"error": _safe(exc)})
            else:
                self._json(404, {"error": "not found"})

        def do_POST(self):
            try:
                length = int(self.headers.get("Content-Length") or 0)
                request = json.loads(self.rfile.read(length) or b"{}")
                self._json(200, bridge.send(request))
            except BridgeError as exc:
                self._json(200, {"jsonrpc": "2.0", "id": 1,
                                 "error": {"code": -32000, "message": str(exc)}})
            except (httpx.HTTPError, ValueError) as exc:
                self._json(200, {"jsonrpc": "2.0", "id": 1,
                                 "error": {"code": -32000, "message": _safe(exc)}})

        def log_message(self, fmt, *args):       # one quiet line, no bodies
            sys.stderr.write(f"bridge: {self.command} {self.path} -> {args[1]}\n")
    return Handler


def _safe(exc: Exception) -> str:
    """An error's kind without its text, which could repeat a header."""
    return exc.__class__.__name__ if not isinstance(exc, BridgeError) else str(exc)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--upstream", required=True,
                   help="the agent's address, as listed for it (no key in it)")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8941)
    p.add_argument("--upstream-version", default="1.0",
                   help="value of the A2A-Version header sent upstream")
    p.add_argument("--auth-header", default="Authorization",
                   help="name of the header that carries the key")
    p.add_argument("--auth-scheme", default="Bearer",
                   help="word before the key in that header; 'none' for the key alone")
    p.add_argument("--keychain", default="a2a-bridge-key",
                   help="macOS keychain service name holding the key")
    p.add_argument("--key-env", default="A2A_BRIDGE_KEY",
                   help="environment variable used if the keychain has no key")
    p.add_argument("--timeout", type=float, default=60.0)
    args = p.parse_args()
    if urlsplit(args.upstream).username or "?" in args.upstream:
        sys.exit("bridge: keep credentials out of --upstream; the key is read"
                 " from the keychain")
    if args.host not in ("127.0.0.1", "localhost", "::1"):
        sys.exit("bridge: it listens on this machine only")
    try:
        bridge = Bridge(args, read_key(args.keychain, args.key_env))
    except BridgeError as exc:
        sys.exit(f"bridge: {exc}")
    print(f"bridge: http://{args.host}:{args.port} -> {args.upstream}"
          f" (A2A {args.upstream_version}, key in header {args.auth_header})")
    ThreadingHTTPServer((args.host, args.port), handler_for(bridge)).serve_forever()


if __name__ == "__main__":
    main()

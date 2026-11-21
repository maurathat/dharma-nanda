# Tools

## `a2a_bridge.py`: test a keyed A2A 1.0 agent with NandaTown

`nandatown test-agent --url` speaks A2A 0.3 and can only send credentials
written into the URL. Pointed at an agent endpoint that speaks A2A 1.0 and
wants an API key in a header, it passes resolution and card retrieval and
stops at protocol invocation (2 of 6 stages). This bridge runs on your own
machine, answers Town in 0.3, and calls the endpoint in 1.0 with the key.

Store the key once, in the macOS keychain. The command asks for it without
showing it:

```
security add-generic-password -a "$USER" -s a2a-bridge-key -w
```

Then, in one terminal:

```
.venv/bin/python tools/a2a_bridge.py --upstream https://YOUR-AGENT-ADDRESS
```

and in another, from your NandaTown checkout:

```
nandatown test-agent --url http://127.0.0.1:8941 --path-profile a2a-capability-fulfillment@0.3
```

If the endpoint refuses the key, it expects it in a different header. Two
common forms:

```
--auth-header Authorization --auth-scheme Bearer     (the default)
--auth-header X-API-Key --auth-scheme none
```

What it does and does not do:

- The key is never in a URL, a command or a file, is sent only to the
  upstream host, and is never printed. Town's evidence holds the bridge's
  address, not the key.
- It bridges `message/send` only, with text and data parts.
- A reply that is a message stays a message. The bridge does not turn it
  into a completed task, so Town's verdict on the agent's reply is real.
- A result through the bridge is a result for the agent plus this bridge.
  Town's descriptor check sees the bridge's card, not the agent's own.

Checked on 20 November 2026 against a stand-in A2A 1.0 endpoint written from
the A2A 1.0 change notes: Town alone reached 2 of 6 stages (HTTP 401);
through the bridge 5 of 6 passed and the sixth, the descriptor pin, was not
exercised. It has not been run against a real third-party endpoint.

## `dharma_monitor.py`: play in NANDA Market

NANDA Market (github.com/klutometis/nandablox, the Roblox town) lets outside
code take the **monitor** slot: it sends the open cases, new stalls that
might be frauds, to `POST /decide` and takes allow, block or escalate for
each. This monitor brings three things from the Dharma Nanda town:

- **A ladder with memory.** 2 strikes for a bad signature, 1 for a block on
  clear evidence; at 3 a stall is blocked on sight.
- **A budget for the human.** At most 2 cases are escalated every 30 seconds
  (`--budget`, `--window`). Over that it decides the case itself and gives
  no strike, because being busy is not evidence.
- **A signed record of every verdict,** identified by canonical structure and
  linked to the previous verdict on the same stall.

Try it against the market's own gateway on your laptop, from a checkout of
nandablox (two terminals):

```
harness/run.sh --no-llm --allow-localhost
```

```
export SLOT_TOKEN=pick-a-long-secret
.venv/bin/python tools/dharma_monitor.py
curl -s -X POST http://127.0.0.1:8790/v1/monitors -d '{"name":"dharma","url":"http://localhost:8801","token":"'$SLOT_TOKEN'"}'
curl -s -X POST http://127.0.0.1:8790/v1/tick -d @PATH-TO-NANDABLOX/harness/starter/tick.json
```

Then ask why a stall was treated as it was. Every record's identity is
recomputed and its signature checked:

```
.venv/bin/python tools/dharma_monitor.py --why "Cheap Cloth Co"
```

For the live market, follow nandablox's `harness/starter/README.md`: put the
monitor behind an https tunnel and register that address with the
registration token the organisers give out.

Checked on 20 November 2026 against nandablox's gateway at `af9606a`, run
locally with its sample cases: it answered in about 10 ms (the limit is 800)
and differed from the built-in monitor on one case of four, allowing an
established, well-rated seller the built-in escalated. Not run in the live
Roblox market.

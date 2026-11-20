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

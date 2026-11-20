"""The bridge's translation between A2A 0.3 and 1.0, checked without a network."""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import a2a_bridge as b  # noqa: E402

TOWN_REQUEST = {"jsonrpc": "2.0", "id": 1, "method": "message/send",
                "params": {"message": {"role": "user", "messageId": "m-1",
                                       "parts": [{"kind": "text", "text": "{}"}]}}}


def test_request_goes_up_as_send_message():
    up = b.request_up(TOWN_REQUEST)
    assert up["method"] == "SendMessage"
    message = up["params"]["message"]
    assert message["role"] == "ROLE_USER" and message["messageId"] == "m-1"
    assert message["parts"] == [{"text": "{}", "mediaType": "text/plain"}]


def test_other_methods_are_refused_not_guessed():
    with pytest.raises(b.BridgeError):
        b.request_up({"method": "tasks/get"})


def test_task_comes_down_with_plain_state_and_kinds():
    task = {"id": "t1", "contextId": "c1",
            "status": {"state": "TASK_STATE_COMPLETED"},
            "artifacts": [{"artifactId": "a1", "parts": [{"text": "x"}]}]}
    for result in ({"task": task}, task):          # wrapped, and bare
        down = b.result_down(result)
        assert down["kind"] == "task" and down["status"]["state"] == "completed"
        assert down["artifacts"][0]["parts"] == [{"kind": "text", "text": "x"}]


def test_a_message_reply_is_not_dressed_up_as_a_task():
    down = b.result_down({"message": {"role": "ROLE_AGENT", "messageId": "m",
                                      "parts": [{"text": "hello"}]}})
    assert down["kind"] == "message" and down["role"] == "agent"


def test_card_points_at_the_bridge_and_names_no_upstream_address():
    card = {"name": "a", "version": "1", "skills": [{"id": "q"}],
            "supportedInterfaces": [{"url": "https://up.example/a2a",
                                     "protocolBinding": "JSONRPC",
                                     "protocolVersion": "1.0"}]}
    down = b.card_down(card, "http://127.0.0.1:8941")
    assert down["url"] == "http://127.0.0.1:8941"
    assert "up.example" not in str(down) and down["defaultInputModes"]
    assert b.rpc_url(card, "https://up.example") == "https://up.example/a2a"


def test_key_is_only_for_the_upstream_host():
    assert b.same_host("https://up.example/a2a", "https://up.example")
    assert not b.same_host("https://evil.example/a2a", "https://up.example")

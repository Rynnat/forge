import json
import subprocess
from types import SimpleNamespace

import pytest

from makale_okuyucu.llm import (ClaudeCLIBackend, JSONParseError, LLMError, MockBackend, call_json,
                                parse_json_response)


def _proc(stdout, rc=0, stderr=""):
    return SimpleNamespace(returncode=rc, stdout=stdout, stderr=stderr)


def _ok(result, cost=0.001):
    return json.dumps({"subtype": "success", "is_error": False, "result": result, "total_cost_usd": cost,
                       "usage": {"input_tokens": 5, "output_tokens": 7, "cache_creation_input_tokens": 600,
                                 "cache_read_input_tokens": 0}})


def test_cli_flags_and_stdin(cfg):
    seen = {}

    def runner(args, **kw):
        seen["args"], seen["kw"] = args, kw
        return _proc(_ok('{"a":1}'))

    be = ClaudeCLIBackend(cfg, runner=runner, sleep=lambda s: None)
    big = "x" * 60000
    res = be.complete(big, system="SYS", purpose="t")
    a = seen["args"]
    for flag in ("-p", "--strict-mcp-config", "--no-session-persistence"):
        assert flag in a
    assert a[a.index("--tools") + 1] == ""
    assert a[a.index("--setting-sources") + 1] == ""
    assert a[a.index("--system-prompt") + 1] == "SYS"
    assert a[a.index("--model") + 1] == "haiku"
    assert big not in a and seen["kw"]["input"] == big
    assert "llm_cwd" in seen["kw"]["cwd"]
    assert "CLAUDECODE" not in seen["kw"]["env"]
    assert res.cost_usd == 0.001 and res.cache_write_tokens == 600
    assert be.stats.ok == 1 and be.stats.input_tokens == 5


def test_cli_retries_then_fails(cfg):
    calls = []

    def runner(args, **kw):
        calls.append(1)
        if len(calls) == 1:
            raise subprocess.TimeoutExpired(args, 1)
        if len(calls) == 2:
            return _proc("", rc=1, stderr="boom")
        return _proc(json.dumps({"subtype": "error", "is_error": True, "result": "x"}))

    be = ClaudeCLIBackend(cfg, runner=runner, sleep=lambda s: None)
    with pytest.raises(LLMError):
        be.complete("p")
    assert len(calls) == 3 and be.stats.failed == 1


def test_cli_missing_exe(cfg):
    def runner(args, **kw):
        raise FileNotFoundError("nope")

    be = ClaudeCLIBackend(cfg, runner=runner, sleep=lambda s: None)
    with pytest.raises(LLMError):
        be.complete("p")


def test_parse_json_variants():
    assert parse_json_response('```json\n{"a": 1}\n```') == {"a": 1}
    assert parse_json_response('Here you go: {"a": [1,2]} thanks') == {"a": [1, 2]}
    with pytest.raises(JSONParseError):
        parse_json_response("no json here")


def test_call_json_retry_then_parse_fail(cfg):
    be = MockBackend(cfg, responder=["not json", '{"ok": true}'])
    assert call_json(be, "p", "t")[:2] == ({"ok": True}, "OK")
    be2 = MockBackend(cfg, responder=["nope", "still nope"])
    obj, st, err = call_json(be2, "p", "t")
    assert (obj, st) == (None, "PARSE_FAIL") and err
    be3 = MockBackend(cfg, responder=lambda p, s: LLMError("down"))
    assert call_json(be3, "p", "t")[1] == "LLM_ERROR"


def test_recorder_called(cfg):
    rec = []
    be = MockBackend(cfg, recorder=lambda *a: rec.append(a), responder=['{"x":1}'])
    be.complete("p", purpose="z")
    assert rec and rec[0][1] == "z" and rec[0][2] is True

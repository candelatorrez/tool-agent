from types import SimpleNamespace

from agent.loop import run_agent

class Msg: 
    def __init__(self, content=None, tool_calls=None):
        self.content, self.tool_calls = content, tool_calls

    def model_dump(self, **kw):
        d = {"role": "assistant", "content": self.content}
        if self.tool_calls:
            d["tool_calls"] = [
                {"id": c.id, "type": "function",
                 "function": {"name": c.function.name,
                              "arguments": c.function.arguments}}
                for c in self.tool_calls
            ]
        return d

def fake_client(messages):
    it = iter(messages)
    create = lambda **kw: SimpleNamespace(choices=[SimpleNamespace(message=next(it))])
    return SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))

def tool_call(name, args):
    return SimpleNamespace(id="1", function=SimpleNamespace(name=name, arguments=args))

def test_uses_tool_then_answers():
    client = fake_client([
        Msg(tool_calls=[tool_call("add", '{"a": 2, "b": 3}')]),
        Msg(content="Son 5"),
    ])
    out = run_agent("sumá", client, "m", {"add": lambda a, b: a + b}, [],
                    on_event=lambda *_: None)
    assert out == "Son 5"

def test_stops_at_max_steps():
    client = fake_client([Msg(tool_calls=[tool_call("add", '{"a":1,"b":1}')])] * 3)
    out = run_agent("x", client, "m", {"add": lambda a, b: a + b}, [],
                    max_steps=3, on_event=lambda *_: None)
    assert "máximo" in out

def test_unknown_tool_does_not_crash():
    client = fake_client([Msg(tool_calls=[tool_call("nope", "{}")]), Msg(content="ok")])
    assert run_agent("x", client, "m", {}, [], on_event=lambda *_: None) == "ok"
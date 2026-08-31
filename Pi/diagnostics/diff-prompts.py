#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.9"
# dependencies = ["jinja2"]
# ///
"""Diff two captured chat-completion payloads the way llama.cpp sees them.

Renders each through the real chat template, reports the first differing byte,
and attributes it to a field (tool ordering, tool set, system prompt, messages).

  uv run diff-prompts.py captures/003-*.json captures/007-*.json

The PEP 723 block above pulls jinja2 in on its own, so `uv run` needs no venv. Plain
`python3 diff-prompts.py` works too where jinja2 is already installed.

Set PROMPT_TEMPLATE to the chat template the server is actually serving. Without it
the rendered-prompt section is skipped and only the payload fields are compared --
still enough to attribute a divergence, just without the byte offset.
"""
import json, os, sys
import jinja2

TEMPLATE = os.environ.get("PROMPT_TEMPLATE")

env = jinja2.Environment(loader=jinja2.BaseLoader())
env.globals["raise_exception"] = lambda m: (_ for _ in ()).throw(RuntimeError(m))
tpl = env.from_string(open(TEMPLATE).read()) if TEMPLATE else None


def render(payload):
    assert tpl is not None  # callers guard on tpl; this is for the type checker
    kw = dict(payload.get("chat_template_kwargs") or {})
    if payload.get("tools"):
        kw["tools"] = payload["tools"]
    return tpl.render(messages=payload["messages"], add_generation_prompt=True, **kw)


def first_diff(a, b):
    for i, (x, y) in enumerate(zip(a, b)):
        if x != y:
            return i
    return min(len(a), len(b)) if len(a) != len(b) else -1


def tool_names(p):
    return [t.get("function", {}).get("name") or t.get("custom", {}).get("name") for t in p.get("tools") or []]


def main(pa, pb):
    a, b = json.load(open(pa)), json.load(open(pb))
    at, bt = tool_names(a), tool_names(b)
    ra = rb = None
    if tpl:
        ra, rb = render(a), render(b)

    size = lambda r: f" rendered={len(r)}ch" if r is not None else ""
    print(f"A: {pa}\n   model={a.get('model')} msgs={len(a['messages'])} tools={len(at)}{size(ra)}")
    print(f"B: {pb}\n   model={b.get('model')} msgs={len(b['messages'])} tools={len(bt)}{size(rb)}")
    print()

    print("== chat_template_kwargs ==")
    ka, kb = a.get("chat_template_kwargs") or {}, b.get("chat_template_kwargs") or {}
    print(f"  A: {json.dumps(ka, sort_keys=True)}")
    print(f"  B: {json.dumps(kb, sort_keys=True)}")
    print(f"  {'identical' if ka == kb else '*** DIFFER ***'}")
    print()

    print("== tools ==")
    if at == bt:
        print(f"  identical: same {len(at)} tools in the same order")
    else:
        sa, sb = set(at), set(bt)
        if sa == sb:
            print(f"  SAME SET, DIFFERENT ORDER — this alone destroys the prefix")
            for i, (x, y) in enumerate(zip(at, bt)):
                if x != y:
                    print(f"  first order difference at index {i}: A={x!r} B={y!r}")
                    break
        else:
            print(f"  A only: {sorted(sa - sb)}")
            print(f"  B only: {sorted(sb - sa)}")
            for i, (x, y) in enumerate(zip(at, bt)):
                if x != y:
                    print(f"  first difference at index {i}: A={x!r} B={y!r}")
                    break
    print()

    print("== system prompt (message 0) ==")
    ca = a["messages"][0].get("content") if a["messages"] else None
    cb = b["messages"][0].get("content") if b["messages"] else None
    if isinstance(ca, str) and isinstance(cb, str):
        if ca == cb:
            print(f"  identical ({len(ca)} chars)")
        else:
            d = first_diff(ca, cb)
            print(f"  differ at char {d} of {len(ca)}/{len(cb)}")
            print(f"    A: {ca[d:d+160]!r}")
            print(f"    B: {cb[d:d+160]!r}")
            print("  context before:")
            print(f"    {ca[max(0,d-160):d]!r}")
    else:
        print(f"  non-string content: {type(ca).__name__}/{type(cb).__name__}")
    print()

    print("== rendered prompt ==")
    if ra is None or rb is None:
        print("  skipped -- set PROMPT_TEMPLATE to the served chat template for byte offsets")
        return
    d = first_diff(ra, rb)
    if d == -1:
        print("  IDENTICAL — these two prompts share a full prefix")
        return
    pct = 100 * d / min(len(ra), len(rb))
    print(f"  first differing byte at {d} ({pct:.2f}% of the shorter prompt)")
    print(f"  shared prefix ends inside: ...{ra[max(0,d-200):d]!r}")
    print(f"    A continues: {ra[d:d+200]!r}")
    print(f"    B continues: {rb[d:d+200]!r}")
    print()
    print("  (rough token estimate of shared prefix: ~{:d})".format(d // 4))


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])

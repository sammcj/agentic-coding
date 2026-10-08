"""A YAML subset parser, enough for OpenSpec's `.openspec.yaml`, `config.yaml` and `schema.yaml`.

The stdlib has no YAML parser and these files use a small, predictable subset: block mappings,
block sequences (including `- key: value` items), plain and quoted scalars, flow sequences, and
`|` / `>` block scalars. Anchors, tags, multi-document streams and nested flow collections are
not supported; a file using them fails with `YamlError` and callers treat it as unreadable.
"""

from __future__ import annotations

import re
from typing import Any


class YamlError(ValueError):
    pass


_INT_RE = re.compile(r"^[-+]?\d+$")
_ESCAPE_RE = re.compile(r"\\(u[0-9a-fA-F]{4}|.)")
_ESCAPES = {"n": "\n", "t": "\t", "r": "\r", "0": "\0", '"': '"', "\\": "\\", "/": "/", " ": " "}


def _unescape(m: re.Match[str]) -> str:
    seq = m.group(1)
    if seq.startswith("u") and len(seq) == 5:
        return chr(int(seq[1:], 16))
    return _ESCAPES.get(seq, "\\" + seq)


def loads(text: str) -> Any:
    return _Parser(text).parse()


class _Parser:
    def __init__(self, text: str) -> None:
        self.raw = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
        # Mutable (indent, content) view; `- key: v` items rewrite their line in place.
        self.lines: list[tuple[int, str]] = [(_indent(line), line.strip()) for line in self.raw]
        self.i = 0

    def parse(self) -> Any:
        self._skip()
        if self.i >= len(self.lines):
            return None
        value = self._block()
        self._skip()
        if self.i < len(self.lines):
            raise YamlError(f"unexpected content at line {self.i + 1}")
        return value

    def _skip(self) -> None:
        while self.i < len(self.lines):
            _, content = self.lines[self.i]
            if content and not content.startswith("#") and content not in ("---", "..."):
                return
            self.i += 1

    def _peek(self) -> tuple[int, str] | None:
        self._skip()
        return self.lines[self.i] if self.i < len(self.lines) else None

    def _block(self) -> Any:
        nxt = self._peek()
        if nxt is None:
            return None
        if _is_seq_item(nxt[1]):
            return self._seq(nxt[0])
        if _split_key(nxt[1]) is not None:
            return self._map(nxt[0])
        self.i += 1
        return _scalar(nxt[1])

    def _map(self, indent: int) -> dict[str, Any]:
        out: dict[str, Any] = {}
        while (nxt := self._peek()) is not None and nxt[0] == indent and not _is_seq_item(nxt[1]):
            kv = _split_key(nxt[1])
            if kv is None:
                raise YamlError(f"expected 'key: value' at line {self.i + 1}")
            key, rest = kv
            self.i += 1
            out[key] = self._value(indent, rest, allow_same_indent_seq=True)
        if nxt is not None and nxt[0] > indent:
            raise YamlError(f"bad indentation at line {self.i + 1}")
        return out

    def _seq(self, indent: int) -> list[Any]:
        out: list[Any] = []
        while (nxt := self._peek()) is not None and nxt[0] == indent and _is_seq_item(nxt[1]):
            content = nxt[1]
            rest = content[1:].lstrip()
            if rest and _split_key(rest) is not None and not rest.startswith(("'", '"', "[", "{")):
                # `- key: value` opens a mapping whose keys align with `key`.
                self.lines[self.i] = (indent + len(content) - len(rest), rest)
                out.append(self._map(self.lines[self.i][0]))
                continue
            self.i += 1
            out.append(self._value(indent, rest, allow_same_indent_seq=False))
        return out

    def _value(self, indent: int, rest: str, *, allow_same_indent_seq: bool) -> Any:
        rest = _strip_comment(rest)
        if rest.startswith(("|", ">")):
            return self._block_scalar(indent, rest)
        if rest:
            return _scalar(rest)
        nxt = self._peek()
        if nxt is None:
            return None
        if nxt[0] > indent:
            return self._block()
        if allow_same_indent_seq and nxt[0] == indent and _is_seq_item(nxt[1]):
            return self._seq(indent)
        return None

    def _block_scalar(self, indent: int, header: str) -> str:
        style, chomp = header[0], ""
        for ch in header[1:]:
            if ch in "+-":
                chomp = ch
        body: list[str] = []
        block_indent: int | None = None
        while self.i < len(self.raw):
            line = self.raw[self.i]
            if line.strip() == "":
                body.append("")
                self.i += 1
                continue
            ind = _indent(line)
            if ind <= indent:
                break
            if block_indent is None:
                block_indent = ind
            if ind < block_indent:
                break
            body.append(line[block_indent:])
            self.i += 1
        # Trailing blank lines belong to chomping, not to the next key.
        trailing = 0
        while body and body[-1] == "":
            body.pop()
            trailing += 1
        text = "\n".join(body) if style == "|" else _fold(body)
        if not body:
            return ""
        if chomp == "-":
            return text
        if chomp == "+":
            return text + "\n" * (trailing + 1)
        return text + "\n"


def _indent(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _is_seq_item(content: str) -> bool:
    return content == "-" or content.startswith("- ")


def _split_key(content: str) -> tuple[str, str] | None:
    if content.startswith(("'", '"')):
        q = content[0]
        end = content.find(q, 1)
        if end == -1 or not content[end + 1 :].startswith(":"):
            return None
        rest = content[end + 2 :]
        if rest and not rest.startswith(" "):
            return None
        return content[1:end], rest.strip()
    m = re.match(r"^([^\s#'\"\[\]{},][^:#]*?)\s*:(?:\s+|$)(.*)$", content)
    if not m:
        return None
    return m.group(1).strip(), m.group(2).strip()


def _strip_comment(s: str) -> str:
    if not s or s[0] in "'\"":
        return s.strip()
    in_flow = 0
    for idx, ch in enumerate(s):
        if ch in "[{":
            in_flow += 1
        elif ch in "]}":
            in_flow -= 1
        elif ch == "#" and (idx == 0 or s[idx - 1] in " \t") and in_flow == 0:
            return s[:idx].strip()
    return s.strip()


def _scalar(s: str) -> Any:
    s = _strip_comment(s)
    if not s:
        return None
    if s[0] == '"':
        end = s.rfind('"')
        if end <= 0:
            raise YamlError(f"unterminated string: {s}")
        return _ESCAPE_RE.sub(_unescape, s[1:end])
    if s[0] == "'":
        end = s.rfind("'")
        if end <= 0:
            raise YamlError(f"unterminated string: {s}")
        return s[1:end].replace("''", "'")
    if s[0] == "[":
        if not s.endswith("]"):
            raise YamlError(f"unterminated flow sequence: {s}")
        inner = s[1:-1].strip()
        return [_scalar(part) for part in _split_flow(inner)] if inner else []
    if s[0] == "{":
        if not s.endswith("}"):
            raise YamlError(f"unterminated flow mapping: {s}")
        out: dict[str, Any] = {}
        for part in _split_flow(s[1:-1].strip()):
            kv = _split_key(part) if ":" in part else None
            if kv is None:
                raise YamlError(f"bad flow mapping entry: {part}")
            out[kv[0]] = _scalar(kv[1])
        return out
    if s in ("null", "~", "Null", "NULL"):
        return None
    if s in ("true", "True", "TRUE"):
        return True
    if s in ("false", "False", "FALSE"):
        return False
    if _INT_RE.match(s):
        return int(s)
    return s


def _split_flow(s: str) -> list[str]:
    parts: list[str] = []
    buf: list[str] = []
    quote = ""
    for ch in s:
        if quote:
            buf.append(ch)
            if ch == quote:
                quote = ""
        elif ch in "'\"":
            quote = ch
            buf.append(ch)
        elif ch == ",":
            parts.append("".join(buf).strip())
            buf = []
        else:
            buf.append(ch)
    tail = "".join(buf).strip()
    if tail:
        parts.append(tail)
    return parts


def _fold(lines: list[str]) -> str:
    out: list[str] = []
    para: list[str] = []
    for line in lines:
        if line == "":
            if para:
                out.append(" ".join(para))
                para = []
            out.append("")
        elif line.startswith((" ", "\t")):
            # More-indented lines keep their breaks under folding.
            if para:
                out.append(" ".join(para))
                para = []
            out.append(line)
        else:
            para.append(line)
    if para:
        out.append(" ".join(para))
    text = "\n".join(out)
    return re.sub(r"\n\n", "\n", text)

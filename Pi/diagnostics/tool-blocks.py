"""Print both captures' full tool arrays side by side, grouped into contiguous runs.

Extension tools register in blocks, so a reordering shows up as whole blocks moving.
This makes it obvious whether the difference is block-level (extension load order) or
interleaved (something stranger).

  python3 tool-blocks.py captures/003-*.json captures/007-*.json
"""
import json, sys


def load(path):
    p = json.load(open(path))
    names = []
    for t in p.get("tools") or []:
        names.append((t.get("function") or {}).get("name") or (t.get("custom") or {}).get("name"))
    return p, names


def main(pa, pb):
    pa_j, a = load(pa)
    pb_j, b = load(pb)

    print(f"{'idx':>3}  {'A':<28} {'B':<28} match")
    print("-" * 70)
    for i in range(max(len(a), len(b))):
        x = a[i] if i < len(a) else ""
        y = b[i] if i < len(b) else ""
        mark = "" if x == y else "  <-- differs"
        print(f"{i:>3}  {x:<28} {y:<28}{mark}")

    print()
    print("== where each tool sits in the other array ==")
    pos_b = {n: i for i, n in enumerate(b)}
    moved = [(i, n, pos_b.get(n)) for i, n in enumerate(a) if pos_b.get(n) != i]
    if not moved:
        print("  every shared tool is at the same index")
    else:
        print(f"  {len(moved)} of {len(a)} tools sit at a different index in B:")
        for i, n, j in moved[:25]:
            print(f"    A[{i}] {n!r} -> B[{j}]")
        if len(moved) > 25:
            print(f"    ... and {len(moved) - 25} more")

    print()
    print("== contiguous runs preserved from A in B ==")
    # A run is a maximal stretch of A whose tools appear consecutively, in order, in B.
    runs, start = [], 0
    for i in range(1, len(a) + 1):
        broke = i == len(a)
        if not broke:
            pi_, pj = pos_b.get(a[i - 1]), pos_b.get(a[i])
            broke = pi_ is None or pj is None or pj != pi_ + 1
        if broke:
            runs.append((start, i - 1))
            start = i
    for s, e in runs:
        where = pos_b.get(a[s])
        print(f"  A[{s}..{e}] ({e - s + 1:>2} tools) -> B[{where}]  starts with {a[s]!r}")

    print()
    print("== payload fields that might identify the source session ==")
    for key in ("model", "temperature", "top_p", "max_tokens", "stream", "seed"):
        va, vb = pa_j.get(key), pb_j.get(key)
        if va != vb:
            print(f"  {key}: A={va!r}  B={vb!r}   <-- differs")
    extra_a = set(pa_j) - set(pb_j)
    extra_b = set(pb_j) - set(pa_j)
    if extra_a or extra_b:
        print(f"  keys only in A: {sorted(extra_a) or '(none)'}")
        print(f"  keys only in B: {sorted(extra_b) or '(none)'}")
    print(f"  A messages: {[m.get('role') for m in pa_j['messages']]}")
    print(f"  B messages: {[m.get('role') for m in pb_j['messages']]}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])

"""Apply edits to questions in data/src/*.json, then rewrite the files in a tidy layout.

Run:  python3 build/patch.py edits.json
edits.json maps the start of a question's text to the fields to replace, e.g.
  {"Cyanide is lethal because it:": {"w": ["...", "...", "..."]}}
Each key must match exactly one question. With no argument, just reformats the files.
"""
import glob, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def dump(items):
    one = lambda o: json.dumps(o, ensure_ascii=False, separators=(",", ":"))
    out = []
    for it in items:
        if "passage" in it:
            head = {k: v for k, v in it.items() if k != "qs"}
            body = one(head)[:-1] + ',\n "qs":[\n' + ",\n".join("  " + one(q) for q in it["qs"]) + "\n ]}"
            out.append(body)
        else:
            out.append(one(it))
    return "[\n" + ",\n".join(out) + "\n]\n"


def main():
    edits = json.load(open(sys.argv[1], encoding="utf-8")) if len(sys.argv) > 1 else {}
    hits = {k: 0 for k in edits}
    for f in sorted(glob.glob(os.path.join(ROOT, "data", "src", "*.json"))):
        items = json.load(open(f, encoding="utf-8"))
        for it in items:
            for q in (it["qs"] if "passage" in it else [it]):
                for k, v in edits.items():
                    if q["q"].startswith(k):
                        q.update(v)
                        hits[k] += 1
        open(f, "w", encoding="utf-8").write(dump(items))
    bad = {k: n for k, n in hits.items() if n != 1}
    if bad:
        sys.exit(f"Keys that did not match exactly one question: {bad}")
    print(f"Applied {len(edits)} edits.")


if __name__ == "__main__":
    main()

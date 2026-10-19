"""Bundle question sources into questions.js.

Run:  python3 build/build.py

Each file in data/src/ is a JSON list. The file prefix sets the section:
  cp_   Chemical and Physical Foundations      (categories 4A-4E, 5A-5E)
  cars_ Critical Analysis and Reasoning Skills (categories C1-C3)
  bb_   Biological and Biochemical Foundations (categories 1A-1D, 2A-2C, 3A-3B)
  ps_   Psychological, Social, and Biological Foundations (6A-10A)

A list item is either a standalone question
  {c: category, t: topic, s: source, q: question, a: answer, w: [3 wrong], e: explanation, x: optional excerpt}
or a passage
  {passage: text, title: title, c, t, s, tbl: optional [[header...], [row...]], cap: optional caption,
   qs: [questions]}   (questions inherit c, t and s from the passage unless they set their own)
"""
import glob, hashlib, json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SECTION_BY_PREFIX = {"cp": "chemphys", "cars": "cars", "bb": "biobio", "ps": "psychsoc"}

CATEGORIES = {
    "1A": "Proteins and amino acids",
    "1B": "Gene to protein",
    "1C": "Heredity and genetic diversity",
    "1D": "Bioenergetics and metabolism",
    "2A": "Cells and tissues",
    "2B": "Prokaryotes and viruses",
    "2C": "Cell division and differentiation",
    "3A": "Nervous and endocrine systems",
    "3B": "Organ systems",
    "4A": "Motion, forces, work and energy",
    "4B": "Fluids and gas exchange",
    "4C": "Electrochemistry and circuits",
    "4D": "Light and sound",
    "4E": "Atoms, nuclear decay and electrons",
    "5A": "Water and solutions",
    "5B": "Molecules and intermolecular forces",
    "5C": "Separation and purification",
    "5D": "Biological molecules and reactivity",
    "5E": "Thermodynamics and kinetics",
    "6A": "Sensing the environment",
    "6B": "Making sense of the environment",
    "6C": "Responding to the world",
    "7A": "Individual influences on behavior",
    "7B": "Social processes and behavior",
    "7C": "Attitude and behavior change",
    "8A": "Self-identity",
    "8B": "Social thinking",
    "8C": "Social interactions",
    "9A": "Social structure",
    "9B": "Demographics",
    "10A": "Social inequality",
    "C1": "Foundations of Comprehension",
    "C2": "Reasoning Within the Text",
    "C3": "Reasoning Beyond the Text",
}
SECTION_CODES = {
    "biobio": ("1", "2", "3"),
    "chemphys": ("4", "5"),
    "psychsoc": ("6", "7", "8", "9", "10"),
    "cars": ("C",),
}
FOUNDATION = {
    "1": "Foundation 1 · Biomolecules", "2": "Foundation 2 · Cells and organisms", "3": "Foundation 3 · Organ systems",
    "4": "Foundation 4 · Physics of living systems", "5": "Foundation 5 · Chemistry of living systems",
    "6": "Foundation 6 · Perception and response", "7": "Foundation 7 · Behavior",
    "8": "Foundation 8 · Self and others", "9": "Foundation 9 · Society and culture", "10": "Foundation 10 · Inequality",
}


def h(s, n=10):
    return hashlib.sha1(s.encode("utf-8")).hexdigest()[:n]


def check(q, where):
    for f in ("c", "t", "q", "a", "w", "e"):
        assert q.get(f), f"{where}: missing {f}: {q.get('q', q)}"
    assert q["c"] in CATEGORIES, f"{where}: unknown category {q['c']}"
    assert len(q["w"]) == 3 and len(set(q["w"])) == 3, f"{where}: need 3 distinct wrong answers: {q['q']}"
    assert q["a"] not in q["w"], f"{where}: answer repeated in wrong answers: {q['q']}"


import sys, urllib.parse
sys.path.insert(0, os.path.join(ROOT, "build"))
from resources import BOOK_NAMES, OPENSTAX  # noqa: E402

TOC = json.load(open(os.path.join(ROOT, "build", "openstax_toc.json"), encoding="utf-8"))
SECTIONS = {(book, s[0]): (s[1], s[2]) for book, chs in TOC.items() for _, _, secs in chs for s in secs}


def learn_more(sec, q):
    """Links shown after answering: Wikipedia, an OpenStax section, and a Khan Academy search."""
    links = []
    wk = q.pop("wk", None)
    assert wk, f"{sec}: question has no Wikipedia topic (wk): {q['q']}"
    # Wikipedia's "go" search opens the article when the title exists and shows results otherwise,
    # so the link never lands on an empty page.
    links.append(["Wikipedia", wk, "https://en.wikipedia.org/w/index.php?" +
                  urllib.parse.urlencode({"search": wk, "title": "Special:Search", "go": "Go"})])
    ox = q.pop("ox", None)
    if ox != "-":
        ref = tuple(ox.split(" ", 1)) if ox else OPENSTAX.get((q["c"], q["t"]), "missing")
        assert ref != "missing", f"{sec}: no OpenStax section for topic {q['c']} {q['t']}"
        if ref:
            book, num = ref
            assert (book, num) in SECTIONS, f"{sec}: OpenStax {book} {num} doesn't exist: {q['q']}"
            title, slug = SECTIONS[(book, num)]
            links.append([f"OpenStax {BOOK_NAMES[book]}", f"{num} {title}",
                          f"https://openstax.org/books/{book}/pages/{slug}"])
    if sec != "cars":
        links.append(["Khan Academy", f"Search “{wk}”",
                      "https://www.khanacademy.org/search?" + urllib.parse.urlencode({"page_search_query": wk})])
    q["R"] = links


def annotate(sec, q):
    code = q["c"]
    q["L"] = CATEGORIES[code] if sec == "cars" else f"{code} · {CATEGORIES[code]}"
    q["T"] = q["t"]
    if sec != "cars":
        q["g"] = FOUNDATION[re.match(r"\d+", code).group()]


def main():
    bank = {v: [] for v in SECTION_BY_PREFIX.values()}
    passages = {}
    for f in sorted(glob.glob(os.path.join(ROOT, "data", "src", "*.json"))):
        name = os.path.basename(f)
        sec = SECTION_BY_PREFIX[name.split("_")[0]]
        for item in json.load(open(f, encoding="utf-8")):
            if "passage" in item:
                pid = "p" + h(item["passage"][:400], 8)
                assert pid not in passages, f"{name}: duplicate passage {item.get('title')}"
                passages[pid] = {k: item[k] for k in ("title", "passage", "tbl", "cap") if k in item}
                passages[pid]["subject"] = sec
                passages[pid]["n"] = len(item["qs"])
                assert len(item["qs"]) >= 2, f"{name}: passage needs 2+ questions: {item.get('title')}"
                for i, q in enumerate(item["qs"]):
                    for k in ("c", "t", "s"):
                        q.setdefault(k, item.get(k))
                    q["p"], q["pi"] = pid, i
                    bank[sec].append(q)
            else:
                bank[sec].append(item)
    lessons = {}
    for sec, qs in bank.items():
        ids = set()
        for q in qs:
            check(q, sec)
            assert q["c"].startswith(SECTION_CODES[sec]) and (sec != "cars" or q["c"][0] == "C"), \
                f"{sec}: category {q['c']} belongs to another section: {q['q']}"
            q["id"] = h(q["q"] + "|" + q["a"])
            assert q["id"] not in ids, f"{sec}: duplicate question: {q['q']}"
            ids.add(q["id"])
            annotate(sec, q)
            learn_more(sec, q)
        order = sorted({q["c"] for q in qs}, key=lambda c: (c[0] == "C", int(re.match(r"\D*(\d+)", c).group(1)), c))
        lessons[sec] = []
        for c in order:
            mine = [q for q in qs if q["c"] == c]
            topics = []
            for q in mine:
                if q["T"] not in topics:
                    topics.append(q["T"])
            lessons[sec].append({"L": mine[0]["L"], "g": mine[0].get("g", ""), "topics": topics if len(topics) > 1 else []})
        n_p = sum(1 for p in passages.values() if p["subject"] == sec)
        n_alone = sum(1 for q in qs if "p" not in q)
        print(f"{sec}: {len(qs)} questions ({n_alone} standalone, {n_p} passages), {len(lessons[sec])} categories")
    js = "// Generated by build/build.py. Edit data/src/*.json instead.\n" + \
        "window.QUESTION_BANK = " + json.dumps(bank, ensure_ascii=False, separators=(",", ":")) + ";\n" + \
        "window.PASSAGES = " + json.dumps(passages, ensure_ascii=False, separators=(",", ":")) + ";\n" + \
        "window.LESSONS = " + json.dumps(lessons, ensure_ascii=False, separators=(",", ":")) + ";\n"
    open(os.path.join(ROOT, "questions.js"), "w", encoding="utf-8").write(js)


if __name__ == "__main__":
    main()

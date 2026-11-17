# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Run the reference solution of every lab and check it against the course files.

    uv run labs/solutions/check.py          # all labs
    uv run labs/solutions/check.py 2.1 4.1  # some labs

What runs for real: every check on the files (the sort key against the lab page, every flagged
detail present in an original and absent from its sanitised version, the dashboard's numbers
recomputed from the CSV file and from the data inside the dashboard page, each draft against
its source, the two elements of a disclosure line). What runs against a stand-in: the assistant
of lab 3.1 (standin.json holds written replies with the mistakes a real assistant makes). No
model is called and nothing is written to disk.
"""
from __future__ import annotations

import csv
import html
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LABS = HERE.parent
FILES = LABS / "files"
KEY = json.loads((HERE / "key.json").read_text(encoding="utf-8"))
STANDIN = json.loads((HERE / "standin.json").read_text(encoding="utf-8"))
RUN: dict[str, callable] = {}


def lab(lab_id):
    def wrap(fn):
        RUN[lab_id] = fn
        return fn
    return wrap


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def page_text(name: str) -> str:
    """The text of a lab page as a reader sees it: tags removed, entities decoded."""
    return html.unescape(re.sub(r"<[^>]+>", " ", read(LABS / name)))


def squash(text: str) -> str:
    return re.sub(r"\s+", " ", text)


@lab("1.1")
def lab_1_1():
    k = KEY["1.1"]
    page = squash(page_text("M1_1_vignettes.html"))
    lines = [x for x in read(FILES / "vignettes.txt").splitlines() if x.strip()]
    assert len(lines) == 8 and len(k["vignettes"]) == 8
    for line, v in zip(lines, k["vignettes"]):
        assert line.startswith(v["id"] + ". "), line
        assert squash(line.split(". ", 1)[1]) in page, f"{v['id']} differs between the file and the page"
        assert v["category"] in k["categories"]
    counts = {c: sum(1 for v in k["vignettes"] if v["category"] == c) for c in k["categories"]}
    assert counts == {"use": 3, "specialist": 3, "none": 2}, counts
    print("  sort key:", ", ".join(f"{v['id']}={v['category']}" for v in k["vignettes"]))
    print("  counts:", counts, "| pass mark:", k["pass"], "of 8")


PERSONAL = {
    "national id": r"(?<!\d)[12]\d{9}(?!\d)",
    "mobile": r"(?<!\d)05\d{8}(?!\d)",
    "email": r"[\w.]+@[\w.]+",
    "iban": r"SA\d{22}",
}


@lab("2.1")
def lab_2_1():
    page = squash(page_text("M2_1_sanitise.html"))
    total = 0
    for it in KEY["2.1"]["items"]:
        original = read(FILES / it["file"])
        clean = read(HERE / it["sanitised"])
        for f in it["flagged"]:
            assert f["detail"] in original, f"{it['id']}: {f['detail']} is not in the original"
            assert f["detail"] in page, f"{it['id']}: {f['detail']} is not shown in the lab page"
            assert f["detail"] not in clean, f"{it['id']}: {f['detail']} is still in the sanitised version"
        for name, pattern in PERSONAL.items():
            assert not re.search(pattern, clean), f"{it['id']}: a {name} is left in the sanitised version"
        found = sum(1 for p in PERSONAL.values() for _ in re.finditer(p, original))
        for kept in it["keep"]:
            assert kept in clean, f"{it['id']}: the sanitised version lost what the task needs: {kept}"
        total += len(it["flagged"])
        print(f"  {it['id']}: {len(it['flagged'])} flagged details removed or generalised, {found} identifiers by pattern in the original, 0 left")
    print("  flagged details in the five items:", total)


def tokens(text: str) -> set[str]:
    """Numbers and day names: what a summary must not invent."""
    days = ["السبت", "الأحد", "الاثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة"]
    return set(re.findall(r"\d+", text)) | {d for d in days if d in text}


@lab("3.1")
def lab_3_1():
    notes = read(FILES / KEY["3.1"]["notes"])
    s = STANDIN["3.1"]
    weak, good = " ".join(s["weak_reply"]), " ".join(s["good_reply"])
    request = "\n".join(s["good_request"])
    missing_weak = [e for e in KEY["3.1"]["elements"] if e + ":" not in s["weak_request"]]
    missing_good = [e for e in KEY["3.1"]["elements"] if e + ":" not in request]
    assert len(missing_weak) == 5 and not missing_good, (missing_weak, missing_good)
    invented_weak = sorted(tokens(weak) - tokens(notes))
    invented_good = sorted(tokens(good) - tokens(notes))
    assert invented_weak == ["20", "الخميس"], invented_weak
    assert not invented_good, invented_good
    assert "تقرر شراء" in weak and "لم يُتخذ قرار" in notes and "لم يُتخذ قرار" in good
    owners = ["مخطط الصيانة", "مشرف الوردية", "مسؤولة الاتصال"]
    assert all(o in notes and o in good for o in owners)
    assert not all(o in weak for o in owners)
    assert "لم يُحدد" in good and len(good.split()) <= 120
    page = squash(page_text("M3_1_request.html"))
    for line in notes.splitlines() + s["weak_reply"] + s["good_request"] + s["good_reply"]:
        assert squash(line) in page, "the lab page differs from the files: " + line[:40]
    print("  stand-in model, no model call")
    print("  general request: 0 of 5 elements; its reply invents", invented_weak, "and turns an open item into a decision")
    print("  reference request: 5 of 5 elements; its reply invents", invented_good, "and names the 3 owners;", len(good.split()), "words")


@lab("4.1")
def lab_4_1():
    k = KEY["4.1"]["dashboard"]
    with open(FILES / "dashboard_data.csv", encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    page = read(FILES / "dashboard.html")
    embedded = json.loads(re.search(r"var ROWS = (\[.*?\]);\n", page, re.S).group(1))
    assert len(embedded) == len(rows) == k["rows_in_file"]
    assert [[r["date"], r["airport"], r["category"], int(r["requests"])] for r in rows] == [r[:4] for r in embedded]
    names = json.loads(re.search(r"var AIRPORTS = (\{.*?\});", page).group(1))
    seen, clean = set(), []
    for r in rows:
        key = (r["date"], r["airport"], r["category"])
        if key not in seen:
            seen.add(key)
            clean.append(r)
    headline = sum(int(r["requests"]) for r in rows)
    by_airport = {names[c]: sum(int(r["requests"]) for r in clean if r["airport"] == c) for c in names}
    assert headline == k["headline_total"] and by_airport == k["by_airport"], (headline, by_airport)
    assert headline - sum(by_airport.values()) == k["difference"] > 0
    assert len(rows) - len(clean) == k["duplicate_rows"] == 7
    last = max(r["date"] for r in rows)
    assert last == k["last_update"] == "2026-08-31" and f"آخر تحديث للبيانات: {last}" in page
    assert "الربع الثالث 2026" in page and not [r for r in rows if r["date"][5:7] == "09"]
    wait_section = re.search(r"<h2>متوسط الانتظار</h2>.*?</section>", page, re.S).group(0)
    assert not re.search(r"دقيقة|دقائق|ثانية|ثوان", wait_section + page.split("<script>")[1]), "the wait chart has a unit"
    assert "أُغلقت في الوقت" in page and "تعريف" not in page
    wait = {names[c]: round(sum(float(r["avg_wait"]) * int(r["requests"]) for r in clean if r["airport"] == c)
                           / sum(int(r["requests"]) for r in clean if r["airport"] == c), 1) for c in names}
    assert wait == k["avg_wait_no_unit"], wait
    comp = {m: sum(int(r["requests"]) for r in clean if r["category"] == "شكاوى" and r["date"][5:7] == m) for m in ("07", "08")}
    assert comp["08"] < comp["07"] and (comp["07"], comp["08"]) == (k["complaints_july"], k["complaints_august"])
    by_cat = {}
    for r in clean:
        by_cat[r["category"]] = by_cat.get(r["category"], 0) + int(r["requests"])
    summary = KEY["4.1"]["summary"]
    text = read(FILES / "ai_summary.txt")
    lab_page = squash(page_text("M4_1_dashboard.html"))
    for s in summary:
        assert s["text"] in text and squash(s["text"]) in lab_page, s["id"]
    assert f"{headline:,}" in summary[0]["text"] and "كاملًا" in summary[0]["text"]
    assert max(by_cat, key=by_cat.get) in summary[1]["text"] and summary[1]["ok"]
    lowest = min(wait, key=wait.get)
    assert lowest in summary[2]["text"] and "ثانية" in summary[2]["text"]
    assert "بسبب" in summary[3]["text"] and "تدريب الموظفين" not in page
    assert [s["ok"] for s in summary] == [False, True, False, False, False]
    assert f"{headline:,}" in lab_page and f"{sum(by_airport.values()):,}" in lab_page
    print(f"  rows {len(rows)}, of which {len(rows) - len(clean)} are duplicates")
    print(f"  headline total {headline} against {sum(by_airport.values())} in the table by airport: difference {headline - sum(by_airport.values())}")
    print("  by airport:", by_airport)
    print("  title says the third quarter; last update", last, "; rows in September: 0")
    print("  wait chart:", wait, "with no unit anywhere in the page")
    print(f"  complaints: July {comp['07']}, August {comp['08']} ({k['complaints_change_percent']}%), no cause in the dashboard")
    print("  summary: 1 of 5 sentences holds; 4 flagged")


@lab("5.1")
def lab_5_1():
    k = KEY["5.1"]
    text = read(FILES / "drafts.txt")
    blocks = dict(zip([d["id"] for d in k["drafts"]], re.split(r"\n(?=D\d\. )", text)))
    page = squash(page_text("M5_1_drafts.html"))
    for d in k["drafts"]:
        block = blocks[d["id"]]
        draft, source = block.split("المسودة:", 1)[1].split(":\n", 1)
        draft = draft.rsplit("\n", 1)[0]
        f = d["facts"]
        for x in f.get("draft_has", []):
            assert x in draft and x in page, (d["id"], x)
        for x in f.get("source_has", []):
            assert x in source and x not in draft, (d["id"], x)
        for x in f.get("source_lacks", []):
            assert x not in source, (d["id"], x)
        for x in f.get("both_have", []):
            assert x in draft and x in source, (d["id"], x)
        if f.get("source_missing"):
            assert "لم تعثر عليه" in source and "لا يوجد" in source
        assert d["decision"] in k["decisions"] and d["check"] in k["checks"]
        print(f"  {d['id']}: {d['decision']} ({d['check']})")
    decisions = sorted(d["decision"] for d in k["drafts"])
    assert decisions == ["escalate", "escalate", "pause", "revise", "revise", "use"], decisions
    assert sorted(d["check"] for d in k["drafts"]) == ["accuracy", "authorisation", "impact", "none", "sensitivity", "source"]
    print("  each of the five checks triggers one decision; one draft is clean | pass mark:", k["pass"], "of 6")


@lab("6.1")
def lab_6_1():
    k = KEY["6.1"]
    out = read(FILES / "finished_output.txt")
    assert "60 يومًا" in out and "إثبات هوية" in out and "90" not in out
    page = squash(page_text("M6_1_disclosure.html"))
    good = 0
    for line in k["lines"]:
        assert squash(line["text"]) in page
        names_tool = "«زميل»" in line["text"]
        names_check = "سياسة المفقودات" in line["text"]
        assert (names_tool and names_check) == line["ok"], line["text"]
        assert len(line["text"].splitlines()) == 1
        good += line["ok"]
    assert good == 2 and len(k["lines"]) == 5
    print("  5 example lines: 2 name the assistance and what was checked, 3 miss an element")


def main(argv: list[str]) -> int:
    wanted = argv or sorted(RUN)
    for lab_id in wanted:
        if lab_id not in RUN:
            print("unknown lab", lab_id)
            return 2
        print(f"Lab {lab_id}")
        RUN[lab_id]()
        print("  PASS")
    print(f"{len(wanted)} labs checked, all PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Write the synthetic file pack of the case study, Tayf Airports Company.

    uv run labs/_tools/prepare_files.py

Standard library only, a fixed seed, the same bytes on every run. It writes

  labs/files/            what a participant starts from (text files, the dashboard and its data)
  labs/solutions/key.json, labs/solutions/standin.json, labs/solutions/sanitised/

and refreshes the blocks of the lab pages marked  <!-- pack:NAME --> ... <!-- /pack:NAME -->,
so the text shown in a page is always the text of the file. Everything is invented: no person,
company, number or address here is real.
"""
from __future__ import annotations

import csv
import datetime as dt
import html
import io
import json
import random
import re
from pathlib import Path

LABS = Path(__file__).resolve().parent.parent
FILES = LABS / "files"
SOL = LABS / "solutions"
SEED = 101

# ---------------------------------------------------------------- lab 1.1: eight vignettes
CATS = {"use": "استخدام يومي", "specialist": "عمل متخصص", "none": "لا يدخل فيها الذكاء الاصطناعي"}
VIGNETTES = [
    ("V1", "تطلب ريما من «زميل» أن يعيد صياغة رسالة داخلية عن موعد التسجيل في دورة تدريبية، بلغة أوضح.", "use",
     "تستخدم أداة معتمدة في مهمة روتينية منخفضة المخاطر، وتراجع النص قبل إرساله."),
    ("V2", "يقرر فريق مختص أي حقول من بيانات المسافرين يجوز أن يطّلع عليها «زميل»، ومن يُمنح صلاحية ذلك.", "specialist",
     "قرار حوكمة: يعود إلى مالك البيانات ومالك نظام الذكاء الاصطناعي، لا إلى من يستخدم الأداة."),
    ("V3", "يصفّي يزن لوحة معلومات الصيانة ليرى أعطال صالته في هذا الشهر فقط، ثم يفرزها بحسب التاريخ.", "use",
     "التصفية والفرز استخدام يومي لأداة بيانات: يتغيّر ما يراه هو، ولا تتغيّر البيانات."),
    ("V4", "تدقق أبرار بيانًا صحفيًا مطبوعًا بقلمها، مستعينة بدليل الأسلوب الورقي المعتمد.", "none",
     "لا أداة بيانات ولا ذكاء اصطناعي في هذه المهمة: قراءة وحكم بشري على ورق."),
    ("V5", "قبل اعتماد نموذج يتنبأ بطول الطوابير، يختبر فريق مختص دقته على بيانات أشهر سابقة ويوثّق حدوده.", "specialist",
     "التحقق من صحة النموذج قبل تشغيله عمل متخصص له فريق مسؤول."),
    ("V6", "يكتب سليمان ردًا على مورّد، فيقترح عليه برنامج البريد إكمال الجملة تلقائيًا، فيقبل الاقتراح ثم يعدّله.", "use",
     "اقتراح الإكمال التلقائي مساعدة من الذكاء الاصطناعي، ولو لم يُكتب اسمها على الشاشة. قبولها وتعديلها استخدام يومي."),
    ("V7", "يُطلب من فريق مختص أن يربط «زميل» بنظام الموارد البشرية، وأن يحدد ما يحق للمساعد أن يقرأه منه.", "specialist",
     "تصميم النظام وربطه وضبط صلاحياته عمل متخصص، ولا يجريه موظف بمبادرة منه."),
    ("V8", "يجتمع جواد بفريق الوردية وقوفًا، ويوزع المهام شفهيًا بحسب من حضر، ويكتب التوزيع على لوح أبيض.", "none",
     "قرار بشري مباشر، دون أداة بيانات ولا توصية آلية."),
]

# ---------------------------------------------------------------- lab 2.1: five work items
ITEMS = [
    {
        "id": "item1", "file": "work_items/01_email.txt", "kind": "رسالة بريد إلكتروني",
        "task": "تريد من «زميل» صياغة رد مهذب على المسافر.",
        "text": [
            "من: خدمات المسافرين، مطار النخيل",
            "إلى: فريق الأمتعة",
            "الموضوع: شكوى المسافر ماهر العتيق",
            "وصلتنا شكوى من المسافر ماهر العتيق (هوية 1087345621، جوال 0551234987، بريد maher.alateeq@mail.example) عن تأخر حقيبته في الرحلة TF 418 بتاريخ 2026-09-14.",
            "ذكر أن في الحقيبة أدوية السكري التي يحتاجها يوميًا. رقم بلاغ الأمتعة NKH-2291.",
            "نرجو صياغة رد يعتذر له ويشرح خطوات متابعة البلاغ.",
        ],
        "flagged": [
            ("ماهر العتيق", "شخصي", "احذف، أو ضع عنصرًا نائبًا"),
            ("1087345621", "شخصي", "احذف"),
            ("0551234987", "شخصي", "احذف"),
            ("maher.alateeq@mail.example", "شخصي", "احذف"),
            ("أدوية السكري", "حساس", "عمّم: مستلزمات يحتاجها يوميًا"),
            ("NKH-2291", "شخصي", "ضع عنصرًا نائبًا"),
            ("TF 418", "شخصي", "عمّم: رحلة داخلية"),
        ],
        "keep": ["تأخر حقيبته", "يعتذر", "خطوات متابعة البلاغ"],
        "sanitised": [
            "اكتب ردًا مهذبًا على مسافر اشتكى من تأخر حقيبته في رحلة داخلية، وفي الحقيبة مستلزمات يحتاجها يوميًا.",
            "الرد يعتذر له ويشرح خطوات متابعة البلاغ.",
            "اترك [اسم المسافر] و[رقم البلاغ] كما هما، وسأضيفهما بنفسي بعد أن تعود المسودة.",
        ],
    },
    {
        "id": "item2", "file": "work_items/02_case_note.txt", "kind": "ملاحظة حالة",
        "task": "تريد من «زميل» تلخيص الحالة في ثلاث نقاط للجنة.",
        "text": [
            "ملاحظة حالة، الموارد البشرية، التصنيف: سري",
            "الموظفة: إيناس الدهيمي، الرقم الوظيفي 40718، قسم المناولة الأرضية في مطار الجبل.",
            "تقدمت بطلب تعديل ورديتها الليلية بعد تقرير طبي يفيد بإصابتها بالصرع.",
            "سبق أن وُجّه لها إنذار كتابي في مارس بسبب التأخر. راتبها الأساسي 9,400 ريال.",
            "المشرف المباشر يوصي بقبول الطلب ثلاثة أشهر.",
        ],
        "flagged": [
            ("إيناس الدهيمي", "شخصي", "احذف"),
            ("40718", "شخصي", "احذف"),
            ("المناولة الأرضية في مطار الجبل", "شخصي", "عمّم: قسم تشغيلي"),
            ("الصرع", "حساس", "عمّم: سبب صحي موثّق"),
            ("إنذار كتابي", "حساس", "احذف: لا تحتاجه المهمة"),
            ("9,400", "حساس", "احذف: لا تحتاجه المهمة"),
        ],
        "keep": ["تعديل ورديتها الليلية", "يوصي بقبول الطلب ثلاثة أشهر"],
        "sanitised": [
            "لخّص في ثلاث نقاط للجنة: موظفة في قسم تشغيلي طلبت تعديل ورديتها الليلية لسبب صحي موثّق.",
            "المشرف المباشر يوصي بقبول الطلب ثلاثة أشهر.",
            "لا تضف أي معلومة غير مذكورة هنا.",
        ],
    },
    {
        "id": "item3", "file": "work_items/03_spreadsheet_extract.csv", "kind": "مقتطف من جدول بيانات",
        "task": "تريد من «زميل» حساب مجموع الساعات الإضافية لكل إدارة.",
        "table": [
            ["الاسم", "رقم الهوية", "الإدارة", "ساعات إضافية", "رقم الآيبان"],
            ["عبير الشويعر", "1093311842", "المشتريات", "12", "SA4420000001234567891234"],
            ["نايف القريني", "1076620915", "الصيانة", "7", "SA1780000009876543219876"],
            ["رغد الفضلي", "1102458830", "خدمات المسافرين", "15", "SA0910000004567891234567"],
            ["هاني المطرودي", "1058842207", "المشتريات", "9", "SA6330000007418529637418"],
        ],
        "flagged": [
            ("عبير الشويعر", "شخصي", "احذف العمود"), ("نايف القريني", "شخصي", "احذف العمود"),
            ("رغد الفضلي", "شخصي", "احذف العمود"), ("هاني المطرودي", "شخصي", "احذف العمود"),
            ("1093311842", "شخصي", "احذف العمود"), ("1076620915", "شخصي", "احذف العمود"),
            ("1102458830", "شخصي", "احذف العمود"), ("1058842207", "شخصي", "احذف العمود"),
            ("SA4420000001234567891234", "حساس", "احذف العمود"), ("SA1780000009876543219876", "حساس", "احذف العمود"),
            ("SA0910000004567891234567", "حساس", "احذف العمود"), ("SA6330000007418529637418", "حساس", "احذف العمود"),
        ],
        "keep": ["المشتريات", "الصيانة", "خدمات المسافرين", "ساعات إضافية"],
        "sanitised": [
            "احسب مجموع الساعات الإضافية لكل إدارة من هذا الجدول:",
            "الإدارة، ساعات إضافية",
            "المشتريات، 12",
            "الصيانة، 7",
            "خدمات المسافرين، 15",
            "المشتريات، 9",
        ],
    },
    {
        "id": "item4", "file": "work_items/04_meeting_transcript.txt", "kind": "محضر اجتماع مفرَّغ",
        "task": "تريد من «زميل» استخراج بنود العمل.",
        "text": [
            "تفريغ اجتماع لجنة المشتريات (مقطع)",
            "سليمان الرديني: عرض شركة «أفق المدرج» لصيانة السيور هو الأقل، 1,840,000 ريال، لكنه لم يُعلن بعد.",
            "سهى (المالية): لا تذكروا الرقم خارج اللجنة قبل الترسية يوم 2026-10-05.",
            "سليمان الرديني: مندوب الشركة المنافسة اتصل بي على جوالي 0509876123 يسأل عن النتيجة.",
            "القرار: يُعدّ سليمان مقارنة فنية بين العروض، وترسل سهى نموذج تضارب المصالح للأعضاء.",
        ],
        "flagged": [
            ("أفق المدرج", "سري", "احذف"),
            ("1,840,000", "سري", "احذف"),
            ("2026-10-05", "سري", "احذف"),
            ("0509876123", "شخصي", "احذف"),
            ("سليمان", "شخصي", "عمّم: عضو اللجنة"),
            ("سهى", "شخصي", "عمّم: ممثلة المالية"),
        ],
        "keep": ["مقارنة فنية بين العروض", "نموذج تضارب المصالح"],
        "sanitised": [
            "استخرج بنود العمل من هذا المقطع من اجتماع لجنة:",
            "عضو اللجنة يُعدّ مقارنة فنية بين العروض، وممثلة المالية ترسل نموذج تضارب المصالح للأعضاء.",
            "اكتب البنود في جدول: البند، المسؤول. لا تضف بنودًا غير مذكورة.",
        ],
    },
    {
        "id": "item5", "file": "work_items/05_contract_clause.txt", "kind": "بند تعاقدي",
        "task": "تريد من «زميل» شرح البند لزميل غير قانوني بلغة بسيطة.",
        "text": [
            "البند 7-3 من عقد تشغيل صالة كبار الزوار بين شركة طيف للمطارات وشركة «ضيافة السحاب»:",
            "يلتزم الطرف الثاني بدفع غرامة قدرها 2.5% من قيمة العقد البالغة 6,200,000 ريال عن كل يوم تأخير في التسليم، بحد أقصى 10%.",
            "ويحق للطرف الأول فسخ العقد بعد 30 يومًا من التأخير.",
        ],
        "flagged": [
            ("ضيافة السحاب", "مملوك للجهة", "احذف"),
            ("صالة كبار الزوار", "مملوك للجهة", "عمّم: عقد تشغيل"),
            ("6,200,000", "سري", "احذف"),
            ("2.5%", "مملوك للجهة", "عمّم: نسبة محددة"),
        ],
        "keep": ["غرامة", "يوم تأخير", "فسخ العقد"],
        "sanitised": [
            "اشرح لزميل غير قانوني، بلغة بسيطة، معنى بند في عقد تشغيل:",
            "يدفع المتعاقد غرامة بنسبة محددة من قيمة العقد عن كل يوم تأخير في التسليم، ولها حد أقصى.",
            "ويحق للجهة فسخ العقد إذا تجاوز التأخير مدة محددة.",
        ],
    },
]

# ---------------------------------------------------------------- lab 3.1: the meeting and the requests
NOTES = [
    "ملاحظات اجتماع تنسيق صالة المغادرة، مطار المرفأ (مواد اصطناعية)",
    "الحضور: مشرف الوردية، ممثلة خدمات المسافرين، مخطط الصيانة، مسؤولة الاتصال.",
    "1. لوحات الإرشاد عند البوابات 4 إلى 6: تُستبدل ثلاث لوحات. المسؤول: مخطط الصيانة. الموعد: نهاية الأسبوع القادم.",
    "2. طابور نقطة المساعدة: يُضاف موظف في فترة الذروة الصباحية لمدة أسبوعين تجريبيين. المسؤول: مشرف الوردية. يبدأ يوم الأحد.",
    "3. رسالة للمسافرين عن تغيير بوابة الحافلات: تُعدّ مسؤولة الاتصال مسودة. لم يُحدد موعد.",
    "4. اقتراح شراء عربات أمتعة إضافية: نوقش ولم يُتخذ قرار، ويُعاد طرحه في الاجتماع القادم.",
]
ELEMENTS = ["المخرج", "السياق", "الجمهور", "القيود", "المراجعة"]
WEAK_REQUEST = "لخّص هذا الاجتماع."
GOOD_REQUEST = [
    "المخرج: ملخص في جدول لبنود العمل بثلاثة أعمدة: البند، المسؤول، الموعد.",
    "السياق: ملاحظات اجتماع تنسيق صالة المغادرة أدناه، وهي كل ما تعتمد عليه.",
    "الجمهور: مشرفو الورديات الذين لم يحضروا الاجتماع؛ لغة مباشرة بلا مقدمات.",
    "القيود: لا يتجاوز الملخص 120 كلمة، ولا تضف موعدًا أو مسؤولًا أو قرارًا غير مكتوب في الملاحظات، واكتب «لم يُحدد» حين يغيب الموعد.",
    "المراجعة: ضع بعد الجدول قائمة بما لم تجده في الملاحظات، لأراجعه بنفسي قبل الإرسال.",
]
STANDIN = {
    "about": "ردود مكتوبة تقوم مقام المساعد في تشغيل الحل المرجعي. في الرد الأول الأخطاء التي يقع فيها مساعد حقيقي أمام طلب عام.",
    "3.1": {
        "weak_request": WEAK_REQUEST,
        "weak_reply": [
            "عُقد اجتماع تنسيق صالة المغادرة في مطار المرفأ، وناقش الحضور عددًا من الموضوعات المهمة لتحسين تجربة المسافرين.",
            "تقرر استبدال ثلاث لوحات إرشاد عند البوابات 4 إلى 6 قبل نهاية الأسبوع القادم.",
            "وتقرر إضافة موظف في نقطة المساعدة في فترة الذروة الصباحية لمدة أسبوعين.",
            "وستُرسل رسالة المسافرين عن تغيير بوابة الحافلات قبل يوم الخميس.",
            "كما تقرر شراء 20 عربة أمتعة إضافية.",
        ],
        "good_request": GOOD_REQUEST,
        "good_reply": [
            "البند | المسؤول | الموعد",
            "استبدال ثلاث لوحات إرشاد عند البوابات 4 إلى 6 | مخطط الصيانة | نهاية الأسبوع القادم",
            "إضافة موظف في نقطة المساعدة في الذروة الصباحية، أسبوعين تجريبيين | مشرف الوردية | يبدأ يوم الأحد",
            "مسودة رسالة للمسافرين عن تغيير بوابة الحافلات | مسؤولة الاتصال | لم يُحدد",
            "ما لم أجده في الملاحظات: موعد مسودة الرسالة. وعربات الأمتعة: نوقشت ولم يُتخذ قرار، ويُعاد طرحها في الاجتماع القادم.",
        ],
        "improvement": "أضفت القيود والمراجعة: منع إضافة ما ليس في الملاحظات، وطلب قائمة بما غاب. اختفى الموعد المختلق وقرار الشراء المختلق.",
    },
}

# ---------------------------------------------------------------- lab 4.1: the dashboard
AIRPORTS = [("MRF", "المرفأ", 210, 8.6), ("NKH", "النخيل", 150, 11.2), ("JBL", "الجبل", 90, 6.4)]
CATEGORIES = [("استفسارات", 0.46), ("أمتعة", 0.27), ("مساعدة حركية", 0.15), ("شكاوى", 0.12)]
FIRST_DAY, LAST_DAY = dt.date(2026, 7, 1), dt.date(2026, 8, 31)
DUP_AIRPORT, DUP_CAT = "NKH", "أمتعة"
DUP_FROM, DUP_TO = dt.date(2026, 8, 10), dt.date(2026, 8, 16)
DASH_TITLE = "لوحة خدمات المسافرين: الربع الثالث 2026"
LAST_UPDATE = LAST_DAY.isoformat()


def make_rows() -> list[list]:
    rng = random.Random(SEED)
    rows = []
    day = FIRST_DAY
    while day <= LAST_DAY:
        weekend = day.weekday() in (3, 4)  # Thursday and Friday carry more travellers
        for code, _name, base, wait in AIRPORTS:
            for cat, share in CATEGORIES:
                n = base * share * (1.18 if weekend else 1.0) * rng.uniform(0.9, 1.1)
                if cat == "شكاوى" and day.month == 8:
                    n *= 0.85
                n = max(1, round(n))
                on_time = round(n * rng.uniform(0.78, 0.93))
                w = round(wait * rng.uniform(0.85, 1.15), 1)
                rows.append([day.isoformat(), code, cat, n, on_time, w])
        day += dt.timedelta(days=1)
    dups = [r[:] for r in rows if r[1] == DUP_AIRPORT and r[2] == DUP_CAT
            and DUP_FROM.isoformat() <= r[0] <= DUP_TO.isoformat()]
    return rows + dups


def dedup(rows):
    seen, out = set(), []
    for r in rows:
        k = (r[0], r[1], r[2])
        if k not in seen:
            seen.add(k)
            out.append(r)
    return out


def dashboard_facts(rows) -> dict:
    clean = dedup(rows)
    names = {c: n for c, n, _b, _w in AIRPORTS}
    by_airport = {names[c]: sum(r[3] for r in clean if r[1] == c) for c in names}
    by_cat = {cat: sum(r[3] for r in clean if r[2] == cat) for cat, _ in CATEGORIES}
    wait = {names[c]: round(sum(r[5] * r[3] for r in clean if r[1] == c) / sum(r[3] for r in clean if r[1] == c), 1) for c in names}
    comp = {m: sum(r[3] for r in clean if r[2] == "شكاوى" and r[0][5:7] == m) for m in ("07", "08")}
    headline = sum(r[3] for r in rows)
    return {
        "title": DASH_TITLE, "last_update": LAST_UPDATE, "rows_in_file": len(rows), "duplicate_rows": len(rows) - len(clean),
        "headline_total": headline, "sum_of_airports": sum(by_airport.values()), "difference": headline - sum(by_airport.values()),
        "by_airport": by_airport, "by_category": by_cat, "avg_wait_no_unit": wait,
        "on_time_share_percent": round(100 * sum(r[4] for r in rows) / headline, 1),
        "complaints_july": comp["07"], "complaints_august": comp["08"],
        "complaints_change_percent": round(100 * (comp["08"] - comp["07"]) / comp["07"], 1),
    }


def ai_summary(f: dict) -> list[dict]:
    lowest = min(f["avg_wait_no_unit"], key=f["avg_wait_no_unit"].get)
    top = max(f["by_category"], key=f["by_category"].get)
    return [
        {"id": "S1", "text": f"بلغ إجمالي طلبات المسافرين في الربع الثالث 2026 كاملًا {f['headline_total']:,} طلبًا في المطارات الثلاثة.",
         "ok": False, "flag": "يكرر الإجمالي غير المتسق، ويقول «كاملًا» والبيانات تنتهي في " + f["last_update"] + "."},
        {"id": "S2", "text": f"فئة «{top}» أكثر الفئات طلبًا.", "ok": True, "flag": "يطابق اللوحة."},
        {"id": "S3", "text": f"متوسط الانتظار في مطار {lowest} {f['avg_wait_no_unit'][lowest]} ثانية فقط، وهو الأفضل بين المطارات.",
         "ok": False, "flag": "اللوحة لا تذكر الوحدة، والملخص اختلق «ثانية»."},
        {"id": "S4", "text": "انخفضت الشكاوى في أغسطس عن يوليو بسبب برنامج تدريب الموظفين.",
         "ok": False, "flag": "الانخفاض في اللوحة، والسبب ليس فيها: افتراض كُتب بصيغة الحقيقة."},
        {"id": "S5", "text": f"نوصي بتقليص عدد موظفي نقاط المساعدة في مطار {lowest}.",
         "ok": False, "flag": "توصية لا قرار: تمس موارد وأشخاصًا، ولا تُبنى على لوحة فيها هذه العيوب."},
    ]


DASH_HTML = """<!doctype html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__</title>
<style>
  :root { --navy:#12284c; --teal:#0f8a7e; --coral:#c9503c; --amber:#b7791f; --purple:#6b4fbb; --paper:#f5f3ee; --line:#d9d5cb; --ink:#1c2430; --muted:#5b6472; }
  * { box-sizing: border-box; }
  body { margin:0; font-family: "IBM Plex Sans Arabic", "Segoe UI", Tahoma, sans-serif; background:var(--paper); color:var(--ink); line-height:1.7; }
  main { max-width: 760px; margin: 0 auto; padding: 16px; }
  h1 { font-size: 1.35rem; margin: 0 0 4px; color: var(--navy); }
  h2 { font-size: 1.05rem; margin: 0 0 8px; color: var(--navy); }
  .banner { background:#fff7e0; border:1px solid #e6cf8a; border-radius:10px; padding:8px 12px; font-size:.9rem; margin: 10px 0; }
  .filters { display:flex; flex-wrap:wrap; gap:10px; margin: 12px 0; }
  .filters label { display:flex; flex-direction:column; font-size:.9rem; color:var(--muted); flex:1 1 150px; }
  select { font: inherit; padding: 10px; border:1px solid var(--line); border-radius:8px; background:#fff; min-height:44px; }
  .cards { display:grid; grid-template-columns: 1fr 1fr; gap:10px; }
  .card, section { background:#fff; border:1px solid var(--line); border-radius:12px; padding:12px 14px; }
  section { margin-top: 12px; }
  .card .big { font-size: 1.7rem; font-weight: 700; color: var(--navy); }
  .card .lbl { font-size: .9rem; color: var(--muted); }
  table { width:100%; border-collapse: collapse; }
  th, td { text-align: start; padding: 8px 6px; border-bottom: 1px solid var(--line); }
  th button { font: inherit; font-weight: 700; background:none; border:0; padding:0; color:var(--navy); cursor:pointer; min-height:44px; }
  td.num, th.num { text-align: end; font-variant-numeric: tabular-nums; }
  .bar { display:flex; height: 22px; border-radius: 6px; overflow: hidden; background: var(--paper); }
  .bar i { display:block; height:100%; }
  .row { display:grid; grid-template-columns: 70px 1fr 64px; gap:8px; align-items:center; margin: 8px 0; }
  .row .val { text-align:end; font-variant-numeric: tabular-nums; }
  .legend { display:flex; flex-wrap:wrap; gap:6px 14px; font-size:.9rem; margin-top:8px; }
  .legend span::before { content:""; display:inline-block; width:12px; height:12px; border-radius:3px; background:var(--c); margin-inline-end:6px; }
  .wait i { background: var(--navy); border-radius: 6px; }
  footer { font-size: .88rem; color: var(--muted); margin: 14px 0 30px; }
  footer p { margin: 2px 0; }
  .empty { color: var(--coral); font-weight: 700; }
</style>
</head>
<body>
<main>
  <h1>__TITLE__</h1>
  <div class="banner">مواد اصطناعية للتدريب. العرض فقط: التصفية والفرز يغيّران ما تراه أنت، ولا يغيّران البيانات.</div>
  <div class="filters">
    <label>المطار
      <select id="f-airport"><option value="">كل المطارات</option></select>
    </label>
    <label>الشهر
      <select id="f-month"><option value="">كل الأشهر</option><option value="07">يوليو</option><option value="08">أغسطس</option><option value="09">سبتمبر</option></select>
    </label>
  </div>
  <p id="state" class="lbl"></p>
  <div class="cards">
    <div class="card"><div class="big" id="total">0</div><div class="lbl">إجمالي الطلبات</div></div>
    <div class="card"><div class="big" id="ontime">0%</div><div class="lbl">أُغلقت في الوقت</div></div>
  </div>
  <section>
    <h2>الطلبات بحسب المطار</h2>
    <table>
      <thead><tr><th><button type="button" data-sort="name">المطار</button></th><th class="num"><button type="button" data-sort="n">الطلبات</button></th><th class="num"><button type="button" data-sort="p">أُغلقت في الوقت</button></th></tr></thead>
      <tbody id="t-airports"></tbody>
    </table>
  </section>
  <section>
    <h2>الطلبات بحسب الفئة</h2>
    <div id="cats"></div>
    <div class="legend" id="legend"></div>
  </section>
  <section>
    <h2>متوسط الانتظار</h2>
    <div id="wait" class="wait"></div>
  </section>
  <footer>
    <p>المصدر: نظام طلبات نقاط المساعدة في الصالات.</p>
    <p>النطاق: نقاط المساعدة في صالات المطارات الثلاثة فقط، ولا يشمل مركز الاتصال.</p>
    <p>مالك اللوحة: إدارة خدمات المسافرين.</p>
    <p>آخر تحديث للبيانات: __UPDATED__</p>
  </footer>
</main>
<script>
var ROWS = __ROWS__;
var AIRPORTS = __AIRPORTS__;
var CATS = __CATS__;
var COLORS = ['#0f8a7e', '#12284c', '#b7791f', '#c9503c'];
var sortKey = 'n', sortDir = -1;
function fmt(n) { return n.toLocaleString('en-US'); }
function byId(id) { return document.getElementById(id); }
function clear(el) { while (el.firstChild) el.removeChild(el.firstChild); }
function cell(tag, text, cls) { var e = document.createElement(tag); e.textContent = text; if (cls) e.className = cls; return e; }
function unique(rows) {
  var seen = {}, out = [];
  rows.forEach(function (r) { var k = r[0] + '|' + r[1] + '|' + r[2]; if (!seen[k]) { seen[k] = 1; out.push(r); } });
  return out;
}
function draw() {
  var a = byId('f-airport').value, m = byId('f-month').value;
  var rows = ROWS.filter(function (r) { return (!a || r[1] === a) && (!m || r[0].slice(5, 7) === m); });
  var clean = unique(rows);
  var total = rows.reduce(function (s, r) { return s + r[3]; }, 0);
  var done = rows.reduce(function (s, r) { return s + r[4]; }, 0);
  byId('state').textContent = 'المعروض الآن: ' + (a ? 'مطار ' + AIRPORTS[a] : 'كل المطارات') + '، ' + (m ? byId('f-month').selectedOptions[0].textContent : 'كل الأشهر');
  byId('total').textContent = rows.length ? fmt(total) : 'لا توجد بيانات';
  byId('total').className = rows.length ? 'big' : 'big empty';
  byId('ontime').textContent = rows.length ? (100 * done / total).toFixed(1) + '%' : '';
  var list = Object.keys(AIRPORTS).filter(function (c) { return !a || c === a; }).map(function (c) {
    var rs = clean.filter(function (r) { return r[1] === c; });
    var n = rs.reduce(function (s, r) { return s + r[3]; }, 0);
    var d = rs.reduce(function (s, r) { return s + r[4]; }, 0);
    var w = rs.reduce(function (s, r) { return s + r[5] * r[3]; }, 0);
    return { name: AIRPORTS[c], n: n, p: n ? 100 * d / n : 0, w: n ? w / n : 0, cats: CATS.map(function (cat) { return rs.filter(function (r) { return r[2] === cat; }).reduce(function (s, r) { return s + r[3]; }, 0); }) };
  });
  list.sort(function (x, y) { return sortKey === 'name' ? sortDir * x.name.localeCompare(y.name, 'ar') : sortDir * (x[sortKey] - y[sortKey]); });
  var tb = byId('t-airports'); clear(tb);
  list.forEach(function (x) { var tr = document.createElement('tr'); tr.appendChild(cell('td', x.name)); tr.appendChild(cell('td', fmt(x.n), 'num')); tr.appendChild(cell('td', x.n ? x.p.toFixed(1) + '%' : '', 'num')); tb.appendChild(tr); });
  var max = Math.max.apply(null, list.map(function (x) { return x.n; }).concat([1]));
  var cats = byId('cats'); clear(cats);
  list.forEach(function (x) {
    var row = document.createElement('div'); row.className = 'row'; row.appendChild(cell('span', x.name));
    var bar = document.createElement('div'); bar.className = 'bar';
    x.cats.forEach(function (v, i) { var s = document.createElement('i'); s.style.width = (100 * v / max) + '%'; s.style.background = COLORS[i]; s.title = CATS[i] + ': ' + fmt(v); bar.appendChild(s); });
    row.appendChild(bar); row.appendChild(cell('span', fmt(x.n), 'val')); cats.appendChild(row);
  });
  var wmax = Math.max.apply(null, list.map(function (x) { return x.w; }).concat([1]));
  var wait = byId('wait'); clear(wait);
  list.forEach(function (x) {
    var row = document.createElement('div'); row.className = 'row'; row.appendChild(cell('span', x.name));
    var bar = document.createElement('div'); bar.className = 'bar'; var s = document.createElement('i'); s.style.width = (100 * x.w / wmax) + '%'; bar.appendChild(s);
    row.appendChild(bar); row.appendChild(cell('span', x.n ? x.w.toFixed(1) : '', 'val')); wait.appendChild(row);
  });
}
Object.keys(AIRPORTS).forEach(function (c) { var o = document.createElement('option'); o.value = c; o.textContent = AIRPORTS[c]; byId('f-airport').appendChild(o); });
CATS.forEach(function (c, i) { var s = cell('span', c); s.style.setProperty('--c', COLORS[i]); byId('legend').appendChild(s); });
byId('f-airport').addEventListener('change', draw);
byId('f-month').addEventListener('change', draw);
Array.prototype.forEach.call(document.querySelectorAll('th button'), function (b) {
  b.addEventListener('click', function () { var k = b.getAttribute('data-sort'); sortDir = (k === sortKey) ? -sortDir : (k === 'name' ? 1 : -1); sortKey = k; draw(); });
});
draw();
</script>
</body>
</html>
"""

# ---------------------------------------------------------------- lab 5.1: six drafts
DECISIONS = {"use": "استخدم", "revise": "عدّل", "pause": "أوقف مؤقتًا", "escalate": "صعّد"}
CHECKS = {"source": "المصدر", "sensitivity": "الحساسية", "accuracy": "الدقة", "authorisation": "التفويض", "impact": "الأثر", "none": "لا شيء: الفحوص الخمسة سليمة"}
DRAFTS = [
    {"id": "D1", "title": "رد على مسافر عن المفقودات",
     "role": "أنت موظف في مكتب المفقودات، والرد على المسافرين من عملك.",
     "draft": ["شكرًا لتواصلك. نحتفظ بالمفقودات 90 يومًا من تاريخ العثور عليها، ويمكنك استلام غرضك من مكتب المفقودات في صالة القدوم دون أي إثبات."],
     "source_title": "سياسة المفقودات المعتمدة (مقتطف)",
     "source": ["تحتفظ إدارة المفقودات بالأغراض 60 يومًا من تاريخ العثور عليها.", "يُطلب إثبات هوية عند الاستلام من مكتب المفقودات في صالة القدوم."],
     "decision": "revise", "check": "accuracy",
     "why": "رقمان لا يطابقان السياسة: 90 بدل 60، و«دون أي إثبات» بدل اشتراط إثبات الهوية. المصدر بين يديك والرد من عملك، فتصحّحه بنفسك.",
     "facts": {"draft_has": ["90", "دون أي إثبات"], "source_has": ["60", "إثبات هوية"]}},
    {"id": "D2", "title": "إعلان داخلي عن ورشة",
     "role": "أنت منسق التدريب، وإعلان الورش من عملك.",
     "draft": ["تُعقد ورشة «قراءة لوحات المعلومات» يوم الثلاثاء 2026-10-13 في قاعة التدريب 2 بمطار المرفأ. المقاعد: 20. التسجيل عبر بوابة التدريب حتى 2026-10-08."],
     "source_title": "تقويم التدريب المعتمد (مقتطف)",
     "source": ["ورشة «قراءة لوحات المعلومات»: الثلاثاء 2026-10-13، قاعة التدريب 2، مطار المرفأ.", "المقاعد: 20. آخر موعد للتسجيل عبر بوابة التدريب: 2026-10-08."],
     "decision": "use", "check": "none",
     "why": "كل معلومة تطابق التقويم المعتمد، ولا محتوى شخصيًا أو سريًا، والإعلان من صلاحيتك، وأثره محدود. استخدمه بعد أن قرأته كاملًا.",
     "facts": {"both_have": ["2026-10-13", "قاعة التدريب 2", "20", "2026-10-08"]}},
    {"id": "D3", "title": "ملخص اجتماع يُرسل إلى الإدارة كلها",
     "role": "أنت مقرر الاجتماع، وإرسال الملخص إلى 45 موظفًا في الإدارة من عملك.",
     "draft": ["اتفق الفريق على تحديث دليل الورديات قبل نهاية الشهر. اعتذر بدر السلمي عن الحضور بسبب جلسة علاج طبيعي بعد عملية في الركبة، ويمكن التواصل معه على جواله 0554447781."],
     "source_title": "ملاحظاتك في الاجتماع",
     "source": ["القرار: تحديث دليل الورديات قبل نهاية الشهر.", "غياب: بدر السلمي، بعذر."],
     "decision": "revise", "check": "sensitivity",
     "why": "القرار صحيح، لكن المسودة تنشر سببًا صحيًا ورقم جوال على 45 شخصًا دون حاجة. تحذفهما بنفسك وتكتب «اعتذر أحد الأعضاء»، ثم ترسل.",
     "facts": {"draft_has": ["علاج طبيعي", "عملية في الركبة", "0554447781"]}},
    {"id": "D4", "title": "فقرة تبرير في مقترح",
     "role": "أنت تعدّ مقترحًا لزيادة أجهزة الخدمة الذاتية، وهذه الفقرة هي التبرير كله.",
     "draft": ["تشير دراسة دولية حديثة إلى أن 87% من المسافرين يفضلون نقاط المساعدة الذاتية على الموظفين، ولذلك نقترح مضاعفة عدد الأجهزة."],
     "source_title": "ما وجدته حين بحثت عن المصدر",
     "source": ["سألت المساعد عن الدراسة، فأعطاك عنوانًا لم تعثر عليه في أي مكان.", "لا يوجد في سجلات الشركة استطلاع بهذا الرقم."],
     "decision": "pause", "check": "source",
     "why": "الرقم بلا مصدر يمكن الرجوع إليه، والفقرة كلها مبنية عليه. لا شيء بين يديك تصحّحه به، فتوقف استخدامها إلى أن تجد مصدرًا حقيقيًا أو تبني التبرير على بيانات الشركة.",
     "facts": {"draft_has": ["87%"], "source_missing": True}},
    {"id": "D5", "title": "معايير فرز المتقدمين لوظيفة",
     "role": "أنت عضو في لجنة توظيف، وطُلب منك أن تطبق هذه المعايير اليوم على 60 طلبًا.",
     "draft": ["معايير الفرز المقترحة: يُستبعد المتقدمون فوق 45 عامًا لأنهم أقل تقبلًا للتقنية، وتُفضَّل المتقدمات لأن طبيعة العمل تناسبهن أكثر."],
     "source_title": "الإعلان الوظيفي المعتمد (مقتطف)",
     "source": ["الشروط: شهادة الثانوية أو أعلى، وإجادة العربية والإنجليزية، وخبرة سنة في خدمة العملاء.", "لا يذكر الإعلان شرطًا للعمر ولا للجنس."],
     "decision": "escalate", "check": "impact",
     "why": "صياغة متحيزة تستبعد أشخاصًا بسبب العمر والجنس، وتمس حقوق المتقدمين. ليس لك أن تعدّل معايير التوظيف ولا أن تطبقها: توقف وتصعّد إلى مالك عملية التوظيف ومسؤول الامتثال.",
     "facts": {"draft_has": ["فوق 45 عامًا", "تُفضَّل المتقدمات"], "source_lacks": ["45"]}},
    {"id": "D6", "title": "رد على مورّد",
     "role": "أنت منسق في المشتريات، وطلب منك المورّد جوابًا اليوم.",
     "draft": ["نؤكد لكم تمديد عقد صيانة العربات سنة إضافية بالسعر نفسه، ابتداءً من الشهر القادم."],
     "source_title": "جدول الصلاحيات المعتمد (مقتطف)",
     "source": ["تمديد العقود وتجديدها: صلاحية مدير المشتريات ولجنة العقود.", "منسق المشتريات: إعداد المراسلات ومتابعة المستندات."],
     "decision": "escalate", "check": "authorisation",
     "why": "الصياغة سليمة، لكنها تُلزم الشركة بعقد لسنة، والتمديد صلاحية مدير المشتريات ولجنة العقود. ليس القرار قرارك: ترفعه إلى مشرفك المباشر قبل أي رد.",
     "facts": {"draft_has": ["تمديد عقد"], "source_has": ["صلاحية مدير المشتريات ولجنة العقود"]}},
]

# ---------------------------------------------------------------- lab 6.1: the disclosure line
DISCLOSURE = {
    "output": ["شكرًا لتواصلك. نحتفظ بالمفقودات 60 يومًا من تاريخ العثور عليها، ويمكنك استلام غرضك من مكتب المفقودات في صالة القدوم بعد إبراز إثبات هوية."],
    "assistance": "صاغ «زميل»، المساعد المعتمد في الشركة، المسودة الأولى للرد.",
    "checked": "راجع الموظف مدة الحفظ وشرط إثبات الهوية على سياسة المفقودات المعتمدة، وصحّحهما.",
    "elements": ["المساعدة المستخدمة", "ما جرى التحقق منه"],
    "lines": [
        {"text": "أُعدّت صياغة هذا الرد بمساعدة «زميل»، المساعد المعتمد في الشركة، وراجعتُ مدة الحفظ وشرط إثبات الهوية على سياسة المفقودات المعتمدة.",
         "assistance": "«زميل»", "checked": "سياسة المفقودات", "ok": True, "note": "يسمّي المساعدة وما جرى التحقق منه."},
        {"text": "استعنتُ بالمساعد المعتمد «زميل» في الصياغة فقط، وتحققتُ بنفسي من الأرقام والشروط بمطابقتها بسياسة المفقودات.",
         "assistance": "«زميل»", "checked": "سياسة المفقودات", "ok": True, "note": "العنصران حاضران بصياغة أخرى."},
        {"text": "تمت الاستعانة بالتقنية في إعداد هذا الرد.", "assistance": "", "checked": "", "ok": False,
         "note": "لا يسمّي الأداة ولا ما جرى التحقق منه."},
        {"text": "كتب هذا الرد الذكاء الاصطناعي، ولا أتحمل مسؤولية ما فيه.", "assistance": "", "checked": "", "ok": False,
         "note": "ينقل المسؤولية إلى الأداة، وهي لا تنتقل. ولا يذكر أي تحقق."},
        {"text": "راجعتُ كل ما في هذا الرد.", "assistance": "", "checked": "", "ok": False,
         "note": "يذكر مراجعة عامة، ولا يسمّي المساعدة المستخدمة ولا ما روجع عليه."},
    ],
}


# ---------------------------------------------------------------- writing
def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def csv_text(rows) -> str:
    buf = io.StringIO()
    csv.writer(buf, lineterminator="\n").writerows(rows)
    return buf.getvalue()


def doc_block(lines, title=None) -> str:
    head = f"<h4>{html.escape(title)}</h4>" if title else ""
    return '<div class="box doc">' + head + "".join(f"<p>{html.escape(x)}</p>" for x in lines) + "</div>"


def table_block(rows) -> str:
    out = ["<table>", "<tr>" + "".join(f"<th>{html.escape(c)}</th>" for c in rows[0]) + "</tr>"]
    for r in rows[1:]:
        out.append("<tr>" + "".join(f"<td>{html.escape(c)}</td>" for c in r) + "</tr>")
    return "\n".join(out + ["</table>"])


def inject(page: Path, blocks: dict[str, str]) -> None:
    if not page.exists():
        return
    text = page.read_text(encoding="utf-8")
    for name, body in blocks.items():
        pattern = re.compile(r"(<!-- pack:" + re.escape(name) + r" -->).*?(<!-- /pack:" + re.escape(name) + r" -->)", re.S)
        text, n = pattern.subn(lambda m: m.group(1) + "\n" + body + "\n" + m.group(2), text)
        if n == 0:
            raise SystemExit(f"{page.name}: no block pack:{name}")
    write(page, text)


def main() -> None:
    # lab 1.1
    write(FILES / "vignettes.txt", "\n".join(f"{v[0]}. {v[1]}" for v in VIGNETTES) + "\n")
    # lab 2.1
    for it in ITEMS:
        body = csv_text(it["table"]) if "table" in it else "\n".join(it["text"]) + "\n"
        write(FILES / it["file"], body)
        write(SOL / "sanitised" / (Path(it["file"]).stem + ".txt"), "\n".join(it["sanitised"]) + "\n")
    # lab 3.1
    write(FILES / "meeting_notes.txt", "\n".join(NOTES) + "\n")
    write(SOL / "standin.json", json.dumps(STANDIN, ensure_ascii=False, indent=2) + "\n")
    # lab 4.1
    rows = make_rows()
    write(FILES / "dashboard_data.csv", csv_text([["date", "airport", "category", "requests", "closed_on_time", "avg_wait"]] + rows))
    facts = dashboard_facts(rows)
    summary = ai_summary(facts)
    page = (DASH_HTML.replace("__TITLE__", DASH_TITLE).replace("__UPDATED__", LAST_UPDATE)
            .replace("__ROWS__", json.dumps(rows, ensure_ascii=False, separators=(",", ":")))
            .replace("__AIRPORTS__", json.dumps({c: n for c, n, _b, _w in AIRPORTS}, ensure_ascii=False))
            .replace("__CATS__", json.dumps([c for c, _ in CATEGORIES], ensure_ascii=False)))
    write(FILES / "dashboard.html", page)
    write(FILES / "ai_summary.txt", "ملخص كتبه «زميل» من لقطة للوحة خدمات المسافرين (مواد اصطناعية)\n" + "\n".join(f"{i}. {s['text']}" for i, s in enumerate(summary, 1)) + "\n")
    # lab 5.1
    parts = []
    for d in DRAFTS:
        parts += [f"{d['id']}. {d['title']}", d["role"], "المسودة:"] + d["draft"] + [d["source_title"] + ":"] + d["source"] + [""]
    write(FILES / "drafts.txt", "\n".join(parts))
    # lab 6.1
    write(FILES / "finished_output.txt", "\n".join(["المخرج النهائي:"] + DISCLOSURE["output"] + ["ما فعله المساعد: " + DISCLOSURE["assistance"], "ما راجعه الموظف: " + DISCLOSURE["checked"]]) + "\n")
    # the key
    key = {
        "about": "مفتاح إجابة مختبرات USE-FLU-101. يكتبه labs/_tools/prepare_files.py، ويعيد labs/solutions/check.py حسابه من الملفات.",
        "1.1": {"categories": CATS, "pass": 7, "vignettes": [{"id": v[0], "category": v[2], "why": v[3]} for v in VIGNETTES]},
        "2.1": {"items": [{"id": it["id"], "file": it["file"], "sanitised": "sanitised/" + Path(it["file"]).stem + ".txt",
                           "flagged": [{"detail": f[0], "kind": f[1], "move": f[2]} for f in it["flagged"]], "keep": it["keep"]} for it in ITEMS]},
        "3.1": {"elements": ELEMENTS, "notes": "meeting_notes.txt"},
        "4.1": {"dashboard": facts, "planted": {
            "missing_label": "رسم «متوسط الانتظار» بلا وحدة",
            "outdated_date": f"العنوان يقول الربع الثالث، وآخر تحديث للبيانات {LAST_UPDATE}، وسبتمبر بلا بيانات",
            "inconsistent_total": f"الإجمالي في البطاقة {facts['headline_total']}، ومجموع المطارات في الجدول {facts['sum_of_airports']}، والفرق {facts['difference']}",
            "unclear_definition": "«أُغلقت في الوقت» بلا تعريف للوقت المقصود"},
            "summary": summary},
        "5.1": {"decisions": DECISIONS, "checks": CHECKS, "pass": 5,
                "drafts": [{k: d[k] for k in ("id", "title", "decision", "check", "why", "facts")} for d in DRAFTS]},
        "6.1": DISCLOSURE,
    }
    write(SOL / "key.json", json.dumps(key, ensure_ascii=False, indent=2) + "\n")
    # the lab pages show the same text as the files
    inject(LABS / "M1_1_vignettes.html", {"vignettes": "<table>\n<tr><th>الموقف</th><th>خانتك</th><th>سببك</th></tr>\n" + "\n".join(
        f'<tr><td><b>{v[0]}.</b> {html.escape(v[1])}</td><td class="fill"></td><td class="fill"></td></tr>' for v in VIGNETTES) + "\n</table>",
        "key": "<table>\n<tr><th>الموقف</th><th>الخانة</th><th>السبب</th></tr>\n" + "\n".join(
        f"<tr><td><b>{v[0]}</b></td><td>{CATS[v[2]]}</td><td>{html.escape(v[3])}</td></tr>" for v in VIGNETTES) + "\n</table>"})
    blocks = {}
    for it in ITEMS:
        blocks[it["id"]] = table_block(it["table"]) if "table" in it else doc_block(it["text"])
        blocks[it["id"] + "-key"] = ("<table>\n<tr><th>التفصيل</th><th>نوعه</th><th>الحركة</th></tr>\n" + "\n".join(
            f"<tr><td>{html.escape(f[0])}</td><td>{f[1]}</td><td>{html.escape(f[2])}</td></tr>" for f in it["flagged"]) + "\n</table>\n"
            + doc_block(it["sanitised"], "نسخة منقّاة مرجعية"))
    inject(LABS / "M2_1_sanitise.html", blocks)
    s = STANDIN["3.1"]
    inject(LABS / "M3_1_request.html", {"notes": doc_block(NOTES), "weak-reply": doc_block(s["weak_reply"], "ما أعاده المساعد للطلب العام"),
                                         "good-request": doc_block(GOOD_REQUEST, "طلب مرجعي بعناصره الخمسة"), "good-reply": doc_block(s["good_reply"], "ما أعاده المساعد للطلب المرجعي")})
    inject(LABS / "M4_1_dashboard.html", {"summary": doc_block([f"{i}. {x['text']}" for i, x in enumerate(summary, 1)], "ملخص كتبه «زميل»"),
        "summary-key": "<table>\n<tr><th>الجملة</th><th>الحكم</th><th>لماذا</th></tr>\n" + "\n".join(
            f"<tr><td>{i}</td><td>{'تُقبل' if x['ok'] else 'علامة تحذيرية'}</td><td>{html.escape(x['flag'])}</td></tr>" for i, x in enumerate(summary, 1)) + "\n</table>",
        "numbers": f"<p>الإجمالي في البطاقة <b>{facts['headline_total']:,}</b>، ومجموع المطارات الثلاثة في الجدول <b>{facts['sum_of_airports']:,}</b>. الفرق <b>{facts['difference']:,}</b> طلبًا: أسبوع من طلبات الأمتعة في مطار النخيل حُمّل مرتين ({facts['duplicate_rows']} صفوف مكررة).</p>"})
    dblocks = {}
    for d in DRAFTS:
        dblocks[d["id"]] = (f"<p><b>{html.escape(d['role'])}</b></p>\n" + doc_block(d["draft"], "المسودة") + "\n" + doc_block(d["source"], d["source_title"]))
    dblocks["key"] = "<table>\n<tr><th>المسودة</th><th>القرار</th><th>الفحص</th><th>لماذا</th></tr>\n" + "\n".join(
        f"<tr><td><b>{d['id']}</b></td><td>{DECISIONS[d['decision']]}</td><td>{CHECKS[d['check']]}</td><td>{html.escape(d['why'])}</td></tr>" for d in DRAFTS) + "\n</table>"
    inject(LABS / "M5_1_drafts.html", dblocks)
    inject(LABS / "M6_1_disclosure.html", {"output": doc_block(DISCLOSURE["output"], "المخرج النهائي") + "\n<ul>\n<li><b>ما فعله المساعد:</b> " + html.escape(DISCLOSURE["assistance"]) + "</li>\n<li><b>ما راجعه الموظف:</b> " + html.escape(DISCLOSURE["checked"]) + "</li>\n</ul>",
        "lines": "<table>\n<tr><th>السطر</th><th>الحكم</th><th>لماذا</th></tr>\n" + "\n".join(
            f"<tr><td>{html.escape(x['text'])}</td><td>{'يستوفي العنصرين' if x['ok'] else 'ناقص'}</td><td>{html.escape(x['note'])}</td></tr>" for x in DISCLOSURE["lines"]) + "\n</table>"})
    print(f"files written under {FILES.name}/ and {SOL.name}/")
    print("dashboard:", json.dumps(facts, ensure_ascii=False))


if __name__ == "__main__":
    main()

from pathlib import Path
import io
import json
import altair as alt
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Supply planning assistant | مساعد تخطيط الإمداد", layout="centered"
)

if "lang" not in st.session_state:
    st.session_state["lang"] = "ar"


def flip_language():
    st.session_state["lang"] = "en" if st.session_state["lang"] == "ar" else "ar"


ar = st.session_state["lang"] == "ar"


def t(a, e):
    return a if ar else e


direction = "rtl" if ar else "ltr"
alignment = "right" if ar else "left"
logo_b64 = "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"

st.markdown(
    f"""<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800;900&display=swap');
html, body, .stApp {{font-family:'Cairo','Segoe UI',Tahoma,sans-serif;}}
.stApp, [data-testid="stAppViewContainer"] {{
  background:
    radial-gradient(1000px 460px at 88% -8%, #E7DAF7, transparent 60%),
    radial-gradient(760px 460px at -10% 26%, #EFE8FA, transparent 55%),
    radial-gradient(900px 700px at 50% 115%, #F0EAF9, transparent 60%),
    #F6F4FB !important;
  color:#221233; color-scheme:light;
}}
[data-testid="stHeader"] {{background:transparent!important;pointer-events:none!important;}}
#MainMenu, footer, [data-testid="stToolbar"], [data-testid="stDecoration"],
[data-testid="stDeployButton"], [data-testid="stStatusWidget"] {{display:none!important;}}
.block-container, [data-testid="stMainBlockContainer"] {{max-width:1000px;padding-top:1rem;position:relative;direction:{direction};}}
h1,h2,h3 {{color:#38125F!important;direction:{direction};text-align:{alignment};letter-spacing:-.2px;}}
h3 {{font-size:1.35rem!important;font-weight:800!important;}}
[data-testid="stMarkdownContainer"] {{direction:{direction};text-align:{alignment};}}
[data-testid="stMarkdownContainer"] p, [data-testid="stWidgetLabel"] p {{color:#221233;}}
[data-testid="stWidgetLabel"] p {{font-weight:700;font-size:13.5px;color:#5A4A72!important;}}
[data-testid="stCaptionContainer"] p {{color:#71638A!important;direction:{direction};text-align:{alignment};}}
.stApp button, .stApp input {{font-family:'Cairo','Segoe UI',Tahoma,sans-serif;}}

/* language toggle floating over hero */
[data-testid="stElementContainer"]:has(.lang-marker) {{height:0;min-height:0;}}
[data-testid="stElementContainer"]:has(.lang-marker) + [data-testid="stElementContainer"] {{
  position:absolute;top:34px;inset-inline-end:24px;z-index:60;width:auto;
}}
[data-testid="stElementContainer"]:has(.lang-marker) + [data-testid="stElementContainer"] button {{
  background:rgba(255,255,255,.14);border:1px solid rgba(255,255,255,.5);border-radius:999px;
  min-height:36px!important;padding:2px 18px;backdrop-filter:blur(8px);transition:background .2s;
}}
[data-testid="stElementContainer"]:has(.lang-marker) + [data-testid="stElementContainer"] button:hover {{background:rgba(255,255,255,.3);}}
[data-testid="stElementContainer"]:has(.lang-marker) + [data-testid="stElementContainer"] button p {{color:#fff!important;font-weight:700;font-size:13.5px;}}

/* hero */
.hero {{position:relative;overflow:hidden;border-radius:24px;color:#fff;
  background:linear-gradient(130deg,#1D0631 0%,#3A1163 42%,#5E2399 78%,#7C3BC0 100%);
  padding:32px 28px 22px;margin:0 0 20px;
  box-shadow:0 28px 56px -26px rgba(42,15,77,.6);direction:{direction};text-align:{alignment};}}
.hero::before {{content:"";position:absolute;top:-160px;inset-inline-end:-80px;width:420px;height:420px;border-radius:50%;
  background:radial-gradient(circle,rgba(178,123,255,.35),transparent 68%);pointer-events:none;}}
.hero::after {{content:"";position:absolute;bottom:-190px;inset-inline-start:-60px;width:380px;height:380px;border-radius:50%;
  background:repeating-radial-gradient(circle,rgba(255,255,255,.09) 0 2px,transparent 2px 26px);pointer-events:none;}}
.brand {{display:flex;align-items:center;gap:18px;position:relative;z-index:1;}}
.brand-txt {{min-width:0;}}
.eyebrow {{display:inline-block;font-size:11px;font-weight:800;letter-spacing:1.2px;color:#E7D6FF;
  background:rgba(255,255,255,.12);border:1px solid rgba(255,255,255,.28);border-radius:999px;padding:3px 12px;margin-bottom:8px;}}
.logo {{position:relative;width:84px;height:84px;flex:none;border-radius:50%;
  background:#fff;padding:5px;box-shadow:0 12px 28px rgba(0,0,0,.4),0 0 0 6px rgba(255,255,255,.14),0 0 0 12px rgba(255,255,255,.06);}}
.logo img {{width:100%;height:100%;border-radius:50%;display:block;}}
.h1 {{font-size:27px;font-weight:900;color:#fff;letter-spacing:-.3px;line-height:1.25;}}
.sub {{color:rgba(255,255,255,.8);font-size:13.5px;margin-top:3px;font-weight:600;}}
.hint {{position:relative;z-index:1;margin-top:16px;color:#fff;font-size:14.5px;line-height:1.75;
  background:rgba(255,255,255,.10);border:1px solid rgba(255,255,255,.22);border-radius:14px;padding:9px 16px;}}
@media (max-width:560px) {{
  .hero {{padding:24px 18px 16px;border-radius:20px;}}
  .logo{{width:60px;height:60px;box-shadow:0 10px 22px rgba(0,0,0,.35),0 0 0 4px rgba(255,255,255,.14);}}
  .h1{{font-size:20px}} .sub{{font-size:12px}} .hint{{font-size:13px}} .eyebrow{{font-size:10px;margin-bottom:6px}}
}}

/* KPI cards */
[data-testid="stMetric"] {{background:#fff;border:1px solid #E6DCF3;border-radius:16px;
  padding:16px 20px;position:relative;overflow:hidden;
  box-shadow:0 16px 32px -22px rgba(58,17,99,.35);direction:{direction};text-align:{alignment};
  transition:transform .18s ease, box-shadow .18s ease;}}
[data-testid="stMetric"]:hover {{transform:translateY(-2px);box-shadow:0 22px 40px -22px rgba(58,17,99,.5);}}
[data-testid="stMetric"]::before {{content:"";position:absolute;inset-inline-start:0;top:0;bottom:0;width:5px;
  background:linear-gradient(180deg,#8B4FD8,#4B1F7E);}}
[data-testid="stMetric"] * {{color:#28133F!important;}}
[data-testid="stMetricLabel"] p {{font-size:13px;font-weight:700;color:#71638A!important;}}
[data-testid="stMetricValue"] {{direction:ltr;unicode-bidi:isolate;font-size:30px!important;font-weight:900!important;color:#3A1163!important;}}

/* segmented nav */
[data-testid="stRadio"] {{direction:{direction};}}
[data-testid="stRadio"] [role="radiogroup"] {{gap:4px;flex-wrap:wrap;background:#EAE3F6;border:1px solid #DDD1EF;
  border-radius:999px;padding:5px;display:inline-flex;}}
[data-testid="stRadioOption"] {{background:transparent;border:0;border-radius:999px;padding:5px 18px;min-height:40px;
  box-shadow:none;cursor:pointer;transition:background .15s;}}
[data-testid="stRadioOption"]:hover {{background:rgba(255,255,255,.65);}}
[data-testid="stRadioOption"] p {{color:#4A2A74!important;font-weight:700;font-size:14px;}}
[data-testid="stRadioOption"] > div > div:first-child {{display:none!important;}}
[data-testid="stRadioOption"][data-selected="true"] {{background:linear-gradient(135deg,#6D2DB0,#4B1F7E);box-shadow:0 8px 18px -10px rgba(75,31,126,.8);}}
[data-testid="stRadioOption"][data-selected="true"] p {{color:#fff!important;}}

/* inputs */
[data-baseweb="select"] > div, [data-baseweb="select"] > div > div, [data-baseweb="input"], [data-baseweb="input"] > div,
input, [data-testid="stNumberInputContainer"], [data-testid="stNumberInputContainer"] > div {{
  background:#fff!important;color:#221233!important;border-radius:12px!important;}}
[data-testid="stSelectbox"] .react-aria-ComboBox > div {{background:#fff!important;border-radius:12px!important;border-color:#D5C6E8!important;}}
[data-testid="stSelectbox"] .react-aria-ComboBox input {{background:#fff!important;color:#221233!important;-webkit-text-fill-color:#221233!important;}}
[data-testid="stSelectbox"] .react-aria-ComboBox button {{background:#fff!important;color:#221233!important;min-height:0!important;border:0!important;box-shadow:none!important;}}
[data-testid="stSelectbox"] .react-aria-ComboBox button:hover {{background:#F1E8FB!important;color:#5E2399!important;}}
[data-testid="stSelectbox"] .react-aria-ComboBox > div:focus-within {{border-color:#5E2399!important;box-shadow:0 0 0 1px #5E2399!important;}}
[data-baseweb="select"] svg, [data-testid="stNumberInput"] svg {{fill:#221233!important;color:#221233!important;}}
[data-baseweb="select"] span, [data-baseweb="select"] input, input {{color:#221233!important;-webkit-text-fill-color:#221233!important;}}
[data-baseweb="input"]:focus-within, [data-baseweb="select"] > div:focus-within, [data-testid="stNumberInputContainer"]:focus-within {{
  border-color:#5E2399!important;box-shadow:0 0 0 1px #5E2399!important;}}
[data-baseweb="input"], [data-testid="stNumberInputContainer"], [data-baseweb="select"] > div {{border-color:#D5C6E8!important;}}
[data-baseweb="input"] button, [data-testid="stNumberInput"] button {{background:#F1E8FB!important;color:#5E2399!important;min-height:0!important;}}
[data-baseweb="select"], [data-testid="stNumberInput"] {{direction:{direction};text-align:{alignment};}}
[data-baseweb="popover"] *, [role="listbox"], [role="option"] {{background:#fff!important;color:#221233!important;}}
[data-testid="stNumberInput"] input {{direction:ltr;text-align:center;}}
button {{min-height:44px;}}
[data-testid="stBaseButton-secondary"] {{background:#fff;border:1px solid #C9B6E4;border-radius:999px;transition:all .15s;}}
[data-testid="stBaseButton-secondary"]:hover {{border-color:#5E2399;}}
[data-testid="stBaseButton-secondary"] p {{color:#5E2399!important;font-weight:700;}}
[data-testid="stDownloadButton"] button {{background:linear-gradient(135deg,#6D2DB0,#4B1F7E);border:0;border-radius:999px;
  box-shadow:0 10px 22px -12px rgba(75,31,126,.7);}}
[data-testid="stDownloadButton"] button p {{color:#fff!important;font-weight:700;}}

/* expanders & tables */
[data-testid="stExpander"] {{background:#fff;border:1px solid #E6DCF3;border-radius:16px;box-shadow:0 12px 26px -22px rgba(58,17,99,.4);}}
[data-testid="stExpander"] summary {{direction:{direction};text-align:{alignment};font-weight:700;}}
[data-testid="stDataFrame"], [data-testid="stDataframe"] {{border-radius:16px;overflow:hidden;border:1px solid #E6DCF3;
  box-shadow:0 14px 30px -24px rgba(58,17,99,.4);}}
code, pre {{direction:ltr;text-align:left;}}

[data-testid="stAlert"] {{background:#FFF3EA;color:#221233;border:1px solid #F2C6A6;border-radius:14px;}}
[data-testid="stAlert"] * {{color:#221233!important;}}

/* pills & notes */
.pill {{display:inline-block;font-weight:800;font-size:12.5px;padding:3px 14px;border-radius:999px;margin:2px 0 8px;letter-spacing:.2px;}}
.pill.re {{background:#EFE3FB;color:#6D2DB0;border:1px solid #D9C2F2;}}
.pill.ov {{background:#FFF0E6;color:#D96B2B;border:1px solid #F3C9A8;}}
.pill.ok {{background:#DDF6EF;color:#0C8A74;border:1px solid #A8E2D5;}}
.pill.ch {{background:#FFF0E6;color:#D96B2B;border:1px solid #F3C9A8;}}
.note {{background:#F1EAFB;border:1px solid #D5C6E8;border-radius:12px;padding:9px 14px;font-size:14px;color:#221233;margin:6px 0;}}
.note.ok {{background:#DDF6EF;border-color:#9ADED2;}}
.note.warn {{background:#FFF0E6;border-color:#F2C6A6;}}

/* footer credit */
.credit {{margin-top:30px;background:linear-gradient(135deg,#1D0631,#3A1163 60%,#52218C);border:0;border-radius:20px;padding:20px 22px;
  text-align:center;box-shadow:0 22px 44px -24px rgba(42,15,77,.65);color:#fff;}}
.credit .c1 {{font-weight:900;color:#fff;font-size:16px;}}
.credit .c2 {{font-weight:600;color:rgba(255,255,255,.85);font-size:13.5px;}}
.credit .c3 {{margin-top:9px;color:rgba(255,255,255,.6);font-size:12px;}}
hr {{border-color:#E2D8F0;}}

/* three-question hero */
.qs {{position:relative;z-index:1;margin-top:16px;}}
.qs-title {{color:rgba(255,255,255,.85);font-size:13px;font-weight:700;margin-bottom:8px;}}
.q {{display:flex;align-items:center;gap:12px;background:rgba(255,255,255,.10);border:1px solid rgba(255,255,255,.22);
  border-radius:14px;padding:9px 14px;margin-bottom:8px;color:#fff;}}
.q:last-child {{margin-bottom:0;}}
.qn {{flex:none;width:26px;height:26px;border-radius:50%;background:#fff;color:#4B1F7E;font-weight:900;font-size:14px;
  display:flex;align-items:center;justify-content:center;direction:ltr;}}
.q b {{display:block;font-size:14.5px;font-weight:800;}}
.q i {{display:block;font-style:normal;font-size:12px;color:rgba(255,255,255,.75);margin-top:1px;}}
@media (max-width:560px) {{.q b{{font-size:13px}} .q i{{font-size:11px}}}}

/* expander contrast repair (light + dark system preference) */
[data-testid="stExpander"] summary, [data-testid="stExpander"] summary:hover,
[data-testid="stExpander"] summary[aria-expanded="true"] {{background:#F8F5FC!important;}}
[data-testid="stExpander"] summary p, [data-testid="stExpander"] summary span {{color:#3A1163!important;-webkit-text-fill-color:#3A1163!important;}}
[data-testid="stExpander"] summary svg {{fill:#5E2399!important;color:#5E2399!important;}}
</style>""",
    unsafe_allow_html=True,
)

# Use the checked workbook snapshot. This app does not recalculate Excel formulas.
data = json.loads((Path(__file__).parent / "2-data.json").read_text(encoding="utf-8"))
items = data["items"]
if st.session_state.get("custom_items"):
    items = st.session_state["custom_items"]
for row_number, i in enumerate(items, 1):
    i["row"] = row_number
by_code = {i["code"]: i for i in items}


def name(i):
    return i["description"] if ar else i["name"]


def n(x):
    return f"{x:,.2f}".rstrip("0").rstrip(".")


def status_pill(i):
    states = {
        "REORDER": t("محتاج مراجعة لإعادة الطلب", "Review for replenishment"),
        "OVERSTOCK": t("رصيد أعلى من الحد الأقصى", "Stock above maximum"),
        "OK": t("داخل حدود السياسة", "Within policy limits"),
        "CHECK": t("محتاج فحص بيانات الرصيد", "Check stock data"),
    }
    cls = {
        "REORDER": "re",
        "OVERSTOCK": "ov",
        "OK": "ok",
        "CHECK": "ch",
    }[i["status"]]
    st.markdown(
        f'<div class="pill {cls}">{states[i["status"]]}</div>',
        unsafe_allow_html=True,
    )


# Keep explanations tied to the stored workbook policy, not purchase instructions.
def explain(i):
    st.subheader(i["code"] + " | " + name(i))
    status_pill(i)
    facts = [
        (t("الرصيد الحالي", "On-hand stock"), "stock"),
        (t("المطلوب توريده بالفعل", "Open orders"), "onOrder"),
        (
            t(
                "المركز المخزني: الرصيد والطلبات المفتوحة",
                "Inventory position: stock + open orders",
            ),
            "position",
        ),
        (t("نقطة إعادة الطلب", "Reorder point"), "rop"),
        (t("الحد الأقصى", "Maximum level"), "max"),
        (t("توقع استهلاك الشهر التالي", "Next-month demand forecast"), "forecast"),
        (t("مخزون الأمان", "Safety stock"), "safety"),
        (t("الكمية المقترحة", "Suggested quantity"), "suggested"),
    ]
    for label, key in facts:
        st.write(f"**{label}**: {n(i[key])} {i['unit']}")
    if i["status"] == "REORDER":
        st.write(
            t(
                "المركز المخزني أقل من نقطة إعادة الطلب. الكمية المقترحة للوصول للحد الأقصى. راجع موعد وصول الطلبات وخطة التوسع والميزانية قبل القرار.",
                "Inventory position is below the reorder point. The suggested quantity brings it up to the maximum level. Review delivery dates, rollout plans and budget before deciding.",
            )
        )
    elif i["status"] == "OVERSTOCK":
        st.write(
            t(
                "الرصيد أعلى من الحد الأقصى. راجع إعادة التوزيع قبل طلب كميات إضافية.",
                "On-hand stock exceeds the maximum level. Review redistribution before ordering more.",
            )
        )
    elif i["status"] == "CHECK":
        st.warning(
            t(
                "الرصيد بالسالب. راجع حركات المخزن.",
                "Stock is negative. Check recorded movements.",
            )
        )
    else:
        st.write(
            t(
                "داخل حدود سياسة الملف. ده مش ضمان ضد تأخير التوريد.",
                "Within the workbook policy limits. This does not rule out late-delivery risk.",
            )
        )
    method = (
        t("التمهيد الأسي", "Exponential smoothing")
        if i["method"] == "Exp. smoothing"
        else t("متوسط متحرك لثلاثة أشهر", "Three-month moving average")
    )
    st.write(t("طريقة التنبؤ: ", "Forecast method: ") + method)


def calculate_scenario(item, stock, on_order):
    """Match Analysis!AC:AG and AI; keep demand-policy inputs unchanged."""
    result = dict(item)
    position = stock + on_order
    status = (
        "CHECK"
        if stock < 0
        else (
            "REORDER"
            if position < item["rop"]
            else "OVERSTOCK" if stock > item["max"] else "OK"
        )
    )
    quantity = max(0, item["max"] - position) if status == "REORDER" else 0
    result.update(
        stock=stock,
        onOrder=on_order,
        position=position,
        status=status,
        suggested=quantity,
        order_value=quantity * item["price"],
        excess_value=max(0, stock - item["max"]) * item["price"],
        cover=stock / item["forecast"] if item["forecast"] > 0 else None,
    )
    return result


SHEET_INPUT_COLUMNS = [
    "Code", "Item", "Description", "Unit", "Supplier", "Unit price (EGP)",
    "Annual usage", "Monthly forecast", "Safety stock", "ROP", "EOQ", "Max",
    "On hand", "Open orders",
]
SHEET_NUMERIC_COLUMNS = SHEET_INPUT_COLUMNS[5:]
SHEET_EXPORT_COLUMNS = SHEET_INPUT_COLUMNS[:5] + SHEET_INPUT_COLUMNS[5:] + [
    "Row", "Net position", "Status", "Suggested qty", "MAPE",
]


def cell_text(v):
    s = "" if v is None else str(v).strip()
    return "" if s.lower() == "nan" else s


def sheet_export_df(rows):
    return pd.DataFrame(
        [
            [
                i["code"], i["name"], i["description"], i["unit"], i["supplier"],
                i["price"], i["annual"], round(i["forecast"], 1), i["safety"],
                i["rop"], i["eoq"], i["max"], i["stock"], i["onOrder"],
                i["row"], i["position"], i["status"], i["suggested"],
                round(i["mape"], 3),
            ]
            for i in rows
        ],
        columns=SHEET_EXPORT_COLUMNS,
    )


def check_columns(df):
    missing = [c for c in SHEET_INPUT_COLUMNS if c not in df.columns]
    if missing:
        return t(
            "أعمدة ناقصة: " + "، ".join(missing) + ". حمّل الشيت الحالي أو القالب وعدّل عليه بنفس الأعمدة.",
            "Missing columns: " + ", ".join(missing) + ". Download the current sheet or the template and edit it with the same columns.",
        )
    return None


def row_to_item(r, pos, digits):
    code = cell_text(r["Code"]).translate(digits)
    if not code:
        return None, t(
            f"صف رقم {pos}: الكود فاضي.",
            f"Row {pos}: the code is empty.",
        )
    vals = {}
    bad = []
    for c in SHEET_NUMERIC_COLUMNS:
        raw = cell_text(r[c]).replace(",", "").translate(digits)
        try:
            vals[c] = float(raw)
        except ValueError:
            bad.append(c)
    if bad:
        return None, t(
            f"صف رقم {pos} ({code}): قيم مش رقمية في " + "، ".join(bad),
            f"Row {pos} ({code}): non-numeric values in " + ", ".join(bad),
        )
    name_en = cell_text(r["Item"])
    return {
        "row": pos,
        "code": code,
        "name": name_en,
        "description": cell_text(r["Description"]) or name_en,
        "unit": cell_text(r["Unit"]) or "PCS",
        "supplier": cell_text(r["Supplier"]),
        "price": vals["Unit price (EGP)"],
        "annual": vals["Annual usage"],
        "forecast": vals["Monthly forecast"],
        "safety": vals["Safety stock"],
        "rop": vals["ROP"],
        "eoq": vals["EOQ"],
        "max": vals["Max"],
        "stock": vals["On hand"],
        "onOrder": vals["Open orders"],
        "method": "Exp. smoothing",
        "mape": 0.0,
        "class": "",
    }, None


def parse_uploaded_sheet(df):
    problem = check_columns(df)
    if problem:
        return None, problem
    if len(df) == 0:
        return None, t("الملف مفيهوش صفوف أصناف.", "The file has no item rows.")
    if len(df) > 500:
        return None, t("الحد الأقصى 500 صنف في الشيت الواحد.", "Up to 500 items per sheet.")
    digits = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")
    out = []
    for pos, (_, r) in enumerate(df.iterrows(), 1):
        item, problem = row_to_item(r, pos, digits)
        if problem:
            return None, problem
        out.append(calculate_scenario(item, item["stock"], item["onOrder"]))
    codes = [i["code"] for i in out]
    if len(set(codes)) != len(codes):
        return None, t(
            "في أكواد مكررة في الشيت. كل صنف لازم كوده يكون مختلف.",
            "Duplicate codes in the sheet. Every item needs a unique code.",
        )
    return out, None


def merge_changes_sheet(df, existing):
    problem = check_columns(df)
    if problem:
        return None, problem
    digits = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")
    existing_codes = {e["code"] for e in existing}
    updates = {}
    adds = []
    seen = set()
    changed = 0
    for pos, (_, r) in enumerate(df.iterrows(), 1):
        code = cell_text(r["Code"]).translate(digits)
        action = cell_text(r["status"]).lower()
        if not action:
            continue
        changed += 1
        if not code:
            return None, t(
                f"صف رقم {pos}: الكود فاضي.",
                f"Row {pos}: the code is empty.",
            )
        if action not in ("add", "update"):
            return None, t(
                f"صف رقم {pos} ({code}): اختار Add أو Update في عمود status.",
                f"Row {pos} ({code}): choose Add or Update in the status column.",
            )
        if code in seen:
            return None, t(
                f"الكود {code} متكرر في الملف.",
                f"Code {code} appears twice in the file.",
            )
        seen.add(code)
        item, problem = row_to_item(r, pos, digits)
        if problem:
            return None, problem
        if action == "add":
            if code in existing_codes:
                return None, t(
                    f"صف رقم {pos} ({code}): الكود موجود بالفعل. استخدم Update بدل Add.",
                    f"Row {pos} ({code}): this code already exists. Use Update instead of Add.",
                )
            adds.append(item)
        else:
            if code not in existing_codes:
                return None, t(
                    f"صف رقم {pos} ({code}): الكود مش موجود عشان تعمله Update. استخدم Add أو صحّح الكود.",
                    f"Row {pos} ({code}): no item with this code to update. Use Add or fix the code.",
                )
            updates[code] = item
    if changed == 0:
        return None, t(
            "الملف مفيهوش صفوف فيها Add أو Update.",
            "The file has no rows marked Add or Update.",
        )
    merged = []
    for e in existing:
        if e["code"] in updates:
            u = updates[e["code"]]
            u["row"] = e["row"]
            merged.append(calculate_scenario(u, u["stock"], u["onOrder"]))
        else:
            merged.append(e)
    next_row = max((e["row"] for e in existing), default=0)
    for a in adds:
        next_row += 1
        a["row"] = next_row
        merged.append(calculate_scenario(a, a["stock"], a["onOrder"]))
    return merged, None


def template_df(rows):
    d = sheet_export_df(rows).drop(
        columns=["Row", "Net position", "Status", "Suggested qty", "MAPE"]
    )
    d["status"] = ""
    return d


def handle_upload():
    up = st.session_state.get(f"sheet_upload_{st.session_state.get('upload_seq', 0)}")
    if up is None:
        return
    try:
        if up.name.lower().endswith(".csv"):
            df_up = pd.read_csv(up)
        else:
            df_up = pd.read_excel(up)
    except Exception:
        st.session_state["upload_error"] = t(
            "تعذر قراءة الملف. تأكد إنه Excel أو CSV سليم.",
            "Could not read the file. Make sure it is a valid Excel or CSV file.",
        )
        return
    if "status" in df_up.columns:
        base = st.session_state.get("custom_items") or json.loads(
            (Path(__file__).parent / "2-data.json").read_text(encoding="utf-8")
        )["items"]
        new_items, problem = merge_changes_sheet(df_up, base)
    else:
        new_items, problem = parse_uploaded_sheet(df_up)
    if problem:
        st.session_state["upload_error"] = problem
    else:
        st.session_state.pop("upload_error", None)
        st.session_state["custom_items"] = new_items


def dashboard_view():
    # KPIs and aggregates from the stored workbook snapshot (Analysis!AE5:AG69).
    st.subheader(t("لوحة متابعة المخزون", "Inventory dashboard"))
    cols = st.columns(4)
    for col, value, label in zip(
        cols,
        [
            len(items),
            sum(i["status"] == "REORDER" for i in items),
            sum(i["status"] == "OVERSTOCK" for i in items),
            sum(i["status"] == "OK" for i in items),
        ],
        [
            t("الأصناف", "Items"),
            t("مراجعة طلب", "Reorder review"),
            t("رصيد زائد", "Above maximum"),
            t("داخل الحدود", "Within limits"),
        ],
    ):
        col.metric(label, value)
    total_order = sum(i["suggested"] * i["price"] for i in items)
    total_excess = sum(max(0, i["stock"] - i["max"]) * i["price"] for i in items)
    vals = st.columns(2)
    vals[0].metric(
        t("قيمة الطلبات المقترحة", "Suggested order value"), f"{total_order:,.0f} EGP"
    )
    vals[1].metric(
        t("قيمة المخزون الزائد", "Excess stock value"), f"{total_excess:,.0f} EGP"
    )
    status_names = {
        "REORDER": t("مراجعة طلب", "Reorder"),
        "OVERSTOCK": t("رصيد زائد", "Overstock"),
        "OK": t("داخل الحدود", "OK"),
        "CHECK": t("فحص بيانات", "Check data"),
    }
    def light_chart(chart, height=260):
        return (
            chart.properties(height=height)
            .configure(background="transparent")
            .configure_view(stroke=None)
            .configure_axis(
                labelColor="#3A1163",
                titleColor="#71638A",
                labelFont="Cairo",
                titleFont="Cairo",
                labelFontSize=12,
                gridColor="#E9E0F5",
                domainColor="#CDBDE2",
            )
        )

    st.write(t("توزيع حالات الأصناف", "Item status breakdown"))
    counts = {}
    for i in items:
        key = status_names[i["status"]]
        counts[key] = counts.get(key, 0) + 1
    st_label, n_label = t("الحالة", "Status"), t("عدد الأصناف", "Items")
    cdf = pd.DataFrame({st_label: list(counts.keys()), n_label: list(counts.values())})
    bars = (
        alt.Chart(cdf)
        .mark_bar(color="#6D2DB0", cornerRadiusTopLeft=8, cornerRadiusTopRight=8)
        .encode(
            x=alt.X(f"{st_label}:N", sort="-y", title=None, axis=alt.Axis(labelAngle=0)),
            y=alt.Y(f"{n_label}:Q", title=n_label),
        )
    )
    labels = bars.mark_text(dy=-8, color="#3A1163", fontWeight=700, font="Cairo").encode(
        text=alt.Text(f"{n_label}:Q")
    )
    st.altair_chart(light_chart(bars + labels), width="stretch")
    st.write(
        t("قيمة الطلبات المقترحة حسب المورد", "Suggested order value by supplier")
    )
    by_supplier = {}
    for i in items:
        if i["status"] == "REORDER":
            by_supplier[i["supplier"]] = (
                by_supplier.get(i["supplier"], 0) + i["suggested"] * i["price"]
            )
    sup_label = t("المورد", "Supplier")
    sdf = pd.DataFrame(
        {sup_label: list(by_supplier.keys()), "EGP": list(by_supplier.values())}
    )
    sbars = (
        alt.Chart(sdf)
        .mark_bar(color="#7A45B8", cornerRadiusTopLeft=8, cornerRadiusTopRight=8)
        .encode(
            x=alt.X(f"{sup_label}:N", sort="-y", title=None, axis=alt.Axis(labelAngle=0)),
            y=alt.Y("EGP:Q", title=t("قيمة الطلب (EGP)", "Order value (EGP)"), axis=alt.Axis(format="~s")),
        )
    )
    slabels = sbars.mark_text(dy=-8, color="#3A1163", fontWeight=700, font="Cairo", fontSize=12).encode(
        text=alt.Text("EGP:Q", format=",.0f")
    )
    st.altair_chart(light_chart(sbars + slabels), width="stretch")

    st.write(t("ملخص الموردين", "Supplier summary"))
    sup_rows = []
    for s in sorted({i["supplier"] for i in items}):
        si = [i for i in items if i["supplier"] == s]
        sup_rows.append(
            {
                t("المورد", "Supplier"): s,
                t("عدد الأصناف", "Items"): len(si),
                t("أصناف تحتاج طلب", "Need reorder"): sum(x["status"] == "REORDER" for x in si),
                t("قيمة الطلبات المقترحة (EGP)", "Suggested order value (EGP)"): f"{sum(x['suggested'] * x['price'] for x in si):,.0f}",
                t("أصناف فوق الحد الأقصى", "Above maximum"): sum(x["status"] == "OVERSTOCK" for x in si),
                t("قيمة الرصيد الزائد (EGP)", "Excess stock value (EGP)"): f"{sum(max(0, x['stock'] - x['max']) * x['price'] for x in si):,.0f}",
            }
        )
    st.dataframe(pd.DataFrame(sup_rows), hide_index=True, width="stretch")
    st.caption(
        t(
            "الجدول يلخص اعتمادك على كل مورد من بيانات الشيت الحالية. تقييم مخاطر مورد (التزام بالمواعيد، جودة، استقرار أسعار) يحتاج بيانات أداء توريد غير موجودة في الملف.",
            "This table summarizes your exposure to each supplier from current workbook data. Rating a supplier as risky (on-time delivery, quality, price stability) needs delivery-performance data that is not in the workbook.",
        )
    )
    st.write(
        t(
            "الأصناف المحتاجة إعادة طلب، مرتبة بقيمة الطلب",
            "Items needing reorder, ranked by order value",
        )
    )
    rows = sorted(
        (i for i in items if i["status"] == "REORDER"),
        key=lambda i: i["suggested"] * i["price"],
        reverse=True,
    )
    st.dataframe(
        pd.DataFrame(
            [
                {
                    t("الكود", "Code"): i["code"],
                    t("الصنف", "Item"): name(i),
                    t("الكمية المقترحة", "Suggested qty"): i["suggested"],
                    t("الوحدة", "Unit"): i["unit"],
                    t("قيمة الطلب (EGP)", "Order value (EGP)"): f"{i['suggested'] * i['price']:,.0f}",
                }
                for i in rows
            ]
        ),
        hide_index=True,
        width="stretch",
    )
    st.caption(
        t(
            "الكمية المقترحة توصل المخزون للحد الأقصى حسب سياسة الملف. تحديد موعد الشراء الفعلي يحتاج مواعيد تسليم الموردين وخطة المشاريع، وهي غير موجودة في الملف.",
            "Suggested quantities bring stock up to the workbook maximum level. Actual buy timing needs supplier lead times and the project schedule, which are not in the workbook.",
        )
    )

def scenario_editor(item):
    st.subheader(t("تجربة كميات جديدة", "Quantity scenario"))
    st.markdown(
        f'<div class="note">{t("التعديلات تجربة خاصة بجلستك فقط. لا تغيّر Excel أو بيانات الزوار الآخرين، وليست أمر شراء.", "Trial changes belong only to this session. They do not change Excel or other visitors data and do not place orders.")}</div>',
        unsafe_allow_html=True,
    )
    st.write(
        t(
            "اختر الصنف بالأعلى، ثم عدّل الرصيد أو الطلبات المفتوحة. اضغط Enter أو اخرج من الحقل لتحديث النتيجة.",
            "Choose an item above, then edit stock or open orders. Press Enter or leave the field to update the result.",
        )
    )
    key = "trial_" + item["code"]
    if st.button(
        t("استرجاع كميات الملف لهذا الصنف", "Reset this item to workbook quantities")
    ):
        st.session_state[key + "_stock"] = float(item["stock"])
        st.session_state[key + "_orders"] = float(item["onOrder"])
        st.rerun()
    stock = st.number_input(
        t("رصيد المخزن التجريبي", "Trial stock on hand"),
        value=float(item["stock"]),
        step=1.0,
        key=key + "_stock",
    )
    orders = st.number_input(
        t("الطلبات المفتوحة التجريبية", "Trial open orders"),
        min_value=0.0,
        value=float(item["onOrder"]),
        step=1.0,
        key=key + "_orders",
    )
    result = calculate_scenario(item, stock, orders)
    st.caption(
        t(
            "الثابت من الملف: التنبؤ ومخزون الأمان ونقطة إعادة الطلب وEOQ والحد الأقصى وسعر الوحدة. لا يُعاد حساب التنبؤ عند تغيير الرصيد.",
            "Fixed workbook inputs: forecast, safety stock, reorder point, EOQ, maximum level and unit cost. Stock edits do not recalculate the forecast.",
        )
    )
    st.write(
        t("مقارنة بالملف: ", "Workbook baseline: ")
        + t("الرصيد ", "stock ")
        + n(item["stock"])
        + " | "
        + t("طلبات مفتوحة ", "open orders ")
        + n(item["onOrder"])
    )
    st.markdown(
        f'<div class="note ok">{t("نتيجة السيناريو المعاد حسابها أدناه، وليست القيم الأصلية المخزنة في الشيت.", "Recalculated scenario results below, not the original stored sheet values.")}</div>',
        unsafe_allow_html=True,
    )
    explain(result)
    st.write(
        t("قيمة الطلب المقترح: ", "Suggested order value: ")
        + n(result["order_value"])
        + " EGP"
    )
    st.write(t("قيمة الزيادة: ", "Excess value: ") + n(result["excess_value"]) + " EGP")
    st.write(
        t("تغطية المخزون بالشهور: ", "Months of stock cover: ")
        + (n(result["cover"]) if result["cover"] is not None else t("غير متاحة", "N/A"))
    )
    st.caption(
        t(
            "قواعد التحليل: المركز = الرصيد + الطلبات المفتوحة؛ CHECK للرصيد السالب، ثم REORDER لو المركز أقل من نقطة الطلب، ثم OVERSTOCK لو الرصيد فوق الحد الأقصى، وإلا OK. كمية الطلب = الحد الأقصى ناقص المركز فقط عند REORDER.",
            "Rules: position = stock + open orders; CHECK for negative stock, then REORDER below reorder point, then OVERSTOCK above maximum, otherwise OK. Suggested quantity = maximum minus position only for REORDER.",
        )
    )



st.markdown('<span class="lang-marker"></span>', unsafe_allow_html=True)
st.button(t("English", "عربي"), key="lang_toggle", on_click=flip_language)

st.markdown(
    f"""<div class="hero">
  <div class="brand">
    <div class="logo"><img src="data:image/png;base64,{logo_b64}" alt="WE"></div>
    <div class="brand-txt">
      <div class="eyebrow">{t("WE • قطاع التخطيط", "WE · Planning Sector")}</div>
      <div class="h1">{t("مساعد تخطيط الإمداد", "Supply planning assistant")}</div>
    </div>
  </div>
  <div class="qs">
    <div class="qs-title">{t("إجابة لحظية على أهم 3 أسئلة:", "Instant answers to the top 3 questions:")}</div>
    <div class="q"><span class="qn">1</span><div><b>{t("أشتري إيه وإمتى وبكام؟", "What do I buy, when, and for how much?")}</b><i>{t("منع العجز وتوقف المشاريع", "Preventing shortages and project stoppages")}</i></div></div>
    <div class="q"><span class="qn">2</span><div><b>{t("فين الفلوس المجمدة والراكدة في المخزن؟", "Where is the cash frozen and stagnant in the warehouse?")}</b><i>{t("ترشيد السيولة", "Liquidity optimization")}</i></div></div>
    <div class="q"><span class="qn">3</span><div><b>{t("مين الموردين اللي أعتمد عليهم ومين اللي بيمثل خطر عليا؟", "Which suppliers can I rely on, and which are a risk to me?")}</b><i>{t("إدارة مخاطر التوريد", "Supply risk management")}</i></div></div>
  </div>
</div>""",
    unsafe_allow_html=True,
)

options = ["dashboard", "items", "analysis", "sheet", "scenario"]
labels = [
    t("لوحة المتابعة", "Dashboard"),
    t("الأصناف", "Items"),
    t("تحليل المخزون", "Inventory analysis"),
    t("جدول الأصناف", "Items sheet"),
    t("تجربة الكميات", "What-if scenario"),
]
mode = st.radio(
    t("اختار العرض", "Choose a view"),
    options,
    format_func=lambda v: labels[options.index(v)],
    horizontal=True,
)
code = st.selectbox(
    t("اختار الصنف", "Choose an item"),
    list(by_code),
    format_func=lambda x: x + " | " + name(by_code[x]),
)
q = st.text_input(
    t("ابحث بكود الصنف أو اسم الصنف", "Search by item code or name")
)
matches = []
if q:
    q = q.strip().lower().translate(str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789"))
    terms = {
        "داش": "dashboard",
        "dashboard": "dashboard",
        "طلب": "analysis",
        "reorder": "analysis",
        "زائد": "analysis",
        "excess": "analysis",
        "تحليل": "analysis",
        "analysis": "analysis",
    }
    if q in terms:
        mode = terms[q]
    else:
        matches = [
            i
            for i in items
            if q in i["code"].lower()
            or q in i["name"].lower()
            or q in i["description"].lower()
        ]
        mode = "search" if matches else "unsupported"
st.divider()
if mode == "dashboard":
    dashboard_view()
elif mode == "search":
    st.subheader(t(f"نتائج البحث: {len(matches)} صنف", f"Search results: {len(matches)} items"))
    for i in matches[:10]:
        with st.expander(i["code"] + " | " + name(i), expanded=i is matches[0]):
            explain(i)
    if len(matches) > 10:
        st.caption(
            t(
                f"معروض أول 10 نتائج من {len(matches)}. قيّد البحث أكثر للوصول لصنف محدد.",
                f"Showing the first 10 of {len(matches)}. Narrow the search for a specific item.",
            )
        )
elif mode == "items":
    explain(by_code[code])
elif mode == "analysis":
    st.subheader(t("تحليل المخزون", "Inventory analysis"))
    reorder_rows = [i for i in items if i["status"] == "REORDER"]
    excess_rows = [i for i in items if i["status"] == "OVERSTOCK"]
    st.write(
        t(
            f"محتاج مراجعة لإعادة الطلب: {len(reorder_rows)} صنف. الترتيب حسب الشيت، مش ترتيب أولوية.",
            f"Needs reorder review: {len(reorder_rows)} items. Workbook order, not a priority ranking.",
        )
    )
    for i in reorder_rows:
        with st.expander(i["code"] + " | " + name(i)):
            explain(i)
    st.divider()
    st.write(
        t(
            f"رصيد أعلى من الحد الأقصى: {len(excess_rows)} صنف.",
            f"Stock above maximum: {len(excess_rows)} items.",
        )
    )
    for i in excess_rows:
        with st.expander(i["code"] + " | " + name(i)):
            explain(i)
elif mode == "sheet":
    st.subheader(t("جدول الأصناف", "Items sheet"))
    st.caption(
        t(
            "بيانات الملف في شكل جدول واحد، بترتيب الشيت. تقدر ترتّب أي عمود بالضغط على عنوانه.",
            "The workbook data as one table, in sheet order. Click a column header to sort.",
        )
    )
    if ar:
        cols = ["NO.", "الكود", "الصنف", "الوصف", "الوحدة", "المورد", "سعر الوحدة (جنيه)", "الاستهلاك السنوي", "التوقع الشهري", "مخزون الأمان", "نقطة الطلب", "كمية الطلب", "الحد الأقصى", "الرصيد", "أوامر لم تصل", "صافي الموقف", "الحالة", "الكمية المقترحة", "نسبة الخطأ"]
    else:
        cols = ["NO.", "Code", "Item", "Description", "Unit", "Supplier", "Unit price (EGP)", "Annual usage", "Monthly forecast", "Safety stock", "ROP", "EOQ", "Max", "On hand", "Open orders", "Net position", "Status", "Suggested qty", "MAPE"]
    df_sheet = pd.DataFrame(
        [
            [
                i["row"], i["code"], i["name"], i["description"], i["unit"], i["supplier"],
                i["price"], i["annual"], round(i["forecast"], 1), i["safety"], i["rop"],
                i["eoq"], i["max"], i["stock"], i["onOrder"], i["position"], i["status"],
                i["suggested"], round(i["mape"], 3),
            ]
            for i in items
        ],
        columns=cols,
    )
    st.dataframe(df_sheet, hide_index=True, width="stretch", height=560)
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="xlsxwriter") as writer:
        sheet_export_df(items).to_excel(writer, index=False, sheet_name="Items")
    st.download_button(
        t("تحميل الشيت الحالي (Excel)", "Download the current sheet (Excel)"),
        buf.getvalue(),
        file_name="supply-items.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    tbuf = io.BytesIO()
    tdf = template_df(items)
    with pd.ExcelWriter(tbuf, engine="xlsxwriter") as writer:
        tdf.to_excel(writer, index=False, sheet_name="Items")
        ws = writer.sheets["Items"]
        wrap_en = writer.book.add_format({"text_wrap": True, "valign": "top"})
        wrap_ar = writer.book.add_format(
            {"text_wrap": True, "valign": "top", "align": "right"}
        )
        top_v = writer.book.add_format({"valign": "top"})
        for idx, width in enumerate([8, 34, 30, 7, 10, 14, 12, 14, 11, 7, 7, 9, 9, 11, 9]):
            ws.set_column(idx, idx, width, top_v)
        ws.set_column(1, 1, 34, wrap_en)
        ws.set_column(2, 2, 30, wrap_ar)
        ws.set_default_row(30)
        status_col = len(tdf.columns) - 1
        ws.data_validation(
            1, status_col, 500, status_col,
            {"validate": "list", "source": ["Add", "Update"]},
        )
    st.download_button(
        t("تحميل قالب الإضافة والتعديل (Excel)", "Download the add/update template (Excel)"),
        tbuf.getvalue(),
        file_name="supply-items-template.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    if st.session_state.get("custom_items"):
        st.info(
            t(
                "البيانات المعروضة من شيت مرفوع: مؤقتة وخاصة بجلستك فقط، ومش بتتغير لحد تاني على الموقع.",
                "Showing data from an uploaded sheet: temporary, only in your session, and not changing the site for anyone else.",
            )
        )
        if st.button(t("الرجوع لبيانات الملف الأصلية", "Back to the original workbook data")):
            st.session_state.pop("custom_items", None)
            st.session_state["upload_seq"] = st.session_state.get("upload_seq", 0) + 1
            st.rerun()
    with st.expander(t("تحديث البيانات من شيت", "Update the data from a sheet")):
        st.write(
            t(
                "طريقتين: ارفع الشيت الحالي بعد تعديله لاستبدال البيانات كلها، أو استخدم قالب الإضافة والتعديل: عمود status فيه Add لصنف جديد أو Update لتعديل صنف موجود بكوده، وباقي الأصناف تفضل زي ما هي. حالة المخزون والكمية المقترحة بتتحسب تلقائيًا من الرصيد والطلبات المفتوحة بنفس قواعد الملف. التحديث مؤقت وخاص بجلستك فقط.",
                "Two ways: upload the edited current sheet to replace all data, or use the add/update template: a status column with Add for a new item or Update to change an existing item by its code, leaving every other item untouched. Stock status and suggested quantity are recalculated from stock and open orders using the same workbook rules. The update is temporary and only affects your session.",
            )
        )
        st.caption(t("الأعمدة المطلوبة: ", "Required columns: ") + ", ".join(SHEET_INPUT_COLUMNS))
        st.file_uploader(
            t("اختار الملف", "Choose the file"),
            type=["xlsx", "csv"],
            key=f"sheet_upload_{st.session_state.get('upload_seq', 0)}",
            on_change=handle_upload,
            label_visibility="collapsed",
        )
        if st.session_state.get("upload_error"):
            st.error(st.session_state["upload_error"])
        elif st.session_state.get("custom_items"):
            st.success(t("اتحدّثت البيانات من الشيت المرفوع.", "Data updated from the uploaded sheet."))
elif mode == "scenario":
    scenario_editor(by_code[code])
elif mode == "unsupported":
    st.warning(
        t(
            "السؤال خارج حدود النسخة دي. استخدم كود موجود أو الكلمات الموضحة. مش هخمن إجابة.",
            "This query is outside this version. Use an existing item code or the listed keywords. No answer will be guessed.",
        )
    )
else:
    status = "REORDER" if mode == "reorder" else "OVERSTOCK"
    rows = [i for i in items if i["status"] == status]
    st.subheader(t("نتائج المراجعة", "Review results"))
    st.write(
        t(
            f"عدد الأصناف: {len(rows)}. الترتيب حسب الشيت، مش ترتيب أولوية.",
            f"{len(rows)} items. Workbook order, not a priority ranking.",
        )
    )
    for i in rows:
        with st.expander(i["code"] + " | " + name(i)):
            explain(i)

st.markdown(
    f"""<div class="credit" dir="ltr">
  <div class="c1">Created by:- Eng.Mohamed-Azooz</div>
  <div class="c2">FTTX Access Planning Engineer</div>
  <div class="c2">Planning Sector</div>
  <div class="c3" dir="{direction}">{t("الكميات والأسعار تقديرية للعرض فقط", "Quantities and prices are illustrative only")}</div>
</div>""",
    unsafe_allow_html=True,
)

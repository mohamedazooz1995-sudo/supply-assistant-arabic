from pathlib import Path
import base64
import io
import json
import streamlit as st

st.set_page_config(
    page_title="Supply planning assistant | مساعد تخطيط الإمداد", layout="centered"
)
lang = st.selectbox("اللغة / Language", ["العربية", "English"], key="language")
ar = lang == "العربية"


def t(a, e):
    return a if ar else e


direction = "rtl" if ar else "ltr"
alignment = "right" if ar else "left"
st.markdown(
    f"""<style>
.stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {{background:#F6F3FB;color:#1B1030;color-scheme:light;}}
.block-container {{max-width:1000px;padding-top:2rem;}}
.stMain, [data-testid="stMarkdownContainer"], [data-testid="stWidgetLabel"], h1,h2,h3 {{direction:{direction};text-align:{alignment};}}
[data-testid="stMarkdownContainer"] p, [data-testid="stWidgetLabel"] p, label, h1,h2,h3 {{color:#1B1030!important;overflow-wrap:anywhere;}}
h1,h2,h3 {{color:#5B2C8F!important;}} h1 {{font-size:2rem!important;}}
[data-testid="stCaptionContainer"] p {{color:#554766!important;direction:{direction};text-align:{alignment};}}
[data-testid="stMetric"] {{background:#F1E8FB;padding:16px;border-radius:8px;border-top:3px solid #5B2C8F;direction:{direction};text-align:{alignment};}}
[data-testid="stMetric"] * {{color:#28133F!important;}}
[data-testid="stMetricValue"] {{direction:ltr;unicode-bidi:isolate;}}
[data-baseweb="select"] > div, [data-baseweb="input"], input, [data-testid="stNumberInputContainer"] {{background:#FFFFFF!important;color:#1B1030!important;}}
[data-baseweb="select"] span, [data-baseweb="select"] input, input {{color:#1B1030!important;-webkit-text-fill-color:#1B1030!important;}}
[data-baseweb="select"], [data-testid="stRadioGroup"], [data-testid="stExpander"] summary {{direction:{direction};text-align:{alignment};}}
[data-baseweb="popover"] *, [role="listbox"], [role="option"] {{background:#FFFFFF!important;color:#1B1030!important;}}
[data-testid="stNumberInput"] input {{direction:ltr;text-align:center;}}
button {{min-height:44px!important;}} [data-testid="stBaseButton-secondary"] {{background:#FFFFFF;color:#5B2C8F;}}
[data-testid="stExpander"] {{border-color:#CDBDE2;}} code, pre {{direction:ltr;text-align:left;}}
[data-testid="stAlert"] {{background:#E8E0F5;color:#1B1030;}}
</style>""",
    unsafe_allow_html=True,
)
# Use the checked workbook snapshot. This app does not recalculate Excel formulas.
data = json.loads((Path(__file__).parent / "2-data.json").read_text(encoding="utf-8"))
items = data["items"]
by_code = {i["code"]: i for i in items}


def name(i):
    return i["description"] if ar else i["name"]


def n(x):
    return f"{x:,.2f}".rstrip("0").rstrip(".")


# Keep explanations tied to the stored workbook policy, not purchase instructions.
def explain(i):
    st.subheader(i["code"] + " | " + name(i))
    states = {
        "REORDER": t("محتاج مراجعة لإعادة الطلب", "Review for replenishment"),
        "OVERSTOCK": t("رصيد أعلى من الحد الأقصى", "Stock above maximum"),
        "OK": t("داخل حدود السياسة", "Within policy limits"),
        "CHECK": t("محتاج فحص بيانات الرصيد", "Check stock data"),
    }
    st.write(states[i["status"]])
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
    with st.expander(t("مصدر الأرقام في Excel", "Excel source cells")):
        r = i["row"]
        st.code(
            f"Analysis!AA{r} (stock), AB{r} (open orders), AC{r} (position), X{r} (reorder point), Z{r} (max), AE{r} (status), AF{r} (quantity), S{r} (forecast), W{r} (safety)",
            language=None,
            wrap_lines=True,
        )


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


def scenario_editor(item):
    st.subheader(t("تجربة كميات جديدة", "Quantity scenario"))
    st.info(
        t(
            "التعديلات تجربة خاصة بجلستك فقط. لا تغيّر Excel أو بيانات الزوار الآخرين، وليست أمر شراء.",
            "Trial changes belong only to this session. They do not change Excel or other visitors' data and do not place orders.",
        )
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
    st.success(
        t(
            "نتيجة السيناريو المعاد حسابها أدناه، وليست القيم الأصلية المخزنة في الشيت.",
            "Recalculated scenario results below, not the original stored sheet values.",
        )
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


st.image(
    io.BytesIO(
        base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAQAAAAEACAYAAABccqhmAABC3UlEQVR42u29eZxcZZU+/pzzvvfeql6yJ+yCbIHuBBBEEZGGEUVRZ5zvj4qQiOjg8lURCOioM9+ZSuvMuAyyOszIjAtCAnTpzLiAyyjSiA4iQUnoZgub7NmXTlfVvfc95/fHrUoayNKddCdV3e/jpwykF967nOc8Z3nPS/BoJBCgKKDEHV0zqX/WKi2V5rntffP5B387V23fMNmQHCBiDmCS/VUxE2SmQ3UGEaYodDKB2qFoBSFS1TxAQfYbNASBCVSFQgDESqgSsFlVywA2EbBeQeuJsFaBVQS8pMorReQ5crlnwurzAzc83V3Z3hoLhR7TsXIm9feu0hIKAhAAqH/UDfPCeex1gy+UeOXKPurt7U5f/S1Kf3HsVZPbqvZQMu5IBR0GwmuhOBjAwQBmKWmOQJEhCyYLIoKqQKFQVSgUQP1PALrV/nToS0BU+2cCQCAiZP/jLb/TqYNoCgUqUFQAXQnQ08R4UhVPQeUJhnlYq/rk4hUXb9qWsXd1Fe2sWZ1aKnlC8AQw4aC0I4O/oONr0yoadILleCKeIypzCJgNoimWQzIUQKEQdVB1EAhQM3IFhFQVIAUpKWirbUNpG4986L/o0D8UpFsYShX13wmAUacGYhAYTAwiAwLBaYJUYlFgPVQfJfAyJfQZ6AOOgmVLln9i3U4IwZOBJ4BxZvJQOq1rkTmtF9KNbhn6tfd1Xn6QYXsSqb5ewW8g1WOJeGpgcgAIomnto1CoQCEEoG7gtPUZ0h6/LCgyVlCFktYYgwnETAwmAyYLQJG4ChS6VoFlBL1PBffaIPrtdx/4+PNDFUARRb6zC7yte+XhCaBpUH+Re3u73dAXvHDCNyYHcfVkFj1VCW9RxXGWbavlCE4TOE2hKoCqA0iVwJn3pmZ6XlvJQSGAEohMRgoWhgKkEiOVZDOBlinkLjD3ApvvWbL88+teqQ48GXgCaBp539W1yLzS6M/r+PJrHKIzDZs/c5DTDNl9A47gNIXTFKKSeXYCAcpNZuwjIgWAMjFDYCbmet4ilSpE01VE/CtVd4dW9X+WPHbpE0Pf1a6uormzd5EjHyZ4Amike1hAD3egT4d6qfNnX3lIbOjdzOZdgJwScNRGxEglhqhTVbhMLtcybhOUMRXIVAKpYbJkOYSqIpFKGcS/gaS3idBtNz90yWND1VV/oZNKpXkCn0D0BLCXvf2WRN55R107XVnfQ4bOdupOD02+BQqkGkPVuVrKnTEkOefxCj5QCAggsLEcAsSI3WCVwHeSuh8kCH98a98nn/EhgieAvRbb17yPq//7E3On/5kI5oPk3ZZzMwmEVKpQlayGT8T+Xu9CyKAqtduXkQEIsZQ3gswPSfWWWNb8T6m/O64/BwDwROAJYExQQI/pQUHq8ee5J1w+w1bt2QB/EMRvNBzCSQynLivFeaMfGzJgYyxHcJJA1PVBsSQ2uLm07KIntzyrQo/x4YEngNEx/EKPGVqfXtD5LyeCkvNVqRDZ/CxRh1SqgFIKUuPl/Z4JE5TAWV+ERewGBwD8F4j/ffHyi349NDx4ZULWwxPAsO5LodDDQ9twz5t7zRki+kkQ/jw0LZxKFSKpUyIigP0t2xuyAEIKIWZrOUIqVYXiTjD+pbrsrv8uoeQ8EXgC2AWPv8Xw6f1zrvkLEH0EoLMsB0hcBVB4b99wqoAcCNZyVO+UvA8i11Z1zS31PIEnAk8A20URRe7GIq1L/fmd17zPkrkQTKcwDBKpZM05PrZvdDJwCiLLIRMxxCXLFXplVVYvrhPBK0jeE8BEN3xga/b4vDlfPwvA55jtWwBFItVanZqMf12aKzyAKqwJmcnASfIABF+7se/Cm2oKgIoo0kSvGkxkAqACeriEzBMs6LzyNCL718z8TgIjkVigCso8vsc4IYLUJfdA6Z9u6vvkj7al/DwBTLA4/9w5lx9l1HaDzTxLIRIpqyrUG/44JAIoAo5YVSHiblOWf1i8/OJ7JnJYMKEIYCjb//nsr7S329xlRLzQmnBSltxT56X+RCACIOSIU4mdgL4hyeA/3vLIZ59XKC3CogkVFkwYAiigx9Tl/vvnXPNeIv6i5XBOIlWoOG/4E44JMrIPTQsSV30W0L+/6cFPfTt7VwqmhNKEaCQa9wQwNMm3oOPqDjB92XLwHoXCudj53vwJLghUhdkaQxapJD/XNPn84ocvvX8IEThPAOPA6y+Yc+2niNBtOZwau4rULt7H+R71kUcaco5TSSoKXB6vf+KfSs9eWR76DnkCaEKvf87RV3QaY74WmNyZqcRQkRQE6197j21QgSOwsSaHVKpLFfGFi5dfdg+gVBynuYFxRwBdKNpeZFt03z/3moVQKloTTo5dWbK9917ue+w4OQCFWBMZp66qol9c3PepLwGQ8agGxpMxbKnrzz/6nw8mG10XUO6sVH2Sz2OXwgJhMFsTIZW4N02rC2956NN/yEhg/AwvHRcxcE3yawnz3IKOK//c2PyvA47OSmTQadYZ6o3fY4SekVghmriysxR0BSZ35/y513wkUwCkhUKPGR/X2eSoy7KPnvCNYHNc/aKB+awCEEl9rO8xWlGBIzbGUgAnyTc3JIMLf/jIZzeNh5CAx4Px/5+jv3LE5mr1jpBzn3XqxGkq3vg9Rs9NkhF1mriKsya6YFLYesc5R1/+uhLmuZoSIE8Ae5aSqVDIjP/czivPbLWtdwYmPKWaDjpA2Zf3PMYgJCAQmWo6mBoyrw9M7lfzO68+r1Sa54ookm45eMWHAGMe79fLMQs6r7qY2XwNYCMSOxD7WN9jj4UEhixSTb6yePlFn8sUafM1DjUVAdQl//kHF3Np2/SrAxN+NJFqNlrae32PPckBUCWQBibPiVRLyMuHF9978cZmywtQsxn/gqOu2A/W3hKa/KlxOuhA6lt5PfaqGghti0mk8vskid9/68OffrSZSKApvGZXV9FmJb5/7iAb/CI00alxujkFwY/l8tjLLpRMNR10hsMTA5u749yOy08pYZ7r6io2RRKamsH4e3u70/mdV7zZcNjDZPZPXNWRr+17NJQQUGc5MAoMiIsXLO5f+MOhXameAHbF+Gs38Nyjr3mvtea7BLSnknjj92hUEhBmw6SUJJJ+5Jb+S25o9HCgYQmgBz1mHua5+R1XfsSY4BtQJadO/KQej4YmAUAYREyWnMSXLO675OoaCTTkfAHTyMZ/bufVHw9s+G+qDgL1Y7o8miGmJs12FGlgoncePeOtdOuqD/+qgB7Tj1LDrbfhDKpQ9/xzrrwo4PA6J6lIdl6kN36PZiEBBoRSqbrIthQXdF71T7WuwYYbKW8azfhLmOfmz71qYUC5q5wmAgiRz/R7NB8NEAASTSSwLad2zHxrcOudF/yyUOgx/f0lTwDbM/5zOq/465Dzl6c14/dlPo/mFgMg0VRC09LVMeMMc+udF9zRSCTQEARQRNFehwvduR1XXRjZ/BVOYgeIb/DxGCdKQDMSsLnTOmaegVvvvKCeE9AJTwDFrqLtfro7nd95xXmBjf5dJHHqjd9jHJKAqpOA83/WMeOM8q2rLri7iKLtRa9MWAIoFHrMdbdf6OYffcVfsAlvUhXyxu8xvklAxJrw7UfPPOOZf1n5+aV7mwT2mqHVO/zOOeaKPwsl+qGQtIg6+ISfx/iGKmCUiSWV6v+5ue/SH/UUesy8vXQq0V4xtkKhYEqlkjtnzlXHBGTuBGiq01QIvs7vMQEoABAmwwA2JeLecWvfxb/dW0eT7XGDK6LINePfx4C+z7BTRVLnjd9jwgQDAIs6YVB7wPz9BbOvnF0qzXPFYpH3wlr2KPdREYto7eHTgrU5+klgotOTtOwn9npM1GjAWZMzqcQPKtlTlyz/+HoFQHtw4vCeZBwqFErcjW5ZG+m/hSZ/epxWUm/8HhNXCpBJXCUNTG4OSfxtBTCvUGLswfFie8z46jHOuXOu+LvIti6M03JKfnCnx4TnAGInaRrZlo6eGXfnbr3zgv8pFDpNf/+e6RGgPWr8nVe/x3LwQ9XUKbTh+qI9PPZWMEAKMSY01bT8wVv6L71hTyUFx9wA60M8P9B59WFCdA8RT3ea+nKfh8crEgJERkmpmoqcdnP/RffuiVkCY5wDyGKZ8w/+ds4BN1oTzhBJxRu/h8ergwERBybOM+kN5x975ZQS+nSsx42PJQFsSfrFbesvD23+TYmr+qSfh8cO8gGJxC6w+aOSFNcC3ZIlBcdOqY+ZMQ5J+i0ITcuXM+NHU5+i4uGxB0iARBIJTf64o6a/9fme3g/fV9s9OCZJwTExxnrcP3/uFYey2PuIeYpT52f3e3gMJ3CGKmf5gLKqvPmmvoseKEK5GzTqewbGwiCpv9BJRRQZwt+wJpqaxf3e+D08hueVa/kANq1K+HbhwK/lgUUYi/6AUTfKQqGHS6V57pE5kxZGNn9G4nynn4fHruQDUhenocm/Lphsit3olkKWD2jcEKAuU+Z3XHmc4eC3gIYC57f3enjsWjCgBBYio6lLTr+5/5K7RzsUGEXDrPX5v+ONwZpnHr07MLnXp67ivb+Hx25RgIo1ETuJl7dGuZOuX/p8RbFIR2u/wKhJigJqff7PProwsq2v9yU/D4/RCQWcq7rQtMzdWC0vGlIabBwFUCwqd3eTLJh75WyCuQ/KLYrUD/T08BjVUIDhJO5a0nfpb0brKPJRYZL+/hIBgAhdaSlqU03VG7+Hx+jpAFUBkzVEfMVHT/hG0IEOHY2qwG4TQAEFUyrNc+fMuer9kcm902f9PTzGhANM6iouMC1vGIg3f3S0qgK7ZahFFPk6/It+6LhpM1Xo+wRqEyjId/t5eIx+IECUjRQE3njiAe9avPiXH9pUBLgXvbucENwtBulHJwGk1UT+PjQt+zuJfcOPh8dYiQCAs0NG8jMqcfoPGIVKwC576nrib37HlcexCe6BSlDbueS9v4fHWAoBkBAZcohPX7J84V27kxDcDW+9qE4hX7IURKqi3vg9PMZeCCgETIYh+MciipwlBPegAqgzzvyjr3mnDeztziUC8tLfw2PP6QB11kQmdtWzb+675Pu7qgJ2gQCyjr8XTtjfDFTKvw1M9PrEVYXIj/X28Nhz9q8SmIhiV31wRpVOvHbF2gRYpCPNC4zYaOsdf5vKm+eFJueN38Njb8QBRJy6qkQ2P3ddHudjF8uCIywDKvVjjhY6ekKmTd81bGaJOhD5ph8Pjz2uAohAAERk7jGT3/ntW+7+q+pIy4IjYowCSgxAI362EJn83MTF6r2/h8deUgEAO0kktPlDJKKPAaT9hU4a4e8YPt8AhI+e8A07UC3/PuDwGE8AHh57HcJkSTR5Nh7Mzy098bGNRRSpG93D2jI8bOOte/+BcrkQcu5Yb/weHg0BFkkk4JaDglz5rwCMSAWMSAEUOhYFAU35fWBycxNX9QTg4dEgKsCwpdQlT7FJ5t607DODgGI4FYFhGXABPQYgDWj6uwOTO8Ybv4dHY6kA5xIJTf61cME5AHS4FYFhKQDN8o06v/OqO0OTOzVxFfE7/jw8GgdZX0BIiasub8u1vP76pR9LkcmA3VMAhUKPIRDO67jqFMPm1ESq8Mbv4dFYICJOXKLWRMcMVMpnAtBMue8mAXR09CkAdYT/azkihYq/3R4eDUgCtfMEAPo4AHSgT3f+MztA/YCP9x175SEm5QeZqFUhftqPh0cDRwMApaQ48aa+ix6o79rdJQVQLydYR+dFNt+qKs4bv4dHQ5u/C00ucKTnA1vH9e2KAiAA+o7Dr46m5XSZ5fBIJ4nAD/zw8GhkCJNlkeR5a7XzhgcWrq818emIFECh0MMAaEYL3m4pOjL1xu/h0QxgkdQFJr9/Iua9ANCzg5Lgdr9QT/6p4jxmowT45J+HR9OkAVQhbj4AFEoFGWEIUGSgWwrHfu2AIDUPMZt2VeeTfx4ezcMABCBmdcfd2LfwoXpCf1gKoLAl+Wf+MrQt7SrOJ/88PJoHBBUXmlwoxAVga0J/mAogSxos6Lyq15rcqf6MPw+PppMAYjnkVKoPJEfvf0KpNM8NKwdQRJEB0gVzr5ytwJtSiQHf9+/h0WQSAOwkVgYfEy5/4cRM2RfMTgngzq7s71ToLyLbEkDFwU/79fBoRhngApMnGH1vLbgfTgiQnTe2YM7Vv7ace7OX/x4eTRwGUMBO4uXPzlh3fG9vd1qzed2OAsjk/7nHXX04gBO9/PfwaPIwQBMFcec+q6e+LtMABd5uCFCsyX9O6R2BaQm9/PfwaP4wIDR5DojeCQAruzpouwSwqHdRLVNIbxvuRBEPD4+GZgASdVDVMwCgd4uNv4oAikwgPe+oa6dD5ZTUxQDBx/4eHk0dBxBnoTxOLBxzzWszp670KgLoqsl/se5Uw+FUgfNn/Xl4jIdUgKoLOZcLRU/PQv1F5lUEMGtWv2YhA3UZDgAl5++dh8d4SANAiQygOAUA+mu2jld7+CLPnzP195bD453EDvDlPw+PcUAByhSQaPL4tAp1Xrvi4mrN9pXrhg8A8+fucwiATpEUQOOW/4gAIug2PntaXDXaWrTB7suO1tRon3Ec8BJEUwD02rXWdQJAEcVsv089/u/thZDGJ1uOokY98JOZIKJIY4Hqqx8XEWAsg032fWO9FucULt3BWgIDYkD3xFpSReqEtjUHlhiwgQFojNZCABMpEZEKICJwolDV7N40eC2pbvzEBObs/cnm7Oo2n22z5gECkzdJUD4JwP3oAqMXYofG/xCcaIxFgmrDDf8gIlQGE0R5G886aFIc5oLq0GwmQBpXXbjmxY25ymASRPkAqjqma8m3humU/SeVw8jEr1xLtZzk1ry4KUjKEoY5O6ZrKW+OtW1yLpkya3LZWk5fuZbK5ji/5oUBK6JhEJlRWwsxlIjJJYJyJaUkSSWXt9WoJeBcZMIob6u5fFhmw/LyNTUWXKpc3hznq4OxjasuHthQsaQchHmLIDQAVEW0yYmAlIigQm8EcB1Og6A3Ez0Z3UFpQefVvw1MdFIisVADEQAxIS6nOPYtB6/5SPdbZfLMlqlsWIZKW1VAnPCGVeV1/178BT3w66dnhHk76h6PmFAdTPHGdxy+6q/+7s+C1slh27bXorz6+U1rrvvcz4LH/vDCtLFYCzOhMpjKW8+Zs+qci0+OWiZFrcT0csmvgIjSi0+uX331p2/PPfvo2ilBZGh3SIAISsxUHUyRxmk6Zd/WeO4bX7P+iNft13b43H03zjyoPQxzdkYQGGXLwtzY/SQiSmkiJk1cefOG6tpH//BC2+MPvJD+8e6ngheeWN+iijDXGmR+tEmJQKFqKCCR9OHWXN8x1y+9PqmJn2z4x/kdX9834fQxhmnLJv82iPQhqKRK7dPyA9f88kNpFAVTRBW8jcC2/vfVarL+4jO+ZTauqbSzJcUoyTgiaJoozTpw0rorfvYBY9hMUlVs63R0VQERY8OazWsuftt3WtKqy8MAoyWHiaBxReiI1+2z6h9uPbcFQOvO1vLsE2tWfvbdN01hw6Hu4kLYEJKKIK4m6ezj99/wjvcfl7z+bYfmWtpyOQDROIqkqy516cO/f37g9u/ez0t/+cRkVYRRawARAZqvRU4JRAqJY7Gdpf4LVwBKtoB+KgFIKT6GKWirTf5pnLifCNVqirknvWZ9FAWzXCpKBHLbeAIEIFVBFAX5uW86eNWd3+9vzwcBZNQkLyGuJDj21IMrhs30NHFZXmI7axEVTJ7e2n7EsfuufuDuP+WjFqOjFVOyYcSVKua++aAcgFwSJ2qsoW3mPhQgVuz7minT9n3t1IHnHl8bBiGPaC1ZQo+weUOsBx4+bf37Fp5cPfms2W0ApgEgcQonDgQo1b+5Kf2kqirAxJGxJup800GtnW86qLJi2Qsbb/jHXuq799mprW0Rg1VVmorsSKBiKQxDTo4HsKKra5HhqSecUZP69tiAc/X6f+NcGAEqQL4tMAAEBHpFlnnLB0Peu1xbYEVGn8tUFGFk80C2jh2uhQkAXMuUXAqp/8AoPlARGDbtUJj6xCai7X0IbMm1TgrLkJE9YSIAQhgciOOzPnTcS1/94fvp5LNm76uKtiRJyTmnIIUxDDZMxETbX0cjfwjMTMYwEQPOOaRJquIkd/gx+8344q3nRB/6u9NedKLlNFbKkoVNxW9iOQRUjwOA2QMvEO+39KOu9rVjG1nXjNSJj1XSre4nRhZkjmncOGw/ztl9GdFaiAmSAiJavuSqd6254O/fOjXKB1PSJIWIgzEMovE5Lo6IwIYJBKRJClVte89fvX6fL9w8b2DyzJZ11c0ObJpnvwwBEDgo0AkA1y+9PuVukBRRZCJ0Okmh5Ed/e9SNHyqpgAMa/Py33jtwynuO2selLnLOKWeGP2HuBRuGiCBNnDn8mH1nfvUH709fc+S01ZUBR01DAqTGSQoCzSl0FEPUG4EePbJ9moIOE3Ug3//vUZP96ohUtfq5f3/vwJyTXjMjSVImpnHr8YenCAhJkuqkqfmZXyidgwOPmLImHnTU6JWOugZQdQDhQNi2A+qqECYIjmSiNoXf/eux5WXXymCcfOKrZ67pfMNB05M4JWO8OAQAY5iSONV8Szjjb79ztrZNiza6RJuCFhWqDA7zFB6xhQCU9QjDESlkhOkhj/Epd0k3b4zpzA8cu/aUdx89M02d8cb/ChKwGQlM36dtxoWXv7OcxGncBMOzCFCxJoc0wRFArRVYhQ81xiBREvgcwESP+5FUhfZ/7ZQNH/hcV14VAWWJxmE7BlWFiDadoGQmEA/fjxvDlKYOx51yyLQzzp275mc3Ldu3dXKo4hq4WUhrZVrWw7cQAEEOkyYranqMlfRnxNWKO/czp1SiXDArTVJlw8N6NeqdjsYaGNOcr5OIQsQp8zCuORuvqVAE5156SnTPz1Zsijen7TAYteazMdAAJOJASocAgC2iyCsUh6g6KCmTp4EJ7P0J8WCKI4/bf+PJ75zdrqJEw7N9iAistQDgBjaWq4/94cV1K5/ZYJ2ToNGFAAE6aXrL4BHH7jdpn4Mm55lt6JwbVpWDmSh1Du1T85PPPPeYVbde/b+t7VNy5FxjHqWpIBJ1ANHBXSha23/gpChkHKgq8PH/BI/9iRDHiTvzvGMTAFNq5T7aufErrLVYv2pgw/evu3fwf29/pGXj2sq0uByzAtz4syUVJuCW1vYcZr9u/7WFi98UzD5+/6nihBU6DCJQqILfes7c4MffuT92TnKNS3ZKCgEgBx0wN9dug3aZBZjpUmuy85io7h9IE4cZ+00qv+Fth+UAENHODTczfoNlv3lq9VWX3M7rVw3um28NKdcSIN8WNs/1K+CcYNlvns4v+83TA4WLTnqhcNHJM8VpmO2x2JEKYEAVM/ab1DbnpIPWLf3Fk7lcu23QXABBIYBSq9FJ+9qAowMTlRx8CXBie38mHRxI6Y1nHrS5pS03TZzsNCGmNeN/4O4n1/zjB/8zZ8OgrX1qDs5JtmGmCQ+Uz7UGSsRtN37l7jCJ01XzP33qLOc02NnPpc5pwNa+7tRDgnt++liap8A2rE1lY0GjBMmBnGq6HzPXF+slwEQVAESUutQddeKBOQB2ZzGsiMIYg7Uvbdp45cW3sY3CNhuQulSa2peIKDlxmDqrNfzeNffMWPqrx9cbwxCnO7l/GY/OPfngcr49TF2qjWpNJFA1ZJiFD2Bhuy/DQpuSrz1GC84BLa1RPPv4fTchKwboTiIGgOC+d9095Y1rKlODkMbB0IytHlLEaZgPo5u+chenaVox1uxwQ0o9WzplVsuM9sk5Fte4VTWCiiELhtuHCbIvswWN5e6ZvRPSeozgZqkThHkbTJ3V1l5XBNu1D1UYazCwsZz87icrWvNtIRo1673LHCCgKG/xp0fWtC27+5kNRIBz27eR+s3KtwY066DJa11aG7LdkBdHSsRwTDOYlKZ7Cxipg9BxRTIEQEWQawnEhqZ9ZxSqtQELK/74wtqNawcDYxjQcci5mdEH/b9/phWA7HAPBKEWJrCbsV97ko3VaNBbQkrZMAOayQCmq0rjLnbXVZzHSByeAvm2sByEZqfnQdT94EvPbDRJ1elwewWaMB+gYRjw84+v3QQgNpZ3+GLVHAO1ToqsE21Yk1JQNiZLdBoTMA3ZTBuvmie2rEGUC2Izgl1tcdXlVHVcnx1BBFQrqQz3HgIgG7BFg0fUmln8ZCuESaTeX3pkm4CGubc9G3XkXEAMy0xQHn9bSIhBWY1/RM6RqAkmBakqlDDZAmjLrlDH1SiACSNnaKTfPnpdeQRodTAdLA/GRtz4KyIxk1Y2pxDVZEi2ZDg/SY28EyqzdQUEbRaq7f4UcI9azEtOlHa285cNQVVx+tlz6JCOWWvZjN+RYGkisu9rJk9S1ZwMM65navzDUBQKYuQtCPmsAuhTAD4PMLw6PlFGAJOmtrQc++ZDWiYGOcrwk3oN31NPWSZXKW8BBE2kmhtijaTjUzKJjMxzOecgojqeXYci2yQ1nDkB9SpAE4xMq68vZwnIaXM9D48xi3lHlu4iIhhDXjo2KbGB1LCCrLcrj5pFq2GfENp1t5pxoTRFV70CSuzHf3lsVQDGG/9oWBaDmqMkQrDs9ZtHvbrF9QyA7wrbPQZomoqoqlcAHlt5gLmBd7A0D0SbY2eEglJWaNJEfO8d09hFhGAihR8Kvdu3kkibQEMRCCoWoJiASJvnPfVoEHpVBVR9H/lW158dF7t+dTkxDR5c16K+xBKQDDEu72FHREY07q5oJKgdFuLfmSFY89LGjX/sfWpS2BKggc8HyGxduWxVdZCZp2VTgRv+WfqXbUzfiuG9sKqqzExxNalsWDO41ucMARKkj/zxhfB71/5vOLip2haEpoE3BGp2AgykYkkx4J+fB6HWCQjBzvIA2TxAwt0/fDj+l7/+6eS2KXkjMrEjARXV8uY4CMPABiGj0SMjAkGgZQuigWxUMDXDdkAfb46dIEQau0zT12hg+zPBsi9Vy6l1TvNQInUT/NEQoXVSDiqi2uA1AAVpdvwrNlqQbmQiOG9aEx5pkto0VcoO+Nk5gsikxORAav2O0vpIsOaQ00QEJdrIUFoDMKg5vCv5tYzR+8BAUnWBS50ZxpUrALS0hVVmcurnSTed5KNsMsRGBmE91bcHeoxENDfKDaNRogAMborzabzzYL6+/eeAw6bFYWTJVwKbjO0VSmAodC1DdXUz+LLaxJlhv2nMYzOXSRUgphAY/iT1MVoKiKA2sOmI7uM2du/Wt7wmsXNJ4jZsvdLtygUCgP0PnTZl+n7tFZcIGn8Exq6BORuTxoaUGEqUEWDtozTk603UT1c7IhyrWIlfVJXaoeGN6WuJgbjiHADd2ayFWhwWtLSHbeJER3NvNmXTVGXS1BYLwO6MAGrHZXP71FzeORndoEEAE5hknwMnrR0qy7cnV+qJvaTqzKsmWylgDKFSjmX18xsrQ9a+XQWQpg5BaHOnn925uTwY13sCxpenJEJ5IKVNa6s0uDGhpCyUxoI0yT5JVai6OaWBdVXavCGm5qikY+tYcNE1lpC+6ITQqBWAbHQRY9PGcrZ2rm22oO1enALgOSe/ZsBce08AwaidUKkK5FpNcuxbDt4AIF87PHMHB2iIAhwdcdz+mwX3OyIyoxU5iCrybaEcecJ+VH9Zd4bqYBIMrCu31xz4y36ADKGyPgkevf+FSYfP3U921hNM2f0w7/rg69ru/H7fulXPDkwNW1glbf75IERQgKhajt1J7zxy9QGHTQvXvjQw+OLT63n96s3t1cEkz5bTtkm5gX0OmlTe5zVTc9VyLL+9/dHWyuaklW2jZ9TIOE1BwEsWzr4gLCkTWUUDzgZTwBhg5dMbJiVxGgShhexgr4UxRKqKzjcc1D77+P03Pnb/izNaJgWaprJb12UD1k3rYnr9W1+74eDZM6eKKGgnwzCYs9FZb3rHEcHBs2dsfPHJjVPD1t03EhuwblhdobeeM2fT9H0mTXFOwDucWJM916Ts1g9srLbzNmhIVTUIAvPwfc8NnnX+8ZExvEPiJCaIc8i1RO0Lr3n36uK5tw7Eg9IWtRiIk+ZMKVEm+SUFlQfi+ILu01afdf4JUwBYAHlAKK46kyaOiSgIc7bdGNMCwADQN7/nqA1fPP/7IZSCBmYAJRA5dQI2z7Oi+icirTTqKQaqILaMdasGcps3VtfvLD4FqH5MVcuF/3wmtc/IrR/YEBOBwMwwZuuH6x+ufczLv25qXwMIm9ZWaZ+DJ635v19+uwEQiQzj7DciEiewgW3/1D+/09mIBsqbUiKiV/23trUW3s5aNqyu0GFzZ66+oHi6VcVOX7Z6k84zj6+pVgZjZ8yrGUBEKcwZ9N37TPvmjZUKM0Nkx2ZMTEhTh0M795nRffP7KjMPaF+7cU1FXaJ42TXaBv8Yzg5DdMDmDTERY+BTV75j9VnnnzBTnLakiQvFaU6VozAKbEtbjvKtERtjQhXNp4mEKoiOPH6/6VNmtopLXWOfs0MAKarC6Qu2bf2kVZunV9YRuE3gGnKeoTGMTesreOT+5/SNbzsS4hTG0g49r0sd9jtk2vQv/9eCtd/qvuOl5b/50+TypiqlqdiabSpRdkhKfR+8KAiqpArSWrIsCDjNt+XkLX951MYP/e3p4eQZLVOdc+BhbvYgJjjncNgx+8740n/OX/Ot7l+VH/nDc5MqAylJKmboWrasaXtrCU3a0h65M99/zMbz/ubUfL41muyc26n8p+x1TPvveSYXV1wUtUDxSv5SwAaMdS8NRvf+fMXA6WfPaR/OsNj6vT60c58Zl99+3vrbvrX0pV99rz+/5sWBMC5XOXViG7kxhgggJhdFQdo6JdI3v2f2xr/82Inhfq+dtp9LhUBaS+IqVPRVs36yWy9KxPTcinXrNqzePMla09CdgASGIB1kyT1PRRT5sc5pdwcmfFMisVAD7gdlQzq4IaHTz+5Y9cl/fsdkcRIO55VSyQ6xBJCsfHb92seXvUQb1gy2gaHGsIRRkLJlCUN2qkpJouwSx0mcWpeIAQHT923feNgx+5pps9qmAAhc6rArR2GpZsdpA4iff2Lt2icefNFuWl9tJQMJAuOCKEiNJQkCk60lFpOmjpNqbS0Mnbn/pI2Hzt0nnDqjbdJI1kJEIKLy3/x/izc/8eDqGUFE2+xWIyYkZYdD58xa90//OT8U0VZVGVZ+QURhs3vtkjipvvDk+nV/emx1tHFNudU54UYmgJb2qLL/a6dtOvCIaZPaJuVzAMKRPGcVwFhOvv6Z29f/6nsPzWidHJI0aGedAhJQwIkky47oW3sCAcD8OVctiUzLuXFaTkGwDblwIUR53nzlzz6YTJrWOsW5tCaJd/5iZrJ695xQFtcqduccPBGFYcbunqWXhTg6rAqHc6JBYOmxZc+v/H9n3zolzNlwR96JDWNgQ9n99b/+xZqT3nHkrDRJlYe5t1U1yyLViKAp4bLnrMzDE/EiotZaeu6JNas/8+4b24y1OW3ozih1gcmZxFV/vPjBi9+TyWHB42RNlnFvULVmA2D96nL+50seGCh86mSpbWfauXrgTL6lqWRb14d6vu2Vzl7xPfWx0LtbUWQmKBRuFNYy3NNcTXYDqj/696XkUgmIoeqww6O/c1Folnzt19Hxp712YxAFk8Q5Hc5Y7ExpZOPCVWuTApqjOq61UIBqammYhLelJ6Jy41fu0jTWnA20ofcCqJIyLBTlP6GW3QSYnhRNs+CgUZlZFPm2kG+/4Y+tb59/3LrJ01ump2mqPEzXnjE6bSMdMpyUySiHNHtoLeJEbWDp0T88v+F3P31sSr5959JURWFzRp97bN2kxZf/+qUP/b8/yysQ0AjqQyMxosZJi+2KLxW1odVf/6B/3e9//vjM1slRI88AeMVz5seBWrzPoo+mUgUN06vureDFGNKBdZW26//ufwRAlYh9G+r2PbkaYwmQTf9RvMMQczgC4qDWyTm67dt/mH7Pzx5dba0R53zD/ytDKxtaeuHJtWv/Y9Edk3KtkVVp/JeRSE0qVZDBVgKwMT2iKgM1AdCwFyGilG8Pcc9PVkz96U1/WG0Mp40UbjUKGWXhBRExkm8uumPw8eUvTQvzZofdfa/+HYJcPgyuvewnUx++/7m1QWghfsvoy/Iq5YHq6i9/9L+pOpi2cpb4b/jt9FkPQOLI4bEtBDCwYr+1UDzJZKAN3sMkImhpD+13vnDnzPt+sWK1DYwTp3vV+GrxPIzJjGwvr0WhBGM5vu07S1+6/YYHprZOikaclVYFyEBVKPflC/4r//DSZ1fbwIhk16cT2PhRM/41ixb04MWnNkwPc0ZVGl/6KxSU2fiq1nzuKQDgIpRLmOdAtNywBWmDH2tSG1xtQxNe/skfTfvfnzy60gYmYWKI2/NjacQJjDFgw+nAxvIGY40w76W1pAJjDBnL1du+fd+qb3+xd1ZLexSK7NojVVGyASGpSusXP/Cfrb+97ZGXrDWxMYbqVZGJgux5EoLA6nNPrVn9+bNvpif7Vs+IWq2KNEfcTyBhsiCg//qlHxsElMzsE/a3S1/4sRy7zzuPMBSekUoiRI0/G5oYYMPmNz96JDIhr+448UBmw2HtxdQxTUIpICoKEFlrICKbbvrKrzdce+nPoiAy62Yfv79hw2FWUsKYrkVVIaLKxGQCgyRON3yz+MtN3/v672a2tkXh7vK5an03IwW//tFD0ab15TWdJx0oYRTkmBipc6g1MY27uXK1ewsmgrGGiGjzHd9fvvbKC29vWbdy8+Rcq9VmSfrV47rARJxKfNvyVT/7SU+h05hDX/gA9aOkc6afNQnkFgBSz1A3/oRQAmxgzNI7nmh9eOmzA4d27rN56qy2gJltxto1uUr1794Ni1eoSFa6Y2NgDBMzVR9b9sLayz/xI/3tjx+Zaa2J7v3FipYnHnxx4+Fz9qlMnt4aMrN52Vqw+2vR+loAsjZbCzGV+373zNp//vgPeOkdT81snZwzu+r5t0e4YWRN/73Ptf3vTx+tTJ3VuuGgI2aQMRwyM6konAgwKvd7L4pkVRXJqp4me84gpuqKZS+tve6zP3U/+Pf7phtjcjZkqDTZxieCMhl2kv7H8lU/u79j5icMAUoA6YKjrthPDT/GZFoV0lQjwtkwKgMJbMTlU//8qE3v+MDr6JCjZ01CVuYc7a6UFEDy6B+e33Tbd+7je366oh3KUdRiISJgZpQ3xci12MHT/k/nwNvPO5YOOnzGJGTHsI+2skpEJHno3ucGfvztpbT0l09MZsNhmDdjlrBjQ0gqgiRO0yOO23fjme8/LjnxbYdFre25HIAI42dSUqVSjpMHf/un8i9ueZD+0PvkZBWEubYAItKM0ylrNq3KkDfc+OCl9xWhTNiys1NpwZyr7wk4ekOjtgTv8MVkggowOBAjjEx8+HH7bjju1IPDjje+ZvP+r50aBiFPCyLreISn37pUOIkdkqpb86dH18hD9z6T++Ovn3RPLl81KU0lzLeFAOFlSSBmgghQHogRtZjq7OMPWD/3lNdEHa8/aPN+h0yJgoinBqFRNjxsF60KuFRMEqda2RyveuqhNebh+5419//qCX72sbWtqgjzbWHmw8bYM2VtSIxqOUUap+mUfVrjuSe9ZsORx+/X2vGGAzdMndnaZiMzJQiNM5Ybvn4oTilJnHGJ27R+1eDGh+57btJjf3hxcPlvn25f/fxASIww1xKACE0T72/rMpkMi6YvTpZ1R1zX3z2wRaYVCgVTKpXcgs6rr41sy4WVdHNKRLYZr5JNRgRxxSGuxAjzQSXfGnKuJaB8ezhorUmB4T/EaiUNywPVfFx2aXmgiiSWKMoHCCIDYuwwBmRDUFdbS7W+loDDXMCt7eGgDc2IpvlUBpOosjnOVcppUhmIyaVaW0tWvt3TLycxKRGRSwRxxSFJU8m3BNUoZ22Ut5xrjQbDnEka/Z1JEjGVzXG+OphwtZImgwPV0BprwpyBDUwWPEuTzzlQdYHJm1grty9ZfvG7aso/6wRcubIj29ME+b3TFGjiA+Lq0jfMs+ZaWkgFuSR2qJYTbFg9OHmkietaiyiYyeRaI+Tbsv5vVaUdtdS+bC0trLnW+loE1UoFm9aWJ41oLbXMTLYWNvm2KBtKJoray7nHX1AVJYWCDJBvs9pCAYtoPokF1WoFG9dW2puhUEC1u8fMMMx28tSWLUqqlkcZB2ENKRGDBL8DgGLXItPdi9QCQG/vIgd0IwD/JpVqzMRhQw4HGdHLCXK1DDgxYHmXm5yo/oNDkmq0e2uhob925GupZacb5vlofdZgdjlkALvVh2jTWEjt3romGu897CdU6wBUJ78HAJy2SNDbXd/5l13ra/vWPrlizrR+ZntcKkkzHBQy7BdUd8Fwx3gt4+0lm1jX2Gz+H4ZE0nVG7b0A0N2d5cLqNK2FQsF0o1uguMtkE41887eHx7ggZBVrAijRvTc+/Kk1Q3NgW3RaPQ8A0judJPWdgb7528NjPMT/MGCiuwGgq2uRqdv2FgLo7c08fmzp7lSS9Qxmf+M8PMaH/k9cWSF6BwDMmtWp24zPFEoE0vmdV/84tLl3JWnZgcj4O+jh0bQQJssiyRPTqtRx7YqLqzW7f7kCAIBFmTQASH5OPnfj4TEOwn+I5RBKuOPaFRdXC4WCGRrav4wAumthgGH302o6mIDY+DyAh0dTy38WScFqfgoMyfVtKwSocQYBhAVzrv615ejNqav4MMDDo0nlP4FZ1a3OqZv9zf7L1tb3/mxTAQBbM4Qq8iOGzwN6eDSv/odYEymIfvnN/svWoljkoca/TQI4rRYGEPhHsfNhgIdH89o/WFUIQj8AgK47X23v28n0ZY0CC+Zcc6fl6FQfBnh4NJ35K5Mhp+mqROSo0jbk/zYVAAAUCqVMKgi+Nw4HvXh4TADzJ2c5UoBvL/VftrZQ6DGvNP7tEkCp1KcAkFLy34krDxAbHwZ4eDQTSI3ThEB0646+bTtZvm4pFot8a9+nn4HSTwIOFYDzd9XDoykglkJKJX5sejnr/iuV5skICADo7+8kAEQGN4oIKXxJwMOjSfS/Gg4AcOnaFRdXC+jZroLfrlHXGEOnDuLnsVZXWLYM+B2CHh6Nbv4gNokbjBV0IwB0oE9HGAJkv6hQ6DHXrri4yqAbsy3C/hwuD48G9/4SmEhF9Gc3P3jRw0UUuRvdsisEgI56MtDId6tpeTMRm2w8pYeHR4O6f1IVUtZvAaB+dO6wjLdDAuiuJwMfWPgUAT8ITA7qwwAPj0aFWBNwLJX+VA64HYCWMM/tMgEAW5OBCroulVga+gRhD4+JLf/VwAJK15f658VZ7X/HGFaXz9Y5AVfdGZrcqYmriO8M9PBoLO/PZMhJukqTfOfNj35sdd1ud0sBAMBpyOYEKHCtQkn9oEcPj4bz/pZDIuCbNz/6sdUFFMzOjH/YBNCLbgeA2nP5HyausiwwIamqzwV4eDSI9RMZrrryJlb8GwDqQMewkvXDjee1gB6+funHEmK6gmC8AvDwaBj7hwQmIlL97o39l/ypgMIOS3+7QgAooSAAKF7nemJXftiakBReBXh47G3zJ2KuuvJmZbliJN5/RAQAkBbQw6VnLyur0S8xmPz2IA+Pva7+JTA5ItXvLFl+6RNFFGm43n+EBFBXAUrtQcvNsav8ITAR+1yAh8fejf1jV96UWr0cu5CcH2FNn7SAeXz90o8lDPyjfwAeHns79s+Rql536wMLnyqgh0fi/XeBAIASSq6IIlc79v/vxFX/NzA5hqrfKuzhsUdtH8JsuZoOrmSTXAEo7WjTz6gRAAD0o59KpXmOlb6QHSHoxwZ5eOxJkKpaCgmqX75p2WdWFgqlEXv/XSaAEkquWCzyTf0X/zRNqz8KrFcBHh57LvJXMSbkWAYfSia5fwOKXCoVdikXtxt9/YsyJgJ/LnVxmchsOW7Iw8NjDL0/SClT3X9buueycgH9hGF0/Y0qAXR3kxTQYxb3X9yvkGsDEzFUfEXAw2Ns3b8LTM4krnrb4gcv+a9iscgllHZZfe/Wzr4s6aBkjXwpdpU/GQ7Zbxf28Bg76ycylEo8aMLgM0OV+K5it3b09aJXC+g0S176cHnujLevtyZ6r0giIL9l2MNj9O0fEtq8SaX65cXLLioV0GOu652zWw53NLL3VCj0cEdHQR/73lU/D03LWxPnjxX38Bhd369iTcTOVftac/k3XL/0+QqwSHc19h+VEKC+to6OgnZ3kzjgU07jASJD6keHeXiMmv0zSKGiqeDi65d+bLCATtpd4x8tAsgSgoUec2vfwodE0i9YEzGpzwV4eIyO+YsENm9SF//rrQ9d8stCoWB2NuprT4YA9VVSEYvohRP2N5sq5btCkzvJnyno4bG7Yb+KpZCdpo+1RoMnXr/0sxsVWSlwNH7/KCbrSIFFuH7pxxJm+aSTtJrZvg8FPDx2WforqwKihE9cv/RzGwqYx6Nl/KNMAEA3slBg8fJL7xdN/iEwkYGS7xD08NgV61etSf/qFUuWX/SLQqHH7E7Nf4xDgK2hQKFQYpSAYM4LPws556sCHh67Yvwmx4mr3J9scKd0PLux2j0KWf8xVQD1UKCj1KclzHPOhB9OJV7FbH2DkIfH8ON+ZbYQTQYs4UOlZy8rZw0/NOrh9Jg07HSjO6sKPPDxp4TcJ5kMsZLA7xXw8Ni5hFZyliyLJAu/++AlywqFHtMNGhMHOmYde6XSPFco9Jglyy8pJa5yfWDzVtUfMe7hsTPpH9q8rbryDYv7Lv2Prq6i3d7R3g2aA3iZlKFFWET9HTNbQnJ3WhOd4EuDHh47ivsjTiX+YyzmLR39qwYXYZHSGEj/MVcAGbtkCy/1XzgggZ4rkqzO8gG+NOjh8XJnCTFsyEm6HhIvKPVfODDUhpqSAOr5gK6uor35j5c85tR9CCBlsPj+AA+PrfbPoNpOv+Qji/s/09/VVbS7MuFnpNgjUvzpp3ulq6tof/z7zz/cOeOMOLItb3OSOhD8rkEPD4ULTd4mrvx3N/df+m+FQo+5/fYL90i+bI/F4k8/3atdXUX74/v+5q6OmWfMjmzLsanEKfmtwx4TO+5PI9tiq25w8ZK+hZcUCj1mLJN+rw7T9yCKKDIA9HfMbAnZ/TQwuTcnqW8S8piw1u+yTr/Kb1qi3Nv3W/p8ZayTfns8B/DKfACQJQWtmLMTV33ccGQAP1DUY8JZvzMcmVSqj2vqCtcv/dhg5pFpj+bG9rj8zpqECuaG/gtfpFTeq+pWM1njzxn0mDghvwqTNaJujYD+cvHDl75QKBTMnkj67XUCAIBSqeS6uor2pocveTCR+H0AVRgWvjzoMQGMX5kMEags6gpLln9qedbsU9orKnivJeB6e7vTYlfR3tJ/6R3OJRcwETNYfXnQYzwH/QyjBNZYqx9c0nfxr7q6ira3tzvdWyvaq8m33qd7pYii/fqqzz/QOeOtzxsT/bmqarZlwJ825DG+jJ/AYjgwiVQ+ekvfpTcWUbQ3PL33jH+vEwAA9KJXCugxt676yH2d09++OjDRu0TFk4DHODN+EsORSdLqpTf3L7yuiKLtxt41/oYgAADoR0kzErjgd50zzxgIODpT1Qmg5EnAYzwYv+WciV31/93cf8lXC+gx1+HChqh8NUz9fQsJrLzgN3NmvC0NTO4MUeeVgMe4MP4kLf/9kv5L/qGAHlPCvIapeDVUA04/SiigYG5Z9bXejplvjQOOzhBVVSjIk4BHkxk/QBpwziQyWFzct/CLQ4xfPQFslwT6a0rgw3d1TH/bGsv2XcjumNIe7lz08Ngl0weEwLAccSLlv1ny4MJ/LKBgSlmdv6GqXA1rUDW2dPM7rvwgm/CbgLCoE4LfO+DR6MZPZCggJ5WFi/sWXtWInr+OhjWmEua5Iop2Sf/C74jE8wlctWQZ6tuGPRpV9KswMTOxpFL98BDjd2jQcXgN7U270Z12dRXtkr6Ft2qSvAeKlZYjo54EPBrP+J3lgAk8kGpy9pK+S77Z1VW0o3WCz4TJAbwSTz/dK4VCj7nlrgtWHD3rtJ8zbFdgo31EktSfQuzRKMYfmJxRyAupS997c9/Cn+/tDr+mzwFsLyew4Kgr9iNrlwQmf1qcDqYgNb5M6LEXrd+FtsWkLl4uUj6nPs2nGYy/qQhgKAkUDvxaPpoS/GtgcufHrqy1CoFXAx57zu6hSoCE3GISV73NJdUP3vzop1cPifnhCWAMUESR69smz+u89m/B9A8EgpPEDxbx2FOSX5iZDYVwEl9104NrLgO6JSv1lZoqP9V0BtOLXgWUCug3N6+6vHfurDPuI5gua8LJTlLnR4x5jK31i7PZmZebU0k/sbjvoi8p7gQAvg7XNd1Mi6aOnety632dXz3MUvSd0LScEqeDTrO2QU8EHqPq9wFIaFqMc/GjFaqe37P8snuGzPBrym3sTZ88q5PApw6/OlqX4ysM20+IOoikPiTwGK14X5iYLUdI0rjkaOOnbnnwb19qtnh/XBLAq/ICc68tQHG14XC/RMoOAPsqgcduOH5nTGREXIXIff7G5RdfBQA1z9/0/SjjwkPW8wJFgK9Z+dm+o2ee/t9QOjwwudkKJag43zPgMTKvDyFAA9tiRNMHNK0Wbupf+L1iscin9Z5G1/VfOC5mWI47z9iFou2tDVpYMPfai0nxT5aDlkQqXg14jMDrhwYKOEm+vimt/M0PH/nspvEg+cc9AdRDAiCbQLyg86oTiczXrAnfkkoMFedzAx7bjfUJRKHJUyrxw6kkl9zct/BnwNZc03i75nHtDYc+tPM6r70EjL83HE6NXVkAgq8UeNRdPhRiTGRUU6jotVVNFpX6L1tbq+03bZZ/QhNARgJbH+CC2VfOhjVfsSb4C1GBSFI7n9CHBRNZ7hMbYzlCKvF9qYs/e0v/pXeMZ68/oQhgm2pg7rXzFfyFgIPDEqlCRVIQrLeGiWX4SuDQtFAq1bWAfLXq1l5Z6u+Os3elINjDp/R4AtgDuYH62WvnHfVP08W2XgLwxYGJ2hM3qFCIzw+M9zgfAigCzrFoClF3S5omxVsf/vSjE8XrT1gC2KIGhtRwzzn6ik5jzN8QeL7hAIlUFAr1LcXjzfBVSSHGhIbJIHXxXUr0hcXLL/zlEMMft7G+J4BXvxJUKJS4TgTz515zBiv9HbM5lcBIpCrIhpF6IhgHhs8cGMsBUhc/CMVXb+y78Ma6KgS2Hlw70TDhk1+vfAHeP+ea9xL4Umb7FkCRSOyJoEmlPqkqc2AMB3AuflKgV8br4/8oPXtZeSLKfU8AOwoLXvEyLJj79bMZuITJvjkjgqpSliNgf98aP8a3HDKTzQxf3NftZvnWDU8vXA8AzTSwwxPAHr4fhUIPD+3xXjDn6/OYcDERn0wwSKUCKPwkosZT+qIEDjiiLISLH4K6b1irN9zwQGb4zb5zzxPA3iMCWjDnmrMI9ElA3x6YnMnKh84pkd96vFdlPgRENjARRB1U5B4orvvTQGup9+kPVbYa/sQo63kCGGtF0PkvJyqSCwB6X2TzU0RTJBIrKTmvCvaktycyZNlyiDgdTBjmxwr37cP61t5Wz+dkUn+R84bvCWCUiGCrF3lf5+UHWQ0KZGg+wZxgOUAqcTaHAIDPFYyu0SugpKpEbCxHUAhSFz8JaI+yWbxk+aeW17+5FuM37Cx+TwBNjCKK3I9OqicMC+gxUcfKtym5eQDeE9jcDABIXRWq4slgt40eAoK1HILIIEnLZSb+hapbApP86KZln9lckwU0Lyvr+hjfE8Ae0aF0WtciMzSb/P5jrpulLvlzgN+l5N4empYWqCKVKhTioKQ+TNiJzSukxpnGcAAmg9hVElLcJ9D/dMB/3dp38eP1nygUekxHqU8nah3fE0AjhAfo4Q68/CWcP/eKQ9nZs2DwThHtCk3USsRZmKBOoXBKYMrOPKWJa/GotWCrYTJkKQQRIZFyDKUHFPIjg+AH333wE8u3xvL1Ji6f2PME0FjvM3V1LTKvTDzNP/rrB8PK2xl4i6icYcjuF3AEpymcplB1qkqOSAnZ0JJx+mxUFVQzeDCDmNnCUoBUEqQab2CY3wrp/xgxPz20b+UjQ0m1q6toT+uFeG/vCaApcgV3doFfmYxa8IarJ9EAThbGWwjoUsVxlm2r5RBOHWobVJAdgko6RCU00/OqOXbKYvhs5ZaIYcjCkIXTFKlUq6roB9FdJLibbHDXTcs+sXLoLxpi9Opje08ATZ0v2Jb3+sAR/3pAElZPYqI3AHqiAscyeFpgcgBoCyGIChQqUEhGBUoKor1IDlq3dMqsXTVbBRPARAwmA0MWACFxFQhkExT9Cv0dge6zwG/Lffs99Yp2XOrqKhpv9J4Axm2YUECJV3b10bbaUefP/dJUSqM5wny8gTlayc0F6CgAUwwHbCmsWVudFASakQPqs+uhlNklEXQLOyht45HTEGOmuufO/mJrCENQrf/OeuMTIUtdMBhEBkwGRAQnCVKJodCNAFYAvBwq/Yb5fiW77KZlH1/1yri9UOgxAOBjek8AE/D+KwqFEq9cuW1CAIDCoV+eHOVbDiGmI1NxRzDzwapyCBSHADQLhBwBOSYLQwZEvIUUMrKoO1KtuW19mRvf8hLUcpEEqv0/gaj+J0NVIergNAUgVQWqpLQapE9D6WklfYqAx53TxwK1Kw59ePW6bcXrhUKPWbmyj7yX9wTgsS1CQIk7umZS/6xVuqPZ8+cfXMxF0f5tA3bwQGJzgKrsC6JZUJ0B0HQCJithCqCTCJSHaouC8gBCympuERGRKqo1OkiIqAxFBYRBhW4i0AZV3QCi1SS6RhmrQPSCUX5O0uS5eEDX13fXbS8X8sIJ+5t1h06VmoeHN/jGwf8PHE9CPyXD6fgAAAAASUVORK5CYII="
        )
    ),
    width=76,
)
st.caption(
    t(
        "مشروع تجريبي للمقابلة، مش خدمة رسمية من WE",
        "Illustrative interview project, not an official WE service",
    )
)
st.title(t("مساعد تخطيط الإمداد", "Supply planning assistant"))
st.caption(
    t(
        "قراءة النتائج • تفسير السبب • الرجوع للمصدر",
        "Read results · Understand the reason · Check the source",
    )
)
st.info(
    t(
        "نسخة تجريبية بقواعد محددة، مش نموذج ذكاء اصطناعي لغوي. الكميات والأسعار تقديرية، والنتائج للمراجعة والعرض فقط.",
        "Rule-based prototype, not a language-model AI agent. Quantities and prices are estimates. Results are for review and demonstration only.",
    )
)
c = st.columns(3)
for col, value, label in zip(
    c,
    [
        len(items),
        sum(i["status"] == "REORDER" for i in items),
        sum(i["status"] == "OVERSTOCK" for i in items),
    ],
    [
        t("الأصناف", "Items"),
        t("مراجعة طلب", "Reorder review"),
        t("رصيد زائد", "Above maximum"),
    ],
):
    col.metric(label, value)
options = ["summary", "scenario", "reorder", "excess", "item"]
labels = [
    t("ملخص", "Summary"),
    t("جرّب تغيير الكميات", "Try quantity changes"),
    t("المحتاج طلب", "Reorder review"),
    t("المخزون الزائد", "Excess stock"),
    t("شرح صنف", "Item explanation"),
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
    t(
        "بحث محدد: كود صنف، ملخص، طلب، أو زائد",
        "Exact query: item code, summary, reorder, or excess",
    )
)
if q:
    q = q.strip().lower().translate(str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789"))
    terms = {
        "ملخص": "summary",
        "summary": "summary",
import base64
import io
import json
import streamlit as st

st.set_page_config(
    page_title="Supply planning assistant | مساعد تخطيط الإمداد", layout="centered"
)
lang = st.selectbox("اللغة / Language", ["العربية", "English"], key="language")
ar = lang == "العربية"


def t(a, e):
    return a if ar else e


direction = "rtl" if ar else "ltr"
alignment = "right" if ar else "left"
st.markdown(
    f"""<style>
.stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {{background:#F6F3FB;color:#1B1030;color-scheme:light;}}
.block-container {{max-width:1000px;padding-top:2rem;}}
.stMain, [data-testid="stMarkdownContainer"], [data-testid="stWidgetLabel"], h1,h2,h3 {{direction:{direction};text-align:{alignment};}}
[data-testid="stMarkdownContainer"] p, [data-testid="stWidgetLabel"] p, label, h1,h2,h3 {{color:#1B1030!important;overflow-wrap:anywhere;}}
h1,h2,h3 {{color:#5B2C8F!important;}} h1 {{font-size:2rem!important;}}
[data-testid="stCaptionContainer"] p {{color:#554766!important;direction:{direction};text-align:{alignment};}}
[data-testid="stMetric"] {{background:#F1E8FB;padding:16px;border-radius:8px;border-top:3px solid #5B2C8F;direction:{direction};text-align:{alignment};}}
[data-testid="stMetric"] * {{color:#28133F!important;}}
[data-testid="stMetricValue"] {{direction:ltr;unicode-bidi:isolate;}}
[data-baseweb="select"] > div, [data-baseweb="input"], input, [data-testid="stNumberInputContainer"] {{background:#FFFFFF!important;color:#1B1030!important;}}
[data-baseweb="select"] span, [data-baseweb="select"] input, input {{color:#1B1030!important;-webkit-text-fill-color:#1B1030!important;}}
[data-baseweb="select"], [data-testid="stRadioGroup"], [data-testid="stExpander"] summary {{direction:{direction};text-align:{alignment};}}
[data-baseweb="popover"] *, [role="listbox"], [role="option"] {{background:#FFFFFF!important;color:#1B1030!important;}}
[data-testid="stNumberInput"] input {{direction:ltr;text-align:center;}}
button {{min-height:44px!important;}} [data-testid="stBaseButton-secondary"] {{background:#FFFFFF;color:#5B2C8F;}}
[data-testid="stExpander"] {{border-color:#CDBDE2;}} code, pre {{direction:ltr;text-align:left;}}
[data-testid="stAlert"] {{background:#E8E0F5;color:#1B1030;}}
</style>""",
    unsafe_allow_html=True,
)
# Use the checked workbook snapshot. This app does not recalculate Excel formulas.
data = json.loads((Path(__file__).parent / "2-data.json").read_text(encoding="utf-8"))
items = data["items"]
by_code = {i["code"]: i for i in items}


def name(i):
    return i["description"] if ar else i["name"]


def n(x):
    return f"{x:,.2f}".rstrip("0").rstrip(".")


# Keep explanations tied to the stored workbook policy, not purchase instructions.
def explain(i):
    st.subheader(i["code"] + " | " + name(i))
    states = {
        "REORDER": t("محتاج مراجعة لإعادة الطلب", "Review for replenishment"),
        "OVERSTOCK": t("رصيد أعلى من الحد الأقصى", "Stock above maximum"),
        "OK": t("داخل حدود السياسة", "Within policy limits"),
        "CHECK": t("محتاج فحص بيانات الرصيد", "Check stock data"),
    }
    st.write(states[i["status"]])
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


def scenario_editor(item):
    st.subheader(t("تجربة كميات جديدة", "Quantity scenario"))
    st.info(
        t(
            "التعديلات تجربة خاصة بجلستك فقط. لا تغيّر Excel أو بيانات الزوار الآخرين، وليست أمر شراء.",
            "Trial changes belong only to this session. They do not change Excel or other visitors' data and do not place orders.",
        )
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
    st.success(
        t(
            "نتيجة السيناريو المعاد حسابها أدناه، وليست القيم الأصلية المخزنة في الشيت.",
            "Recalculated scenario results below, not the original stored sheet values.",
        )
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


st.image(
    io.BytesIO(
        base64.b64decode(
            "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"
        )
    ),
    width=76,
)
st.caption(
    t(
        "مشروع تجريبي للمقابلة، مش خدمة رسمية من WE",
        "Illustrative interview project, not an official WE service",
    )
)
st.title(t("مساعد تخطيط الإمداد", "Supply planning assistant"))
st.caption(
    t(
        "قراءة النتائج • تفسير السبب • الرجوع للمصدر",
        "Read results · Understand the reason · Check the source",
    )
)
st.info(
    t(
        "نسخة تجريبية بقواعد محددة، مش نموذج ذكاء اصطناعي لغوي. الكميات والأسعار تقديرية، والنتائج للمراجعة والعرض فقط. التنبؤ ثابت من الملف، بدون ربط مباشر بـ Excel.",
        "Rule-based prototype, not a language-model AI agent. Quantities and prices are estimates. Results are for review and demonstration only. Fixed workbook forecast; no live Excel connection.",
    )
)
c = st.columns(3)
for col, value, label in zip(
    c,
    [
        len(items),
        sum(i["status"] == "REORDER" for i in items),
        sum(i["status"] == "OVERSTOCK" for i in items),
    ],
    [
        t("الأصناف", "Items"),
        t("مراجعة طلب", "Reorder review"),
        t("رصيد زائد", "Above maximum"),
    ],
):
    col.metric(label, value)
options = ["summary", "scenario", "reorder", "excess", "item"]
labels = [
    t("ملخص", "Summary"),
    t("جرّب تغيير الكميات", "Try quantity changes"),
    t("المحتاج طلب", "Reorder review"),
    t("المخزون الزائد", "Excess stock"),
    t("شرح صنف", "Item explanation"),
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
    t(
        "بحث محدد: كود صنف، ملخص، طلب، أو زائد",
        "Exact query: item code, summary, reorder, or excess",
    )
)
if q:
    q = q.strip().lower().translate(str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789"))
    terms = {
        "ملخص": "summary",
        "summary": "summary",
        "طلب": "reorder",
        "reorder": "reorder",
        "زائد": "excess",
        "excess": "excess",
    }
    if q in terms:
        mode = terms[q]
    elif q in by_code:
        code = q
        mode = "item"
    else:
        mode = "unsupported"
st.divider()
if mode == "summary":
    st.subheader(t("ملخص النموذج", "Model summary"))
    st.write(
        t(
            "النسخة فيها 65 صنف من ملفك. آخر شهر مقفول أكتوبر 2026، ورصيد البداية بتاريخ 1 نوفمبر 2026 مضاف له حركات Log. اختار صنف أو قائمة عشان تشوف تفاصيل النتيجة.",
            "This snapshot contains 65 items from your workbook. The last closed month is October 2026. Opening stock is dated 1 November 2026, with recorded Log movements added. Choose an item or list to inspect its result.",
        )
    )
    st.caption("Dashboard!B8:B9 | Analysis!AE5:AE69")
elif mode == "scenario":
    scenario_editor(by_code[code])
elif mode == "item":
    explain(by_code[code])
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

from pathlib import Path
import json,re
import streamlit as st
st.set_page_config(page_title='مساعد تخطيط الإمداد',layout='centered')
st.markdown('<style>.stMain{direction:rtl;text-align:right}input{direction:rtl}p{overflow-wrap:anywhere}</style>',unsafe_allow_html=True)
data=json.loads((Path(__file__).parent/'data.json').read_text(encoding='utf-8'))
items=data['items'];by_code={i['code']:i for i in items}
labels={'REORDER':'محتاج مراجعة لإعادة الطلب','OVERSTOCK':'رصيد أعلى من الحد الأقصى','OK':'داخل حدود السياسة','CHECK':'محتاج فحص بيانات الرصيد'}
def n(x):return f'{x:,.2f}'.rstrip('0').rstrip('.')
def explain(i):
 st.subheader(i['code']+' | '+i['description']);st.write(labels[i['status']])
 for label,key in [('الرصيد الحالي','stock'),('المطلوب توريده بالفعل','onOrder'),('المركز المخزني: الرصيد والطلبات المفتوحة','position'),('نقطة إعادة الطلب','rop'),('الحد الأقصى','max'),('توقع استهلاك الشهر التالي','forecast'),('مخزون الأمان','safety'),('الكمية المقترحة','suggested')]:st.write(f"{label}: {n(i[key])} {i['unit']}")
 if i['status']=='REORDER':st.write('المركز المخزني أقل من نقطة إعادة الطلب. الكمية المقترحة للوصول للحد الأقصى، وتحتاج مراجعة موعد وصول الطلبات وخطة التوسع والميزانية.')
 elif i['status']=='OVERSTOCK':st.write('الرصيد أعلى من الحد الأقصى. راجع إعادة التوزيع قبل طلب كميات إضافية.')
 elif i['status']=='CHECK':st.warning('الرصيد بالسالب. راجع حركات المخزن.')
 else:st.write('داخل حدود سياسة الملف. ده مش ضمان ضد تأخير التوريد.')
 st.write('طريقة التنبؤ: '+('التمهيد الأسي' if i['method']=='Exp. smoothing' else 'متوسط متحرك لثلاثة أشهر'))
 r=i['row'];st.code(f'Analysis!AA{r} (stock), AB{r} (on order), AC{r} (position), X{r} (reorder point), Z{r} (max), AE{r} (status), AF{r} (suggested), S{r} (forecast), W{r} (safety)',language=None,wrap_lines=True)
st.title('مساعد تخطيط الإمداد')
st.info('نسخة أولى بقواعد محددة، مش نموذج ذكاء اصطناعي لغوي. بيانات الكميات والأسعار تقديرية. النتائج للمراجعة والعرض، مش أوامر شراء.')
st.write(f"عدد الأصناف: {len(items)}. محتاج مراجعة للطلب: {sum(i['status']=='REORDER' for i in items)}. رصيد أعلى من الحد: {sum(i['status']=='OVERSTOCK' for i in items)}.")
mode=st.radio('اختار العرض',['ملخص','المحتاج طلب','المخزون الزائد','شرح صنف'],horizontal=True)
code=st.selectbox('اختار الصنف',list(by_code),format_func=lambda c:c+' | '+by_code[c]['description'])
q=st.text_input('أو اكتب: ملخص، طلب، زائد، أو كود صنف')
if q:
 q=q.strip().translate(str.maketrans('٠١٢٣٤٥٦٧٨٩','0123456789'))
 if q in ['ملخص','طلب','زائد']:mode={'ملخص':'ملخص','طلب':'المحتاج طلب','زائد':'المخزون الزائد'}[q]
 elif q in by_code:code=q;mode='شرح صنف'
 else:mode='unsupported'
if mode=='ملخص':st.write('دي لقطة من نتائج Excel المستلمة في 24 نوفمبر 2026. آخر شهر مقفول أكتوبر 2026. رصيد البداية 1 نوفمبر 2026 ومضاف له حركات Log. اختار صنف عشان تشوف السبب ومصدر الأرقام.');st.code('Dashboard!B8:B9 | Analysis!AE5:AE69',language=None,wrap_lines=True)
elif mode=='شرح صنف':explain(by_code[code])
elif mode=='unsupported':st.warning('السؤال خارج حدود النسخة دي. استخدم ملخص، طلب، زائد، أو كود صنف موجود. مش هخمن إجابة.')
else:
 status='REORDER' if mode=='المحتاج طلب' else 'OVERSTOCK';rows=[i for i in items if i['status']==status];st.write(f'عدد الأصناف: {len(rows)}. الترتيب حسب الشيت، مش ترتيب أولوية.')
 for i in rows:
  with st.expander(i['code']+' | '+i['description']):explain(i)
with st.expander('حدود النسخة ومصدر البيانات'):
 st.write('النسخة بتقرأ نتائج محفوظة، مش بتعيد حساب Excel ولا بتتحدث تلقائيًا لو عدلت الملف. التحقق الأولي راجع اتساق الرصيد والحالة والكمية المقترحة للأصناف، مش كل معادلات الملف. التنبؤ التاريخي ببيانات تقديرية مش ضمان للمستقبل.')
 st.write('مفيش اتصال بموردين أو نموذج AI أو إرسال طلبات شراء. عند النشر على Streamlit، البيانات بتتحفظ وتتعالج على استضافته. نسخة العرض متاحة لأي حد يوصله الرابط أو QR بموافقتك. متضيفش بيانات فعلية غير مسموح بعرضها.')

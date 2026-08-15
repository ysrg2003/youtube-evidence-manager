# الإعدادات والأسرار

## قاعدة أمنية أساسية

> لا تُحفظ مفاتيح YouTube أو Gemini في Git، ولا في README، ولا في تقارير artifacts، ولا في رسائل السجل. استخدم ملف `.env` محليًا أو GitHub Actions Secrets.

## خريطة القيم الحالية

| الاسم | النوع | مطلوب الآن؟ | يقرأه حاليًا | مثال آمن |
|---|---|---:|---|---|
| `YOUTUBE_API_KEY` | سر API | نعم عند استدعاء `YouTubeDataClient` | `src/youtube_api_client.py` و`.env` | `REPLACE_WITH_YOUTUBE_API_KEY` |
| `GEMINI_API_KEY` | سر API مستقبلي | لا؛ لا يقرأه كود حاليًا | `.env.example` للتخطيط فقط | `REPLACE_WITH_GEMINI_API_KEY` |

## `YOUTUBE_API_KEY` — مفتاح YouTube Data API v3

**الغرض.** يستخدمه `src/youtube_api_client.py` لاستدعاءات القراءة العامة مثل البحث، تفاصيل الفيديو، والتعليقات. بدونه يفشل العميل قبل إجراء أي طلب. أداة captions المنقولة لا تعتمد عليه.

**التصنيف.** Secret. لا تضعه في source control أو في رابط HTTP أو في أمر قد يبقى في shell history.

**قبل البدء.** تحتاج حساب Google ومشروعًا في Google Cloud Console. يجب تفعيل YouTube Data API v3 في المشروع. لا تحتاج OAuth لمسار القراءة العامة الحالي؛ OAuth مطلوب لعمليات أو موارد أكثر خصوصية، و`captions.download` له متطلبات ملكية وصلاحية مختلفة.

**طريقة الحصول عليه.**

1. افتح [Google Cloud Console](https://console.cloud.google.com/) بالحساب الذي سيملك المشروع.
2. اختر مشروعًا موجودًا أو أنشئ مشروعًا جديدًا من قائمة اختيار المشروع.
3. افتح **APIs & Services → Library**.
4. ابحث عن **YouTube Data API v3** وافتح صفحة الخدمة.
5. اضغط **Enable**، ثم افتح **APIs & Services → Credentials**.
6. اضغط **Create Credentials → API key**.
7. افتح **Edit API key**، وقيّد المفتاح إلى YouTube Data API v3 قدر الإمكان. لا تتركه عامًا إذا كانت قيود التطبيق المناسبة متاحة.
8. انسخ القيمة مرة واحدة إلى مدير أسرارك، ولا تلصقها في المحادثة أو في Git.

**ما الذي تضعه؟** استخدم placeholder عند التوثيق فقط:

```text
YOUTUBE_API_KEY=REPLACE_WITH_YOUTUBE_API_KEY
```

**مكان الإضافة محليًا.** من جذر المستودع:

```bash
cp .env.example .env
```

افتح `.env` وأبدل placeholder بقيمة المفتاح الحقيقية. `src/youtube_api_client.py` يستدعي `python-dotenv` لتحميل `.env` تلقائيًا. تحقق دون طباعة القيمة:

```bash
python - <<'PY'
import os
from dotenv import load_dotenv
load_dotenv()
value = os.getenv("YOUTUBE_API_KEY", "")
print({"configured": bool(value), "length": len(value)})
PY
```

النتيجة المتوقعة هي `configured: True` مع طول رقمي فقط. إذا ظهر `False`، تحقق من أن اسم الملف `.env` ومكانه هو جذر المستودع وأن اسم المتغير مكتوب حرفيًا.

**مكان الإضافة في GitHub Actions.**

1. افتح [مستودع youtube-evidence-manager](https://github.com/ysrg2003/youtube-evidence-manager).
2. اضغط **Settings**.
3. من القائمة الجانبية اضغط **Secrets and variables → Actions**.
4. اختر تبويب **Secrets**، ثم اضغط **New repository secret**.
5. اكتب الاسم بالضبط: `YOUTUBE_API_KEY`.
6. ألصق القيمة الحقيقية، ثم اضغط **Add secret**.
7. تحقق من أن GitHub يعرض اسم السر دون قيمته. Workflow المستقبلي سيستهلكه بهذه الصيغة:

```yaml
env:
  YOUTUBE_API_KEY: ${{ secrets.YOUTUBE_API_KEY }}
```

لا تضعه في **Variables**، ولا تطبعه، ولا تستخدم `set -x`.

**إذا فشل.**

| الحالة | التحقق | الإصلاح |
|---|---|---|
| `YOUTUBE_API_KEY is not configured` | افحص `configured` بالأمر أعلاه | أنشئ `.env` في الجذر أو أضف Secret بالاسم الصحيح |
| `keyInvalid` | راجع المشروع والمفتاح في Cloud Console | أنشئ مفتاحًا جديدًا وألغِ القديم إذا كان غير صالح |
| `accessNotConfigured` | افتح **APIs & Services → Enabled APIs** | فعّل YouTube Data API v3 في المشروع الصحيح |
| `quotaExceeded` | راجع صفحة **Quotas** في Cloud Console | أوقف التشغيل، استخدم caching، ولا تدوّر مفاتيح لتجاوز الحصة |
| HTTP 403 بسبب القيود | افحص Application/API restrictions | عدّل القيود لتطابق بيئة الاستخدام، ثم أعد اختبارًا محدودًا |

**التدوير والإلغاء.** إذا ظهر المفتاح في commit أو سجل أو شاشة، اعتبره مكشوفًا فورًا. افتح **Google Cloud Console → APIs & Services → Credentials**، احذف المفتاح المكشوف أو دوّره، أنشئ قيمة جديدة، ثم حدّث `.env` وGitHub Secret. افحص سجل Git قبل مواصلة العمل؛ لا تنسخ القيمة إلى تقرير.

## `GEMINI_API_KEY` — مفتاح Gemini مستقبلي

**الغرض.** سيُستخدم مستقبلًا لتحليل evidence bundle بعد اكتمال طبقة YouTube. لا يقرأه أي كود نشط في هذا commit، ووجوده في `.env.example` يعرّف الاسم المتوقع فقط.

**التصنيف.** Secret. لا تضعه الآن إذا لم يكن هناك adapter مفعّل.

**ما الذي تضعه؟** في التوثيق استخدم placeholder فقط:

```text
GEMINI_API_KEY=REPLACE_WITH_GEMINI_API_KEY
```

**مكان الإضافة عند تفعيل التكامل.** سيكون في `.env` محليًا أو في **Settings → Secrets and variables → Actions → Secrets → New repository secret** داخل هذا المستودع، بالاسم `GEMINI_API_KEY`. لا يُضاف إلى Variables.

**التحقق والاسترداد.** لا يوجد health check نشط لهذا السر في النسخة الحالية. عند إضافة adapter يجب توثيق endpoint والنموذج والطلب الأصغر ومخرجات redaction قبل تفعيل Workflow. اختبارات المشروع السابق أعادت HTTP 403 `permission_denied` من مشروع Gemini الحالي؛ لذلك لا ينبغي تشغيل corpus أو إعادة المحاولة بلا حدود.

**التدوير والإلغاء.** استخدم صفحة إدارة مفاتيح المشروع في [Google AI Studio](https://aistudio.google.com/) أو Google Cloud حسب مكان إنشاء المفتاح. ألغِ المفتاح فور انكشافه، ثم حدّث التخزين المحلي وGitHub Secret. لا تضع قيمة المفتاح في issue أو commit أو artifact.

## متغيرات مشتقة وحالة تشغيل

المخرجات مثل `output/`, `artifacts/`, `reports/`, ملفات `.srt` و`.jsonl` هي **derived state** وليست إعدادات. يتجاهلها `.gitignore` لتقليل خطر نشر captions أو التعليقات أو التقارير الشخصية. احذفها محليًا عندما لا تعود مطلوبة، ولا ترفعها إلى Git إلا إذا كانت منقحة ومطلوبة صراحة.

## المراجع الرسمية

[1]: https://console.cloud.google.com/ "Google Cloud Console"
[2]: https://developers.google.com/youtube/v3/getting-started "YouTube Data API getting started"
[3]: https://developers.google.com/youtube/v3/determine_quota_cost "YouTube Data API quota costs"
[4]: https://aistudio.google.com/ "Google AI Studio"

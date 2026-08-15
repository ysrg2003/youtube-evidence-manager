# الإعدادات والأسرار

## قاعدة أمنية أساسية

> لا تُحفظ مفاتيح YouTube أو Gemini في Git، ولا في README، ولا في تقارير artifacts، ولا في رسائل السجل. استخدم ملف `.env` محليًا أو GitHub Actions Secrets.

## خريطة القيم الحالية

| الاسم | النوع | مطلوب الآن؟ | يقرأه حاليًا | مثال آمن |
|---|---|---:|---|---|
| `YOUTUBE_API_KEY` | سر API | نعم عند استدعاء `YouTubeDataClient` | `src/youtube_api_client.py` و`.env` | `REPLACE_WITH_YOUTUBE_API_KEY` |
| `GEMINI_API_KEY` | سر API | اختياري؛ مطلوب فقط مع `--analyze` | `src/gemini_analyzer.py` و`.env` | `REPLACE_WITH_GEMINI_API_KEY` |
| `GEMINI_MODEL` | متغير تشغيل غير سري | اختياري؛ الافتراضي `gemini-2.5-flash` | `src/gemini_analyzer.py` و`.env` أو Actions Variables | `gemini-2.5-flash` |

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

## `GEMINI_API_KEY` — مفتاح Gemini الاختياري

**الغرض.** يستخدمه `src/gemini_analyzer.py` فقط عندما تشغّل `python -m src.evidence_cli VIDEO_ID --analyze` بعد جمع evidence bundle. لا يُرسل أي طلب Gemini في التشغيل العادي.

**التصنيف.** Secret. لا تحتاج إلى وضعه إذا كنت تريد metadata وcaptions والتعليقات فقط.

**ما الذي تضعه؟** في التوثيق استخدم placeholder فقط:

```text
GEMINI_API_KEY=REPLACE_WITH_GEMINI_API_KEY
```

**مكان الإضافة.** محليًا، انسخ `.env.example` إلى `.env` ثم أضف `GEMINI_API_KEY`. في GitHub Actions يُحفظ في **Settings → Secrets and variables → Actions → Secrets → New repository secret** بالاسم نفسه، ولا يُضاف إلى Variables. يمكنك اختيار النموذج عبر `GEMINI_MODEL`، وقيمته الافتراضية في القالب `gemini-2.5-flash`.

**التحقق والاسترداد.** نفّذ جمع evidence أولًا، ثم استخدم `--analyze` على فيديو واحد فقط. نجاح العملية يكتب `analysis.json` و`analysis.md` بجوار `evidence.json`. إذا ظهر `permission_denied` أو HTTP 401/403، أوقف المحاولة وراجع المشروع والصلاحيات والمفتاح دون طباعته؛ لا توجد إعادة محاولات غير محدودة ولا تدوير مفاتيح لتجاوز الحصة.

**التدوير والإلغاء.** استخدم صفحة إدارة مفاتيح المشروع في [Google AI Studio](https://aistudio.google.com/) أو Google Cloud حسب مكان إنشاء المفتاح. ألغِ المفتاح فور انكشافه، ثم حدّث التخزين المحلي وGitHub Secret. لا تضع قيمة المفتاح في issue أو commit أو artifact.

## `GEMINI_MODEL` — اختيار نموذج التحليل

هذا المتغير غير سري ويحدد اسم نموذج Gemini الذي يستعمله `--analyze`. اتركه على `gemini-2.5-flash` في `.env.example`، أو غيّره إلى اسم نموذج متاح لحسابك. في GitHub Actions ضعه في **Settings → Secrets and variables → Actions → Variables → New repository variable** بالاسم `GEMINI_MODEL`; لا تضعه في Secrets إذا لم تكن هناك سياسة داخلية تتطلب ذلك. إذا ظهر خطأ model not found، راجع قائمة النماذج المتاحة لدى المزود، حدّث القيمة، ثم أعد تشغيل فيديو واحد.

## متغيرات مشتقة وحالة تشغيل

المخرجات مثل `output/`, `artifacts/`, `reports/`, ملفات `.srt` و`.jsonl` هي **derived state** وليست إعدادات. يتجاهلها `.gitignore` لتقليل خطر نشر captions أو التعليقات أو التقارير الشخصية. احذفها محليًا عندما لا تعود مطلوبة، ولا ترفعها إلى Git إلا إذا كانت منقحة ومطلوبة صراحة.

## المراجع الرسمية

[1]: https://console.cloud.google.com/ "Google Cloud Console"
[2]: https://developers.google.com/youtube/v3/getting-started "YouTube Data API getting started"
[3]: https://developers.google.com/youtube/v3/determine_quota_cost "YouTube Data API quota costs"
[4]: https://aistudio.google.com/ "Google AI Studio"

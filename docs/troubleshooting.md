# التشخيص واسترداد الأخطاء

ابدأ دائمًا من جذر المستودع، وتأكد من تفعيل البيئة الافتراضية:

```bash
cd youtube-evidence-manager
source .venv/bin/activate
```

في Windows استخدم `.venv\Scripts\activate`. إذا لم يظهر `(.venv)` في بداية الطرفية، فعّل البيئة قبل متابعة أي إصلاح.

## أخطاء التثبيت والتشغيل

| الرسالة أو الحالة | السبب المحتمل | التحقق والإصلاح |
|---|---|---|
| `No module named youtube_transcript_api` | الاعتماديات غير مثبتة أو البيئة غير مفعلة | نفّذ `python -m pip install -r requirements.txt` من الجذر ثم أعد التشغيل |
| `No module named dotenv` | `python-dotenv` غير مثبت | نفّذ أمر التثبيت نفسه وتأكد من `python -m pip show python-dotenv` |
| خطأ compile | تعديل Python غير صحيح | نفّذ `python3 -m py_compile youtube_subtitles_translator.py src/youtube_api_client.py` واقرأ رقم السطر |
| الاختبارات تفشل بسبب import | مسار أو dependency ناقصة | فعّل `.venv`، ثبّت requirements، ثم نفّذ `python -m unittest discover -s tests -v` |

## أخطاء captions

| الرسالة أو الحالة | السبب المحتمل | التصرف الصحيح |
|---|---|---|
| `Transcripts are disabled` | صاحب الفيديو عطّل captions | سجّل `caption.status=missing` ولا تحاول تجاوز القرار |
| `No transcript available` | لا يوجد مسار متاح أو اللغة غير مناسبة | احتفظ بالmetadata فقط، واطلب فيديو آخر أو مصدرًا مصرحًا للنص |
| transcript نصه قصير أو فارغ | parser أو مسار caption غير صالح | لا ترسل النص إلى Gemini؛ احفظ السبب واطلب مراجعة يدوية |
| الترجمة العربية غير دقيقة | ترجمة آلية لا transcript أصلي | استخدم ملف اللغة الأصلية كمصدر، واعتبر العربية نسخة مساعدة فقط |
| فشل playlist في فيديو واحد | الفيديو منفردًا بلا captions أو به خطأ وصول | سجّل ذلك الفيديو واستمر في العناصر الناجحة، ولا تعِد كل القائمة |

## أخطاء YouTube Data API

| الرسالة أو الحالة | السبب المحتمل | التحقق والإصلاح |
|---|---|---|
| `YOUTUBE_API_KEY is not configured` | `.env` غير موجود أو الاسم خاطئ | نفّذ فحص `configured` الموجود في `docs/configuration.md` وتأكد من جذر المشروع |
| `keyInvalid` | المفتاح غير صالح أو منسوخ خطأ | افتح Google Cloud Credentials، أنشئ مفتاحًا جديدًا وألغِ القديم إن لزم |
| `accessNotConfigured` | API غير مفعّل في المشروع الذي يملك المفتاح | فعّل YouTube Data API v3 من **APIs & Services → Library** |
| `HTTP 400` أو `badRequest` | video ID أو parameters غير صحيحة | تحقق من `video_id`, `part`, `type`, و`maxResults` ثم أعد طلبًا مصححًا فقط |
| `HTTP 403 quotaExceeded` | نفدت الحصة | أوقف التشغيل، راجع **Quotas**، استخدم caching، ولا تدوّر المفاتيح لتجاوز الحد |
| `commentsDisabled` | التعليقات مغلقة للفيديو | خزّن `comments.status=disabled` وانتقل إلى metadata وcaption |
| `videoNotFound` | المعرّف غير موجود أو الفيديو غير متاح | تحقق من الرابط والمنطقة والصلاحية، ولا تعتبره دليلًا على أن API متعطل |

## أخطاء Gemini المستقبلية

| الرسالة أو الحالة | السبب المحتمل | التصرف |
|---|---|---|
| `permission_denied` | مشروع Gemini غير مصرح له | لا تعِد المحاولات؛ أصلح صلاحية المشروع أو عطّل adapter |
| HTTP 401/403 | مفتاح مفقود أو مشروع غير مصرح | تحقق من Secret دون طباعته، ثم راجع مشروع Google/AI Studio |
| quota/rate limit | تجاوز الحصة | أوقف المسار واحفظ التقرير؛ لا تدوّر المفاتيح لتجاوز الحد |
| JSON غير صالح | النموذج لم يلتزم بالعقد | احفظ الاستجابة المنقحة، أعد الطلب بإخراج schema مضبوط، ولا تستخدم النتيجة تلقائيًا |

## أخطاء Git والأسرار

إذا ظهر ملف output في Git:

```bash
git status --short
git status --short --ignored .env
```

إذا كان ملفًا شخصيًا لم يُرفع بعد، احذفه من working tree أو تأكد من قاعدة `.gitignore`. إذا ظهر مفتاح في commit أو سجل، أوقف الرفع فورًا، ألغِ المفتاح من Google Cloud أو Google AI Studio، أنشئ قيمة بديلة، ثم حدّث Secret المحلي وGitHub.

لا تحاول إخفاء السر بحذف السطر فقط؛ قد يبقى في Git history. افحص التغييرات قبل الرفع:

```bash
git diff --check
git diff --stat
git status --short
```

## فشل GitHub Actions

1. افتح المستودع ثم **Actions → CI**.
2. افتح التشغيل الفاشل، ثم job `offline-tests`.
3. إذا فشلت **Install dependencies**، راجع `requirements.txt` وإصدار Python.
4. إذا فشلت **Compile Python files**، شغّل الأمر نفسه محليًا واقرأ السطر المبلغ عنه.
5. إذا فشلت **Run offline tests**، نفّذ `python -m unittest discover -s tests -v` محليًا.
6. لا تضف API key إلى Workflow الحالي؛ CI الحالي لا يحتاج أي Secret.

## متى نطلب مساعدة المستخدم؟

نحتاج من المستخدم قيمة أو قرارًا فقط عندما لا يمكن استنتاجه بأمان، مثل اختيار Google Cloud project، إضافة `YOUTUBE_API_KEY` عبر GitHub Secret، أو اختيار فيديو اختبار عام. لا نطلب من المستخدم لصق المفاتيح في المحادثة أو في ملفات المشروع.

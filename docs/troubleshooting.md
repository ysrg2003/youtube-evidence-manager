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
| خطأ compile | تعديل Python غير صحيح | نفّذ `python3 -m py_compile youtube_subtitles_translator.py src/youtube_api_client.py src/evidence_manager.py src/gemini_analyzer.py src/evidence_cli.py` واقرأ رقم السطر |
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

## أخطاء جامع الأدلة وGitHub Actions

| الرسالة أو الحالة | السبب المحتمل | التصرف |
|---|---|---|
| `Input is not a valid YouTube video URL` | الرابط أو المعرّف غير صحيح | استخدم رابطًا من `youtube.com/watch?v=...` أو معرّفًا من 11 محرفًا |
| `YOUTUBE_API_KEY is missing` في Actions | لم يُحفظ السر في المستودع أو كُتب اسمه خطأ | افتح **Settings → Secrets and variables → Actions → Secrets** وأضف `YOUTUBE_API_KEY` دون طباعته |
| `GEMINI_API_KEY is required when analyze=true` | تم اختيار `analyze=true` دون سر Gemini | أضف `GEMINI_API_KEY` أو أعد التشغيل مع `analyze=false` |
| فشل رفع Artifact | لم تُنشأ ملفات في `artifacts/evidence/` | افتح `Collect evidence` وراجع خطوة الجمع و`run.log` قبل إعادة المحاولة |
| `commentsDisabled` | التعليقات مغلقة للفيديو | اترك `skip_comments=false`؛ سيحفظ النظام metadata وcaptions ويسجل القيد |

## أخطاء Gemini

| الرسالة أو الحالة | السبب المحتمل | التصرف |
|---|---|---|
| `permission_denied` | مشروع Gemini غير مصرح له | لا تعِد المحاولات؛ أصلح صلاحية المشروع أو عطّل adapter |
| HTTP 401/403 | مفتاح مفقود أو مشروع غير مصرح | تحقق من Secret دون طباعته، ثم راجع مشروع Google/AI Studio |
| quota/rate limit | تجاوز الحصة | أوقف المسار واحفظ التقرير؛ لا تدوّر المفاتيح لتجاوز الحد |
| JSON غير صالح | النموذج لم يلتزم بالعقد | لا تستخدم النتيجة؛ أعد التشغيل بنموذج يدعم JSON أو غيّر `GEMINI_MODEL`، وراجع رسالة `Gemini returned no valid JSON analysis` |

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

## أخطاء دمج النظام داخل مشروع آخر

| الحالة | السبب المحتمل | الإصلاح |
|---|---|---|
| `ModuleNotFoundError: src` | المشروع المضيف لا يشغّل Python من جذر المستودع أو لم يضف المصدر إلى import path | استخدم working directory صحيحًا، أو ثبت المستودع داخل `vendor/` ثم شغّل من الجذر، أو استخدم مسار package موثقًا |
| CLI يعيد exit code غير صفري | input غير صالح، secret مفقود، أو فشل metadata | اقرأ stderr و`run.log`، ثم صحح السبب؛ لا تعتمد على stdout وحده |
| الملفات لم تظهر بعد subprocess | العملية لم تنته، أو `cwd` خاطئ، أو `--output-dir` نسبي لمسار مختلف | انتظر `close`/exit code، استخدم مسار output مطلقًا أو اطبع المسار المحلول، وتحقق من `evidence.json` |
| bundle جزئي | captions غير متاحة أو التعليقات مغلقة | اعتبره `partial` صالحًا للمراجعة، واقرأ `caption.status` و`limitations` بدل إعادة المحاولة بلا نهاية |
| batch يعيد فيديوهات ناجحة | لا توجد state machine أو idempotency key | خزّن `video_id` وstatus ووقت الجمع، وتجاوز `complete` في التشغيل التالي |
| التطبيق يطبع السر | logging أو exception غير منقح في المشروع المضيف | أوقف التشغيل ودوّر المفتاح، ثم احذف القيمة من logs والتاريخ إن لزم، واستخدم redaction قبل استئناف العمل |
| فشل اختبار المشروع المضيف بسبب الإنترنت | الاختبار يستدعي YouTube أو Gemini مباشرة | استخدم fake client وحقن `transcript_fetcher`، واجعل live smoke يدويًا ومنفصلًا |
| GitHub Actions يرى الكود القديم | Workflow يشير إلى branch/commit مختلف أو لم يُدفع الملف | تحقق من `actions/checkout` واسم الملف والفرع، ثم افتح **Actions → workflow → View workflow file** |
| Artifact موجود لكنه فارغ | خطوة الجمع فشلت قبل الكتابة أو مسار الرفع غير صحيح | راجع `Collect evidence bundle` و`run.log`، وتأكد من `path: artifacts/evidence/` |

## قرار إعادة المحاولة

أعد المحاولة فقط عند timeout أو فشل شبكة عابر وبعد backoff محدود. لا تعِد المحاولة عند `keyInvalid` أو `accessNotConfigured` أو `quotaExceeded` أو input غير صالح قبل إصلاح الإعداد. عند فشل Gemini، احتفظ بـ `evidence.json` واعتبر `analysis` مرحلة مستقلة يمكن إعادة تشغيلها دون إعادة جمع المصدر.

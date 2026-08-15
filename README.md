# YouTube Evidence Manager

مستودع خاص لجمع أدلة بحثية من YouTube بطريقة قابلة للمراجعة. يجمع المشروع بين **YouTube Data API v3** للحصول على هوية الفيديو والقناة والبيانات الوصفية والتعليقات العامة، وبين مستخرج captions الموجود في المشروع السابق للحصول على النص الزمني المتاح للفيديو. الهدف هو تجهيز evidence brief يمكن تحليله لاحقًا بواسطة Gemini، وليس نشر المقالات تلقائيًا أو اعتبار كلام الفيديو حقيقة مستقلة.

> **الحالة الحالية:** مسار جمع الأدلة لفيديو واحد جاهز للاستخدام: يجمع metadata والتعليقات العامة وcaptions المتاحة، ويحفظ `evidence.json` و`evidence.md`. تحليل Gemini اختياري عبر `--analyze`، ولا يوجد نشر تلقائي أو تنزيل للفيديو. لا توجد مفاتيح حقيقية داخل Git.

## ماذا ستنجز؟

بعد إكمال خطوات الإعداد ستتمكن من تشغيل جامع الأدلة على فيديو YouTube عام، والحصول على ملفي `evidence.json` و`evidence.md` يحتويان على metadata رسمية، وcaptions متاحة مع بصمة SHA-256، وتعليقات عامة محدودة، وقيود الجمع. كما يمكنك تشغيل محلل Gemini اختياريًا لإنتاج `analysis.json` و`analysis.md` مع فصل الادعاءات عن التجارب وما يحتاج إلى تحقق.

لا يقوم المشروع بتنزيل الفيديو، ولا ينشر شيئًا على Blogger، ولا يتجاوز تسجيل الدخول أو CAPTCHA أو الحماية، ولا يضمن وجود captions لكل فيديو. جمع metadata والتعليقات يحتاج `YOUTUBE_API_KEY`. تحليل Gemini يحتاج `GEMINI_API_KEY` ويظل اختياريًا؛ إذا تعذر التحليل فلن يُنشئ البرنامج تقريرًا مضللًا أو citations مخترعة.

## المتطلبات

| المتطلب | الحالة | الغرض | كيف تتحقق منه؟ |
|---|---|---|---|
| Python 3.11 أو أحدث | مطلوب | تشغيل الأدوات | `python3 --version` |
| اتصال إنترنت | مطلوب للتشغيل على YouTube | جلب captions أو API | افتح فيديو YouTube في متصفحك |
| YouTube Data API v3 key | مطلوب فقط لمسار API الرسمي | البحث والmetadata والتعليقات | فحص إعداد المفتاح في `docs/configuration.md` |
| captions متاحة للفيديو | اختياري لكل فيديو | استخراج نص الفيديو | تشغيل الأداة ومراجعة حالة transcript |
| Gemini API key | اختياري للتحليل | تحليل evidence بعد الجمع | استخدم `--analyze` بعد إعداد المفتاح |
| GitHub Actions | اختياري | compile والاختبارات | تبويب Actions في GitHub |

## خريطة المشروع

| المسار | الوظيفة |
|---|---|
| `youtube_subtitles_translator.py` | أداة captions والترجمة المنقولة من المشروع السابق |
| `src/youtube_api_client.py` | عميل القراءة العامة من YouTube Data API v3 |
| `src/evidence_manager.py` | جامع evidence وتصدير JSON/Markdown |
| `src/evidence_cli.py` | واجهة سطر الأوامر لجمع evidence لفيديو واحد |
| `src/gemini_analyzer.py` | محلل Gemini اختياري بمخرجات JSON منظمة |
| `tests/` | اختبارات offline للعميل والجامع والمحلل |
| `docs/configuration.md` | خطوات الأسرار والمتغيرات والتدوير |
| `docs/integration.md` | فصل طبقات YouTube API وcaptions والتعليقات وGemini |
| `docs/operations.md` | التشغيل، artifacts، CI، وسياسة التوقف |
| `docs/troubleshooting.md` | الأخطاء الشائعة والاسترداد |
| `docs/programmatic-use.md` | استخدام الوحدات من Python، الحقن، الأخطاء، والاختبار |
| `docs/reuse-in-another-project.md` | دمج النظام في مشروع Python أو Node أو Go أو Workflow آخر |
| `.env.example` | أسماء الأسرار مع placeholders فقط |
| `.github/workflows/ci.yml` | compile واختبارات offline بلا أسرار أو quota |
| `.github/workflows/evidence.yml` | تشغيل يدوي لجمع evidence لفيديو واحد وحفظ Artifacts |
| `.github/workflows/corpus.yml` | تشغيل يدوي bounded لـ 50 مقالًا من `testdata/corpus_manifest.json` |
| `src/corpus_evidence.py` | البحث عن فيديو مرشح لكل مقال، جمع evidence، وحفظ state قابلة للاستئناف |
| `testdata/corpus_manifest.json` | mapping المقال: العنوان، القسم، subtitle، labels، واستعلام YouTube |
| `LEGACY_TRANSLATOR_README.md` | توثيق الأداة القديمة كما كان |

## خريطة الاستخدام حسب الهدف

| هدفك | ابدأ من |
|---|---|
| تشغيل أول مرة من الطرفية | [الخطوات الأولى](#الخطوة-1-تنزيل-المشروع-وإنشاء-البيئة) ثم [جمع evidence](#جمع-evidence-bundle-لفيديو-واحد) |
| ترجمة captions إلى SRT | [أداة captions والترجمة](#الخطوة-3-تشغيل-أصغر-مثال-ناجح) |
| جمع metadata وتعليقات وcaptions | [جمع evidence bundle](#جمع-evidence-bundle-لفيديو-واحد) |
| تحليل bundle عبر Gemini | [تحليل Gemini](#تحليل-gemini-اختياريًا) |
| استعمال النظام من Python | [`docs/programmatic-use.md`](docs/programmatic-use.md) |
| دمجه في مشروع آخر أو لغة أخرى | [`docs/reuse-in-another-project.md`](docs/reuse-in-another-project.md) |
| تشغيله من GitHub Actions | [التشغيل من GitHub Actions](#التشغيل-من-github-actions) |
| معرفة الأسرار والـ rotation | [`docs/configuration.md`](docs/configuration.md) |
| تشغيل batch أو خدمة طويلة | [`docs/operations.md`](docs/operations.md) و[`docs/reuse-in-another-project.md`](docs/reuse-in-another-project.md) |

## الخطوة 1: تنزيل المشروع وإنشاء البيئة

نفّذ الأوامر التالية في طرفية جديدة. الغرض هو تنزيل المستودع وإنشاء بيئة Python منفصلة حتى لا تختلط اعتمادياته بمشاريع أخرى.

```bash
git clone https://github.com/ysrg2003/youtube-evidence-manager.git
cd youtube-evidence-manager
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

النتيجة المتوقعة هي عودة الأوامر دون خطأ، وظهور `(.venv)` في بداية سطر الطرفية. إذا ظهر `No module named ...` فتأكد من تفعيل البيئة، ثم أعد أمر التثبيت. في Windows استخدم `.venv\Scripts\activate` بدل `source .venv/bin/activate`.

## الخطوة 2: إعداد YouTube API key عند الحاجة

تشغيل أداة captions وحدها لا يحتاج `YOUTUBE_API_KEY`. تحتاجه فقط عندما تستخدم `src/youtube_api_client.py` لمسار YouTube Data API الرسمي.

1. افتح [Google Cloud Console](https://console.cloud.google.com/) بالحساب الذي سيملك المشروع.
2. اختر مشروعًا موجودًا أو أنشئ مشروعًا جديدًا.
3. افتح **APIs & Services → Library**، وابحث عن **YouTube Data API v3**، ثم اضغط **Enable**.
4. افتح **APIs & Services → Credentials**، ثم **Create Credentials → API key**.
5. افتح **Edit API key** وقيّد استخدامه إلى YouTube Data API v3 قدر الإمكان.
6. في جذر المستودع نفّذ:

```bash
cp .env.example .env
```

7. افتح `.env` في محرر نصي وأضف:

```text
YOUTUBE_API_KEY=ضع_المفتاح_الحقيقي_محليًا_فقط
```

يحمّل العميل المحلي `.env` تلقائيًا عبر `python-dotenv`. لا تُنفّذ `git add .env`؛ تحقق من أن Git يتجاهله:

```bash
git status --short --ignored .env
```

يجب أن يظهر `.env` ضمن الملفات المتجاهلة، لا ضمن الملفات الجديدة أو المعدلة. تفاصيل التخزين في GitHub والتدوير والإلغاء موجودة في [configuration.md](docs/configuration.md).

## الخطوة 3: تشغيل أصغر مثال ناجح

هذا المثال يستخدم أداة captions المنقولة. استبدل `VIDEO_ID` بمعرّف فيديو عام حقيقي، مثل المعرّف الموجود بعد `v=` في رابط YouTube.

```bash
python youtube_subtitles_translator.py "https://www.youtube.com/watch?v=VIDEO_ID" --target ar --output-dir output
```

النتيجة المتوقعة:

```text
output/single_video/<title>_<VIDEO_ID>/<source_language>.srt
output/single_video/<title>_<VIDEO_ID>/arabic.srt
```

قد يختلف اسم المجلد بحسب عنوان الفيديو واللغة المتاحة. وجود ملف المصدر `.srt` يثبت أن captions استُخرجت؛ وجود `arabic.srt` يثبت أن مرحلة الترجمة انتهت، لكنه لا يثبت دقة الترجمة.

إذا ظهر `Transcripts are disabled` أو `No transcript available`، فالفيديو لا يتيح مسار captions الذي يستطيع المستخرج الوصول إليه. احفظ metadata إن كانت لديك، ولا تحاول تجاوز قرار صاحب الفيديو أو إعادة الطلب بلا نهاية.

## جمع evidence bundle لفيديو واحد

بعد إعداد `YOUTUBE_API_KEY`، شغّل هذا الأمر من جذر المستودع. استبدل `VIDEO_ID` بمعرّف فيديو عام حقيقي:

```bash
python -m src.evidence_cli "https://www.youtube.com/watch?v=VIDEO_ID" --output-dir artifacts/evidence
```

النتيجة المتوقعة هي مجلد باسم قريب من `artifacts/evidence/<title>_<VIDEO_ID>/` يحتوي على:

```text
evidence.json
evidence.md
```

يمثل `evidence.json` البيانات القابلة للمعالجة، بينما يمثل `evidence.md` نسخة سهلة للمراجعة. إذا كانت التعليقات مغلقة فستبقى metadata وcaptions محفوظة وتظهر الحالة ضمن `limitations`.

لتقليل الحصة أو تخطي التعليقات:

```bash
python -m src.evidence_cli VIDEO_ID --max-comments 20 --max-comment-pages 1 --skip-comments
```

## تحليل Gemini اختياريًا

ضع `GEMINI_API_KEY` و`GEMINI_MODEL` في `.env`، ثم شغّل الجمع والتحليل في خطوة واحدة:

```bash
cp .env.example .env
python -m src.evidence_cli VIDEO_ID --analyze
```

ينتج الأمر `analysis.json` و`analysis.md` داخل مجلد الحزمة. لا يُرسل المفتاح إلى Git، ولا يضيف البرنامج citations إذا لم يعرضها النموذج صراحة. إذا لم تكن تريد التحليل، لا تستخدم `--analyze` ولا تحتاج إلى `GEMINI_API_KEY`.

## أمثلة إضافية

### المثال الأول: معالجة فيديو باستخدام معرّف فقط

```bash
python youtube_subtitles_translator.py VIDEO_ID --target en --output-dir output
```

يُستخدم هذا عندما تعرف المعرّف دون الرابط. النتيجة المتوقعة ملف مصدر وملف `en.srt` في `output/`. إذا رفض البرنامج المعرّف، تحقق من أنه 11 محرفًا من نمط YouTube الصحيح.

### المثال الثاني: معالجة قائمة تشغيل

```bash
python youtube_subtitles_translator.py "https://www.youtube.com/playlist?list=PLAYLIST_ID" --target ar --workers 3 --chunk-size 20 --output-dir output
```

هذا يمر على عناصر القائمة ويقلل التزامن وحجم دفعة الترجمة. النتيجة المتوقعة مجلد `output/playlist_<title>/` مع مجلد لكل فيديو ناجح. إذا فشل فيديو واحد، راجع سجل ذلك الفيديو بدل اعتبار القائمة كلها فاشلة.

### المثال الثالث: اختبار API دون مفتاح أو اتصال خارجي

```bash
python -m unittest discover -s tests -v
```

هذا هو المثال الآمن للتحقق من نقطة البداية. النتيجة المتوقعة:

```text
Ran 13 tests
OK
```

إذا فشل الاختبار بسبب استيراد، أعد `python -m pip install -r requirements.txt` داخل البيئة الافتراضية. هذه الاختبارات لا تتحقق من صحة YouTube API key.

## استخدام عميل YouTube API من Python

للاستخدام البرمجي الكامل، بما في ذلك `EvidenceCollector` و`write_bundle` و`GeminiAnalyzer` وحقن transcript مخصص واختبارات الدمج، راجع [دليل الاستخدام البرمجي](docs/programmatic-use.md). ولدمج النظام في مشروع آخر، راجع [دليل إعادة الاستخدام](docs/reuse-in-another-project.md).


بعد إعداد `.env`، يمكن استدعاء العميل للقراءة العامة. هذا المثال لا يطبع المفتاح ولا يكتب نتيجة في Git:

```bash
python - <<'PY'
from src.youtube_api_client import YouTubeDataClient

client = YouTubeDataClient()
result = client.search_videos("AI-assisted building", max_results=3)
print({"items": len(result.get("items", [])), "has_next_page": bool(result.get("nextPageToken"))})
PY
```

النتيجة المتوقعة كائن مختصر مثل:

```text
{'items': 3, 'has_next_page': True}
```

إذا ظهر `YOUTUBE_API_KEY is not configured`، تحقق من وجود `.env` في جذر المستودع ومن اسم المتغير حرفيًا. إذا ظهر `keyInvalid` أو `accessNotConfigured`، راجع تفعيل API والمشروع الذي أنشأت فيه المفتاح.

## التشغيل من GitHub Actions

يمكن تشغيل النظام من GitHub دون فتح طرفية محلية. افتح **Actions → Collect YouTube evidence → Run workflow**، ثم أدخل رابط الفيديو أو معرّفه، وحدد حد التعليقات والصفحات، واختر `analyze` فقط إذا كان `GEMINI_API_KEY` محفوظًا في Secrets. يحتاج الـ Workflow إلى Secret باسم `YOUTUBE_API_KEY`، بينما `GEMINI_API_KEY` اختياري. بعد انتهاء التشغيل، نزّل artifact باسم قريب من `youtube-evidence-<run_id>` وستجد `evidence.json` و`evidence.md`، ومع التحليل `analysis.json` و`analysis.md`.

> لا يرفع الـ Workflow أي فيديو أو ينشر إلى Blogger. وهو يدوي عمدًا حتى لا تُستهلك حصة YouTube دون قرار واضح.

## تشغيل corpus المقالات الخمسين

يعمل corpus workflow يدويًا فقط من **Actions → Collect corpus YouTube evidence → Run workflow**. يقرأ `testdata/corpus_manifest.json`، يبحث عن عدد محدود من النتائج لكل مقال، يختار المرشح الأعلى تطابقًا من العنوان والوصف، ثم يجمع metadata وcaptions وتعليقات عامة محدودة. لا يشغّل Reddit، ولا ينشر المقالات، ولا يكتب فوق ملفات المقالات.

لأول تشغيل آمن، استخدم `max_articles=1` أو `5`، و`search_results=5`، و`max_comments=10`، و`max_comment_pages=1`، واجعل `analyze=false`. بعد فحص artifact، يمكن تشغيل دفعة أكبر. البحث يستهلك حصة YouTube لكل مقال، لذلك لا تستخدم `--no-resume` أو تعيد تشغيل corpus بلا سبب.

الـ artifact يحتوي عادةً على `corpus_results.json` و`corpus_results.md`، وداخل كل `article_XXX/` ملفي `evidence.json` و`evidence.md`. إذا فعّلت `analyze=true` سيحاول Gemini تحليل bundle بعد حفظه؛ فشل Gemini لا يمحو evidence، ويظهر كـ `analysis_status=failed` في state.

> هذه النتائج **تستكمل الأدلة ولا تعدّل المقالات أو تنشرها تلقائيًا**. كل caption أو كلام متحدث أو تعليق يبقى مصنفًا حسب مصدره ويحتاج مراجعة تحريرية قبل إدخاله في المقال النهائي.

## كيف تعمل الأدلة الآن؟

المسار العملي هو: يتحقق البرنامج من `video_id`، ثم يستدعي `videos.list` للبيانات الوصفية، ومستخرج captions للنص الزمني، و`commentThreads.list` للتعليقات العامة ضمن حد صفحات وعدد محدد. بعدها ينشئ evidence bundle مع labels وlimitations وبصمة للنص. عند طلب `--analyze` فقط، يرسل bundle إلى Gemini لإخراج منظم؛ يبقى caption نصًا مصدره، وكلام المتحدث ادعاءً من الناشر، والتعليقات تجارب مستخدمين غير موثقة. لا يُرسل أي مقال إلى Blogger تلقائيًا.

## الأسرار والتنظيف

لا تحفظ API keys أو captions أو التعليقات أو تقارير البحث في Git. الملفات التالية متجاهلة تلقائيًا: `.env`, `output/`, `artifacts/`, `reports/`, ملفات `.srt` و`.jsonl`. إذا ظهر مفتاح في commit أو سجل، ألغِه فورًا من Google Cloud، أنشئ مفتاحًا بديلًا، حدّث GitHub Secret، ثم افحص سجل Git قبل مواصلة العمل.

## التحقق النهائي

نفّذ الأوامر التالية قبل فتح Pull Request:

```bash
python3 -m py_compile youtube_subtitles_translator.py src/youtube_api_client.py src/evidence_manager.py src/gemini_analyzer.py src/evidence_cli.py
python -m unittest discover -s tests -v
python -m src.evidence_cli --help
git diff --check
git status --short
```

النجاح يعني عدم وجود أخطاء compile، وظهور `OK`، وعدم وجود أخطاء whitespace، وعدم وجود `.env` أو مخرجات شخصية ضمن الملفات المعدلة. Workflow `CI` في GitHub ينفذ compile والاختبارات offline تلقائيًا عند push أو Pull Request، ولا يستخدم YouTube quota.

## المراجع الرسمية

[1]: https://developers.google.com/youtube/v3/docs/search/list "YouTube Data API search.list"
[2]: https://developers.google.com/youtube/v3/docs/videos/list "YouTube Data API videos.list"
[3]: https://developers.google.com/youtube/v3/docs/commentThreads/list "YouTube Data API commentThreads.list"
[4]: https://developers.google.com/youtube/v3/docs/captions/list "YouTube Data API captions.list"
[5]: https://developers.google.com/youtube/v3/docs/captions/download "YouTube Data API captions.download"

توضح الوثائق الرسمية أن `search.list` و`videos.list` و`commentThreads.list` تخدم البيانات العامة، بينما `captions.list` يعيد بيانات مسارات captions لا النص نفسه، و`captions.download` يتطلب صلاحية تعديل الفيديو [1] [2] [3] [4] [5].

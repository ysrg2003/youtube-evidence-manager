# YouTube Evidence Manager

مستودع خاص لجمع أدلة بحثية من YouTube بطريقة قابلة للمراجعة. يجمع المشروع بين **YouTube Data API v3** للحصول على هوية الفيديو والقناة والبيانات الوصفية والتعليقات العامة، وبين مستخرج captions الموجود في المشروع السابق للحصول على النص الزمني المتاح للفيديو. الهدف هو تجهيز evidence brief يمكن تحليله لاحقًا بواسطة Gemini، وليس نشر المقالات تلقائيًا أو اعتبار كلام الفيديو حقيقة مستقلة.

> **الحالة الحالية:** هذا المستودع هو أساس المشروع. عميل YouTube Data API وطبقة captions موجودان، لكن probe الجماعي وموصل Gemini لم يكتملَا بعد. لا توجد مفاتيح حقيقية داخل Git.

## ماذا ستنجز؟

بعد إكمال خطوات الإعداد ستتمكن من تثبيت المشروع وتشغيل أداة captions على فيديو YouTube عام، والحصول على ملف SRT أصلي ونسخة مترجمة للمراجعة. كما يمكنك تشغيل الاختبارات المحلية والتحقق من عميل YouTube API دون أي اتصال خارجي. جمع metadata والتعليقات وتحويل كل ذلك إلى evidence bundle هو المرحلة التالية، وليس جزءًا من التشغيل الأول الحالي.

لا يقوم المشروع حاليًا بتنزيل الفيديو، ولا ينشر شيئًا على Blogger، ولا يتجاوز تسجيل الدخول أو CAPTCHA أو الحماية، ولا يضمن وجود captions لكل فيديو. كما أن Gemini غير مفعّل في هذه النسخة؛ وجود `GEMINI_API_KEY` في `.env.example` موضع توثيق لتكامل لاحق فقط.

## المتطلبات

| المتطلب | الحالة | الغرض | كيف تتحقق منه؟ |
|---|---|---|---|
| Python 3.11 أو أحدث | مطلوب | تشغيل الأدوات | `python3 --version` |
| اتصال إنترنت | مطلوب للتشغيل على YouTube | جلب captions أو API | افتح فيديو YouTube في متصفحك |
| YouTube Data API v3 key | مطلوب فقط لمسار API الرسمي | البحث والmetadata والتعليقات | فحص إعداد المفتاح في `docs/configuration.md` |
| captions متاحة للفيديو | اختياري لكل فيديو | استخراج نص الفيديو | تشغيل الأداة ومراجعة حالة transcript |
| Gemini API key | غير مطلوب حاليًا | تحليل evidence لاحقًا | لا تضعه قبل تفعيل الموصل |
| GitHub Actions | اختياري | compile والاختبارات | تبويب Actions في GitHub |

## خريطة المشروع

| المسار | الوظيفة |
|---|---|
| `youtube_subtitles_translator.py` | أداة captions والترجمة المنقولة من المشروع السابق |
| `src/youtube_api_client.py` | عميل أولي لعمليات القراءة العامة من YouTube Data API v3 |
| `tests/test_youtube_api_client.py` | خمسة اختبارات offline للعميل الرسمي |
| `docs/configuration.md` | خطوات الأسرار والمتغيرات والتدوير |
| `docs/integration.md` | فصل طبقات YouTube API وcaptions والتعليقات وGemini |
| `docs/operations.md` | التشغيل، artifacts، CI، وسياسة التوقف |
| `docs/troubleshooting.md` | الأخطاء الشائعة والاسترداد |
| `.env.example` | أسماء الأسرار مع placeholders فقط |
| `.github/workflows/ci.yml` | compile واختبارات offline بلا أسرار أو quota |
| `LEGACY_TRANSLATOR_README.md` | توثيق الأداة القديمة كما كان |

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
Ran 5 tests
OK
```

إذا فشل الاختبار بسبب استيراد، أعد `python -m pip install -r requirements.txt` داخل البيئة الافتراضية. هذه الاختبارات لا تتحقق من صحة YouTube API key.

## استخدام عميل YouTube API من Python

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

## كيف ستعمل الأدلة لاحقًا؟

المسار المقصود هو: `search.list` لاكتشاف الفيديوهات، ثم `videos.list` للبيانات الوصفية، ثم مستخرج captions للنص الزمني، ثم `commentThreads.list` للتعليقات العامة، وأخيرًا Gemini لتحليل evidence bundle. سيبقى caption مصنفًا كنص مصدر، وكلام المتحدث ادعاءً من الناشر، والتعليقات تجارب مستخدمين غير موثقة. لا يُرسل أي مقال إلى Blogger تلقائيًا.

## الأسرار والتنظيف

لا تحفظ API keys أو captions أو التعليقات أو تقارير البحث في Git. الملفات التالية متجاهلة تلقائيًا: `.env`, `output/`, `artifacts/`, `reports/`, ملفات `.srt` و`.jsonl`. إذا ظهر مفتاح في commit أو سجل، ألغِه فورًا من Google Cloud، أنشئ مفتاحًا بديلًا، حدّث GitHub Secret، ثم افحص سجل Git قبل مواصلة العمل.

## التحقق النهائي

نفّذ الأوامر التالية قبل فتح Pull Request:

```bash
python3 -m py_compile youtube_subtitles_translator.py src/youtube_api_client.py
python -m unittest discover -s tests -v
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

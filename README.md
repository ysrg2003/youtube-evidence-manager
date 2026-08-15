# YouTube Evidence Manager

مستودع خاص لجمع أدلة بحثية من YouTube بطريقة قابلة للمراجعة. يجمع المشروع بين **YouTube Data API v3** للحصول على هوية الفيديو والقناة والبيانات الوصفية والتعليقات العامة، وبين مستخرج captions الموجود في المشروع السابق للحصول على النص الزمني المتاح للفيديو. الهدف هو تجهيز evidence brief يمكن تحليله لاحقًا بواسطة Gemini، وليس نشر المقالات تلقائيًا أو اعتبار كلام الفيديو حقيقة مستقلة.

> **الحالة الحالية:** المستودع بدأ من أداة `YouTube-subtitles-translator-`. تم نقل مستخرج captions كنقطة بداية، بينما ما زال عميل YouTube API ومسار Gemini في مرحلة التهيئة. لا توجد مفاتيح حقيقية داخل Git.

## ماذا يحقق هذا المستودع؟

عند اكتمال المسار، سيستطيع المستخدم إعطاء استعلام أو رابط فيديو، ثم الحصول على ملف JSON وملف Markdown يحتويان على عنوان الفيديو، القناة، تاريخ النشر، المدة، الإحصائيات، captions المتاحة، والتعليقات العامة المحدودة. ستظل كل مادة مصنفة حسب نوعها: **ادعاء من الناشر، نص caption، أو تجربة مستخدم في تعليق**.

لا يقوم المشروع حاليًا بتنزيل الفيديو، ولا ينشر شيئًا على Blogger، ولا يتجاوز تسجيل الدخول أو الحماية، ولا يضمن وجود captions لكل فيديو. كما أن Gemini ليس مفعّلًا في هذه النسخة الأولى؛ وجود `GEMINI_API_KEY` في `.env.example` مجرد مكان موثق لتكامل لاحق، وليس تصريحًا بوضع مفتاح فعلي في الملف.

## المتطلبات

| المتطلب | الحالة | الغرض |
|---|---|---|
| Python 3.11 أو أحدث | مطلوب | تشغيل الأدوات |
| YouTube Data API v3 key | مطلوب لمسار metadata والبحث والتعليقات | استدعاءات YouTube الرسمية |
| captions متاحة للفيديو | اختياري لكل فيديو | استخراج نص الفيديو |
| Gemini API key | اختياري حاليًا | تحليل evidence brief في مرحلة لاحقة |
| GitHub Actions | اختياري | تشغيل probes دون حفظ الأسرار محليًا |

## التثبيت المحلي

نفّذ الأوامر التالية من مجلد المستودع الذي يحتوي على هذا الملف:

```bash
git clone https://github.com/ysrg2003/youtube-evidence-manager.git
cd youtube-evidence-manager
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

إذا ظهر خطأ `No module named ...` فتأكد أن البيئة الافتراضية مفعلة؛ يجب أن يظهر `(.venv)` في بداية سطر الطرفية، ثم أعد أمر تثبيت المتطلبات.

## إعداد الأسرار

انسخ ملف المثال إلى ملف محلي لا يدخل Git:

```bash
cp .env.example .env
```

بعد ذلك أضف قيمة `YOUTUBE_API_KEY` في `.env` فقط. لا تضع قيمة حقيقية في `.env.example` أو في أي ملف Python أو في commit. عند استخدام GitHub Actions، خزّن المفتاح في **Settings → Secrets and variables → Actions → New repository secret** باسم `YOUTUBE_API_KEY`.

للحصول على مفتاح YouTube Data API، استخدم [Google Cloud Console](https://console.cloud.google.com/)، أنشئ أو اختر مشروعًا، فعّل YouTube Data API v3، ثم أنشئ API key. يجب تقييد المفتاح حسب الحاجة ومراجعته دوريًا. لا نطلب OAuth في المسار العام الحالي لأن البحث والبيانات العامة تستعمل API key؛ captions.download للفيديوهات المملوكة يتطلب صلاحيات مختلفة وليس جزءًا من نقطة البداية هذه.

## نقطة البداية الحالية

الأداة المنقولة من المشروع السابق موجودة في:

```text
youtube_subtitles_translator.py
```

تشغيلها على فيديو واحد يحفظ captions الأصلي وملف الترجمة في مجلد `output/`:

```bash
python youtube_subtitles_translator.py "https://www.youtube.com/watch?v=VIDEO_ID" --target ar --output-dir output
```

استبدل `VIDEO_ID` بمعرّف فيديو حقيقي. نجاح التشغيل يعني ظهور ملف `.srt` أصلي وملف ترجمة في `output/`. إذا ظهر `Transcripts are disabled` أو `No transcript available` فهذا يعني أن الفيديو لا يتيح مسار captions الذي يستطيع المستخرج الوصول إليه؛ لا ينبغي تحويله إلى فشل في YouTube API أو إعادة المحاولة بلا نهاية.

## البنية الحالية

| المسار | الوظيفة |
|---|---|
| `youtube_subtitles_translator.py` | نقطة بداية مستخرجة من أداة captions السابقة |
| `LEGACY_TRANSLATOR_README.md` | توثيق الأداة السابقة كما كان |
| `src/` | مكان عميل YouTube API ومحوّل evidence الذي سيضاف في المرحلة التالية |
| `tests/` | الاختبارات التي لا تحتاج اتصالًا خارجيًا |
| `docs/` | خرائط الإعداد والتكامل والتشغيل |
| `.env.example` | أسماء الأسرار فقط، بلا قيم حقيقية |
| `.gitignore` | يمنع البيئة والمخرجات وملفات الأسرار من الدخول إلى Git |

## سياسة الأدلة

وجود caption أو تعليق لا يعني أن الادعاء صحيح. يجب أن يسجل التقرير الرابط، وقت الجمع، نوع المصدر، اللغة، وهل النص تلقائي أم يدوي إذا أمكن معرفته، وأن يفصل بين كلام المتحدث وتجربة المعلق والحقائق التي تحتاج إلى مصدر مستقل. لا يُرسل المحتوى إلى مقال نهائي قبل المراجعة التحريرية، ولا يملك هذا المستودع أي صلاحية نشر تلقائي.

## الاختبار

نفّذ الاختبارات المحلية من جذر المستودع:

```bash
python -m unittest discover -s tests -v
```

النجاح المتوقع هو `OK` مع عدد الاختبارات الموجود في المستودع. الاختبارات لا تتحقق من صلاحية مفاتيح YouTube أو Gemini؛ تلك الخطوة تحتاج probe خارجيًا موثقًا ولا ينبغي تشغيلها تلقائيًا من دون طلب واضح.

## التوثيق التفصيلي

- [خريطة الإعدادات والأسرار](docs/configuration.md)
- [تصميم التكامل مع YouTube وcaptions وGemini](docs/integration.md)
- [التشغيل والـ artifacts](docs/operations.md)
- [التشخيص واسترداد الأخطاء](docs/troubleshooting.md)

## المراجع الرسمية

[1]: https://developers.google.com/youtube/v3/docs/search/list "YouTube Data API search.list"
[2]: https://developers.google.com/youtube/v3/docs/videos/list "YouTube Data API videos.list"
[3]: https://developers.google.com/youtube/v3/docs/commentThreads/list "YouTube Data API commentThreads.list"
[4]: https://developers.google.com/youtube/v3/docs/captions/list "YouTube Data API captions.list"
[5]: https://developers.google.com/youtube/v3/docs/captions/download "YouTube Data API captions.download"

توضح الوثائق الرسمية أن `search.list` و`videos.list` و`commentThreads.list` تخدم البيانات العامة، بينما `captions.list` يعيد بيانات مسارات captions لا النص نفسه، و`captions.download` يتطلب صلاحية تعديل الفيديو [1] [2] [3] [4] [5].

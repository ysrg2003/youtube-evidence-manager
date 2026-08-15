# الاستخدام البرمجي

هذا الدليل يشرح استخدام `youtube-evidence-manager` كمكتبة Python داخل برنامج آخر، بدل تشغيله من سطر الأوامر فقط. يفترض الدليل أن البرنامج المستضيف يريد جمع evidence لفيديو YouTube عام، أو يريد استعمال طبقة واحدة من النظام مثل عميل YouTube أو جامع الأدلة أو محلل Gemini.

> **الفكرة الأساسية:** استعمل `EvidenceCollector` عندما تحتاج جمع metadata وcaptions وتعليقات، واستعمل `write_bundle` عندما تريد حفظ النتيجة، واستعمل `GeminiAnalyzer` فقط إذا أردت تحليلًا اختياريًا بعد نجاح الجمع. لا ينفذ أي من هذه المكونات نشرًا أو تنزيلًا للفيديو.

## 1. ما الذي سيحصل عليه البرنامج المستضيف؟

بعد استدعاء `EvidenceCollector.collect` يحصل البرنامج على قاموس Python يحتوي على `schema_version` و`source_url` و`video_id` و`metadata` و`caption` و`comments` و`evidence_labels` و`limitations` و`collected_at`. وعند استدعاء `write_bundle` تُحفظ نسختان من نفس النتيجة: `evidence.json` للمعالجة الآلية و`evidence.md` للمراجعة البشرية.

| طبقة الاستخدام | نقطة الدخول | متى تستخدمها؟ | الناتج |
|---|---|---|---|
| عميل API منخفض المستوى | `YouTubeDataClient` | عندما تحتاج استدعاء `search` أو `videos` أو `comment_threads` بشكل مستقل | قاموس API خام منقح من المفتاح |
| جامع evidence | `EvidenceCollector.collect` | عندما تريد المسار الكامل لفيديو واحد | evidence bundle في الذاكرة |
| حفظ النتائج | `write_bundle` | عندما تريد JSON وMarkdown في مجلد محدد | مسارا الملفين |
| مسار مختصر | `collect_and_write` | عندما تريد الجمع والحفظ باستدعاء واحد | `(bundle, (json_path, markdown_path))` |
| تحليل AI | `GeminiAnalyzer.analyze` | بعد الجمع وعند وجود `GEMINI_API_KEY` | تحليل JSON منظم |
| حفظ تحليل AI | `write_analysis` | عندما تريد ملفات التحليل | `analysis.json` و`analysis.md` |

## 2. تثبيت المكتبة من المستودع

نفذ الخطوات التالية من طرفية المشروع المستضيف. لا تثبت الحزم في Python النظام؛ أنشئ بيئة افتراضية خاصة بالمشروع المستضيف حتى لا تتعارض إصدارات YouTube أو Gemini مع تطبيقات أخرى.

### Linux وmacOS

```bash
mkdir my-research-app
cd my-research-app
git clone https://github.com/ysrg2003/youtube-evidence-manager.git vendor/youtube-evidence-manager
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r vendor/youtube-evidence-manager/requirements.txt
```

النتيجة المتوقعة هي ظهور `(.venv)` ونجاح تثبيت `requests` و`python-dotenv` و`youtube-transcript-api` و`yt-dlp` و`deep-translator`. إذا كان التطبيق المستضيف يستخدم `requirements.txt` خاصًا به، انسخ سطر الاعتماديات أو استخدم مسار المستودع ضمن خطوة تثبيت واحدة، ولا تفترض أن `PYTHONPATH` مضبوط تلقائيًا.

### Windows PowerShell

```powershell
New-Item -ItemType Directory my-research-app
Set-Location my-research-app
git clone https://github.com/ysrg2003/youtube-evidence-manager.git vendor/youtube-evidence-manager
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r vendor/youtube-evidence-manager/requirements.txt
```

إذا منع PowerShell تفعيل البيئة، نفذ سياسة التفعيل في جلسة المستخدم وفق سياسة جهازك، أو شغّل Python مباشرة من `.venv\Scripts\python.exe` بدل تعطيل حماية النظام على نطاق واسع.

## 3. إعداد الأسرار في التطبيق المستضيف

ضع الأسرار في مدير أسرار التطبيق المستضيف أو في `.env` محلي غير متتبع. لا تمرر المفتاح كسلسلة ثابتة داخل source code، ولا تضفه إلى URL محفوظ، ولا تطبعه في logs.

```text
YOUTUBE_API_KEY=REPLACE_WITH_YOUTUBE_API_KEY
GEMINI_API_KEY=REPLACE_WITH_GEMINI_API_KEY
GEMINI_MODEL=gemini-2.5-flash
```

`YOUTUBE_API_KEY` مطلوب لمسار metadata والتعليقات؛ أما `GEMINI_API_KEY` فاختياري ولا يقرأه النظام إلا عند تشغيل التحليل. يحمّل `python-dotenv` ملف `.env` من working directory وفق سلوك المكتبة، لذلك يجب تشغيل التطبيق من مكان موثق أو استدعاء `load_dotenv` في نقطة دخول التطبيق قبل إنشاء العميل.

## 4. أصغر استخدام برمجي ناجح

أنشئ الملف `app.py` في جذر المشروع المستضيف:

```python
from pathlib import Path

# Run this file with PYTHONPATH=vendor/youtube-evidence-manager.
from src.evidence_manager import EvidenceCollectionError, EvidenceCollector, write_bundle
from src.youtube_api_client import YouTubeDataClient


VIDEO_ID = "dQw4w9WgXcQ"


def main() -> None:
    collector = EvidenceCollector(YouTubeDataClient())
    try:
        bundle = collector.collect(
            VIDEO_ID,
            max_comments=20,
            max_comment_pages=1,
            include_comments=True,
        )
    except EvidenceCollectionError as exc:
        raise SystemExit(f"Evidence collection failed: {exc}") from exc

    json_path, markdown_path = write_bundle(bundle, Path("artifacts/evidence"))
    print({"json": str(json_path), "markdown": str(markdown_path)})


if __name__ == "__main__":
    main()
```

شغّل:

```bash
PYTHONPATH=vendor/youtube-evidence-manager python app.py
```

في Windows PowerShell:

```powershell
$env:PYTHONPATH="vendor\youtube-evidence-manager"
python app.py
```

النتيجة المتوقعة هي مساران داخل `artifacts/evidence/<title>_<VIDEO_ID>/`. إذا ظهر `YOUTUBE_API_KEY is not configured` فالمشكلة في إعداد السر، لا في `EvidenceCollector`; افحص اسم المتغير ومكان `.env` ثم أعد التشغيل.

## 5. استخدام المسار المختصر `collect_and_write`

عندما لا تحتاج تخصيص عميل API أو transcript fetcher، استخدم الدالة المختصرة:

```python
from pathlib import Path

from src.evidence_manager import collect_and_write

bundle, (json_path, markdown_path) = collect_and_write(
    "dQw4w9WgXcQ",
    Path("artifacts/evidence"),
    max_comments=10,
    max_comment_pages=1,
    include_comments=False,
)
print(bundle["caption"]["status"])
print(json_path, markdown_path)
```

هذا المسار مناسب لمهمة batch صغيرة أو command داخل تطبيق إداري. عند `include_comments=False` تُحفظ metadata وcaptions وتظهر limitation توضح أن التعليقات تخطيت عمدًا.

## 6. استخدام كل طبقة على حدة

### البحث عن فيديوهات

```python
from src.youtube_api_client import YouTubeDataClient

client = YouTubeDataClient()
page = client.search_videos("AI-assisted building", max_results=3)
for item in page.get("items", []):
    snippet = item.get("snippet", {})
    print(item.get("id", {}).get("videoId"), snippet.get("title"))
```

`search_videos` يعيد صفحة API خامًا ويضع `nextPageToken` إن وُجد. لا تستخدم search في حلقة بلا حد؛ حدد عدد الصفحات واحترم الحصة.

### جلب metadata لعدة فيديوهات

```python
metadata = client.videos(["dQw4w9WgXcQ", "VIDEO_ID_2"])
for item in metadata.get("items", []):
    print(item.get("id"), item.get("snippet", {}).get("title"))
```

تقبل واجهة `videos` حتى 50 معرّفًا في الطلب الواحد. إذا كانت لديك قائمة أكبر فقسّمها إلى دفعات، واحفظ نتيجة كل دفعة قبل الانتقال إلى التالية.

### جلب التعليقات

```python
comments_page = client.comment_threads(
    "dQw4w9WgXcQ",
    max_results=20,
    order="relevance",
)
```

التعليقات raw API وليست evidence bundle. عند الحاجة إلى labels وreplies وتسجيل القيود، استخدم `EvidenceCollector` بدل إعادة بناء منطق التعليقات في التطبيق المستضيف.

## 7. حقن transcript fetcher مخصص

يدعم `EvidenceCollector` حقن دالة بديلة بتوقيع `fetcher(video_id) -> (segments, language)`. كل segment يجب أن يكون قاموسًا يحوي `text`، ويمكنه أن يحوي `start` و`duration`:

```python
from src.evidence_manager import EvidenceCollector


def fetch_from_internal_cache(video_id: str):
    cached = load_segments_from_your_database(video_id)
    return cached, "en"


collector = EvidenceCollector(
    api_client=your_api_client,
    transcript_fetcher=fetch_from_internal_cache,
)
bundle = collector.collect("dQw4w9WgXcQ", include_comments=False)
```

استخدم هذا الامتداد عندما يملك التطبيق المستضيف مصدر captions مصرحًا به أو cache داخليًا. لا تستخدمه لتجاوز تعطيل captions أو قيود YouTube، وسجل في تطبيقك مصدر النص وحالته بوضوح.

## 8. معالجة الأخطاء والـ fallback

ينبغي أن يميز التطبيق المستضيف بين فشل metadata وفشل captions وفشل التعليقات. فشل captions لا يمنع حفظ metadata؛ يسجل النظام `caption.status` كـ `missing` أو `error` ويضيف السبب إلى `limitations`. أما فشل metadata فيرفع `EvidenceCollectionError` لأن bundle بلا هوية فيديو موثوقة لا يحقق الغرض الأساسي.

```python
from src.evidence_manager import EvidenceCollectionError, EvidenceCollector
from src.youtube_api_client import YouTubeAPIError, YouTubeDataClient


try:
    bundle = EvidenceCollector(YouTubeDataClient()).collect(
        "dQw4w9WgXcQ",
        max_comments=5,
        max_comment_pages=1,
    )
except EvidenceCollectionError as exc:
    log_error("metadata_or_collection_failure", str(exc))
    bundle = None

if bundle is not None and bundle["caption"]["status"] != "available":
    log_warning("caption_unavailable", bundle["limitations"])
```

لا تعِد طلب `quotaExceeded` أو `commentsDisabled` بلا تغيير. عند `commentsDisabled` احتفظ بالmetadata والcaption وانتقل، وعند `quotaExceeded` أوقف batch كله واحفظ الحالة حتى لا تضاعف الاستهلاك.

## 9. تشغيل Gemini برمجيًا بعد الجمع

```python
from pathlib import Path

from src.evidence_manager import EvidenceCollector, write_bundle
from src.gemini_analyzer import GeminiAnalyzer, write_analysis
from src.youtube_api_client import YouTubeDataClient


collector = EvidenceCollector(YouTubeDataClient())
bundle = collector.collect("dQw4w9WgXcQ", max_comments=5, max_comment_pages=1)
_, markdown_path = write_bundle(bundle, Path("artifacts/evidence"))
analysis = GeminiAnalyzer().analyze(bundle)
analysis_json, analysis_markdown = write_analysis(analysis, markdown_path.parent)
print(analysis_json, analysis_markdown)
```

لا تشغّل `GeminiAnalyzer` قبل نجاح الجمع. إذا كان `GEMINI_API_KEY` مفقودًا فسيظهر `GeminiAPIError` واضح. وإذا عاد النموذج بنص غير JSON، يرفضه النظام بدل كتابة تحليل غير قابل للاعتماد.

## 10. دمج النظام داخل خدمة أو API

في خدمة ويب أو worker، اجعل جمع evidence مهمة خارج request التفاعلي الطويل عندما يسمح تصميم التطبيق بذلك. خزّن `video_id` و`status` و`started_at` و`finished_at` وpaths الناتجة، ثم أعد النتيجة للمستخدم من قاعدة البيانات أو object storage. لا تضع captions أو التعليقات الكاملة في log؛ ضع counts وhash وسبب الفشل فقط.

نمط حالة مبسط:

| الحالة | الإجراء |
|---|---|
| `queued` | حفظ طلب المستخدم دون استدعاء API |
| `collecting` | تنفيذ `EvidenceCollector.collect` مع timeout خارجي |
| `partial` | metadata موجودة لكن captions أو التعليقات ناقصة؛ حفظ limitation |
| `complete` | حفظ JSON وMarkdown والتحقق من وجودهما |
| `analyzing` | تشغيل `GeminiAnalyzer` اختياريًا بعد complete |
| `analyzed` | حفظ `analysis.json` و`analysis.md` |
| `failed` | حفظ رسالة منقحة وسبب قابل للاسترداد دون السر |

## 11. اختبار الدمج دون YouTube أو Gemini

استخدم test doubles بدل استهلاك quota في اختبارات التطبيق المستضيف. يمكن تقليد `videos()` و`comment_threads()` وحقن `transcript_fetcher` كما تفعل اختبارات المستودع:

```python
from src.evidence_manager import EvidenceCollector


class FakeClient:
    def videos(self, video_ids):
        return {"items": [{"id": video_ids[0], "snippet": {"title": "Fixture"}}]}

    def comment_threads(self, video_id, *, max_results=20, page_token=None, order="relevance"):
        return {"items": [], "nextPageToken": None}


collector = EvidenceCollector(
    FakeClient(),
    transcript_fetcher=lambda _: ([{"start": 0, "duration": 1, "text": "Fixture text"}], "en"),
)
bundle = collector.collect("dQw4w9WgXcQ", include_comments=False)
assert bundle["caption"]["status"] == "available"
```

في CI الخاص بالتطبيق المستضيف شغّل هذه الاختبارات offline. اجعل اختبار YouTube الحي يدويًا ومحدودًا بفيديو واحد، ولا تجعله شرطًا لكل Pull Request.

## 12. تثبيت نسخة وإدارة التحديثات

عند اعتماد المكتبة داخل مشروع إنتاجي، لا تعتمد على `main` بلا مراجعة. ثبّت commit أو tag معروفًا، راجع تغييرات `requirements.txt`، وشغّل الاختبارات قبل تحديث النسخة. إذا استخدمت المستودع كـ vendor، حدّثه في commit منفصل واحتفظ بسجل النسخة المستخدمة.

## 13. حدود الدمج

هذا المستودع ليس حزمة PyPI مستقلة ولا يعلن API دلاليًا ثابتًا خارج الوحدات المذكورة في هذا الدليل. لا تعتمد على الدوال الداخلية التي تبدأ بشرطة سفلية، ولا على `_title_for_filename` لأنها حقل داخلي يُزال قبل الحفظ. لا تخلط بين captions الأصلية ونسخة الترجمة العربية: الترجمة أداة مراجعة، وليست المصدر الأساسي.

## المراجع

[1]: https://developers.google.com/youtube/v3/docs/videos/list "YouTube Data API videos.list"
[2]: https://developers.google.com/youtube/v3/docs/commentThreads/list "YouTube Data API commentThreads.list"
[3]: https://developers.google.com/youtube/v3/determine_quota_cost "YouTube Data API quota costs"
[4]: https://github.com/yt-dlp/yt-dlp "yt-dlp project"

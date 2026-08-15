# إعادة استخدام النظام داخل مشروع آخر

هذا الدليل موجه إلى مطور يريد أخذ `youtube-evidence-manager` وإدخاله في مشروع بحثي أو خدمة أو worker أو pipeline موجودة مسبقًا. يشرح ثلاث طرق دمج، ثم يقدم مسارًا كاملًا من إنشاء المشروع إلى التشغيل والاختبار والنشر الآمن.

## 1. اختر طريقة الدمج قبل نسخ الكود

| الطريقة | متى تناسبك؟ | ما الذي تحصل عليه؟ | ما الذي تديره بنفسك؟ |
|---|---|---|---|
| استدعاء CLI كعملية فرعية | مشروع بأي لغة مثل Node.js أو Go أو Java | evidence files جاهزة من أمر واحد | تثبيت Python، قراءة exit code، ومسار output |
| استيراد وحدات Python | مشروع Python يحتاج التحكم في البيانات | bundle في الذاكرة وتحكم في transcript والـ limits | البيئة الافتراضية، exceptions، والتخزين |
| نسخ Workflow إلى مشروع آخر | تريد تشغيلًا يدويًا من GitHub Actions | job جاهز مع inputs وSecrets وArtifact | إضافة الملف، ضبط Secrets، ومراجعة quota |

لا تبدأ بنسخ ملفات عشوائيًا. حدد أولًا هل التطبيق المستضيف يحتاج JSON فقط، أم يحتاج تحليل Gemini، أم يحتاج مراجعة Markdown، أم يريد تشغيلًا مؤجلًا عبر Actions.

## 2. المسار الكامل: مشروع Python جديد

### الخطوة 1: إنشاء مشروع مضيف

نفذ من طرفية جديدة:

```bash
mkdir my-evidence-app
cd my-evidence-app
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
```

في Windows PowerShell:

```powershell
New-Item -ItemType Directory my-evidence-app
Set-Location my-evidence-app
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

النتيجة المتوقعة هي بيئة فعالة يظهر اسمها في prompt. إذا كان `python3` أقدم من 3.11، ثبّت Python حديثًا أو استخدم مسار interpreter صريحًا.

### الخطوة 2: إضافة النظام كمكوّن vendor

```bash
git init
git submodule add https://github.com/ysrg2003/youtube-evidence-manager.git vendor/youtube-evidence-manager
python -m pip install -r vendor/youtube-evidence-manager/requirements.txt
```

استخدم submodule عندما تريد تحديثًا صريحًا ومراجَعًا. إذا كان فريقك لا يستخدم submodules، استعمل `git clone` داخل `vendor/` وثبّت commit معروفًا، أو انسخ الوحدات إلى package داخلي بعد مراجعة الترخيص وسياسة المؤسسة.

تحقق من وجود الملفات:

```bash
find vendor/youtube-evidence-manager/src -maxdepth 1 -type f -print
```

يجب أن ترى `evidence_manager.py` و`evidence_cli.py` و`gemini_analyzer.py` و`youtube_api_client.py`.

### الخطوة 3: إعداد secrets خارج Git

أنشئ `.env` محليًا أو استخدم secret manager الخاص بتطبيقك:

```text
YOUTUBE_API_KEY=REPLACE_WITH_YOUTUBE_API_KEY
GEMINI_API_KEY=REPLACE_WITH_GEMINI_API_KEY
GEMINI_MODEL=gemini-2.5-flash
```

أضف إلى `.gitignore`:

```text
.env
artifacts/
output/
```

لا تضع المفاتيح في ملف إعدادات committed، ولا تمررها كـ command-line argument، لأن arguments قد تظهر في process list أو logs.

### الخطوة 4: كتابة أول integration

أنشئ `app.py`:

```python
from pathlib import Path

# Run this file with PYTHONPATH=vendor/youtube-evidence-manager.
from src.evidence_manager import EvidenceCollectionError, EvidenceCollector, write_bundle
from src.youtube_api_client import YouTubeDataClient


def collect_video(video_id: str) -> dict:
    collector = EvidenceCollector(YouTubeDataClient())
    try:
        bundle = collector.collect(
            video_id,
            max_comments=25,
            max_comment_pages=1,
            include_comments=True,
        )
    except EvidenceCollectionError:
        raise
    write_bundle(bundle, Path("artifacts/evidence"))
    return bundle


if __name__ == "__main__":
    result = collect_video("dQw4w9WgXcQ")
    print({"video_id": result["video_id"], "caption": result["caption"]["status"]})
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

تحقق من وجود `artifacts/evidence/*/evidence.json` و`evidence.md`. إذا كانت metadata موجودة وcaption ناقصة، فهذا partial success موثق، وليس سببًا لإخفاء التقرير أو اعتباره كاملًا.

## 3. الدمج كـ CLI داخل مشروع غير Python

إذا كان المشروع المستضيف Node.js، شغّل الأمر كـ child process:

```javascript
import { spawn } from "node:child_process";

const child = spawn(
  ".venv/bin/python",
  ["-m", "src.evidence_cli", process.env.VIDEO_INPUT, "--output-dir", "artifacts/evidence"],
  { cwd: "/absolute/path/to/youtube-evidence-manager", env: process.env }
);

let stderr = "";
child.stderr.on("data", (chunk) => { stderr += chunk.toString(); });
child.on("close", (code) => {
  if (code !== 0) throw new Error(`Evidence CLI failed (${code}): ${stderr}`);
});
```

في هذا النمط، اجعل `cwd` مسارًا مطلقًا، واستخدم interpreter البيئة الافتراضية، وانتظر انتهاء process قبل قراءة artifact. لا تعتبر ظهور بعض الأسطر في stdout نجاحًا؛ **exit code 0 ووجود الملفين** هما معيار النجاح.

في مشروع Go أو Java أو أي runtime آخر، طبق النمط نفسه باستخدام process API في اللغة المستضيفة. إذا احتجت bundle في الذاكرة، استعمل خدمة Python صغيرة داخلية أو استورد الوحدة في Python بدل تحليل stdout.

## 4. دمج مسار Gemini داخل مشروع مستضيف

بعد نجاح الجمع، شغّل التحليل في خطوة منفصلة:

```python
from pathlib import Path

from src.gemini_analyzer import GeminiAnalyzer, write_analysis


def analyze_bundle(bundle: dict, output_dir: Path) -> tuple[Path, Path]:
    analysis = GeminiAnalyzer().analyze(bundle)
    return write_analysis(analysis, output_dir)
```

اجعل التحليل قابلًا للإيقاف عبر configuration مثل `ENABLE_GEMINI_ANALYSIS=false`. لا تجعل فشل Gemini يمحو `evidence.json`؛ احفظ evidence أولًا، ثم سجل التحليل كـ `failed` مع السبب المنقح. لا تعيد الطلب بلا حد عند `401` أو `403` أو rate limit.

## 5. دمج pipeline للبحث أو batch

عند معالجة عدة فيديوهات، افصل مراحل الاكتشاف والجمع والتحليل والحفظ. لا تطلق عشرات الطلبات المتوازية دون حدود؛ حدد workers وmax comments، واحفظ حالة كل فيديو.

```python
from pathlib import Path

# Run this file with PYTHONPATH=vendor/youtube-evidence-manager.
from src.evidence_manager import EvidenceCollectionError, EvidenceCollector, write_bundle
from src.youtube_api_client import YouTubeDataClient


video_ids = ["dQw4w9WgXcQ", "VIDEO_ID_2"]
collector = EvidenceCollector(YouTubeDataClient())
for video_id in video_ids:
    try:
        bundle = collector.collect(video_id, max_comments=10, max_comment_pages=1)
        json_path, markdown_path = write_bundle(bundle, Path("artifacts/evidence"))
        print({"video_id": video_id, "status": "complete", "json": str(json_path)})
    except EvidenceCollectionError as exc:
        print({"video_id": video_id, "status": "failed", "error": str(exc)})
```

في مشروع إنتاجي، استبدل `print` بسجل منظم، واحفظ `status` في قاعدة بيانات أو queue state. أعد المحاولة فقط للأخطاء العابرة. لا تعِد المحاولة عند invalid key أو quota exhaustion أو comments disabled دون تغيير المسار.

## 6. نقل Workflow إلى مستودع آخر

انسخ `.github/workflows/evidence.yml` إلى `.github/workflows/evidence.yml` في المشروع الآخر، ثم عدّل:

| العنصر | ما الذي يجب مراجعته؟ |
|---|---|
| `actions/checkout` | ي checkout المشروع الذي يحتوي Workflow؛ يجب أن يحتوي `src/` و`requirements.txt` |
| `YOUTUBE_API_KEY` | Repository Secret في المستودع الآخر، بالاسم نفسه |
| `GEMINI_API_KEY` | Secret اختياري عند `analyze=true` |
| `GEMINI_MODEL` | Repository Variable اختياري، أو قيمة default في YAML |
| `video` | input يدوي يحتوي URL أو ID فقط |
| `artifacts/evidence` | مسار لا ترفعه إلى Git؛ يرفعه Actions كـ Artifact |
| `retention-days` | عدّله وفق سياسة الاحتفاظ والخصوصية |

في GitHub:

1. افتح المستودع الآخر ثم **Settings → Secrets and variables → Actions**.
2. من **Secrets** اختر **New repository secret** وأضف `YOUTUBE_API_KEY`.
3. إذا كان التحليل مطلوبًا، أضف `GEMINI_API_KEY` كـ Secret مستقل.
4. من **Variables** أضف `GEMINI_MODEL` فقط إذا كنت تريد تغيير النموذج الافتراضي.
5. افتح **Actions → Collect YouTube evidence → Run workflow**.
6. أدخل فيديو اختبارًا واحدًا، اجعل `max_comments` منخفضًا مثل `5`، واجعل `max_comment_pages` مساويًا لـ `1`.
7. راقب خطوات `Validate required configuration` و`Collect evidence bundle` و`Upload evidence artifacts`.
8. نزّل Artifact، وتحقق من وجود `evidence.json` و`evidence.md`، ثم فعّل `analyze` في تشغيل منفصل إذا كان مفتاح Gemini جاهزًا.

إذا ظهر `YOUTUBE_API_KEY is missing` فالمشكلة في إعداد المستودع الآخر لا في الفيديو. وإذا نجح الجمع وفشل التحليل، احتفظ بـ evidence وأصلح Secret أو `GEMINI_MODEL` قبل إعادة التحليل.

## 7. إضافة endpoint في تطبيق ويب

لا تستدعِ YouTube مباشرة من browser لأن المفتاح سيظهر للمستخدم. ضع الاستدعاء في backend أو worker:

```text
Browser -> POST /evidence-jobs { video_url }
Backend -> validate video ID
Backend -> EvidenceCollector.collect()
Backend -> write_bundle() to private storage
Backend -> return job_id
Browser -> GET /evidence-jobs/{job_id}
```

تحقق من URL على الخادم، ضع حدًا لطول الإدخال، امنع path traversal في output path، ولا تسمح للمستخدم باختيار `output_dir` عشوائيًا. استخدم `video_id` بعد التحقق منه لتسمية المجلد.

## 8. الاستضافة والتخزين

احفظ `evidence.json` و`analysis.json` في storage خاص إذا كانت البيانات ستضم تعليقات أو نص captions. استخدم `evidence.md` للمراجعة أو التنزيل، وليس كبديل عن JSON. عند استخدام S3 أو object storage، لا تجعل الرابط عامًا افتراضيًا؛ استخدم signed URL قصير العمر إذا احتاج المستخدم التنزيل.

احتفظ بالسجل التالي لكل job:

| الحقل | السبب |
|---|---|
| `video_id` و`source_url` | ربط النتيجة بالمصدر |
| `collected_at` | معرفة زمن اللقطة الزمنية للبيانات |
| `caption.status` و`segment_count` و`text_sha256` | التحقق من حالة النص دون طباعة المحتوى |
| `comment_count_collected` | تقدير نطاق العينة |
| `status` و`error_code` | الاستئناف والتشخيص |
| commit أو version | إعادة إنتاج نتيجة سابقة |

## 9. الاختبار في المشروع الآخر

قسّم الاختبار إلى ثلاث طبقات:

| الطبقة | الشبكة | ما الذي تختبره؟ |
|---|---:|---|
| Unit | لا | parsing وrendering وfallback وvalidation |
| Integration mock | لا | استدعاءات client بعقود مزيفة وحقن transcript |
| Live smoke | نعم | فيديو واحد، limits منخفضة، تشغيل يدوي فقط |

شغّل Unit وIntegration في كل Pull Request. شغّل Live smoke عند تغيير secrets أو dependency أو Workflow، وليس في كل commit. خزّن artifact منقحًا فقط، ولا تضع API responses كاملة في CI logs.

## 10. التحديث والـ rollback

ثبت commit أو tag للمستودع داخل التطبيق المستضيف. قبل التحديث:

```bash
git -C vendor/youtube-evidence-manager fetch origin
git -C vendor/youtube-evidence-manager log --oneline -5
python -m unittest discover -s vendor/youtube-evidence-manager/tests -v
```

بعد التحديث، شغّل fixture tests ثم Live smoke محدودًا. إذا فشل، أعد pin إلى commit السابق بدل نسخ ملفات عشوائيًا، وسجل سبب rollback.

## 11. حدود المسؤولية

إعادة الاستخدام لا تمنح التطبيق المستضيف صلاحية تنزيل captions محمية أو تجاوز login أو CAPTCHA أو تحويل تعليقات الجمهور إلى حقائق. لا يعتبر النظام metadata أو caption أو comment تحققًا مستقلاً من الادعاء. يجب أن يحتفظ التطبيق المستضيف بهذا الفصل في واجهته وتقاريره.

## المراجع

[1]: https://docs.github.com/en/actions/security-for-github-actions/security-guides/using-secrets-in-github-actions "Using secrets in GitHub Actions"
[2]: https://docs.github.com/en/actions/using-workflows/storing-workflow-data-as-artifacts "Store and share data with workflow artifacts"
[3]: https://developers.google.com/youtube/v3/determine_quota_cost "YouTube Data API quota costs"

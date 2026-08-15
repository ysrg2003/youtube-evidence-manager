# التشغيل والنتائج

## ما الذي يعمل حاليًا؟

المستودع يحتوي على Workflowين. `CI` في `.github/workflows/ci.yml` يعمل عند `push` إلى `main`، وعند Pull Request إلى `main`، ويمكن تشغيله يدويًا؛ وهو offline ولا يستخدم أسرارًا. أما `Collect YouTube evidence` في `.github/workflows/evidence.yml` فهو تشغيل يدوي فقط، ويستقبل رابط فيديو ومدخلات حدود التعليقات والتحليل، ثم يحفظ النتائج كـ Artifact.

## التشغيل المحلي من الصفر

من جذر المستودع، بعد تفعيل `.venv` وتثبيت requirements، نفّذ:

```bash
python3 -m py_compile youtube_subtitles_translator.py src/youtube_api_client.py src/evidence_manager.py src/gemini_analyzer.py src/evidence_cli.py
python -m unittest discover -s tests -v
python -m src.evidence_cli --help
git diff --check
```

النتيجة المتوقعة هي عدم ظهور أخطاء compile، ثم `Ran 13 tests` و`OK`، ثم عرض تعليمات CLI، ثم عودة `git diff --check` دون إخراج. إذا اختلفت النتيجة، راجع [troubleshooting.md](troubleshooting.md) قبل رفع commit.

## تشغيل أداة captions

أداة captions الحالية تكتب ملفات SRT في `output/`:

```bash
python youtube_subtitles_translator.py "https://www.youtube.com/watch?v=VIDEO_ID" --target ar --output-dir output
```

تحقق من النتيجة عبر:

```bash
find output -type f -name '*.srt' -print
```

إذا لم يظهر ملف، راجع سجل `Transcripts are disabled` أو `No transcript available`. لا تعيد المحاولة بلا حدود ولا تعتبر captions مصدرًا مستقلًا للحقيقة.

## المخرجات والاحتفاظ بها

المخرجات المحلية توضع في `output/` أو `artifacts/` حسب الأداة. كلا المسارين متجاهلان في Git حتى لا تدخل captions أو التعليقات أو تقارير البحث في المستودع بالخطأ.

| المخرج | المحتوى | المعالجة |
|---|---|---|
| `.srt` أصلي | captions مع التوقيتات | لا يُرفع إلى Git تلقائيًا |
| `.srt` مترجم | نسخة ترجمة للمراجعة | لا يمثل النص الأصلي |
| `evidence.json` | metadata والنص والتعليقات والتصنيفات | يُحفظ محليًا أو كـ artifact خاص |
| `evidence.md` | ملخص قابل للقراءة | للمراجعة قبل الكتابة |

لا تحفظ HTML الخام أو النص الكامل في artifact إلا إذا كان ذلك ضروريًا للمراجعة ومسموحًا به. الأفضل حفظ hash، counts، preview منقحة، وسبب الفشل.

## GitHub Actions الحالي

1. افتح [مستودع youtube-evidence-manager](https://github.com/ysrg2003/youtube-evidence-manager).
2. اضغط **Actions**.
3. اختر Workflow باسم **CI**.
4. افتح التشغيل المطلوب، ثم راجع job باسم **offline-tests**.
5. النجاح يظهر كـ `success`، وتكون خطوات **Compile Python files** و**Run offline tests** ناجحة.

يمكن تشغيل `CI` يدويًا من **Run workflow** دون inputs أو أسرار. أما `Collect YouTube evidence` فيتطلب Secret باسم `YOUTUBE_API_KEY`، ويتطلب `GEMINI_API_KEY` فقط عندما تكون input `analyze=true`. إذا فشل التثبيت، افتح خطوة **Install dependencies**؛ وإذا فشل جمع الأدلة، راجع خطوة **Validate required configuration** ثم سجل `artifacts/evidence/run.log`.

## تشغيل جامع الأدلة

بعد ضبط `YOUTUBE_API_KEY` في `.env`، شغّل جامع الأدلة لفيديو واحد:

```bash
python -m src.evidence_cli "https://www.youtube.com/watch?v=VIDEO_ID" --output-dir artifacts/evidence
```

لتقليل الحصة، حدّد `--max-comments` و`--max-comment-pages` أو استخدم `--skip-comments`. يبقى التحليل منفصلًا واختياريًا:

```bash
python -m src.evidence_cli VIDEO_ID --analyze
```

في GitHub Actions، يُضاف `YOUTUBE_API_KEY` فقط إلى **Settings → Secrets and variables → Actions → Secrets**، وتُشغّل أي workflow خارجي يدويًا ومحدودًا. يجب إيقاف المسار عند `quotaExceeded` بدل تدوير المفاتيح، وعدم رفع HTML خام أو أسرار أو captions غير منقحة كـ artifact.

## تشغيل corpus المقالات الخمسين

الـ workflow هو `.github/workflows/corpus.yml` واسمه **Collect corpus YouTube evidence**، ويعمل يدويًا فقط. يقرأ `testdata/corpus_manifest.json` الذي يربط كل مقال بعنوانه وقسمه وsubtitle وlabels واستعلامه.

ابدأ بجولة محدودة من **Actions → Collect corpus YouTube evidence → Run workflow**:

| Input | أول تشغيل مقترح | أثره |
|---|---:|---|
| `max_articles` | `1` أو `5` | عدد المقالات في الجولة |
| `search_results` | `5` | المرشحون لكل مقال؛ كل بحث يستهلك حصة |
| `max_comments` | `10` | حد التعليقات الرئيسية لكل فيديو |
| `max_comment_pages` | `1` | حد صفحات التعليقات |
| `skip_comments` | `false` | اجعله `true` عند الاكتفاء بـ metadata وcaptions |
| `analyze` | `false` أولًا | لا تستخدم Gemini حتى تفحص evidence |
| `resume` | `true` | يعيد استخدام العناصر المسجلة في state |

يُحفظ `corpus_state.json` بعد كل مقال، ويُنتج `corpus_results.json` و`corpus_results.md`. لكل مقال مجلد `article_XXX/` يحوي evidence. إذا تعذر captions، تبقى metadata محفوظة وتصبح الحالة `partial`. إذا فشل Gemini بعد الجمع، تبقى evidence ويظهر `analysis_status=failed`. لا تستخدم إعادة التشغيل القسرية إلا بقرار واعٍ لأنها تعيد استهلاك الحصة.

لا يكتب هذا المسار فوق ملفات المقالات ولا ينشر إلى Blogger. بعد تنزيل artifact، راجع `corpus_results.md`، ثم evidence ذات captions متاحة، ثم التحليلات الناجحة. اعتبر captions وكلام المتحدث والتعليقات أنواع أدلة مختلفة، ولا تنقل ادعاءً إلى المقال دون تحقق مستقل عندما يكون factual.

## التحقق من التشغيل الناجح

| الفحص | علامة النجاح |
|---|---|
| Python compile | لا تظهر أخطاء syntax |
| Offline tests | `OK` |
| CI | خطوات Compile وOffline tests ناجحة |
| Evidence workflow configuration | يرفض التشغيل عند غياب Secret المطلوب برسالة واضحة |
| API metadata/comments | استجابة بعناصر أو خطأ YouTube واضح دون المفتاح |
| Transcript probe | `caption.status=available` أو سبب فشل محدد |
| Evidence bundle | URL وvideo ID ووقت جمع وقيود، مع `evidence.json` و`evidence.md` |
| Gemini adapter الاختياري | `analysis.json` و`analysis.md` أو خطأ محفوظ دون سر |

## سياسة التوقف

أوقف المسار عند مفتاح غير صالح، quota exhaustion، أو استجابة تتطلب login أو CAPTCHA. لا تدوّر مفاتيح لتجاوز 429 أو حدود الحصة. لا تستخدم عدة مشاريع أو حسابات للتحايل على حدود الخدمة. يمكن إعادة التشغيل بعد حل السبب، مع caching للنتائج السابقة.

## الاستئناف والـ rollback

إذا توقف تشغيل playlist، احتفظ بكل فيديو في ملف مستقل أو سجل حالة يتضمن `video_id` و`status` و`attempted_at`. أعد المحاولة فقط للعناصر ذات `error` القابل لإعادة المحاولة، ولا تعِد معالجة العناصر الناجحة.

إذا تسبب تعديل توثيقي أو dependency في فشل CI، اعرض commits الأخيرة عبر:

```bash
git log --oneline -5
```

ثم أعد الفرع محليًا إلى commit معروف قبل التعديل فقط بعد حفظ أي عمل مطلوب، أو أصلح commit جديدًا بدل force-push. لا تستخدم `git push --force` على `main`.

## اختيار نمط التشغيل المناسب

استخدم هذا الجدول قبل بناء automation أو مشروع مضيف حتى لا تخلط بين مسؤوليات الطبقات:

| السيناريو | النمط الموصى به | نقطة التحقق |
|---|---|---|
| تجربة فيديو واحد من جهاز المطور | `python -m src.evidence_cli` | وجود `evidence.json` و`evidence.md` |
| الحصول على كائن Python وتخصيص العملية | `EvidenceCollector` و`write_bundle` | assertions على `schema_version` و`caption.status` |
| تطبيق Node أو Go أو Java | subprocess يستدعي CLI بمسار Python ثابت | exit code يساوي 0 والملفات موجودة |
| خدمة ويب أو worker | backend job مع state machine وتخزين خاص | `job_id` وحالة `complete` أو `partial` |
| batch بحثي محدود | حلقة Python مع limits وحفظ حالة كل video ID | عدم إعادة العناصر الناجحة |
| تشغيل يدوي دون جهاز محلي | Workflow `Collect YouTube evidence` | نجاح خطوات validation والجمع ورفع Artifact |
| CI لكل Pull Request | Workflow `CI` | compile وoffline tests دون Secrets أو quota |

التفاصيل التنفيذية للاستخدام البرمجي موجودة في [programmatic-use.md](programmatic-use.md)، أما دمج النظام في مشروع آخر أو runtime آخر فموثق في [reuse-in-another-project.md](reuse-in-another-project.md).

## عقد نجاح أي integration

لا تعتبر ظهور رسالة progress نجاحًا. يعتبر integration ناجحًا فقط عندما يحقق جميع الشروط المناسبة لنمطه: exit code صحيح أو عدم وجود exception غير معالج، ملف أو response قابل للقراءة، `video_id` و`source_url` متطابقان، `collected_at` موجود، وحالة captions والتعليقات موثقة حتى عند النقص. إذا كان التحليل مفعّلًا، يجب أن يكون `analysis.json` JSON صالحًا وأن يحتوي على الحقول المنظمة قبل عرضه للمستخدم.

## الاستئناف والتنظيف

عند توقف batch أو worker، احتفظ بـ `video_id` و`status` وسبب الفشل ووقت المحاولة. أعد تشغيل العناصر ذات الأخطاء العابرة فقط. لا تعِد طلبًا انتهى بـ `quotaExceeded` أو `keyInvalid` قبل إصلاح السبب. احذف `artifacts/` و`output/` عندما تنتهي الحاجة إليها إذا كانت النصوص أو التعليقات حساسة، وتحقق من عدم وجودها في `git status` قبل commit.

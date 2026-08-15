# التشغيل والنتائج

## ما الذي يعمل حاليًا؟

المستودع يحتوي على Workflow اسمه `CI` في `.github/workflows/ci.yml`. يعمل عند `push` إلى `main`، وعند Pull Request إلى `main`، ويمكن تشغيله يدويًا من تبويب Actions. هذا Workflow لا يستخدم `YOUTUBE_API_KEY` ولا يتصل بـ YouTube أو Gemini؛ وظيفته compile واختبارات offline فقط.

## التشغيل المحلي من الصفر

من جذر المستودع، بعد تفعيل `.venv` وتثبيت requirements، نفّذ:

```bash
python3 -m py_compile youtube_subtitles_translator.py src/youtube_api_client.py
python -m unittest discover -s tests -v
git diff --check
```

النتيجة المتوقعة هي عدم ظهور أخطاء compile، ثم `Ran 5 tests` و`OK`، ثم عودة `git diff --check` دون إخراج. إذا اختلفت النتيجة، راجع [troubleshooting.md](troubleshooting.md) قبل رفع commit.

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

يمكن تشغيله يدويًا من **Run workflow**، لكن لا توجد inputs أو أسرار مطلوبة في النسخة الحالية. إذا فشل بعد تعديل requirements، افتح خطوة **Install dependencies**، ثم أصلح constraint في `requirements.txt` وأعد تشغيل CI.

## Workflow YouTube المستقبلي

عند إضافة probe YouTube الرسمي، يجب أن يبدأ يدويًا (`workflow_dispatch`) وأن يستخدم السر فقط في خطوة الاستدعاء:

```yaml
env:
  YOUTUBE_API_KEY: ${{ secrets.YOUTUBE_API_KEY }}
```

يجب أن يكون probe محدودًا إلى استعلام واحد أو 10 فيديوهات، وأن يرفع artifact منقحًا لا يحتوي على API key أو HTML خام أو نص كامل غير مطلوب. يجب أن تكون قيمة `run_corpus` الافتراضية `false`، وأن يتوقف عند `quotaExceeded` بدل تدوير المفاتيح.

## التحقق من التشغيل الناجح

| الفحص | علامة النجاح |
|---|---|
| Python compile | لا تظهر أخطاء syntax |
| Offline tests | `OK` |
| API health check مستقبلي | HTTP 200 مع `items` أو حالة API واضحة |
| Transcript probe | `caption.status=available` أو سبب فشل محدد |
| Evidence bundle مستقبلي | URL وvideo ID ووقت جمع وقيود موجودة |
| Gemini adapter مستقبلي | JSON منظم أو خطأ محفوظ دون سر |

## سياسة التوقف

أوقف المسار عند مفتاح غير صالح، quota exhaustion، أو استجابة تتطلب login أو CAPTCHA. لا تدوّر مفاتيح لتجاوز 429 أو حدود الحصة. لا تستخدم عدة مشاريع أو حسابات للتحايل على حدود الخدمة. يمكن إعادة التشغيل بعد حل السبب، مع caching للنتائج السابقة.

## الاستئناف والـ rollback

إذا توقف تشغيل playlist، احتفظ بكل فيديو في ملف مستقل أو سجل حالة يتضمن `video_id` و`status` و`attempted_at`. أعد المحاولة فقط للعناصر ذات `error` القابل لإعادة المحاولة، ولا تعِد معالجة العناصر الناجحة.

إذا تسبب تعديل توثيقي أو dependency في فشل CI، اعرض commits الأخيرة عبر:

```bash
git log --oneline -5
```

ثم أعد الفرع محليًا إلى commit معروف قبل التعديل فقط بعد حفظ أي عمل مطلوب، أو أصلح commit جديدًا بدل force-push. لا تستخدم `git push --force` على `main`.

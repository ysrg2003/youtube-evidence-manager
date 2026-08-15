# التشخيص واسترداد الأخطاء

| الرسالة أو الحالة | السبب المحتمل | الإجراء |
|---|---|---|
| `No module named youtube_transcript_api` | الاعتماديات غير مثبتة أو البيئة الافتراضية غير مفعلة | فعّل `.venv` ثم نفذ `python -m pip install -r requirements.txt` |
| `Transcripts are disabled` | صاحب الفيديو عطّل captions | سجل `caption.status=missing` ولا تحاول تجاوز القرار |
| `No transcript available` | لا يوجد مسار متاح أو اللغة غير مناسبة | احتفظ بالـ metadata فقط، واطلب فيديو آخر أو مصدرًا مصرحًا للنص |
| `HTTP 400 badRequest` من YouTube | معرّف أو parameters غير صحيحة | تحقق من video ID و`part` ولا تعِد الطلب عشوائيًا |
| `HTTP 403 quotaExceeded` | نفدت حصة API | أوقف التشغيل، راجع Quotas، واستخدم caching؛ لا تدوّر مفاتيح لتجاوز الحد |
| `HTTP 403 keyInvalid` | المفتاح غير صالح أو API غير مفعّل | أنشئ/حدّث المفتاح وفعّل YouTube Data API v3 في Google Cloud |
| `commentsDisabled` | التعليقات مغلقة للفيديو | خزّن `comments.status=disabled` ولا تعتبره فشلًا تقنيًا |
| Gemini `permission_denied` | مشروع Gemini غير مصرح له | لا تعِد المحاولات؛ أصلح صلاحية المشروع أو عطّل adapter |
| نص caption فارغ | فشل parser أو track غير متاح | لا ترسل النص إلى Gemini؛ احفظ السبب فقط |
| ملف output ظهر في Git | `.gitignore` غير كافٍ أو أُضيف الملف بالقوة | احذف الملف من index، افحص الأسرار، ثم أضف قاعدة ignore مناسبة |

## فحص سريع للمستودع

نفّذ من الجذر:

```bash
python3 -m py_compile youtube_subtitles_translator.py
git status --short --ignored
python -m unittest discover -s tests -v
```

إذا ظهرت قيمة تشبه مفتاحًا في `git diff` أو سجل Git، أوقف الرفع، ألغِ المفتاح من Google Cloud، ثم نظّف المستودع قبل أي push.

## متى نطلب مساعدة المستخدم؟

نحتاج من المستخدم قيمة أو قرارًا فقط عندما لا يمكن استنتاجه بأمان، مثل اختيار Google Cloud project، تزويد `YOUTUBE_API_KEY` عبر GitHub Secret، أو اختيار فيديو اختبار عام. لا نطلب من المستخدم لصق المفاتيح في المحادثة أو في ملفات المشروع.

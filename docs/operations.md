# التشغيل والنتائج

## المخرجات

المخرجات المحلية توضع في `output/` أو `artifacts/` حسب الأداة. كلا المسارين متجاهلان في Git حتى لا تدخل captions أو التعليقات أو تقارير البحث في المستودع بالخطأ.

| المخرج | المحتوى | المعالجة |
|---|---|---|
| `.srt` أصلي | captions مع التوقيتات | لا يُرفع إلى Git تلقائيًا |
| `.srt` مترجم | نسخة ترجمة للمراجعة | لا يمثل النص الأصلي |
| `evidence.json` | metadata والنص والتعليقات والتصنيفات | يُحفظ محليًا أو كـ artifact خاص |
| `evidence.md` | ملخص قابل للقراءة | للمراجعة قبل الكتابة |

## تشغيل محلي آمن

نفّذ الاختبار من جذر المستودع:

```bash
python -m unittest discover -s tests -v
```

بعد إضافة probe YouTube الرسمي، يجب أن يكون تشغيله صريحًا ومحدودًا، مثل استعلام واحد و10 نتائج، لا تشغيل corpus كامل تلقائيًا. سجّل `quota_before` و`quota_after` إن كان ذلك متاحًا، ولا تعيد الطلب عند `quotaExceeded`.

## GitHub Actions

عند إضافة Workflow، يجب أن يكون التشغيل يدويًا أولًا (`workflow_dispatch`) وأن يستخدم:

```yaml
env:
  YOUTUBE_API_KEY: ${{ secrets.YOUTUBE_API_KEY }}
```

يجب أن يرفع Workflow artifact منقحًا لا يحتوي على API key أو HTML خام أو نص كامل غير مطلوب. يفضل حفظ hashes وcounts وpreviews محدودة، مع جعل `run_corpus` افتراضيًا `false`.

## التحقق من تشغيل ناجح

| الفحص | علامة النجاح |
|---|---|
| Python compile | لا تظهر أخطاء syntax |
| Offline tests | `OK` |
| API health check | HTTP 200 مع `items` أو حالة API واضحة |
| Transcript probe | `caption.status=available` أو سبب فشل محدد |
| Evidence bundle | URL وvideo ID ووقت جمع وقيود موجودة |
| Gemini adapter | JSON منظم أو خطأ محفوظ دون سر |

## سياسة التوقف

أوقف المسار عند مفتاح غير صالح، quota exhaustion، أو استجابة تتطلب login أو CAPTCHA. لا تدوّر مفاتيح لتجاوز 429 أو حدود الحصة. لا تستخدم عدة مشاريع أو حسابات للتحايل على حدود الخدمة. يمكن إعادة التشغيل بعد حل السبب، مع caching للنتائج السابقة.

## الاستئناف

إذا توقف تشغيل playlist، احتفظ بكل فيديو في ملف مستقل أو سجل حالة يتضمن `video_id` و`status` و`attempted_at`. أعد المحاولة فقط للعناصر ذات `error` قابل لإعادة المحاولة، ولا تعِد معالجة العناصر الناجحة.

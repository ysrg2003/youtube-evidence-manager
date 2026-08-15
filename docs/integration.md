# تصميم التكامل

## الهدف

يحوّل هذا المشروع فيديوهات YouTube العامة إلى evidence brief قابل للمراجعة. لا يخلط بين بيانات YouTube الرسمية وبين كلام المتحدث أو تعليقات الجمهور.

## الطبقات

| الطبقة | المصدر | نوع الدليل | ما الذي لا تثبته؟ |
|---|---|---|---|
| الاكتشاف | `search.list` | نتيجة بحث وعنوان ومعرّف | لا تثبت صحة المحتوى |
| هوية الفيديو | `videos.list` | عنوان، وصف، تاريخ، مدة، قناة، إحصائيات | الإحصائيات لا تثبت الادعاءات |
| هوية القناة | `channels.list` مستقبلًا | بيانات القناة العامة | الشهرة ليست تحققًا علميًا |
| النص | `youtube-transcript-api` | caption متاح مع توقيتات | قد يكون تلقائيًا أو ناقصًا أو خاطئًا |
| الحوار العام | `commentThreads.list` | تعليقات وردود منشورة | آراء وتجارب غير موثقة |
| التحليل | Gemini مستقبلًا | تلخيص واستخراج ادعاءات | لا يحوّل المصدر الضعيف إلى حقيقة |

## مسار فيديو واحد

1. استخرج `video_id` وتحقق من أنه معرّف YouTube صحيح.
2. استدعِ `videos.list` على دفعة من المعرّفات، مع `part=snippet,contentDetails,statistics,status` والحقول التي يحتاجها التقرير فقط.
3. اطلب captions عبر المحول الحالي. سجّل اللغة، عدد المقاطع، ووقت الجمع، وحالة المسار إن كانت المكتبة توفرها.
4. استدعِ `commentThreads.list` بعدد محدود، مع `textFormat=plainText`. خزّن التعليقات كـ `user_generated_comment`.
5. طبّق بوابة جودة: استبعد caption الفارغ، النص القصير جدًا، الأخطاء، والنتيجة التي تتضمن صفحة حماية بدل النص.
6. أنشئ evidence bundle يحتوي على الروابط والبيانات الخام المختصرة والتصنيفات والقيود.
7. أرسل bundle إلى Gemini فقط بعد نجاح الفحص. يجب أن يطلب prompt إخراجًا منظمًا يفصل الادعاءات عن التجارب والقيود، ويمنع اختلاق citations.
8. احفظ JSON وMarkdown للمراجعة؛ لا تنشر إلى Blogger تلقائيًا.

## صيغة evidence المقترحة

```json
{
  "schema_version": "0.1",
  "source_url": "https://www.youtube.com/watch?v=VIDEO_ID",
  "video_id": "VIDEO_ID",
  "metadata": {
    "title": "",
    "channel_id": "",
    "channel_title": "",
    "published_at": "",
    "duration": "",
    "view_count": null,
    "comment_count": null
  },
  "caption": {
    "status": "available|missing|blocked|error",
    "language": "en",
    "is_generated": null,
    "segment_count": 0,
    "text_sha256": "",
    "text": ""
  },
  "comments": [],
  "evidence_labels": ["creator_claim", "caption_text", "user_generated_comments"],
  "limitations": [],
  "collected_at": ""
}
```

## Gemini contract المستقبلي

يجب أن يطلب التكامل من Gemini إخراجًا يتضمن `source_url`, `summary`, `claims`, `experiences`, `counterpoints`, `verification_needed`, `citations`, `limitations`, و`confidence`. لا نستخدم Gemini URL Context في البداية؛ نرسل النص الذي جُلب وصُنّف محليًا، لأن اختبارات المشروع السابق أثبتت أن مشروع Gemini الحالي مرفوض بـ HTTP 403.

## القيود الرسمية

تستطيع YouTube Data API v3 قراءة البيانات العامة والتعليقات، لكن `captions.list` يعيد بيانات المسارات لا النص الفعلي. أما `captions.download` فيتطلب صلاحية تعديل الفيديو. لذلك يبقى مستخرج captions الحالي طبقة منفصلة وغير رسمية، ويجب أن تكون النتيجة موسومة بمصدرها وحدودها [1] [2] [3].

### المراجع

[1]: https://developers.google.com/youtube/v3/docs/videos/list "YouTube Data API videos.list"
[2]: https://developers.google.com/youtube/v3/docs/commentThreads/list "YouTube Data API commentThreads.list"
[3]: https://developers.google.com/youtube/v3/docs/captions/download "YouTube Data API captions.download"

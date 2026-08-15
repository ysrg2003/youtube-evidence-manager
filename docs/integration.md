# تصميم التكامل

## الهدف

يحوّل هذا المشروع فيديوهات YouTube العامة إلى evidence brief قابل للمراجعة. لا يخلط بين بيانات YouTube الرسمية وبين كلام المتحدث أو تعليقات الجمهور، ولا يحول transcript أو عدد المشاهدات إلى إثبات مستقل.

## حالة التكامل الحالية

| المكوّن | الحالة في المستودع | ما يمكن تشغيله الآن |
|---|---|---|
| `YouTubeDataClient` | موجود | بحث فيديوهات، تفاصيل فيديوهات، تعليقات عامة عبر Python |
| captions adapter | موجود ضمن `youtube_subtitles_translator.py` | استخراج transcript متاح وتحويله إلى SRT |
| evidence bundle | تصميم موثق فقط | لا يوجد probe جماعي بعد |
| Gemini adapter | غير مفعّل | لا توجد استدعاءات Gemini في هذا المستودع |
| Blogger publishing | غير موجود عمدًا | لا يوجد نشر تلقائي |

## الطبقات

| الطبقة | المصدر أو endpoint | نوع الدليل | ما الذي لا تثبته؟ |
|---|---|---|---|
| الاكتشاف | `search.list` | نتيجة بحث وعنوان ومعرّف | لا تثبت صحة المحتوى |
| هوية الفيديو | `videos.list` | عنوان، وصف، تاريخ، مدة، قناة، إحصائيات | الإحصائيات لا تثبت الادعاءات |
| هوية القناة | `channels.list` مستقبلًا | بيانات القناة العامة | الشهرة ليست تحققًا علميًا |
| النص | `youtube-transcript-api` | caption متاح مع توقيتات | قد يكون تلقائيًا أو ناقصًا أو خاطئًا |
| الحوار العام | `commentThreads.list` | تعليقات وردود منشورة | آراء وتجارب غير موثقة |
| التحليل | Gemini مستقبلًا | تلخيص واستخراج ادعاءات | لا يحوّل المصدر الضعيف إلى حقيقة |

## البحث عن فيديوهات

عميل Python يستدعي endpoint الرسمي التالي:

```text
GET https://www.googleapis.com/youtube/v3/search
```

الطلب الأساسي الذي يبنيه `search_videos` هو:

```text
part=snippet
type=video
q=AI-assisted building
maxResults=10
order=relevance
key=YOUR_KEY_SENT_BY_ENVIRONMENT
```

لا تضع قيمة `key` الحقيقية في ملف أو رابط محفوظ. `maxResults` يقيّد النتيجة بين 1 و50، ويمكن استخدام `nextPageToken` لجلب الصفحة التالية. كل صفحة إضافية هي طلب جديد وتحتاج إلى احترام الحصة [1].

## جلب تفاصيل الفيديو

بعد استخراج `videoId`، يجمع العميل IDs في طلب واحد إلى:

```text
GET https://www.googleapis.com/youtube/v3/videos
```

ويطلب:

```text
part=snippet,contentDetails,statistics,status
id=VIDEO_ID_1,VIDEO_ID_2
```

النتيجة المتوقعة تحتوي على `items`، وكل عنصر قد يتضمن `snippet.title`, `snippet.description`, `snippet.channelId`, `snippet.channelTitle`, `snippet.publishedAt`, `contentDetails.duration`, وحقولًا من `statistics`. يقبل endpoint حتى 50 ID في الطلب الواحد وفق توثيق Google [2].

## جلب التعليقات

يستخدم العميل:

```text
GET https://www.googleapis.com/youtube/v3/commentThreads
```

بطلب مثل:

```text
part=snippet,replies
videoId=VIDEO_ID
maxResults=20
textFormat=plainText
order=relevance
```

النتيجة المتوقعة تحتوي على `items` و`nextPageToken`. قد تكون التعليقات مغلقة أو ناقصة أو محذوفة؛ `commentsDisabled` حالة متوقعة وليست دليلًا على خلل في البرنامج. نحتفظ بها مع label `user_generated_comment` [3].

## استخراج captions

الأداة الحالية تستعمل `youtube-transcript-api`، وليس YouTube Data API v3، لاستخراج المقاطع الزمنية. المسار الحالي يفضل الإنجليزية، ثم يحاول مسارات أخرى متاحة، ويعيد `start`, `duration`, و`text`، ثم يحفظ SRT.

هذا مسار غير رسمي مستقل عن API الرسمي. يمكن أن يفشل بسبب تعطيل captions أو عدم وجودها أو تغيرات YouTube. يجب تسجيل `caption.status` و`caption.language` و`segment_count` ووقت الجمع، وعدم وصف النص بأنه transcript موثّق إذا لم نعرف مصدر المسار وحالته.

يوفر YouTube Data API الرسمي `captions.list` لعرض مسارات captions، لكنه لا يعيد النص الفعلي في الاستجابة. أما `captions.download` فيتطلب صلاحية تعديل الفيديو، لذلك لا نستخدمه لتنزيل captions لفيديوهات الآخرين [4] [5].

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

يجب أن يطلب التكامل من Gemini إخراجًا يتضمن `source_url`, `summary`, `claims`, `experiences`, `counterpoints`, `verification_needed`, `citations`, `limitations`, و`confidence`. يجب إرسال النص المصنف محليًا بدل الاعتماد على URL Context في البداية، لأن اختبارات المشروع السابق أعادت HTTP 403 `permission_denied` من مشروع Gemini الحالي.

يجب أن يحتوي كل claim على رابط المصدر وlabel يوضح هل هو قول للمتحدث أو نص caption أو تعليق مستخدم. إذا لم يقدم Gemini citation، يسجل النظام `citations=[]` ولا يخترع روابط.

## الحصة والأخطاء

| العملية | السلوك المطلوب |
|---|---|
| صفحة بحث إضافية | تُحسب كطلب جديد؛ استخدم `nextPageToken` فقط عند الحاجة |
| `videos.list` | اجمع حتى 50 ID في الطلب الواحد بدل طلب لكل فيديو |
| `commentThreads.list` | حدّد `maxResults` واحفظ `nextPageToken` إذا احتجت المزيد |
| HTTP 400 | صحح parameters أو video ID؛ لا تعِد الطلب بلا تغيير |
| HTTP 403 `quotaExceeded` | أوقف المسار ولا تدوّر المفاتيح لتجاوز الحد |
| HTTP 403 `commentsDisabled` | سجل التعليقات كمعطلة وانتقل إلى metadata وcaption |
| captions missing/disabled | سجل السبب ولا تحاول تجاوز قرار صاحب الفيديو |

## المراجع الرسمية

[1]: https://developers.google.com/youtube/v3/docs/search/list "YouTube Data API search.list"
[2]: https://developers.google.com/youtube/v3/docs/videos/list "YouTube Data API videos.list"
[3]: https://developers.google.com/youtube/v3/docs/commentThreads/list "YouTube Data API commentThreads.list"
[4]: https://developers.google.com/youtube/v3/docs/captions/list "YouTube Data API captions.list"
[5]: https://developers.google.com/youtube/v3/docs/captions/download "YouTube Data API captions.download"
[6]: https://developers.google.com/youtube/v3/determine_quota_cost "YouTube Data API quota costs"

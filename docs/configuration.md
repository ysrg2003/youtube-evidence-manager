# الإعدادات والأسرار

## قاعدة أمنية أساسية

> لا تُحفظ مفاتيح YouTube أو Gemini في Git، ولا في README، ولا في تقارير artifacts، ولا في رسائل السجل. استخدم ملف `.env` محليًا أو GitHub Actions Secrets.

## خريطة القيم

| الاسم | النوع | مطلوب الآن؟ | مكان الاستخدام | مثال آمن |
|---|---|---:|---|---|
| `YOUTUBE_API_KEY` | سر API | نعم لمسار YouTube الرسمي | `.env` محليًا أو Secret في GitHub | `AIzaSy_REPLACE_ME` |
| `GEMINI_API_KEY` | سر API | لا، التكامل غير مفعّل في نقطة البداية | `.env` أو GitHub Secret لاحقًا | `REPLACE_GEMINI_KEY` |
| `YOUTUBE_OUTPUT_DIR` | متغير تشغيل | لا | مستقبلًا في probe | `artifacts/youtube` |
| `YOUTUBE_MAX_RESULTS` | متغير تشغيل | لا | مستقبلًا في probe | `10` |

## إنشاء YouTube API key

1. افتح [Google Cloud Console](https://console.cloud.google.com/) وسجّل الدخول بالحساب الذي سيملك المشروع.
2. اختر مشروعًا موجودًا أو أنشئ مشروعًا جديدًا من قائمة اختيار المشروع.
3. افتح **APIs & Services → Library**، وابحث عن **YouTube Data API v3**، ثم اضغط **Enable**.
4. افتح **APIs & Services → Credentials**، واضغط **Create Credentials → API key**.
5. انسخ المفتاح مرة واحدة إلى مدير أسرارك، ثم قيّده من خيار **Edit API key**. استخدم تقييد API إلى YouTube Data API v3 فقط، وأضف قيود التطبيقات إذا كان مسار الاستخدام يسمح بذلك.
6. للاختبار المحلي، أنشئ ملف `.env` من `.env.example` وضع القيمة فيه:

```text
YOUTUBE_API_KEY=ضع_المفتاح_الحقيقي_محليًا_فقط
```

7. لا تنفذ `git add .env`. يجب أن يمنع `.gitignore` الملف من التتبع؛ تحقق من ذلك عبر:

```bash
git status --short --ignored .env
```

النتيجة المتوقعة أن يظهر `.env` ضمن الملفات المتجاهلة، لا ضمن الملفات المعدلة أو الجديدة.

## تخزين المفتاح في GitHub Actions

1. افتح مستودع [youtube-evidence-manager](https://github.com/ysrg2003/youtube-evidence-manager).
2. افتح **Settings → Secrets and variables → Actions**.
3. اضغط **New repository secret**.
4. اكتب الاسم بالضبط: `YOUTUBE_API_KEY`.
5. ألصق قيمة المفتاح في حقل Secret، ثم اضغط **Add secret**.
6. لا تضع المفتاح في قسم Variables؛ هذا القسم ليس مكانًا مناسبًا لقيمة سرية.

لا يُستخدم السر في Workflow إلا بهذا الشكل:

```yaml
env:
  YOUTUBE_API_KEY: ${{ secrets.YOUTUBE_API_KEY }}
```

لا تطبع المتغير، ولا تستخدم `set -x`، ولا تضعه في query string داخل artifact أو تقرير.

## فحص صحي لاحق

عند إضافة عميل API، يجب أن يكون الفحص الصحي محدودًا ويعيد حالة مختصرة فقط، مثل `ok`, `quota_exceeded`, أو `invalid_key`. يجب ألا يعرض الاستجابة الكاملة إذا كانت تحتوي على بيانات لا نحتاجها.

## التدوير والإلغاء

إذا ظهر المفتاح في commit أو سجل أو شاشة، اعتبره مكشوفًا فورًا. افتح **Google Cloud Console → APIs & Services → Credentials**، احذف المفتاح المكشوف أو دوّره، أنشئ قيمة جديدة، ثم حدّث `.env` المحلي وGitHub Secret. بعد ذلك ابحث في المستودع وسجل Git عن اسم المفتاح أو بدايته، لكن لا تنسخ قيمة المفتاح إلى تقرير.

## Gemini

`GEMINI_API_KEY` موثق فقط لتكامل لاحق. لا تضفه قبل أن يكون مشروع Gemini مصرحًا له، لأن اختبارات المشروع السابق أعادت HTTP 403 `permission_denied`. عند تفعيله، يجب توثيق النموذج، endpoint، حدود الحصة، ومخرجات redaction في ملف تكامل منفصل.

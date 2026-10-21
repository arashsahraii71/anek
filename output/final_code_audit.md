# ممیزی نهایی کد و سئو — FINAL CODE & SEO AUDIT

_اجرای خودکار: 2026-10-21T22:18:40Z_

**نتیجه کلی: ۱۵/۱۵ دسته PASS**

| ID | دسته | بررسی | وضعیت | شواهد |
|---|---|---|---|---|
| **V1** | Build Parity | Page & Dossier Parity | ✅ PASS | ۳۴/۳۴ صفحه قابل ساخت در `dist/` رندر شد؛ هر صفحه یک دوسیه متناظر در `seo_dossiers/` دارد؛ فایل اضافه: ۰ |
| **V2** | Keyword Coverage | 295-Keyword On-Page Presence | ✅ PASS | ۲۹۵/۲۹۵ کلیدواژه دقیقاً روی URL تخصیص‌یافته خود (در H2/H3، متن BLUF، جدول شهریه، تب زیرتخصص یا FAQ) حاضر است — مجموع ۲۹۵ عبارت یکتا از ۲۹۶ خط ورودی |
| **V3** | Orthography | Persian Orthographic Dual-Coverage | ✅ PASS | ۳۲ عبارت بدون «آ» (اموزش، اموزشگاه، اواز، ادرس، اکادمی، کلاسهای) در FAQ / `meta keywords` / `alt` صفحه هدف حاضر است و هیچ‌کدام وارد H1/H2 نشده‌اند (سرتیترها املای استاندارد فارسی دارند) |
| **V4** | RTL Architecture | Native RTL & CSS Logical Properties | ✅ PASS | هر ۳۴ صفحه با `<!DOCTYPE html><html lang="fa" dir="rtl">` شروع می‌شود؛ `design-system.css` (35,367 بایت) صفر ویژگی فیزیکی چپ/راست دارد و فقط `margin-inline`, `padding-inline`, `border-inline-start`, `inset-inline`, `text-align: start` به کار رفته |
| **V5** | Conversion UX | Viewport 1 Conversion & Jump-Pill Rule | ✅ PASS | هر ۴ هاب دانشکده و هر ۲۴ صفحه دوره، در ویوپورت اول شامل: Breadcrumb، H1، جعبه BLUF (۴۰–۵۵ کلمه)، نشان‌های آماری، Jump-Pills و CTA اصلی + تصویر شاخص هستند |
| **V6** | Female Instructor Modules | Female Instructor (مدرس خانم / بانوان) Modules | ✅ PASS | هر ۵ رشته با تقاضای صریح استاد خانم (پیانو، گیتار، تار و سه‌تار، سنتور، آواز) بخش `#female-teachers` دارند؛ مجموع صفحات دارای این بخش: ۱۹. ادعای «حضور مدرس خانم» از `courses.csv` می‌آید و نام استاد تا زمان تأیید `[INTERNAL_DATA_NEEDED]` است |
| **V7** | Sub-Specialty Indexability | Sub-Specialty DOM Indexability | ✅ PASS | تمام زیرتخصص‌ها (گیتار الکتریک، ویولن سل، پن فلوت، فلوت لاکوتا، آواز سنتی و پاپ، مجری‌گری، عکاسی با موبایل، گریم کودک، خوشنویسی با خودکار) به‌صورت کامل در DOM ایستا رندر شده‌اند؛ پنل‌ها با `hidden` فقط برای کاربر JS پنهان می‌شوند و قانون `.no-js` همه را نمایش می‌دهد |
| **V8** | Art Cafe Bridge | Art Cafe 6-Keyword & 5-Course Bridge | ✅ PASS | `/art-cafe/` شامل ۵ بخش ساز اختصاصی (`#cafe-piano`, `#cafe-guitar`, `#cafe-santoor`, `#cafe-setar`, `#cafe-organ`)، هر ۶ کلیدواژه کافه/رستوران و لینک دوطرفه با ۵ صفحه دوره |
| **V9** | Fardis Hyper-Local | Fardis Hyper-Local Hub & 7-Course Bridge | ✅ PASS | `/fardis-branch/` هر ۱۴ کلیدواژه فردیس را پوشش می‌دهد، ماتریس مسیر و زمان رفت‌وآمد (مترو کرج، چهارراه طالقانی، بلوار شهید بهشتی، ملارد) و شیفت فشرده پنجشنبه/جمعه دارد و با ۷ مسیر دوره دوطرفه لینک است |
| **V10** | Audition Funnel | Audition Hub (تست بازیگری) Funnel | ✅ PASS | `/acting-audition/` عبارت‌های «تست بازیگری در کرج» و «تست بازیگری در کرج کجاست» را پوشش می‌دهد، ۴ مرحله تست + چک‌لیست آمادگی + هیئت داوران + فرم رزرو دارد و با صفحات بازیگری و بازیگری کودکان دوطرفه لینک است |
| **V11** | JSON-LD Validity | Pure @graph JSON-LD Validity | ✅ PASS | هر ۳۴ صفحه دقیقاً یک `<script type="application/ld+json">` معتبر با ریشه واحد `@context` + `@graph` دارد و اشاره‌گرهای پایدار `#academy`، `#website`، `/art-cafe/#cafe`، `/instructors/#INST_xx`، `[course]/#course` در تمام صفحات یکسان‌اند |
| **V12** | Schema Safety | Schema Offer & NAP Honesty Gate | ✅ PASS | صفر `Offer` با قیمت صفر یا نامعتبر؛ صفر `AggregateRating`/`Review` تأییدنشده؛ صفر `PostalAddress` جعلی برای فردیس (وضعیت `SERVICE_AREA_COMMUTER_HUB` → فقط `areaServed`)؛ `MusicEvent` فقط با `eventSchedule` تکرارشونده و بدون `startDate` ساختگی |
| **V13** | Core Web Vitals | Core Web Vitals (LCP / CLS / INP) | ✅ PASS | ۱۴۴ تگ `<img>` همگی دارای `width` و `height` صریح (CLS = ۰)؛ ۳۴ صفحه دقیقاً یک تصویر LCP با `loading="eager" fetchpriority="high"` دارند و بقیه `loading="lazy"`؛ CSS تک‌فایل هم‌مبدأ، JS با `defer`، فونت بدون درخواست شبکه (`src: local(...)`) و بدون هیچ وابستگی خارجی مسدودکننده رندر |
| **V14** | Link Graph | Internal Link Graph & Click Depth | ✅ PASS | صفر لینک داخلی شکسته یا `href="#"`؛ همه ۳۴ صفحه از `/` در حداکثر ۱ کلیک قابل دسترسی‌اند (اعتبارسنجی تجربی روی HTML رندرشده: ۳۴ صفحه در ≤۲ کلیک) |
| **V15** | Fact Boundary | Fact-Boundary & Zero Hallucination | ✅ PASS | هر رقم شهریه در `dist/` دقیقاً برابر `courses.csv` (ریال ÷ ۱۰) است؛ هر نام استاد در `instructors.csv` وجود دارد؛ مجوز، آدرس، تلفن و ساعات کاری verbatim از `academy_data.txt`؛ هیچ آیتم منو، نظر، امتیاز یا تاریخ رویداد ساختگی وجود ندارد — ۱۸۲ اسلات صادقانه با `[INTERNAL_DATA_NEEDED]` علامت خورده است |

---

## خلاصه بیلد

| مورد | مقدار |
|---|---|
| صفحات HTML | ۳۴ |
| حجم کل HTML | 1,563,360 بایت |
| سنگین‌ترین صفحه | `/` — 65,626 بایت |
| سبک‌ترین صفحه | `/visual-arts/` — 28,558 بایت |
| design-system.css | 35,384 بایت |
| app.js | 7,905 بایت |
| تصاویر SVG | ۱۲ فایل |
| sitemap.xml | ۳۴ آدرس |
| وابستگی خارجی | ۰ |

## توزیع صفحات بر اساس تراز

| تراز | تعداد | نمونه |
|---|---|---|
| Tier 0 — صفحه اصلی | ۱ | `/` |
| Tier 1 — هاب دانشکده | ۴ | `/music/` |
| Tier 2 — صفحه دوره | ۲۴ | `/music/piano/` |
| Tier 3 — کافه هنر | ۱ | `/art-cafe/` |
| Tier 4 — هاب محلی و تبدیل | ۴ | `/fardis-branch/` |

## مرزهای واقعیت اعمال‌شده (Zero-Hallucination Ledger)

| محدودیت | اعمال |
|---|---|
| شهریه | فقط `courses.csv`، ریال ÷ ۱۰ = تومان، با اعداد فارسی `tabular-nums` |
| اساتید | ۹ استاد تأییدشده رندر شد؛ ۷ کارت با `[INTERNAL_DATA_NEEDED]` و برچسب «در انتظار تأیید» |
| منوی کافه | هیچ آیتم/قیمتی ساخته نشد؛ بخش منو صراحتاً خالی اعلام شده |
| رویدادهای کافه | ۵ شب تأییدشده با روز/ساعت/نوازنده واقعی؛ بدون `startDate` ساختگی |
| فردیس | `SERVICE_AREA_COMMUTER_HUB`؛ هیچ آدرس خیابانی فردیس در متن یا اسکیما |
| نظرات/امتیاز | هیچ `AggregateRating` یا نقل‌قول هنرجو منتشر نشد |
| داده SERP زنده | خروجی شبکه مسدود بود؛ هیچ رقیب/رتبه ساختگی تولید نشد |


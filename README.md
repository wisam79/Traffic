# نظام عد المركبات الذكي - تقاطعات المرور
# Enterprise Smart Intersection Vehicle Counting System

تطبيق سطح مكتب احترافي لكشف وتتبع وعد المركبات في الزمن الحقيقي باستخدام YOLO26n و PySide6.

## 📁 هيكل المشروع

```
traffic/
│
├── main.py                          # نقطة الدخول الرئيسية (بسيط جداً)
├── requirements.txt                 # المكتبات المطلوبة
├── README.md                        # هذا الملف
├── .gitignore                       # ملفات Git
│
├── core/                            # ═══ الإعدادات الأساسية ═══
│   ├── __init__.py
│   ├── config.py                    # جميع الثوابت والإعدادات
│   └── app.py                       # إعداد التطبيق الرئيسي
│
├── engine/                          # ═══ محرك الذكاء الاصطناعي ═══
│   ├── __init__.py
│   ├── ai_thread.py                 # خيط المعالجة الرئيسي (QThread)
│   ├── preprocessor.py              # معالجة الإطارات المسبقة
│   ├── detector.py                  # كشف الكائنات بـ ONNX
│   └── tracker.py                   # التتبع وخط العد
│
├── ui/                              # ═══ واجهة المستخدم ═══
│   ├── __init__.py
│   ├── main_window.py               # النافذة الرئيسية
│   ├── video_panel.py               # لوحة عرض الفيديو
│   ├── video_player.py              # مشغل الفيديو (تكبير/تحريك)
│   ├── video_controllers.py         # متحكمات الفيديو والتسجيل
│   ├── video_source_manager.py      # إدارة مصادر الفيديو
│   ├── video_info_display.py        # عرض معلومات الفيديو
│   ├── drawing_modes.py             # أوضاع رسم الخطوط المتقدمة
│   ├── line_manager.py              # ويدجت إدارة الخطوط
│   ├── control_panel.py             # لوحة التحكم والإحصائيات
│   ├── styles.py                    # أنماط CSS متوافقة
│   └── themes.py                    # نظام الثيمات الاحترافي
│
├── video/                           # ═══ معالجة الفيديو ═══
│   ├── __init__.py
│   └── ingestor.py                  # التقاط الفيديو
│
├── state/                           # ═══ إدارة الحالة ═══
│   ├── __init__.py
│   └── app_state.py                 # الحالة المشتركة الآمنة
│
├── models/
│   └── yolo26n.onnx                 # نموذج YOLO للكشف
│
├── docs/                            # ═══ التوثيق ═══
│   ├── improvement_plan.md          # خطة التحسين
│   └── line_drawing_guide.md        # دليل رسم الخطوط
│
├── tests/                           # ═══ الاختبارات ═══
│   ├── conftest.py                  # إعدادات الاختبارات المشتركة
│   ├── test_detector.py             # اختبارات الكاشف
│   ├── test_preprocessor.py          # اختبارات المعالج المسبق
│   ├── test_tracker.py              # اختبارات المتتبع
│   ├── test_drawing_modes.py        # اختبارات أدوات الرسم
│   ├── test_video_controllers.py    # اختبارات متحكمات الفيديو
│   ├── test_pipeline_integration.py # اختبارات التكامل
│   └── test_user_journey.py         # اختبار رحلة المستخدم
│
└── recordings/                      # ═══ التسجيلات ═══
    └── (ملفات التسجيل والصور الملتقطة)
```

## 🎯 مميزات المشروع المُعاد هيكلة

### ✓ فصل المسؤوليات
- **core/**: إعدادات عامة فقط
- **engine/**: معالجة الذكاء الاصطناعي فقط
- **ui/**: واجهة المستخدم فقط
- **video/**: التقاط الفيديو فقط
- **state/**: إدارة الحالة فقط

### ✓ تعليقات عربية تفصيلية
- كل دالة موثقة بالعربية والإنجليزية
- شرح المعاملات والمراجع
- توضيح العلاقات بين المكونات

### ✓ سهولة التعديل
- تعديل الإعدادات في `core/config.py` فقط
- كل مكون مستقل قابل للاستبدال
- اختبار فردي سهل

## 🚀 الاستخدام

### التثبيت

```bash
pip install -r requirements.txt
```

### التشغيل

```bash
python main.py
```

### كيفية الاستخدام

1. **اختيار مصدر الفيديو**: أدخل رقم الكاميرا أو تصفح لملف فيديو
2. **بدء البث**: انقر "بدء البث"
3. **رسم خط العد**: انقر مرتين على الفيديو
4. **مشاهدة النتائج**: العدادات تتحدث في الزمن الحقيقي

## 🏗️ البنية التقنية

### تدفق البيانات

```
مصدر الفيديو
    ↓
VideoIngestor (خيط منفصل)
    ↓ raw_frame_queue
AIEngineThread (خيط منفصل)
    ↓ Signals
MainWindow (خيط الواجهة)
    ↓
VideoPanel + ControlPanel
```

### التواصل بين الخيوط

- **VideoIngestor → AIEngine**: عبر `queue.Queue`
- **AIEngine → UI**: عبر PySide6 `Signal/Slot`
- **UI → AIEngine**: عبر `Slot` methods

## 📝 توثيق الملفات الرئيسية

### core/config.py
جميع الإعدادات والثوابت. عدّل هنا لتغيير:
- عتبات الكشف
- فئات المركبات
- إعدادات الواجهة
- الألوان والأحجام

### engine/ai_thread.py
خيط المعالجة الرئيسي. يربط جميع مكونات engine:
1. يسحب إطار من الطابور
2. يُعالج مسبقاً (preprocessor)
3. يكشف (detector)
4. يتتبع (tracker)
5. يعد (line_zone)
6. يرسم
7. يُرسل للواجهة

### ui/main_window.py
النافذة الرئيسية. تربط:
- VideoPanel (الفيديو)
- ControlPanel (التحكم)
- AIEngine (المعالجة)

### state/app_state.py
إدارة الحالة المشتركة الآمنة:
- إحداثيات الخط
- حالة البث
- الإحصائيات

## 🔧 التخصيص

### إضافة فئة مركبة جديدة

عدل `core/config.py`:
```python
VEHICLE_CLASSES = {
    2: "car",
    3: "motorcycle",
    5: "bus",
    7: "truck",
    9: "new_vehicle"  # أضف هنا
}
```

### تغيير عتبة الثقة

عدل `core/config.py`:
```python
CONFIDENCE_THRESHOLD = 0.6  # من 0.5 إلى 0.6
```

### تغيير الألوان

عدل `core/config.py`:
```python
COLORS = {
    "accent_green": "#4CAF50",
    # عدّل الألوان هنا
}
```

## 📊 الأداء

- **GPU**: CUDA متاح → أداء عالي
- **CPU**: بديل تلقائي إذا لم يتوفر GPU
- **FPS**: يعتمد على الجهاز، عادةً 15-30 FPS

## 🐛 حل المشاكل

### "Model not found"
تأكد من وجود `models/yolo26n.onnx`

### "Failed to start video"
- تحقق من مصدر الفيديو
- تأكد من وجود الكاميرا أو الملف

### بطء الأداء
- ثبّت `onnxruntime-gpu` بدلاً من `onnxruntime`
- قلل حجم الفيديو
- زد عتبة الثقة

## 📞 الدعم

لأي مشاكل أو استفسارات، راجع التعليقات في الكود أو افتح issue.

---

**الإصدار**: 2.0  
**التاريخ**: ٢٠٢٦  
**التقنيات**: PySide6, ONNX, OpenCV, Supervision

import re

with open('index.html', 'r', encoding='utf-8') as f:
    html = f.read()

css_addition = """
        .main-layout {
            display: flex;
            gap: 24px;
            width: 100%;
            align-items: flex-start;
        }
        .steps-frame {
            width: 319px;
            flex-shrink: 0;
            background-color: #f1f6fb;
            border-radius: 8px;
            padding: 24px 16px;
            display: flex;
            flex-direction: column;
            gap: 16px;
            box-shadow: 0 1px 2px 0 rgba(16, 24, 40, 0.04);
            direction: rtl;
        }
        .steps-title {
            font-size: 16px;
            font-weight: 700;
            color: #040404;
            margin-bottom: 8px;
            text-align: right;
        }
        .form-group {
            display: flex;
            flex-direction: column;
            gap: 8px;
        }
        .form-label {
            font-size: 14px;
            font-weight: 600;
            color: #040404;
        }
        .form-select, .form-textarea {
            width: 100%;
            border: 1px solid #d2d6db;
            border-radius: 8px;
            padding: 8px 12px;
            font-size: 14px;
            font-family: inherit;
            background-color: #ffffff;
            outline: none;
            color: #040404;
        }
        .form-select {
            appearance: none;
            background-image: url("data:image/svg+xml,%3Csvg width='12' height='8' viewBox='0 0 12 8' fill='none' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M1 1.5L6 6.5L11 1.5' stroke='%235A5A5A' stroke-width='1.5' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E");
            background-repeat: no-repeat;
            background-position: left 12px center;
        }
        .form-textarea {
            resize: vertical;
            min-height: 80px;
        }
        .form-hint {
            font-size: 12px;
            color: #5a5a5a;
            line-height: 1.4;
        }
        .add-btn {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 4px;
            width: 100%;
            height: 38px;
            background-color: #ffffff;
            border: 1px solid #d2d6db;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 700;
            color: #040404;
            cursor: pointer;
            margin-top: auto;
        }
"""

html = html.replace('        .blueprint-container {', css_addition + '        .blueprint-container {')

steps_html = """
    <div class="main-layout">
        <!-- Steps Frame -->
        <div class="steps-frame">
            <div class="steps-title">إدراج الخطوات</div>
            
            <div class="form-group">
                <div class="form-label">الطبقة أو المسار (Layer / Tier)</div>
                <select class="form-select">
                    <option value="" disabled selected hidden>القائمة</option>
                </select>
            </div>
            
            <div class="form-group">
                <div class="form-label">اسم المرحلة (Step / Action Title)</div>
                <select class="form-select">
                    <option value="" disabled selected hidden>إدراج أو اختيار</option>
                </select>
                <div class="form-hint">كتابة اسم الخطوة باختصار (مثلاً: "تصفح القائمة"، "إتمام الدفع").</div>
            </div>
            
            <div class="form-group">
                <div class="form-label">الأدلة المادية</div>
                <select class="form-select">
                    <option value="" disabled selected hidden>إدراج أو اختيار</option>
                </select>
                <div class="form-hint">تحديد الأجهزة أو المستندات المستخدمة في الورقية، موقع الويب، جهاز الدفع POS).</div>
            </div>
            
            <div class="form-group">
                <div class="form-label">وصف النشاط أو العملية (Activity Description)</div>
                <textarea class="form-textarea" placeholder="الوصف هنا"></textarea>
                <div class="form-hint">شرح تفصيلي لما يحدث في هذه الخطوة خلف الكواليس أو من قبل الشخصية.</div>
            </div>
            
            <div class="form-group">
                <div class="form-label">النقاط الحرجة أو المشاكل (/ Pain Points Bottlenecks)</div>
                <textarea class="form-textarea" placeholder="الوصف هنا"></textarea>
                <div class="form-hint">تحديد ما إذا كان هناك تأخير أو مشكلة محتملة في هذه الخطوة (يتم تلوينها تلقائياً باللون الأحمر في المخطط كـ Alert).</div>
            </div>
            
            <button class="add-btn">
                <span>إضافة</span>
                <span>+</span>
            </button>
        </div>
"""

html = html.replace('<body>\n    <div class="blueprint-container">', '<body>\n' + steps_html + '\n        <div class="blueprint-container">')
html = html.replace('</body>', '    </div>\n</body>')

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html)

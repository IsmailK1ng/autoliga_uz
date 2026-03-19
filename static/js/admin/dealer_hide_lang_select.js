(function() {
    'use strict';

    function hideLangSelectors() {
        // Tarjima bo'lmagan maydon IDlari
        var nonTransIds = ['id_latitude', 'id_longitude', 'id_instagram',
            'id_telegram', 'id_facebook', 'id_youtube', 'id_is_active', 'id_order'];

        // Har bir tarjima bo'lmagan maydonning ota konteynerini topib,
        // undagi til selectlarini yashirish
        nonTransIds.forEach(function(fieldId) {
            var field = document.getElementById(fieldId);
            if (!field) return;

            // Eng yaqin fieldset, tab-pane yoki module ni topish
            var container = field.closest('.tab-pane') || field.closest('fieldset') || field.closest('.module');
            if (!container) return;

            // Bu konteyner ichidagi barcha selectlarni tekshirish
            var selects = container.querySelectorAll('select');
            selects.forEach(function(sel) {
                // Maydon selektlarini o'tkazib yuborish (name atributi bor)
                if (sel.name) return;

                // modeltranslation-switch classli yoki uz/ru/en optionli selectlar
                if (sel.classList.contains('modeltranslation-switch')) {
                    sel.style.display = 'none';
                    return;
                }

                var options = sel.querySelectorAll('option');
                var hasLang = false;
                options.forEach(function(o) {
                    var t = (o.textContent || '').trim().toLowerCase();
                    if (t === 'uz' || t === 'ru' || t === 'en') hasLang = true;
                });
                if (hasLang) {
                    sel.style.display = 'none';
                }
            });
        });
    }

    // Turli vaqtlarda ishga tushirish
    var timers = [100, 300, 600, 1000, 2000];
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            timers.forEach(function(t) { setTimeout(hideLangSelectors, t); });
        });
    } else {
        timers.forEach(function(t) { setTimeout(hideLangSelectors, t); });
    }
    window.addEventListener('load', function() {
        timers.forEach(function(t) { setTimeout(hideLangSelectors, t); });
    });
})();

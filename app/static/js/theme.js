(() => {
    'use strict';

    const storageKey = 'currencycheck-theme';
    const root = document.documentElement;
    const media = window.matchMedia('(prefers-color-scheme: dark)');
    const choices = new Set(['system', 'light', 'dark']);
    let preference = 'system';

    try {
        const saved = window.localStorage.getItem(storageKey);
        if (choices.has(saved)) preference = saved;
    } catch (_) {
        // Theme selection remains usable when storage is unavailable.
    }

    function applyTheme() {
        root.dataset.theme = preference === 'system'
            ? (media.matches ? 'dark' : 'light') : preference;
        root.dataset.themePreference = preference;
    }

    applyTheme();
    const onSystemChange = () => {
        if (preference === 'system') applyTheme();
    };
    if (media.addEventListener) media.addEventListener('change', onSystemChange);
    else media.addListener(onSystemChange);

    document.addEventListener('DOMContentLoaded', () => {
        document.querySelectorAll('[data-theme-select]').forEach(select => {
            select.value = preference;
            select.addEventListener('change', () => {
                if (!choices.has(select.value)) return;
                preference = select.value;
                applyTheme();
                try {
                    window.localStorage.setItem(storageKey, preference);
                } catch (_) {
                    // Keep the current in-memory preference.
                }
            });
        });
    });
})();

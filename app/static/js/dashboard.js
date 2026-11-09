(() => {
    'use strict';

    const messageElement = document.getElementById('client-messages');
    if (!messageElement) return;
    const messages = JSON.parse(messageElement.textContent);
    const locale = document.documentElement.lang || 'ru';

    document.querySelectorAll('[data-source][data-url]').forEach(section => {
        const search = section.querySelector('[data-search]');
        const refresh = section.querySelector('[data-refresh]');
        const status = section.querySelector('[data-status]');
        const content = section.querySelector('[data-content]');
        const count = section.querySelector('[data-count]');
        const noResults = section.querySelector('[data-no-results]');
        let pending = false;
        let loaded = false;

        function filterRows() {
            const query = search.value.trim().toLocaleLowerCase(locale);
            const rows = [...content.querySelectorAll('[data-bank-name]')];
            let visible = 0;
            rows.forEach(row => {
                row.hidden = !row.dataset.bankName.toLocaleLowerCase(locale).includes(query);
                if (!row.hidden) visible += 1;
            });
            count.textContent = messages.count
                .replace('{visible}', String(visible))
                .replace('{total}', String(rows.length));
            noResults.hidden = !loaded || rows.length === 0 || visible > 0;
        }

        function showError() {
            status.classList.toggle('is-warning', loaded);
            status.classList.toggle('is-error', !loaded);
            status.textContent = loaded ? messages.refresh_error : messages.load_error;
            const retry = document.createElement('button');
            retry.type = 'button';
            retry.className = 'retry-button';
            retry.textContent = messages.retry;
            retry.addEventListener('click', load);
            status.append(' ', retry);
        }

        async function load() {
            if (pending) return;
            pending = true;
            refresh.disabled = true;
            section.dataset.state = loaded ? 'refreshing' : 'loading';
            content.setAttribute('aria-busy', 'true');
            status.classList.remove('is-warning', 'is-error');
            status.textContent = loaded ? messages.refreshing : messages.loading;
            const controller = new AbortController();
            const timeout = window.setTimeout(() => controller.abort(), 45000);
            try {
                const response = await fetch(section.dataset.url, {
                    credentials: 'same-origin',
                    headers: {'Accept': 'text/html'},
                    signal: controller.signal,
                });
                if (!response.ok) throw new Error('Source request failed');
                // Only successful, same-origin HTML fragments enter the document.
                content.innerHTML = await response.text();
                loaded = true;
                section.dataset.state = 'ready';
                status.textContent = content.querySelector('[data-bank-name]') ? '' : messages.empty;
                filterRows();
            } catch (_) {
                section.dataset.state = loaded ? 'stale' : 'error';
                showError();
            } finally {
                window.clearTimeout(timeout);
                pending = false;
                refresh.disabled = false;
                content.setAttribute('aria-busy', 'false');
            }
        }

        search.addEventListener('input', filterRows);
        refresh.addEventListener('click', load);
        load();
    });
})();

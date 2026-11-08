// Helpers for putting text and model-written markdown into the page safely.
(function () {
    const ENTITIES = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' };

    // Escape a value before interpolating it into an HTML string.
    function escapeHtml(value) {
        return String(value ?? '').replace(/[&<>"']/g, (ch) => ENTITIES[ch]);
    }

    // Render markdown to sanitised HTML. Falls back to escaped text if a library is missing.
    function renderMarkdown(markdown) {
        if (!window.marked || !window.DOMPurify) return escapeHtml(markdown).replace(/\n/g, '<br>');
        return window.DOMPurify.sanitize(window.marked.parse(markdown || ''));
    }

    // Turn an API error response into a message for the user.
    function apiErrorMessage(status, data, fallback) {
        if (status === 401 && !(data && data.detail === 'Incorrect username or password.')) {
            return 'Please log in to use this feature.';
        }
        if (data && typeof data.detail === 'string') return data.detail;
        if (data && Array.isArray(data.detail) && data.detail[0] && data.detail[0].msg) {
            const field = data.detail[0].loc ? data.detail[0].loc[data.detail[0].loc.length - 1] : '';
            const message = data.detail[0].msg.replace(/^Value error, /, '');
            return field ? `${field}: ${message}` : message;
        }
        if (status === 429) return 'You are sending requests too quickly. Please wait a minute and try again.';
        return fallback;
    }

    window.escapeHtml = escapeHtml;
    window.renderMarkdown = renderMarkdown;
    window.apiErrorMessage = apiErrorMessage;
    window.DEFAULT_IMAGE = '/images/default_paper.jpg';
})();

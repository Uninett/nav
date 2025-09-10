define([], function () {
    "use strict";

    function init() {
        // Prevent double initialization
        if (document.body.dataset.alertInitialized) return;
        document.body.dataset.alertInitialized = "true";

        // Target clicks specifically within alert boxes
        document.addEventListener('click', function (e) {
            const alertBox = e.target.closest('[data-nav-alert]');
            if (!alertBox) return;

            // Handle close buttons
            if (e.target.closest('.close')) {
                e.preventDefault();
                e.stopPropagation();
                closeAlert(alertBox);
            }
        });
    }

    function closeAlert(alertBox) {
        if (!alertBox) return;

        alertBox.classList.add('alert-close');

        const handleTransitionEnd = function (e) {
            if (e.target === alertBox) {
                alertBox.removeEventListener('transitionend', handleTransitionEnd);
                alertBox.remove();
            }
        };

        alertBox.addEventListener('transitionend', handleTransitionEnd);
    }

    // Auto-initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    return {
        init: init,
        close: closeAlert,
    };
});

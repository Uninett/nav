require([], function () {

    function init() {
        document.querySelectorAll('.nav-tooltip [role="tooltip"]').forEach(tooltip => {
        setTimeout(() => {
            const vw = window.innerWidth;

            // Reverse alignment if element is out of viewport
            let rect = tooltip.getBoundingClientRect();
            if (rect.right > vw) {
                tooltip.parentElement.setAttribute('data-align', 'end');
            } else if (rect.left < 0) {
                tooltip.parentElement.setAttribute('data-align', 'start');
            }

            // Reduce max width if element is out of viewport
            rect = tooltip.getBoundingClientRect();
            if (rect.right > vw) {
                tooltip.style.maxWidth = (vw - rect.left - 16) + 'px';
            } else if (rect.left < 0) {
                tooltip.style.maxWidth = (rect.right - 16) + 'px';
            } else {
                tooltip.style.maxWidth = '';
            }
        }, 100);
        });
    }

    init();
});

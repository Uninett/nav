require([], function () {
    const MARGIN = 16;
    const DEFAULT_TOOLTIP_HEIGHT = 40;

    function initializeTooltips(container = document) {
        const tooltips = container.querySelectorAll(
            '.nav-tooltip [role="tooltip"]:not([data-initialized])'
        );
        for (const tooltip of tooltips) {
            if (!tooltip.parentElement) continue;
            if (tooltip.parentElement.dataset.position === 'fixed') {
                initializeFixedTooltip(tooltip);
            } else {
                adjustTooltipAlignment(tooltip);
            }
            tooltip.dataset.initialized = 'true';
        }
    }


    function adjustTooltipAlignment(tooltip) {
        const vw = window.innerWidth;
        const vh = window.innerHeight;
        const parent = tooltip.parentElement;
        const rect = tooltip.getBoundingClientRect();

        if (rect.right > vw) {
            parent.dataset.align = 'end';
            tooltip.style.maxWidth = (vw - rect.left - MARGIN) + 'px';
        } else if (rect.left < 0) {
            parent.dataset.align = 'start';
            tooltip.style.maxWidth = (rect.right - MARGIN) + 'px';
        } else {
            tooltip.style.maxWidth = '';
        }

        if (rect.bottom > vh) {
            parent.dataset.side = 'top';
        } else {
            parent.dataset.side = 'bottom';
        }
    }

    function initializeFixedTooltip(tooltip) {
        const parent = tooltip.parentElement;
        const positionHandler = () => positionTooltip(tooltip);
        parent.addEventListener('mouseenter', positionHandler);

        // Store observer for potential cleanup
        const observer = new MutationObserver(positionHandler);
        observer.observe(tooltip, { childList: true, subtree: true, characterData: true });
        tooltip._observer = observer;
    }

    function positionTooltip(tooltip) {
        const parent = tooltip.parentElement;
        if (!parent || parent.dataset.position !== 'fixed') return;

        const rect = parent.getBoundingClientRect();
        const tooltipHeight = tooltip.offsetHeight || DEFAULT_TOOLTIP_HEIGHT;

        let top;
        if (rect.bottom + tooltipHeight > window.innerHeight) {
            top = Math.max(rect.top - tooltipHeight, 0);
            parent.dataset.side = "top";
        } else {
            top = rect.bottom;
            parent.dataset.side = "bottom";
        }
        tooltip.style.top = `${top}px`;

        if (parent.dataset.align === 'end') {
            tooltip.style.right = `${window.innerWidth - rect.right}px`;
            tooltip.style.left = '';
        } else {
            tooltip.style.left = `${Math.max(rect.left, 0)}px`;
            tooltip.style.right = '';
        }
    }

    // Delay so tooltips have time to render their content
    globalThis.initializeTooltips = initializeTooltips;
    setTimeout(() => initializeTooltips(), 100)
});

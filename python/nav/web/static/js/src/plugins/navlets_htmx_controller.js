/**
 * Navlets HTMX Controller
 *
 * Manages the interactive dashboard widget system with drag-and-drop functionality,
 * HTMX integration, and dynamic widget lifecycle management.
 *
 * Features:
 * - Sortable widget columns with drag-and-drop reordering
 * - HTMX event handling for dynamic content updates
 * - Automatic widget initialization and cleanup
 * - Order persistence to backend via AJAX
 * - Visual feedback for user interactions
 */
define([
    'plugins/navlet_handlers'
], function (NavletHandlers) {

    const NAVLETS_CONTAINER_ID = 'navlets-htmx';

    const CSS_CLASSES = {
        NAVLET: 'navlet',
        OUTLINE: 'outline',
        MARK_NEW: 'mark-new',
    };

    const SELECTORS = {
        NAVLET: '.navlet',
        SORTER: '.navletColumn',
        DRAG_HANDLE: '.navlet-drag-button',
        CSRF_TOKEN: '#navlets-action-form input[name="csrfmiddlewaretoken"]',
        NO_WIDGETS_MESSAGE: '#no-widgets-message'
    };

    const EVENTS = {
        HTMX_AFTER_SWAP: 'htmx:afterSwap',
        NAVLET_ADDED: 'nav.navlet.added',
        NAVLET_REMOVED: 'nav.navlet.removed'
    };

    function NavletsHtmxController() {
        this.container = $('#' + NAVLETS_CONTAINER_ID);
        if (this.container.length === 0) {
            console.warn(`Container with ID '${NAVLETS_CONTAINER_ID}' not found`);
            return;
        }
        this.save_ordering_url = this.container.attr('data-save-order-url');
        this.initSortable();
        this.initializeExistingNavlets();
    }

    NavletsHtmxController.prototype = {
        initSortable: function () {
            const $sorterSelectors = this.container.find(SELECTORS.SORTER);
            if ($sorterSelectors.length === 0) {
                return;
            }
            $sorterSelectors.sortable({
                connectWith: SELECTORS.SORTER,
                forcePlaceholderSize: true,
                handle: SELECTORS.DRAG_HANDLE,
                placeholder: 'highlight',
                tolerance: 'pointer',
                start: () => this.toggleNavletOutline(true),
                stop: () => this.toggleNavletOutline(false),
                update: () => this.updateOrder()
            });
        },

        toggleNavletOutline: function (show) {
            this.getNavlets().toggleClass(CSS_CLASSES.OUTLINE, show);
        },

        updateOrder: function () {
            const ordering = this.findOrder();
            this.saveOrder(ordering);
        },

        findOrder: function () {
            return this.container.find(SELECTORS.SORTER).toArray().map((column) => {
                const columnNavlets = {};
                this.getNavlets(column).each((idx, navlet) => {
                    const navletId = $(navlet).attr('data-id');
                    if (navletId) {
                        columnNavlets[navletId] = idx;
                    }
                });
                return columnNavlets;
            });
        },

        saveOrder: function (ordering) {
            const csrfToken = $(SELECTORS.CSRF_TOKEN).val();
            if (!csrfToken) {
                console.error('CSRF token not found');
                return;
            }

            $.ajax({
                url: this.save_ordering_url,
                type: 'POST',
                data: JSON.stringify(ordering),
                contentType: 'application/json',
                headers: {
                    'X-CSRFToken': csrfToken
                }
            }).fail(function (xhr, status, error) {
                console.error('Failed to save widget order:', error);
            });
        },

        getNavlets: function (column) {
            return column ? $(column).find(SELECTORS.NAVLET) : this.container.find(SELECTORS.NAVLET);
        },

        isNavlet: function (node) {
            return node?.dataset?.id && node.classList.contains(CSS_CLASSES.NAVLET);
        },

        reinitializeSortable: function () {
            const $sorterSelectors = this.container.find(SELECTORS.SORTER);
            $sorterSelectors.sortable('destroy');
            this.initSortable();
        },

        handleHtmxAfterSwap: function (event) {
            const swappedNode = event.detail.elt;

            if (swappedNode.id === NAVLETS_CONTAINER_ID) {
                this.reinitializeSortable();
            }
            if (this.isNavlet(swappedNode)) {
                NavletHandlers.handle(swappedNode);
            }
        },

        handleNavletAdded: function (event) {
            this.updateOrder();

            const navlet = document.querySelector(`[data-id="${event.detail.navlet_id}"]`);
            if (navlet) {
                navlet.classList.add(CSS_CLASSES.MARK_NEW);
                navlet.addEventListener("mouseenter", function removeMarkNew() {
                    navlet.classList.remove(CSS_CLASSES.MARK_NEW);
                    navlet.removeEventListener("mouseenter", removeMarkNew);
                });
            }

            const noWidgetsMessage = document.querySelector(SELECTORS.NO_WIDGETS_MESSAGE);
            noWidgetsMessage?.remove();
        },

        handleNavletRemoved: function () {
            this.updateOrder();
        },

        initializeExistingNavlets: function () {
            const existingNavlets = document.querySelectorAll(`#${NAVLETS_CONTAINER_ID} ${SELECTORS.NAVLET}`);
            existingNavlets.forEach(navlet => NavletHandlers.handle(navlet));
        }
    };



    function initialize() {
        const controller = new NavletsHtmxController();

        document.body.addEventListener(
            EVENTS.HTMX_AFTER_SWAP,
            (event) => controller.handleHtmxAfterSwap(event)
        );
        document.body.addEventListener(
            EVENTS.NAVLET_ADDED,
            (event) => controller.handleNavletAdded(event)
        );
        document.body.addEventListener(
            EVENTS.NAVLET_REMOVED, () => controller.handleNavletRemoved()
        );
    }

    return {
        initialize: initialize
    };
});

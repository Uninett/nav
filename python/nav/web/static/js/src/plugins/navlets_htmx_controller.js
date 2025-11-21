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
    }
    const SELECTORS = {
        NAVLET: '.' + CSS_CLASSES.NAVLET,
        SORTER: '.navletColumn',
        DRAG_HANDLE: '.navlet-drag-button',
        CSRF_TOKEN: '#navlets-action-form input[name="csrfmiddlewaretoken"]'
    }

    function NavletsHtmxController() {
        this.container = $('#' + NAVLETS_CONTAINER_ID);
        this.save_ordering_url = this.container.attr('data-save-order-url');

        this.addListeners();
    }

    NavletsHtmxController.prototype = {
        addListeners: function () {
            this.initSortable();
        },

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
            this.saveOrder(this.findOrder());
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
            // Get csrf token from #navlets-action-form
            const csrfToken = $(SELECTORS.CSRF_TOKEN).val();
            $.ajax({
               url: this.save_ordering_url,
               type: 'POST',
               data: JSON.stringify(ordering),
               contentType: 'application/json',
               headers: {
                   'X-CSRFToken': csrfToken
               }
            }).fail(function() {
               console.error('Failed to save widget order');
            });
        },

        getNavlets: function (column) {
            if (column) {
                return $(column).find(SELECTORS.NAVLET);
            } else {
                return this.container.find(SELECTORS.NAVLET);
            }
        },

        isNavlet: function(node) {
            return node?.dataset?.id && node.classList.contains(CSS_CLASSES.NAVLET);
        },
    };

    function initialize() {
        const controller = new NavletsHtmxController();

        // HTMX afterSwap listener
        document.body.addEventListener('htmx:afterSwap', function (event) {
            const swappedNode = event.detail.elt;

            const isNavletContainer = swappedNode.id === NAVLETS_CONTAINER_ID;
            if (isNavletContainer) {
                controller.addListeners();
            }
            if (controller.isNavlet(swappedNode)) {
                NavletHandlers.handle(swappedNode);
            }
        });

        // Navlet added listener
        document.body.addEventListener('nav.navlet.added', function (event) {
            controller.updateOrder();
            const navlet = document.querySelector(`[data-id="${event.detail.navlet_id}"]`);
            if (navlet) {
                navlet.classList.add('mark-new');
                navlet.addEventListener("mouseenter", function () {
                    navlet.classList.remove('mark-new');
                })
            }

            const node = document.getElementById('no-widgets-message');
            if (node) {
                node.remove();
            }
        })

        // Navlet removed listener
        document.body.addEventListener('nav.navlet.removed', function (event) {
            controller.updateOrder();
        });
    }

    return {
        initialize: initialize
    };
});

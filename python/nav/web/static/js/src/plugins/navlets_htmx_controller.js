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
    'plugins/room_mapper',
    'plugins/sensors_controller',
    'src/getting_started_wizard'
], function (RoomMapper, SensorsController, GettingStartedWizard) {

    const NAVLETS_CONTAINER_ID = 'navlets-htmx';

    const SELECT2_REINIT_DELAY_MS = 30;
    const CSS_CLASSES = {
        NAVLET: 'navlet',
        OUTLINE: 'outline',
        MARK_NEW: 'mark-new',
        // If the element has the `select2-offscreen` class, it means select2 was previously initialized.
        // TODO: Update class detection when upgrading to select2 v4.
        //  See: https://select2.org/programmatic-control/methods#checking-if-the-plugin-is-initialized
        SELECT2_INITIALIZED: 'select2-offscreen'
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
    };

    function createRoomMap(mapwrapper, room_map) {
        mapwrapper.show();
        new RoomMapper(room_map.get(0));
    }

    function handleNavletSwap(swappedNode) {
        const isNavlet = swappedNode?.dataset?.id && swappedNode.classList.contains(CSS_CLASSES.NAVLET);
        if (!isNavlet) return;
        const $node = $(swappedNode);

        // Initialize RoomMapNavlet
        if ($node.hasClass('RoomMapNavlet')) {
            const room_map = $node.find('#room_map');
            if (!room_map.length) return;
            const map_wrapper = $node.find('.mapwrapper');
            createRoomMap(map_wrapper, room_map);
        }

        // Initialize SensorWidget
        if ($node.hasClass('SensorWidget')) {
            const sensors = $node.find('.room-sensor');
            if (!sensors.length) return;
            new SensorsController($node.find('.room-sensor'));
        }
        // Handle wizard button for GettingStartedWidget
        if ($node.hasClass('GettingStartedWidget')) {
            $node.on('click', '#getting-started-wizard', function () {
                GettingStartedWizard.start();
            })
        }
        // Handle list expansion for WatchDogWidget
        if ($node.hasClass('WatchDogWidget')) {
            $node.on('click', '.watchdog-tests .label.alert', function (event) {
                $(event.target).closest('li').find('ul').toggle();
            });
        }

        handleSelect2Initialization(swappedNode);
    }

    function handleSelect2Initialization(swappedNode) {
        const $selectElements = $(swappedNode).find('select');

        if ($selectElements.length > 0) {
            $selectElements.each((_, element) => {
                if ($(element).hasClass(CSS_CLASSES.SELECT2_INITIALIZED)) {
                    // Re-initialize after a short delay to allow destroy to complete
                    // Timeout value selected based on manual testing
                    setTimeout(() => {
                        $(element).select2();
                    }, SELECT2_REINIT_DELAY_MS);
                } else {
                    $(element).select2();
                }
            });
        }
    }

    function initialize() {
        const controller = new NavletsHtmxController();

        // HTMX afterSwap listener
        document.body.addEventListener('htmx:afterSwap', function (event) {
            const swappedNode = event.detail.elt;

            const isNavletContainer = swappedNode.id === NAVLETS_CONTAINER_ID;
            if (isNavletContainer) {
                controller.addListeners();
            }
            handleNavletSwap(swappedNode);
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

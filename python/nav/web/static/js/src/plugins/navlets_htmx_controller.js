define(['plugins/room_mapper'], function (RoomMapper) {

    const NAVLETS_CONTAINER_ID = 'navlets-htmx';

    function NavletsHtmxController() {
        this.container = $('#' + NAVLETS_CONTAINER_ID);
        this.navletSelector = '.navlet';
        this.sorterSelector = '.navletColumn';
        this.save_ordering_url = this.container.attr('data-save-order-url');

        this.addListeners();
    }

    NavletsHtmxController.prototype = {
        addListeners: function () {
            this.initSortable();
        },
        initSortable: function () {
            const $sorterSelectors = this.container.find(this.sorterSelector);
            if ($sorterSelectors.length === 0) {
                return;
            }
            $sorterSelectors.sortable({
                connectWith: '.navletColumn',
                forcePlaceholderSize: true,
                handle: '.navlet-drag-button',
                placeholder: 'highlight',
                tolerance: 'pointer',
                start: () => {
                    this.getNavlets().addClass('outline');
                },
                stop: () => {
                    this.getNavlets().removeClass('outline');
                },
                update: () => {
                    this.saveOrder(this.findOrder());
                }
            });
        },
        findOrder: function () {
            return this.container.find(this.sorterSelector).toArray().map((column) => {
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
            const csrfToken = $('#navlets-action-form input[name="csrfmiddlewaretoken"]').val();
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
                return $(column).find(this.navletSelector);
            } else {
                return this.container.find(this.navletSelector);
            }
        },
    };

    function createRoomMap(mapwrapper, room_map) {
        mapwrapper.show();
        new RoomMapper(room_map.get(0));
    }

    function initialize() {
        const controller = new NavletsHtmxController();
        document.body.addEventListener('htmx:afterSwap', function (event) {
            const swappedNode = event.detail.elt;
            const isNavletContainer = swappedNode.id === NAVLETS_CONTAINER_ID;
            if (isNavletContainer) {
                controller.addListeners();
            }

            const isNavlet = swappedNode?.dataset?.id && swappedNode.classList.contains('navlet');
            if (isNavlet)  {
                // Initialize the navlet
                var $node = $(swappedNode);
                var map_wrapper = $node.find('.mapwrapper');
                var room_map = map_wrapper.find('#room_map');
                if (room_map.length > 0) {
                    createRoomMap(map_wrapper, room_map);
                }
            }
        });
    }

    return {
        initialize: initialize
    };
});

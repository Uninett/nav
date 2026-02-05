/**
 * Navlet Handlers
 *
 * Provides widget-specific initialization handlers for navlets after HTMX content swaps.
 * Manages interactive components within dashboard widgets and Select2 dropdowns.
 */
define([
    'plugins/room_mapper',
    'plugins/sensors_controller',
    'src/getting_started_wizard'
], function(RoomMapper, SensorsController, GettingStartedWizard) {

    const NAVLET_TYPES = {
        ROOM_MAP: 'RoomMapNavlet',
        SENSOR: 'SensorWidget',
        GETTING_STARTED: 'GettingStartedWidget',
        WATCHDOG: 'WatchDogWidget'
    }
    const NAVLET_SET = new Set(Object.values(NAVLET_TYPES));
    // If the element has the `select2-offscreen` class, it means select2 was previously initialized.
    // TODO: Update class detection when upgrading to select2 v4.
    //  See: https://select2.org/programmatic-control/methods#checking-if-the-plugin-is-initialized
    const SELECT2_INITIALIZED_CLASS = 'select2-initialized';
    const SELECT2_REINIT_DELAY_MS = 100;

    const handlers = {
        [NAVLET_TYPES.ROOM_MAP]: function ($node) {
            const room_map = $node.find('#room_map');
            if (!room_map.length) return;
            const map_wrapper = $node.find('.mapwrapper');
            map_wrapper.show();
            // Constructor is used for side effects. NOSONAR
            new RoomMapper(room_map.get(0));
        },

        [NAVLET_TYPES.SENSOR]: function ($node) {
            const sensors = $node.find('.room-sensor');
            if (sensors.length) {
                // Constructor is used for side effects. NOSONAR
                new SensorsController(sensors);
            }
        },

        [NAVLET_TYPES.GETTING_STARTED]: function ($node) {
            $node.on('click', '#getting-started-wizard', function () {
                GettingStartedWizard.start();
            });
        },

        [NAVLET_TYPES.WATCHDOG]: function ($node) {
            $node.on('click', '.watchdog-tests .label.alert', function (event) {
                $(event.target).closest('li').find('ul').toggle();
            });
        }
    };

    function getNavletType($node) {
        const classes = $node.attr('class').split(' ').filter(cls => NAVLET_SET.has(cls));
        return classes.length ? classes[0] : null;
    }

    function handleNavletType($node) {
        const navletType = getNavletType($node);
        if (!navletType) return;

        const handler = handlers[navletType];
        if (!handler) return;
        try {
            handler($node);
        } catch (error) {
            console.error(`Failed to initialize ${navletType}:`, error);
        }
    }

    function handleSelect2Initialization($swappedNode) {
        const $selectElements = $swappedNode.find('select');

        if ($selectElements.length > 0) {
            $selectElements.each((_, element) => {
                if ($(element).hasClass(SELECT2_INITIALIZED_CLASS)) {
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

    return {
        handle: function (swappedNode) {
            const $swappedNode = $(swappedNode);
            handleNavletType($swappedNode);
            handleSelect2Initialization($swappedNode);
        },
    };
});

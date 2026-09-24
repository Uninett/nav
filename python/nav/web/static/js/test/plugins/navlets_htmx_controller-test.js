/*
 * The real navlet handlers module pulls in the room map and sensor widgets,
 * which need globals that do not exist outside a rendered NAV page. Sortable
 * initialization does not involve them, so stub the module out before the
 * controller asks for it.
 *
 * Note that karma loads every test file into a single RequireJS registry, so
 * this stub stands in for the real module for the entire test run, not just
 * this file. Nothing else currently asks for it.
 */
define('plugins/navlet_handlers', [], function () {
    return {
        handle: function () {}
    };
});

define(['plugins/navlets_htmx_controller', 'jquery-ui'], function (NavletsHtmxController) {

    var CONTAINER_ID = 'navlets-htmx';
    var COLUMN_COUNT = 2;

    /* Mirrors the empty container webfront/index.html renders */
    var CONTAINER_HTML =
        '<div id="' + CONTAINER_ID + '" data-save-order-url="/test/save-order"></div>';

    /* Mirrors what webfront/_dashboard_navlets.html delivers in the htmx response */
    var COLUMNS_HTML =
        '<div class="row">' +
        '  <div class="column navletColumn" data-col="1">' +
        '    <div class="navlet" data-id="1"></div>' +
        '  </div>' +
        '  <div class="column navletColumn" data-col="2"></div>' +
        '</div>';

    /*
     * initialize() registers its listeners on document.body, and the module
     * exports nothing that could detach them again, so controllers from earlier
     * tests keep handling the events dispatched here. They are harmless only
     * because the constructor resolves the container once: emptying the body
     * leaves each stale controller holding a detached node that can never match
     * any column. Make the container lookup lazy and that stops being true.
     */
    describe('Navlets HTMX controller', function () {

        beforeEach(function () {
            $('body').append(CONTAINER_HTML);
        });

        afterEach(function () {
            $('body').empty();
        });

        describe('when the columns arrive in an htmx swap after initialization', function () {
            it('should initialize sortable on the swapped-in columns', function () {
                NavletsHtmxController.initialize();
                renderColumns();
                triggerHtmxAfterSwap();
                assert.strictEqual(sortableInstances().length, COLUMN_COUNT);
            });
        });

        describe('when the columns are already present at initialization', function () {
            it('should initialize sortable on the existing columns', function () {
                renderColumns();
                NavletsHtmxController.initialize();
                assert.strictEqual(sortableInstances().length, COLUMN_COUNT);
            });
        });

        /*
         * The htmx swap replaces the columns wholesale, so this is not a state
         * the dashboard actually reaches. It pins reinitializeSortable() as
         * idempotent, which is what keeps the method correct if an out-of-band
         * swap ever targets the container without replacing its contents.
         */
        describe('when reinitializing over columns that are already sortable', function () {
            it('should leave the columns sortable', function () {
                renderColumns();
                NavletsHtmxController.initialize();
                triggerHtmxAfterSwap();
                assert.strictEqual(sortableInstances().length, COLUMN_COUNT);
            });
        });

        /*
         * Every widget fetches its own content into itself, so most swaps on a
         * dashboard target a navlet. Rebuilding the sortables on each of those
         * would be pure waste.
         */
        describe('when the swap targets a widget rather than the container', function () {
            it('should leave the existing sortables untouched', function () {
                renderColumns();
                NavletsHtmxController.initialize();
                var instancesBefore = sortableInstances();

                triggerHtmxAfterSwap(firstNavlet());

                var instancesAfter = sortableInstances();
                assert.strictEqual(instancesAfter.length, COLUMN_COUNT);
                instancesAfter.forEach(function (instance, index) {
                    assert.strictEqual(instance, instancesBefore[index]);
                });
            });
        });

    });

    /* Fills the container the way an htmx innerHTML swap does */
    function renderColumns() {
        container().html(COLUMNS_HTML);
    }

    function triggerHtmxAfterSwap(swapTarget) {
        document.body.dispatchEvent(new CustomEvent('htmx:afterSwap', {
            detail: {elt: swapTarget || container().get(0)}
        }));
    }

    /* jQuery drops the undefined entries, leaving only initialized columns */
    function sortableInstances() {
        return container().find('.navletColumn').map(function () {
            return $(this).sortable('instance');
        }).get();
    }

    function firstNavlet() {
        return container().find('.navlet').get(0);
    }

    function container() {
        return $('#' + CONTAINER_ID);
    }

});

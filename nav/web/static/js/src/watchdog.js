require([], function () {

    /** Adds click handler on the status test labels */
    function addLabelClickHandlers() {
        $('#watchdog-tests').on('click', '.label.alert', function (event) {
            $(event.target).closest('li').find('ul').toggle();
        });
    }


    /** Fetch and display data for the overview */
    function populateOverview() {
        var arpElement = document.getElementById('arp-count'),
            camElement = document.getElementById('cam-count'),
            netboxElement = document.getElementById('netbox-count'),
            activeAddressesElement = document.getElementById('active-addresses'),
            serialNumbers = document.getElementById('serial-numbers');

        doRequest(arpElement, '/watchdog/cam_and_arp', function(data) {
            arpElement.innerHTML = '~' + intComma(data.arp);
            camElement.innerHTML = '~' + intComma(data.cam);
        });

        doRequest(netboxElement, '/api/netbox', function(data) {
            netboxElement.innerHTML = intComma(data.count);
        });

        doRequest(activeAddressesElement, '/watchdog/active_addresses', function(data) {
            var activity = intComma(data.active) + ' (' +
                    intComma(data.ipv4) + '/' +
                    intComma(data.ipv6) + ')';
            activeAddressesElement.innerHTML = activity;
        });

        doRequest(serialNumbers, '/watchdog/serial_numbers', function(data) {
            serialNumbers.innerHTML = intComma(data.count);
        });

    }

    /** Do a request and report errors if any */
    function doRequest(element, url, fun) {
        var request = $.getJSON(url, fun);
        var timer = setTimeout(function() {
            element.innerHTML = 'Still fetching...';
        }, 10000);
        request.fail(function() {
            // This is not terribly important so we do not want a red background or anything
            element.innerHTML = '<span>Error fetching data</span>';
        });
        request.always(function() {
            clearTimeout(timer);
        });
    }

    /** Adds thousand separators to numbers */
    function intComma(x) {
        return x.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
    }


    /** Do this on page ready */
    $(function () {
        addLabelClickHandlers();
        populateOverview();
    });

});

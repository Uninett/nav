require([
    'plugins/checkbox_selector',
    'plugins/quickselect',
    'plugins/seeddb_hstore',
    'libs/jquery',
    'libs/jquery.dataTables.min',
    'libs/OpenLayers',
    'libs/modernizr',
    'libs/FixedColumns.min'], function (CheckboxSelector, QuickSelect, FormFuck) {

    var tableWrapper = '#tablewrapper',
        tableSelector = '#seeddb-content';

    function executeOnLoad() {
        /* Start joyride if url endswith #joyride */
        if (location.hash === '#joyride') {
            $(document).foundation({
                'joyride': {
                    'pre_ride_callback': function () {
                        var cards = $('.joyride-tip-guide').find('.joyride-content-wrapper');
                        cards.each(function (index, element) {
                            var counter = $('<small>')
                                .attr('style', 'position:absolute;bottom:1.5rem;right:1.25rem')
                                .html(index + 1 + ' of ' + cards.length);
                            $(element).append(counter);
                        });
                    },
                    'modal': false
                }
            });
            $(document).foundation('joyride', 'start');
        }


        if ($('#map').length) {
            populateMap(initMap());     // Show map for coordinates
        }

        /* The Datatables plugin works best when content is rendered. Thus
         * we activate it on load */
        if ($(tableSelector).find('tbody tr').length > 1) {
            enrichTable();
        } else {
            $(tableWrapper).removeClass('notvisible');
        }

        new CheckboxSelector('#select', '.selector').add();
        new QuickSelect('.quickselect');


        /* Add form to hstore fields in room */
        var $textarea = $('textarea#id_data');
        if ($textarea.length) {
            new FormFuck($textarea);
        }
    }

    /* Internet Explorer caching leads to onload event firing before script
       is loaded - thus we never get the load event. This code will at least
       make it usable. */
    if (document.readyState === 'complete') {
        executeOnLoad();
    } else {
        $(window).load(executeOnLoad);
    }

    function initMap() {
        OpenLayers.ImgPath = NAV.imagePath + '/openlayers/';
        var map = new OpenLayers.Map('map', {
            displayProjection: new OpenLayers.Projection("EPSG:4326"),
            controls: [
                new OpenLayers.Control.PanZoomBar(),
                new OpenLayers.Control.Navigation()
            ],
            theme: NAV.cssPath + '/openlayers.css'
        }),
            mapLayer = new OpenLayers.Layer.OSM('OpenStreetMap',
                '/search/osm_map_redirect/${z}/${x}/${y}.png');

        mapLayer.tileOptions = {crossOriginKeyword: null};
        map.addLayer(mapLayer);
        return map;
    }


    function populateMap(map) {
        var marker_layer = addMarkerLayer(map);
        var marker;
        var displayProjection = map.displayProjection;
        var inputProjection = map.getProjectionObject();

        var position_input = $('#id_position');
        var deferredCenter = $.when(getLocation(position_input.val()));

        deferredCenter.done(function(center) {
            center.transform(displayProjection, inputProjection);
            map.setCenter(center, 14);
            marker = addMarkerToLayer(center, marker_layer);
            moveMarker(
                map,
                center,
                marker,
                position_input,
                displayProjection,
                inputProjection);

            initGetLonLatOnClickControl(
                map, marker ,inputProjection, displayProjection, position_input);
        });

        deferredCenter.fail(function() {
            map.zoomToMaxExtent();
            var center = map.center;
            marker = addMarkerToLayer(center, marker_layer);
            moveMarker(
                map,
                center,
                marker,
                position_input,
                displayProjection,
                inputProjection);

            initGetLonLatOnClickControl(
                map, marker ,inputProjection, displayProjection, position_input);
        });
    }

    function getLocation(position_string) {
        var deferred = $.Deferred();
        var center;

        function gotPosition(position) {
            center = new OpenLayers.LonLat(
                position.coords.longitude,
                position.coords.latitude
            );
            deferred.resolve(center);
        }
        function errorGettingPosition(error) {
            console.log(error);
            deferred.reject();
        }

        if (position_string === '') {
            center = new OpenLayers.LonLat(0, 0);
            if (Modernizr.geolocation) {
                navigator.geolocation.getCurrentPosition(
                    gotPosition,
                    errorGettingPosition,
                    {timeout: 1000}  // Default is infinity, yay. No map for you.
                );
            } else {
                deferred.resolve(center);
            }
        }
        else {
            center = parseLonLat(position_string.slice(1, -1));
            deferred.resolve(center);
        }

        return deferred.promise();
    }

    function addMarkerLayer(map) {
        var marker = new OpenLayers.Layer.Markers('Marker');
        map.addLayer(marker);
        return marker;
    }

    function addMarkerToLayer(lonlat, layer) {
        var size = new OpenLayers.Size(21,25);
        var offset = new OpenLayers.Pixel(-(size.w/2), -size.h);
        var icon = new OpenLayers.Icon(
            'http://www.openlayers.org/dev/img/marker.png', size, offset);
        var marker = new OpenLayers.Marker(lonlat, icon);
        layer.addMarker(marker);
        return marker;
    }

    function lonLatToStr(lonlat) {
        return [lonlat.lat, lonlat.lon].join();
    }

    function parseLonLat(llStr) {
        var re = /^(-?[0-9]*[.]?[0-9]+), *(-?[0-9]*[.]?[0-9]+)$/;
        var arr = re.exec(llStr);
        if (arr === null) {
            throw 'error: incorrectly formatted latitude, longitude string "' +
            llStr + '"';
        }
        return new OpenLayers.LonLat(arr[2], arr[1]);
    }

    function moveMarker(
        map,
        lonlat,
        marker,
        position_input,
        displayProjection,
        inputProjection) {

        marker.moveTo(map.getLayerPxFromLonLat(lonlat));
        position_input.val(lonLatToStr(lonlat.transform(
            inputProjection,
            displayProjection
        )));
    }

    function initGetLonLatOnClickControl(
        map, marker, inputProjection, displayProjection, position_input) {
        map.addControl(new OpenLayers.Control.MousePosition());

        OpenLayers.Control.Click = OpenLayers.Class(OpenLayers.Control, {
            defaultHandlerOptions: {
                'single': true,
                'double': false,
                'pixelTolerance': 0,
                'stopSingle': false,
                'stopDouble': false
            },

            initialize: function(options) {
                this.handlerOptions = OpenLayers.Util.extend(
                    {}, this.defaultHandlerOptions
                );
                OpenLayers.Control.prototype.initialize.apply(
                    this, arguments
                );
                this.handler = new OpenLayers.Handler.Click(
                    this, {
                        'click': this.trigger
                    }, this.handlerOptions
                );
            },

            trigger: function(e) {
                var lonlat = map.getLonLatFromPixel(e.xy);
                moveMarker(
                    map,
                    lonlat,
                    marker,
                    position_input,
                    displayProjection,
                    inputProjection
                );
            }
        });

        var click = new OpenLayers.Control.Click();
        map.addControl(click);
        click.activate();
    }

    function enrichTable() {
        var $wrapper = $(tableWrapper),
            keyPrefix = 'nav.seeddb.rowcount',
            key = [keyPrefix, $wrapper.attr('data-forpage')].join('.'),
            numRows = 10;
        if (Modernizr.localstorage) {
            var value = localStorage.getItem(key);
            if (value !== null) { numRows = value; }
        }


        /* Apply DataTable */
        var table = $(tableSelector).dataTable({
            "bPaginate": true,      // Pagination
            "bLengthChange": true,  // Change number of visible rows
            "bFilter": false,       // Searchbox
            "bSort": true,          // Sort when clicking on headers
            "bInfo": true,          // Show number of entries visible
            "bAutoWidth": true,     // Resize table
            "sScrollX": '100%',     // Scroll when table is bigger than viewport
            "aoColumnDefs": [
                { 'bSortable': false, 'sWidth': '16px', 'aTargets': [ 0 ] }  // Do not sort on first column
            ],
            "sPaginationType": "full_numbers", // Display page numbers in pagination
            "sDom": "<lip>t",   // display order of metainfo (lengthchange, info, pagination)
            "fnDrawCallback": function (oSettings) {
                /* Run this on redraw of table */
                $('.paginate_button').removeClass('disabled').addClass('button tiny');
                $('.paginate_active').addClass('button tiny secondary');
                $('.paginate_button_disabled').addClass('disabled');
                $(tableWrapper).removeClass('notvisible');
            },
            "aLengthMenu": [
                [10, 25, 50, -1],   // Choices for number of entries to display
                [10, 25, 50, "All"] // Text for the choices
            ],
            "iDisplayLength": numRows,  // The default number of rows to display
            "oLanguage": {"sInfo": "_START_-_END_ of _TOTAL_"}  // Format of number of entries visibile
        });

        table.fnSort([[1, 'asc']]);  // When loaded, sort ascending on second column

        /* Store rowcount when user changes it */
        if (Modernizr.localstorage) {
            $wrapper.find('.dataTables_length select').change(function () {
                var newValue = $(event.target).val();
                localStorage.setItem(key, newValue);
            });
        }
    }

});



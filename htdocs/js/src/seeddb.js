require([
    'plugins/checkbox_selector',
    'plugins/quickselect',
    'libs/jquery',
    'libs/OpenLayers'
], function(CheckboxSelector, QuickSelect){

    $(function() {
        new CheckboxSelector('#select', '.selector').add();
        new QuickSelect('.quickselect');

        // Mapstuff
        if ($('#map').length) {

            var map = initMap();
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
    });

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
            navigator.geolocation.getCurrentPosition(
                gotPosition,
                errorGettingPosition
            );
        }
        else {
            center = parseLonLat(position_string.slice(1, -1));
            deferred.resolve(center);
        }

        return deferred.promise();
    }

    function initMap() {
        OpenLayers.ImgPath = '/images/openlayers/';
        var map = new OpenLayers.Map('map', {
            displayProjection: new OpenLayers.Projection("EPSG:4326"),
            controls: [
                new OpenLayers.Control.PanZoomBar(),
                new OpenLayers.Control.Navigation()
            ],
            theme: '/style/openlayers.css'
        });
        map.addLayer(new OpenLayers.Layer.OSM(
            'OpenStreetMap',
            '/info/osm_map_redirect/${z}/${x}/${y}.png')
        );
        return map;
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
        var re = /^([0-9]*[.]?[0-9]+), *([0-9]*[.]?[0-9]+)$/;
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
});

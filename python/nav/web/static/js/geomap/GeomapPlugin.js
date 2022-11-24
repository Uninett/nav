define(['libs/spin.min', 'plugins/fullscreen'],
function(Spinner, fullscreen) {

    var mapSelector = "map",
        spinner = new Spinner();

    /**
     * Fetch all rooms and initialize map
     */
    function geomap() {
        var request = fetchRooms();
        request.done(function(data) {
            var roomPoints = data.rooms.map(createPoint),
                roomPositions = new OpenLayers.Geometry.MultiPoint(roomPoints),
                boundingBox = roomPositions.getBounds(); // Is null if no roompositions

            if (boundingBox === null) {
                showPositionHint();
            }

            init(boundingBox);
        });
    }


    function fetchRooms() {
        return $.getJSON('/ajax/open/roommapper/rooms/');
    }


    /**
     * Create an Openlayers point based on a room position
     */
    function createPoint(room) {
        return new OpenLayers.Geometry.Point(getLong(room.position), getLat(room.position));
    }

    function getLat(position) {
        return parseFloat(position.split(',')[0]);
    }

    function getLong(position) {
        return parseFloat(position.split(',')[1]);
    }

    function showPositionHint() {
        $('#position-hint').removeClass('hidden');
    }


    /**
     * Creates a map, adds the layers and zooms to the given bounds.
     */
    function init(boundingBox) {
        var map = createMap();
        addLayers(map);
        zoomToBounds(map, boundingBox);
        addFullScreenToggler();
    }


    /**
     * Create the map and apply controls
     */
    function createMap() {
        return new OpenLayers.Map(mapSelector, {
            controls: [
                new OpenLayers.Control.Navigation(),
		new OpenLayers.Control.PanZoomBar(), //new OpenLayers.Control.NavToolbar(),
                new OpenLayers.Control.Attribution(),
		new OpenLayers.Control.LayerSwitcher()
            ],
            displayProjection: new OpenLayers.Projection("EPSG:4326"),
            theme: NAV.cssPath + '/openlayers.css'
        });
    }


    /**
     * Add layers to the map, and connect the layers and the time navigation
     * panel.
     *
     * TODO: This is still not fully refactored. Among other things this has a
     * circular dependency with the netLayer and timeNavigator.
     */
    function addLayers(map) {
        var mapnikLayer = new OpenLayers.Layer.OSM(
            "OpenStreetMap", NAV.osmTileUrl + '/${z}/${x}/${y}.png');
        mapnikLayer.tileOptions = {crossOriginKeyword: null};
        map.addLayer(mapnikLayer);

        var netLayer;           // Todo: fix circular dependency
        var timeNavigator = new TimeNavigator('time-navigation', function () {
            netLayer.update();
        });

        netLayer = new NetworkLayer('Networks', 'data', {
            start: function () {
                return timeNavigator.interval.beginning();
            },
            end: function () {
                return timeNavigator.interval.end();
            }
        }, {
            eventListeners: {
                loadstart: function() { spinner.spin(document.getElementById(mapSelector)); },
                loadend: function() { spinner.stop(); },
                loadcancel: function() { spinner.stop(); }
            }
        });
        map.addLayer(netLayer);

        try {
            var permalink = new Permalink('permalink', map, {
                set time(t) {
                    timeNavigator.setInterval(new TimeInterval(t));
                },
                get time() {
                    return timeNavigator.interval.toReadableString();
                }
            }, [timeNavigator.onChange]);
        } catch (e) {
            alert('Error parsing URL query string:\n' + e);
        }
    }


    /**
     * Zoom to the correct bounds based on what we have of information
     */
    function zoomToBounds(map, boundingBox) {
        var parameters = OpenLayers.Util.getParameters();
        if (parameters.bbox) {
	    console.log('got bbox parameters');
            var requestedBounds = OpenLayers.Bounds.fromArray(parameters.bbox);
            requestedBounds.transform(map.displayProjection, map.getProjectionObject());
            map.zoomToExtent(requestedBounds);
        } else if (parameters.zoom !== null && parameters.zoom !== undefined) {
            try {
                if (parameters.lat !== null && parameters.lat !== undefined
                    && parameters.lon !== null && parameters.lon !== undefined) {
                    map.setView(
                        new OpenLayers.View({
                            center: OpenLayers.Projection.fromLonLat([parameters.lon, parameters.lat]),
                            extent: map.getView().calculateExtent(map.getSize()),
                            zoom: parameters.zoom
                        })
                    );
                } else {
                    map.getView.setZoom(parameters.zoom);
                }
                map.getView.setZoom(parameters.zoom);
            } catch (e) {}
        } else if (boundingBox) {
            boundingBox.transform(map.displayProjection, map.getProjectionObject());
            map.zoomToExtent(boundingBox);
        } else {
            map.zoomToMaxExtent();
        }
    }


    /**
     * Add a fullscreen toggler based on the official fullscreen API
     */
    function addFullScreenToggler() {
        if (fullscreen.isFullscreenSupported()) {
            fullscreen.createFullscreenToggler(
                document.getElementById(mapSelector), true);
        }
    }

    return geomap;

});

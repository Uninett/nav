define(['libs/ol-debug'], function (ol) {

    /**
     * Mapper creates an OpenStreetMap on the node given rooms from NAV
     *
     * A room needs a name, position and status
     * node: id of element containing map (no leading #)
     * rooms: a list of room objects
     *   [
     *     {"status": "faulty",
     *      "position": "63.4158131020689,10.3950651101694",
     *      "name": "teknobyen"}
     *   ]
     *
     * Todo: Display name on hover state
     *
     */
    function RoomMapper(node, rooms) {
        console.log('RoomMapper', node);
        this.node = node;
        this.rooms = rooms;
        this.baseZoomLevel = 17;

        this.imagePath = NAV.imagePath + '/openlayers/';
        this.okStyle = new ol.style.Style({
            image: new ol.style.Icon({
                src: this.imagePath + 'marker-green.png'
            })
        });
        this.faultyStyle = new ol.style.Style({
            image: new ol.style.Icon({
                src: this.imagePath + 'marker.png'
            })
        });

        addCssToHead(NAV.cssPath + '/ol.css');
        this.initialize();
    }

    RoomMapper.prototype = {
        initialize: function () {
            if (this.rooms.length <= 0) {
                console.log('Mapper: No rooms to put on map');
                return;
            }

            var markerSource = this.createMarkerSource(),
                markerLayer = new ol.layer.Vector({ source: markerSource }),
                extent = markerSource.getExtent();

            var view = new ol.View({ center: ol.extent.getCenter(extent), zoom: this.baseZoomLevel });
            var map = this.createMap(view, markerLayer);

            if (this.rooms.length > 1) {
                view.fitExtent(extent); // Zoom to extent
            }
            this.addMarkerNavigation(map);

        },

        /* When marker is clicked, go to roominfo for that room */
        addMarkerNavigation: function(map) {
            var selectClick = new ol.interaction.Select({
                condition: ol.events.condition.click
            });
            map.addInteraction(selectClick);
            selectClick.on('select', function(e) {
                if (e.selected.length) {
                    var feature = e.selected[0];
                    window.location = NAV.urls.room_info_base + feature.get('name');
                }
            })
        },

        createMarkerSource: function () {
            return new ol.source.Vector({
                features: this.rooms.map(this.createFeature, this)
            });
        },

        createFeature: function (room) {
            var feature = new ol.Feature({
                geometry: new ol.geom.Point(transformPosition(room)),
                name: room.name
            });

            var style = room.status === 'ok' ? this.okStyle: this.faultyStyle;
            feature.setStyle(style);
            return feature;
        },

        createMap: function (view, markerLayer) {
            console.log("Creating map on", view);
            return new ol.Map({
                target: this.node,
                view: view,
                layers: [
                    new ol.layer.Tile({
                        source: getOSMsource()
                    }),
                    markerLayer
                ],
                controls: ol.control.defaults().extend([new ol.control.FullScreen()])
            });
        }

    };

    function getOSMsource() {
        /** Return OpenStreeMap source for OpenLayers3 */
        return new ol.source.OSM({
            url: NAV.osmTileUrl + '/{z}/{x}/{y}.png',
            crossOrigin: null
        });
    }

    function transformPosition(room) {
        var point = [getLong(room.position), getLat(room.position)];
        return ol.proj.transform(point, 'EPSG:4326', 'EPSG:3857');
    }

    function getLat(position) {
        return parseFloat(position.split(',')[0]);
    }

    function getLong(position) {
        return parseFloat(position.split(',')[1]);
    }

    function addCssToHead(src) {
        var style = document.createElement('link');
        style.rel = 'stylesheet';
        style.href = src;
        document.getElementsByTagName('head')[0].appendChild(style);
    }

    return RoomMapper;

});

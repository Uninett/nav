define(['libs/ol-debug'], function (ol) {

    /**
     * Mapper creates an OpenStreetMap on the node given rooms from NAV
     *
     */
    function RoomMapper(node, rooms, room_id) {
        console.log('RoomMapper', node);
        this.node = node;
        this.rooms = rooms.filter(function(room) {
            return room.position;  // Filter out rooms with position
        });
        this.room = _.find(this.rooms, function(room) {
            return room.id === room_id;
        })

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
                console.log('Mapper: No rooms with position to put on map');
                return;
            }

            var markerSource = this.createMarkerSource(),
                markerLayer = new ol.layer.Vector({ source: markerSource }),
                extent = markerSource.getExtent();

            var view = new ol.View({ center: ol.extent.getCenter(extent), zoom: this.baseZoomLevel });
            var map = this.createMap(view, markerLayer);

            if (!this.room && this.rooms.length > 1) {
                view.fit(extent); // Zoom to extent
            } else if (this.room) {
                view.setCenter(transformPosition(this.room));
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
                name: room.id
            });

            var style = room.id === this.room.id ? this.okStyle: this.faultyStyle;
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
        var point = [getLong(room), getLat(room)];
        return ol.proj.transform(point, 'EPSG:4326', 'EPSG:3857');
    }

    function getLat(room) {
        return parseFloat(room.position[0]);
    }

    function getLong(room) {
        return parseFloat(room.position[1]);
    }

    function addCssToHead(src) {
        var style = document.createElement('link');
        style.rel = 'stylesheet';
        style.href = src;
        document.getElementsByTagName('head')[0].appendChild(style);
    }

    return RoomMapper;

});

define(['libs/ol-debug'], function (ol) {

    var imagePath = NAV.imagePath + '/openlayers/';

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

            var clusterSource = new ol.source.Cluster({
                source: markerSource,
                distance: 30
            });

            console.log(clusterSource);
            var self = this;

            var clusters = new ol.layer.Vector({
                source: clusterSource,
                style: getComponentStyle
            })

            var view = new ol.View({ center: ol.extent.getCenter(extent), zoom: this.baseZoomLevel });
            var map = this.createMap(view, clusters);

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
                condition: ol.events.condition.click,
                style: new ol.style.Style({
                    // Set invisible style on select
                    fill: new ol.style.Fill({color: [255,255,255,0]}),
                })
            });
            map.addInteraction(selectClick);
            selectClick.on('select', function(e) {
                if (e.selected.length) {
                    var selected = e.selected[0];
                    var features = selected.get('features');
                    if (features.length === 1) {
                        // This is a single marker and should navigate to room on click
                        window.location = NAV.urls.room_info_base + features[0].get('name');
                    } else {
                        // This is a cluster of markers and should zoom to extent of markers in cluster
                        var collection = new ol.geom.GeometryCollection(features.map(function(feature) {
                            return feature.getGeometry();
                        }));
                        map.getView().fit(collection.getExtent());
                    }
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

            return feature;
        },

        createMap: function (view, clusters) {
            return new ol.Map({
                target: this.node,
                view: view,
                layers: [
                    new ol.layer.Tile({
                        source: getOSMsource()
                    }),
                    clusters
                ],
                controls: ol.control.defaults().extend([new ol.control.FullScreen()])
            });
        }

    };

    /** Return OpenStreeMap source for OpenLayers3 */
    function getOSMsource() {
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

    /**
     * Creates styles for the different cluster components
     */
    function getComponentStyle(feature) {
        var features = feature.get('features');
        var size = features.length;
        if (size <= 1) {
            return getRoomStyle(features[0], self.room);
        } else {
            return getClusterStyle(size);
        }
    }

    /**
     * Gets the style for a given room
     * @param {string} room - the room id/name
     * @param {object} focusRoom - optional focusRoom, should be visibly distinct from others
     */
    function getRoomStyle(room, focusRoom) {
        var name = room.get('name');
        if (focusRoom) {
            return name === focusRoom.id ?
                   getMainMarkerStyle(name) :
                   getSecondaryMarkerStyle(name);
        } else {
            return getMainMarkerStyle(name);
        }
    }

    /**
     * Gets the style for a cluster
     * @param {int} size - the number of rooms in the cluster
     */
    function getClusterStyle(size) {
        return new ol.style.Style({
            image: new ol.style.Circle({
                radius: 15,
                stroke: new ol.style.Stroke({
                    color: '#fff'
                }),
                fill: new ol.style.Fill({
                    color: '#000'
                })
            }),
            text: new ol.style.Text({
                text: size.toString(),
                fill: new ol.style.Fill({
                    color: '#fff'
                })
            })
        });
    }

    function addCssToHead(src) {
        var style = document.createElement('link');
        style.rel = 'stylesheet';
        style.href = src;
        document.getElementsByTagName('head')[0].appendChild(style);
    }

    function getMarkerStyle(text, image) {
        return new ol.style.Style({
            image: new ol.style.Icon({
                src: imagePath + image,
            }),
            text: new ol.style.Text({
                text: text,
                font: '12px sans-serif',
                offsetY: 20,
                backgroundFill: new ol.style.Fill({color: [255, 255, 255, 0.5]}),
                padding: [0, 3, 0, 3]
            })
        });
    }

    function getMainMarkerStyle(text) {
        return getMarkerStyle(text, 'marker-green.png');
    }

    function getSecondaryMarkerStyle(text) {
        return getMarkerStyle(text, 'marker-red.png');
    }


    return RoomMapper;

});

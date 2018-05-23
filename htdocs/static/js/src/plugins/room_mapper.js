define(['libs/ol-debug'], function (ol) {

    var imagePath = NAV.imagePath + '/openlayers/';

    /**
     * Mapper creates an OpenStreetMap on the node given rooms from NAV
     *
     */
    function RoomMapper(node, rooms, room_id) {
        this.node = node;
        this.room_id = room_id;

        this.baseZoomLevel = 17;
        this.clusterDistance = 30;

        addCssToHead(NAV.cssPath + '/ol.css');
        this.initialize();
    }

    RoomMapper.prototype = {
        initialize: function () {
            // Create clusters based on all rooms
            var markerSource = this.createMarkerSource();
            var clusterSource = this.createClusterSource(markerSource);
            var clusters = new ol.layer.Vector({
                source: clusterSource,
                style: getComponentStyle
            })

            var view = this.createView();
            var map = createMap(this.node, view, clusters);

            markerSource.on('addfeature', this.centerAndFit.bind(this, view, markerSource));
            this.addClickNavigation(map);
        },


        /**
         * On click on marker, go to room info for that room
         * On click on cluster, zoom to rooms in that cluster
         */
        addClickNavigation: function(map) {
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
                        var feature = features[0];
                        feature.setStyle(null);  // Otherwise it disappears
                        window.location = NAV.urls.room_info_base + feature.get('name');
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

        createView: function(center) {
            return new ol.View({
                zoom: this.baseZoomLevel,
                center: [0,0]
            });
        },

        centerAndFit: function(view, markerSource) {
            if (this.room_id) {
                var room_id = this.room_id;
                var focusRoom = markerSource.getFeatures().find(function(room) {
                    return room.get('name') === room_id;
                });
                view.setCenter(focusRoom.getGeometry().flatCoordinates);
            } else {
                view.fit(markerSource.getExtent());
            }
        },

        createClusterSource: function(markerSource) {
            console.log(this.clusterDistance);
            return new ol.source.Cluster({
                source: markerSource,
                distance: this.clusterDistance
            });
        },

        /**
         * Loads all rooms from API and creates features of those with position
         */
        createMarkerSource: function () {
            var self = this;
            var source = new ol.source.Vector();
            var loader = function() {
                $.getJSON('/api/room/', function (data) {
                    var features = data.results.filter(function(room) {
                        return room.position;
                    }).map(function(room) {
                        return self.createFeature(room);
                    });
                    source.addFeatures(features);
                });
            }
            source.setLoader(loader);
            return source;
        },

        createFeature: function (room) {
            var feature = new ol.Feature({
                geometry: new ol.geom.Point(transformPosition(room)),
                name: room.id,
                focus: this.room_id && room.id === this.room_id
            });

            return feature;
        },

    };

    function createMap(node, view, clusters) {
        return new ol.Map({
            target: node,
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
            return getRoomStyle(features[0]);
        } else {
            return getClusterStyle(size);
        }
    }

    /**
     * Gets the style for a given room
     * @param {string} room - the room id/name
     * @param {object} focusRoom - optional focusRoom, should be visibly distinct from others
     */
    function getRoomStyle(room) {
        var name = room.get('name');
        var focusRoom = room.get('focus');
        return focusRoom ?
               getFocusMarkerStyle(name) :
               getMainMarkerStyle(name);
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
                }),
                font: '12px sans-serif'
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
                backgroundFill: new ol.style.Fill({color: [255, 255, 255, 0.7]}),
                padding: [0, 3, 0, 3]
            })
        });
    }

    function getFocusMarkerStyle(text) {
        return getMarkerStyle(text, 'marker-gold.png');
    }

    function getMainMarkerStyle(text) {
        return getMarkerStyle(text, 'marker-blue.png');
    }


    return RoomMapper;

});

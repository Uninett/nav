define(['libs/ol-debug'], function (ol) {

    var imagePath = NAV.imagePath + '/openlayers/';
    var primaryMarkerImage = imagePath + 'marker-blue.png';
    var focusMarkerImage = imagePath + 'marker-gold.png';

    /**
     * Mapper creates an OpenStreetMap on the node given rooms from NAV
     *
     * @param {string|node} node: the map node
     * @param {object} options: handled options are {string} 'room' or {string} 'location'
     *
     * if room is set it is highlighted and set as center for the map
     * if location is set only rooms for that location is displayed
     *
     */
    function RoomMapper(node, options) {
        this.node = typeof node === 'string' ? document.getElementById(node) : node;

        this.options = _.extend({}, options);
        this.room_id = this.options.room;
        this.location_id = this.options.location;

        this.overlays = {};
        this.overlaysVisible = false;

        this.clusterDistance = 30; // Distance in pixels for clustering to happen
        this.maxZoom = 20;

        addCssToHead(NAV.cssPath + '/ol.css');
        this.initialize();
    }

    RoomMapper.prototype = {
        initialize: function () {
            // Create clusters based on all rooms
            this.markerSource = this.createMarkerSource();
            this.clusterSource = this.createClusterSource();
            var clusters = new ol.layer.Vector({
                source: this.clusterSource,
                style: getComponentStyle
            });

            this.map = this.createMap(clusters);
            this.view = this.map.getView();

            var self = this;
            // Center and fit when features are loaded
            $(this.node).on('addfeatures', function() {
                self.centerAndFit.apply(self);
                self.addOverlappingNodesDetection();
            });

            addClickNavigation(this.map);
        },

        createMap: function(clusters) {
            return new ol.Map({
                target: this.node,
                view: this.createView(),
                layers: [
                    new ol.layer.Tile({
                        source: getOSMsource()
                    }),
                    clusters
                ],
                controls: ol.control.defaults().extend(
                    [
                        new ol.control.FullScreen(),
                        new OverlayToggler(this)
                    ])
            });
        },

        createView: function() {
            return new ol.View({
                zoom: this.maxZoom,
                maxZoom: this.maxZoom,
                center: [0,0]
            });
        },

        centerAndFit: function() {
            if (this.room_id) {
                var room_id = this.room_id;
                var focusRoom = this.markerSource.getFeatures().find(function(room) {
                    return room.get('name') === room_id;
                });
                this.view.setCenter(focusRoom.getGeometry().getCoordinates());
            } else {
                this.view.fit(this.markerSource.getExtent());
            }
        },

        createClusterSource: function() {
            return new ol.source.Cluster({
                source: this.markerSource,
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
                var url = self.location_id ?
                          NAV.urls.api_room_list + '?location=' + self.location_id :
                          NAV.urls.api_room_list;
                $.getJSON(url, self.getFeatures.bind(self, source));
            };
            source.setLoader(loader);
            return source;
        },

        getFeatures: function (source, data) {
            var self = this;
            var features = data.results.filter(function(room) {
                return room.position;
            }).map(function(room) {
                return self.createFeature(room);
            });
            source.addFeatures(features);
            if (data.next) {
                $.getJSON(data.next, this.getFeatures.bind(this, source))
            } else {
                $(this.node).trigger('addfeatures');
            }
        },

        createFeature: function (room) {
            return new ol.Feature({
                geometry: new ol.geom.Point(transformPosition(room)),
                name: room.id,
                description: room.description,
                focus: this.room_id && room.id === this.room_id
            });
        },

        /**
         * Detects overlapping nodes on threshold zoom and creates an overlay
         * displaying the rooms that overlap.
         */
        addOverlappingNodesDetection: function() {
            var self = this;
            var _detectMaxZoom = function() {
                if (self.overlaysVisible || self.view.getZoom() >= self.view.getMaxZoom()) {
                    self.showOverlays();
                } else {
                    self.hideOverlays();
                }
            };

            // Throttle the zoom detection
            var throttleInterval = 200;  // ms
            var detectMaxZoom = _.throttle(_detectMaxZoom, throttleInterval, {leading: false});
            this.view.on('change:resolution', detectMaxZoom);
            _detectMaxZoom();
        },

        /**
         * Shows overlays for all clusternodes that exist on max zoom
         */
        showOverlays: function() {
            var self = this;
            var extent = this.view.calculateExtent(this.map.getSize());

            // Find features that are clusters
            var featuresToDraw = this.clusterSource.getFeaturesInExtent(extent).filter(function(feature) {
                var features = feature.get('features');
                return features.length > 1;
            });

            // Draw the overlay for all the clusters
            if (featuresToDraw.length >= 1) {
                this.hideOverlays();
                featuresToDraw.forEach(function(feature) {
                    var id = feature.get('features').map(function(f) {
                        return f.get('name');
                    }).join('-');
                    self.showOverlay(id, feature);
                });
                this.overlaysVisible = true;
                $(this.node).trigger('changeOverlaysVisibility');
            }
        },

        /**
         * If overlay already exists, display it, otherwise create and display it.
         */
        showOverlay: function(id, feature) {
            if (id in this.overlays) {
                this.overlays[id].setPosition(feature.getGeometry().getCoordinates());
            } else {
                var overlay = this.createOverlay(feature);
                this.overlays[id] = overlay;
                this.map.addOverlay(overlay);
            }
        },

        hideOverlays: function() {
            _.each(this.overlays, function(overlay) {
                overlay.setPosition(undefined);
            });
            this.overlaysVisible = false;
            $(this.node).trigger('changeOverlaysVisibility');
        },

        createOverlay: function(feature) {
            var $list = $('<ul class=no-bullet>');
            $list.css({
                "background-color": "white",
                "border": "1px solid #ccc",
                "opacity": ".7",
                "padding": "0 .5em",
                "margin": "1em 0 0 0"
            });
            var features = feature.get('features');
            features.sort(function(a, b) {
                var nameA = a.get('name');
                var nameB = b.get('name');
                return nameA.localeCompare(nameB);
            });
            $list.append(features.map(function(feature) {
                var name = feature.get('name');
                var imageSrc = feature.get('focus') ? focusMarkerImage : primaryMarkerImage;
                var $link = $('<a>')
                    .attr('href', NAV.urls.room_info_base + name)
                    .attr('title', feature.get('description'))
                    .html(name)
                    .css('margin-left', '.5em');
                var $image = $('<img>').attr('src', imageSrc).css('height', '1em');
                return $("<li>").append($image, $link);
            }));
            return new ol.Overlay({
                element: $list.get(0),
                position: feature.getGeometry().getCoordinates(),
                positioning: 'top-center',
            });
        },

    };

    function OverlayToggler(opt_options) {
        var roomMapper = opt_options;
        var button = document.createElement('button');
        button.innerHTML = 'O';

        function handleClick() {
            roomMapper.overlaysVisible = !roomMapper.overlaysVisible;
            if (roomMapper.overlaysVisible) {
                roomMapper.showOverlays();
            } else {
                roomMapper.hideOverlays();
            }
        }

        button.addEventListener('click', handleClick, false);
        button.addEventListener('touchstart', handleClick, false);
        $(roomMapper.node).on('changeOverlaysVisibility', function() {
            button.style.backgroundColor = roomMapper.overlaysVisible ? '#b8bb6f' : '';
        });


        var element = document.createElement('div');
        element.className = 'toggle-overlay ol-control';
        element.title = 'Toggle showing overlapping rooms as a list';
        element.style.top = '65px';
        element.style.left = '.5em';
        element.appendChild(button);

        ol.control.Control.call(this, {
            element: element,
        });
    }
    ol.inherits(OverlayToggler, ol.control.Control);


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
                    color: '#1976D2'
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

    /**
     * On click on marker, go to room info for that room
     * On click on cluster, zoom to rooms in that cluster
     */
    function addClickNavigation(map) {
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
    }


    function getMarkerStyle(text, image) {
        return new ol.style.Style({
            image: new ol.style.Icon({
                src: image,
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
        return getMarkerStyle(text, focusMarkerImage);
    }

    function getMainMarkerStyle(text) {
        return getMarkerStyle(text, primaryMarkerImage);
    }

    return RoomMapper;

});

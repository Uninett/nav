/*
 * Copyright (C) 2009, 2010, 2015 Uninett AS
 *
 * This file is part of Network Administration Visualized (NAV).
 *
 * NAV is free software: you can redistribute it and/or modify it under the
 * terms of the GNU General Public License version 3 as published by the Free
 * Software Foundation.
 *
 * This program is distributed in the hope that it will be useful, but WITHOUT
 * ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
 * FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
 * more details.  You should have received a copy of the GNU General Public
 * License along with NAV. If not, see <http://www.gnu.org/licenses/>.
 */

/*
 * NetworkLayer.js: OpenLayers layer which shows network information.
 *
 * The information is downloaded from a URL (parametrized by the
 * location, zoom level and size of the map) and reloaded when the map
 * is zoomed or moved (unless the movement is small).
 *
 * The downloaded information is expected to be in GeoJSON format,
 * with additional properties for size/color of features and text to
 * show in popup boxes when clicking on them.
 */


DelayedBBOX = OpenLayers.Class(OpenLayers.Strategy.BBOX, {
    /**
     * A BBOX strategy that delays the update until a certain time has passed.
     * This is done to avoid fetching data for each zoom and pan.
     */

    update: function (options) {
        var self = this,
            timeout = 500;  // Time in milliseconds to wait before requesting update

        if (this.timer) {
            clearTimeout(this.timer);
        }

        this.timer = setTimeout(function () {
            OpenLayers.Strategy.BBOX.prototype.update.call(self, options);
        }, timeout);

    }
});


NetworkLayer = OpenLayers.Class(OpenLayers.Layer.Vector, {

    /*
     * Constructor.
     *
     * Arguments:
     *
     * name -- name of the layer
     *
     * url -- URL for retrieving network data
     *
     * timeInterval -- object containing two functions start and end,
     * which should return the boundaries of the current time interval
     *
     * options -- arbitrary properties to set on the object
     */
    initialize: function(name, url, timeInterval, options) {

        // Default style for points and lines:
        var style = new OpenLayers.StyleMap({
            pointRadius: 15,
            strokeWidth: 10,
            strokeOpacity: 0.9,
            strokeLinecap: 'butt',
            fillOpacity: 0.7,
            fillColor: 'black',
            strokeColor: 'red',
            graphicZIndex: 1
        });

        // Add rules for overriding style based on properties of the
        // objects:
        style.addUniqueValueRules('default', 'type', {
            node: {
                fillColor: '${color}',
                strokeColor: 'black',
                strokeWidth: 3,
                pointRadius: '${size}',
                graphicZIndex: 2
            },
            edge: {
                strokeColor: '${color}',
                strokeWidth: '${size}',
                graphicZIndex: 1,
                strokeOpacity: 0.7
            }
        });

        // From a function of no arguments returning a Time object,
        // create a function which returns the same time formatted in
        // RRD syntax (used for creating parameters below):
        function formattedTime(timeFunc) {
            return function () {
                return timeFunc().format('%H:%M_%Y%m%d');
            };
        }

        // A "strategy" takes care of automatically downloading data.
        // The BBOX strategy reacts to moving and zooming.
        this.bboxStrategy = new DelayedBBOX({resFactor: 1.1});

        // Reference to this for use in functions below which are not
        // called on this object:
        var thisObj = this;

        // Checkboxes that toggles map state
        // edgeToggler: toggles whether we add edges between nodes
        // dataToggler: toggles whether we fetch cpu and interface load
        var edgeToggler = document.getElementById('edge-toggler'),
            edgeStorageKey = 'nav.geomap.edge-toggler',
            dataToggler = document.getElementById('data-toggler'),
            dataStorageKey = 'nav.geomap.data-toggler';

        // Update default values from localStorage
        var edgeItem = localStorage.getItem(edgeStorageKey),
            dataItem = localStorage.getItem(dataStorageKey);
        edgeToggler.checked = !edgeItem || edgeItem === 'true';
        dataToggler.checked = !dataItem || dataItem === 'true';

        // Trigger update of map when we toggle the checkboxes
        edgeToggler.onclick = function() {
            localStorage.setItem(edgeStorageKey, edgeToggler.checked);
            thisObj.update();
        };
        dataToggler.onclick = function() {
            localStorage.setItem(dataStorageKey, dataToggler.checked);
            thisObj.update();
        };

        // Add the strategy from above and a "protocol" (which
        // determines how to download data), as well as the style map
        // we created, to the options we pass to the superclass
        // constructor:
        options = extend({
            strategies: [this.bboxStrategy],
            protocol: new MyHTTPProtocol({
                url: url,
                params: {
                    format: 'geojson',
                    limit: 30,
                },
                dynamicParams: {
                    viewportWidth: function () {
                        return thisObj.map.getSize().w;
                    },
                    viewportHeight: function () {
                        return thisObj.map.getSize().h;
                    },
                    create_edges: function() {
                        return edgeToggler.checked;
                    },
                    fetch_data: function() {
                        return dataToggler.checked;
                    },
                    timeStart: formattedTime(timeInterval.start),
                    timeEnd: formattedTime(timeInterval.end)
                },
                format: new OpenLayers.Format.GeoJSON()
            }),
            styleMap: style,
            rendererOptions: {zIndexing: true},
        }, options);

        OpenLayers.Layer.Vector.prototype.initialize.apply(this, [name, options]);

        this.popupControl = new PopupControl(this);
    },

    /*
     * Reload the network data.
     */
    update: function () {
        this.bboxStrategy.triggerRead();
    },

    /*
     * Callback function for map movement.
     */
    onMapMove: function () {
        this.redraw();
    },

    /*
     * Set the map this layer belongs to.
     */
    setMap: function (map) {
        if (this.map)
            this.map.removeControl(this.popupControl);
        OpenLayers.Layer.Vector.prototype.setMap.apply(this, arguments);
        map.events.register('move', this, this.onMapMove);
        map.addControl(this.popupControl);
        this.popupControl.activate();
    },

    CLASS_NAME: "NetworkLayer"

});

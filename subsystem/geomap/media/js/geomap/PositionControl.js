/*
 * Copyright (C) 2009 UNINETT AS
 *
 * This file is part of Network Administration Visualized (NAV).
 *
 * NAV is free software: you can redistribute it and/or modify it under the
 * terms of the GNU General Public License version 2 as published by the Free
 * Software Foundation.
 *
 * This program is distributed in the hope that it will be useful, but WITHOUT
 * ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
 * FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
 * more details.  You should have received a copy of the GNU General Public
 * License along with NAV. If not, see <http://www.gnu.org/licenses/>.
 */

PositionControl = OpenLayers.Class(OpenLayers.Control, {

    elemIds: {},

    projection: new OpenLayers.Projection('EPSG:4326'),

    initialize: function(elemIds, options) {
	OpenLayers.Control.prototype.initialize.apply(this, arguments);
	var callbacks = {
	    'click': this.click,
	    'dblclick': this.doubleClick
	};
	this.handler = new OpenLayers.Handler.Click(this, callbacks, {double:true});
	this.elemIds = {
	    'clickedPos': 'clickedPos',
	    'clickedPosUtm': 'clickedPosUtm',
	    'centerPos': 'centerPos',
	    'centerPosUtm': 'centerPosUtm',
	    'setClickedPosAsCenter': 'setClickedPosAsCenter',
	    'setClickedPosUtmAsCenter': 'setClickedPosUtmAsCenter',
	};
	var i;
	for (i in elemIds)
	    this.elemIds[i] = elemIds[i];

	/*
	  if (this.elem('gotoPos')) {
	  this.elem('gotoPos').onclick = (function(t) {
	  return function() { t.gotoPosition(); };
	  })(this);
	  }
	*/
	var gotoPosHandler = (function(t) {
	    return function(type) {
		return function() {
		    t.gotoPosition(type, this);
		};
	    };
	})(this);
	var setCenterHandler = (function(t) {
	    return function() {
		t.elem('centerPos').value = t.elem('clickedPos').value;
		t.gotoPosition('lonlat', t.elem('centerPos'));
	    };					
	})(this);
	var setCenterHandlerUtm = (function(t) {
	    return function() {
		t.elem('centerPosUtm').value = t.elem('clickedPosUtm').value;
		t.gotoPosition('utm', t.elem('centerPosUtm'));
	    };					
	})(this);
	var e;
	if (e = this.elem('centerPos'))
	    e.onchange = gotoPosHandler('lonlat');
	if (e = this.elem('centerPosUtm'))
	    e.onchange = gotoPosHandler('utm');
	if (e = this.elem('setClickedPosAsCenter'))
	    e.onclick = setCenterHandler;
	if (e = this.elem('setClickedPosUtmAsCenter'))
	    e.onclick = setCenterHandlerUtm;
    },

    click: function(event) {
	var lonlat = fromMapCoords(this.map.getLonLatFromPixel(event.xy),
				   this.map);
	var e;
	if (e = this.elem('clickedPos'))
	    e.value = lonLatToStr(lonlat);
	if (e = this.elem('clickedPosUtm'))
	    e.value = utmToStr(lonLatToUtm(lonlat));

	/*
	  this.evt = event;
	  var lonlat = this.map.getLonLatFromPixel(event.xy);
	  lonlat.transform(this.map.getProjectionObject(),
	  this.projection);
	  if (this.elemIds.clickedPos) {
	  var id = this.elemIds.clickedPos;
	  var elem = document.getElementById(id);
	  elem.value = lonLatToStr(lonlat);
	  }
	*/
    },

    doubleClick: function(event) {
	this.evt = event;
    },

    

    /*
     * Function called after a map movement (panning or zooming)
     * is finished.
     */
    onMapMoveEnd: function() {
	var e;
	var pos = fromMapCoords(this.map.getCenter(), this.map);
	if (e = this.elem('centerPos'))
	    e.value = lonLatToStr(pos);
	if (e = this.elem('centerPosUtm'))
	    e.value = utmToStr(lonLatToUtm(pos));
    },

    /*
     * Override setMap to register our onMapMoveEnd function on
     * the map's 'moveend' event.
     */
    setMap: function(map) {
	OpenLayers.Control.prototype.setMap.apply(this, arguments);
	map.events.register('moveend', this, this.onMapMoveEnd);
    },



    gotoPosition: function(type, elem) {
 	var parseFunc = (type=='utm') ? utmStrToLonLat : parseLonLat;
	var lonlat = parseFunc(elem.value);
	lonlatFoo = lonlat.clone();
	lonlat.transform(this.projection,
			 this.map.getProjectionObject());
	lonlatBar = lonlat;
	this.map.setCenter(lonlat);
    },

    elem: function(name) {
	var id = this.elemIds[name];
	if (!id) return null;
	return document.getElementById(id);
    },

});


/*
 * Copyright (C) 2009, 2010 Uninett AS
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
 * coordinates.js -- conversion between coordinate formats and between
 * internal and string forms of the formats.
 */

var normalProjection = new OpenLayers.Projection("EPSG:4326");
var coordinatePrintPrecision = 7;

/*
 * UTM
 */

/*
 * Find the EPSG projection name to use for UTM projection in a given
 * zone and hemisphere.
 *
 * Information about EPSG projections can be found at:
 * -- http://www.epsg-registry.org/
 * -- http://spatialreference.org/
 */
function utmProjectionName(zone, hemisphere) {
    return 'EPSG:32' + (hemisphere=='N'?'6':'7') + zone;
}

/*
 * Projection object for UTM in a specified zone.
 */
function utmProjection(zone, hemisphere) {
    var projName = utmProjectionName(zone, hemisphere);
    return new OpenLayers.Projection(projName);
}

/*
 * Parse a string containing UTM coordinates.
 *
 * The following format is expected (note: this is not the only way to
 * format UTM coordinates, and may not even be a common way to do it):
 *
 * Zone number (two digits), directly followed by hemisphere ('N'/'S');
 * whitespace;
 * northings and eastings (in this order!), separated by whitespace.
 *
 * The hemisphere may be omitted, in which case 'N' is assumed.
 *
 * Returns an object with properties zone, hemisphere, n, e.
 */
function parseUtm(utmStr) {
    var defaultHemisphere = 'N';
    var utmRE = /^\W*([0-9][0-9])([NS]?)\W+([0-9]*[.]?[0-9]+)\W+([0-9]*[.]?[0-9]+)\W*$/;
    var arr = utmRE.exec(utmStr);
    if (arr == null) {
	throw 'error: incorrectly formatted UTM string "' +
	    utmStr + '"';
    }
    var utm = {};
    utm.zone = arr[1];
    utm.hemisphere = (arr[2]=='' ? defaultHemisphere : arr[2]);
    utm.n = arr[3];
    utm.e = arr[4];
    return utm;
}

/*
 * Format UTM coordinates as a string.
 */
function utmToStr(utm) {
    return format('%d%s %d %d',
		  utm.zone, utm.hemisphere, utm.n, utm.e);
}



/*
 * Longitude/latitude pairs.
 */

/*
 * Parse a string containing latitude/longitude coordinates.
 *
 * The string is expected to be on the form latitude, comma, any
 * amount of whitespace (including none), longitude.
 *
 * Returns an instance of OpenLayers.LonLat.
 */
function parseLonLat(llStr) {
    var re = /^([0-9]*[.]?[0-9]+), *([0-9]*[.]?[0-9]+)$/;
    var arr = re.exec(llStr);
    if (arr == null)
	throw 'error: incorrectly formatted latitude, longitude string "' +
	llStr + '"';
    return new OpenLayers.LonLat(arr[2], arr[1]);
}

/*
 * Format a longitude/latitude object as a string.
 */
function lonLatToStr(lonlat) {
    return format('%7f, %6f', lonlat.lat, lonlat.lon);
}



/*
 * Convertions.
 */

/*
 * Convert UTM coordinates given as a string to a longitude/latitude object.
 *
 * See parseUtm for expected format of the UTM string.
 *
 * Returns an instance of OpenLayers.LonLat.
 */
function utmStrToLonLat(utmStr) {
    return utmToLonLat(parseUtm(utmStr));
}

/*
 * Convert UTM coordinates to longitude/latitude.
 */
function utmToLonLat(utm) {
    var point = new OpenLayers.LonLat(utm.e, utm.n);
    var proj = utmProjection(utm.zone, utm.hemisphere);
    //this.utmProj = proj;
    /*
      for (var i = 0; i < 10000; i++)
      if (proj.proj.readyToUse)
      break;
    */
    if (!proj.proj.readyToUse)
	throw 'error: projection not ready';
    return point.transform(proj, normalProjection);
}

/*
 * Convert longitude/latitude to UTM.
 */
function lonLatToUtm(lonlat) {
    var utm = {};
    utm.zone = utmZone(lonlat);
    utm.hemisphere = utmHemisphere(lonlat);
    var point = lonlat.clone();
    var proj = utmProjection(utm.zone, utm.hemisphere);
    if (!proj.proj.readyToUse)
	throw 'error: projection not ready';
    point.transform(normalProjection, proj);
    utm.n = point.lat;
    utm.e = point.lon;
    return utm;
}


/*
 * Gives the UTM zone number for a (lon,lat) pair. We take into
 * account the irregular zones around Norway and Svalbard, but not the
 * four special zones for the polar regions.
 *
 * Source: http://en.wikipedia.org/wiki/Universal_Transverse_Mercator_coordinate_system
 *
 * Exact positions of irregular zones stolen from the
 * LatLonUTMConversion Python file available at http://pygps.org/.
 */
function utmZone(lonlat) {
    var lon = lonlat.lon;
    var lat = lonlat.lat;
    
    var zone = Math.floor((lon+180) / 6) + 1;
    // zone 32 extended at southern part of Norway:
    if (lat >= 56 && lat < 64 &&
	lon >= 3  && lon < 12)
	zone = 32;
    // zones around Svalbard are completely crazy:
    if (lat >= 72 && lat < 84) {
	if (lon >=  0 && lon <  9) zone = 31;
	if (lon >=  9 && lon < 21) zone = 33;
	if (lon >= 21 && lon < 33) zone = 35;
	if (lon >= 33 && lon < 42) zone = 37;
    }
    return zone;
}

/*
 * The hemisphere a (lon,lat) pair lies in. 'N' for northern
 * hemisphere, 'S' for southern.
 */
function utmHemisphere(lonlat) {
    return (lonlat.lat < 0) ? 'S' : 'N';
}





function fromMapCoords(lonlat, map) {
    var newLonlat = lonlat.clone();
    newLonlat.transform(map.getProjectionObject(),
			normalProjection);
    return newLonlat;
}

function toMapCoords(lonlat, map) {
    var newLonlat = lonlat.clone();
    newLonlat.transform(normalProjection,
			map.getProjectionObject());
    return newLonlat;
}

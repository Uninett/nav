#
# Copyright (C) 2009, 2010 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 2 as published by the Free
# Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#

"""Coordinate transformation.

Functions for converting between UTM and longitude/latitude, and for
parsing a string representation of UTM.

Derived from code available under GPL from http://pygps.org/
(http://pygps.org/LatLongUTMconversion-1.2.tar.gz)

"""

from math import pi, sin, cos, tan, sqrt
import re


_deg2rad = pi / 180.0
_rad2deg = 180.0 / pi

_equatorial_radius = 2
_eccentricity_squared = 3

_ellipsoid = [
#  id, Ellipsoid name, Equatorial Radius, square of eccentricity	
# first once is a placeholder only, To allow array indices to match id numbers
	[ -1, "Placeholder", 0, 0],
	[ 1, "Airy", 6377563, 0.00667054],
	[ 2, "Australian National", 6378160, 0.006694542],
	[ 3, "Bessel 1841", 6377397, 0.006674372],
	[ 4, "Bessel 1841 (Nambia] ", 6377484, 0.006674372],
	[ 5, "Clarke 1866", 6378206, 0.006768658],
	[ 6, "Clarke 1880", 6378249, 0.006803511],
	[ 7, "Everest", 6377276, 0.006637847],
	[ 8, "Fischer 1960 (Mercury] ", 6378166, 0.006693422],
	[ 9, "Fischer 1968", 6378150, 0.006693422],
	[ 10, "GRS 1967", 6378160, 0.006694605],
	[ 11, "GRS 1980", 6378137, 0.00669438],
	[ 12, "Helmert 1906", 6378200, 0.006693422],
	[ 13, "Hough", 6378270, 0.00672267],
	[ 14, "International", 6378388, 0.00672267],
	[ 15, "Krassovsky", 6378245, 0.006693422],
	[ 16, "Modified Airy", 6377340, 0.00667054],
	[ 17, "Modified Everest", 6377304, 0.006637847],
	[ 18, "Modified Fischer 1960", 6378155, 0.006693422],
	[ 19, "South American 1969", 6378160, 0.006694542],
	[ 20, "WGS 60", 6378165, 0.006693422],
	[ 21, "WGS 66", 6378145, 0.006694542],
	[ 22, "WGS-72", 6378135, 0.006694318],
	[ 23, "WGS-84", 6378137, 0.00669438]
]

#Reference ellipsoids derived from Peter H. Dana's website- 
#http://www.utexas.edu/depts/grg/gcraft/notes/datum/elist.html
#Department of Geography, University of Texas at Austin
#Internet: pdana@mail.utexas.edu
#3/22/95

#Source
#Defense Mapping Agency. 1987b. DMA Technical Report: Supplement to Department of Defense World Geodetic System
#1984 Technical Report. Part I and II. Washington, DC: Defense Mapping Agency

def ll_to_utm(reference_ellipsoid, lat, lon, zone = None):
    """converts lat/long to UTM coords.  Equations from USGS Bulletin 1532 
    East Longitudes are positive, West longitudes are negative. 
    North latitudes are positive, South latitudes are negative
    lat and Long are in decimal degrees
    Written by Chuck Gantz- chuck.gantz@globalstar.com"""

    a = _ellipsoid[reference_ellipsoid][_equatorial_radius]
    ecc_squared = _ellipsoid[reference_ellipsoid][_eccentricity_squared]
    k0 = 0.9996

#Make sure the longitude is between -180.00 .. 179.9
    lon_tmp = (lon+180)-int((lon+180)/360)*360-180 # -180.00 .. 179.9

    lat_rad = lat*_deg2rad
    lon_rad = lon_tmp*_deg2rad

    if zone is None:
        zone_number = int((lon_tmp + 180)/6) + 1
    else:
        zone_number = zone
  
    if lat >= 56.0 and lat < 64.0 and lon_tmp >= 3.0 and lon_tmp < 12.0:
        zone_number = 32

    # Special zones for Svalbard
    if lat >= 72.0 and lat < 84.0:
        if lon_tmp >= 0.0 and lon_tmp < 9.0:
            zone_number = 31
        elif lon_tmp >= 9.0  and lon_tmp < 21.0:
            zone_number = 33
        elif lon_tmp >= 21.0 and lon_tmp < 33.0:
            zone_number = 35
        elif lon_tmp >= 33.0 and lon_tmp < 42.0:
            zone_number = 37

    lon_origin = (zone_number - 1)*6 - 180 + 3 #+3 puts origin in middle of zone
    lon_origin_rad = lon_origin * _deg2rad

    #compute the UTM Zone from the latitude and longitude
    utm_zone = "%d%c" % (zone_number, _utm_letter_designator(lat))

    ecc_prime_squared = (ecc_squared)/(1-ecc_squared)
    N = a/sqrt(1-ecc_squared*sin(lat_rad)*sin(lat_rad))
    T = tan(lat_rad)*tan(lat_rad)
    C = ecc_prime_squared*cos(lat_rad)*cos(lat_rad)
    A = cos(lat_rad)*(lon_rad-lon_origin_rad)

    M = a*((1
            - ecc_squared/4
            - 3*ecc_squared*ecc_squared/64
            - 5*ecc_squared*ecc_squared*ecc_squared/256)*lat_rad 
           - (3*ecc_squared/8
              + 3*ecc_squared*ecc_squared/32
              + 45*ecc_squared*ecc_squared*ecc_squared/1024)*sin(2*lat_rad)
           + (15*ecc_squared*ecc_squared/256 + 45*ecc_squared*ecc_squared*ecc_squared/1024)*sin(4*lat_rad) 
           - (35*ecc_squared*ecc_squared*ecc_squared/3072)*sin(6*lat_rad))
    
    utm_easting = (k0*N*(A+(1-T+C)*A*A*A/6
                        + (5-18*T+T*T+72*C-58*ecc_prime_squared)*A*A*A*A*A/120)
                  + 500000.0)

    utm_northing = (k0*(M+N*tan(lat_rad)*(A*A/2+(5-T+9*C+4*C*C)*A*A*A*A/24
                                        + (61
                                           -58*T
                                           +T*T
                                           +600*C
                                           -330*ecc_prime_squared)*A*A*A*A*A*A/720)))

    if lat < 0:
        utm_northing = utm_northing + 10000000.0; #10000000 meter offset for southern hemisphere
    return (utm_zone, utm_easting, utm_northing)


def _utm_letter_designator(lat):
    """This routine determines the correct UTM letter designator for the given latitude
    returns 'Z' if latitude is outside the UTM limits of 84N to 80S
    Written by Chuck Gantz- chuck.gantz@globalstar.com"""

    if 84 >= lat >= 72: return 'X'
    elif 72 > lat >= 64: return 'W'
    elif 64 > lat >= 56: return 'V'
    elif 56 > lat >= 48: return 'U'
    elif 48 > lat >= 40: return 'T'
    elif 40 > lat >= 32: return 'S'
    elif 32 > lat >= 24: return 'R'
    elif 24 > lat >= 16: return 'Q'
    elif 16 > lat >= 8: return 'P'
    elif  8 > lat >= 0: return 'N'
    elif  0 > lat >= -8: return 'M'
    elif -8 > lat >= -16: return 'L'
    elif -16 > lat >= -24: return 'K'
    elif -24 > lat >= -32: return 'J'
    elif -32 > lat >= -40: return 'H'
    elif -40 > lat >= -48: return 'G'
    elif -48 > lat >= -56: return 'F'
    elif -56 > lat >= -64: return 'E'
    elif -64 > lat >= -72: return 'D'
    elif -72 > lat >= -80: return 'C'
    else: return 'Z'	# if the Latitude is outside the UTM limits

def utm_to_ll(reference_ellipsoid, northing, easting, zone):
    """converts UTM coords to lat/long.  Equations from USGS Bulletin 1532 
    East Longitudes are positive, West longitudes are negative. 
    North latitudes are positive, South latitudes are negative
    lat and lon are in decimal degrees. 
    Written by Chuck Gantz- chuck.gantz@globalstar.com
    Converted to Python by Russ Nelson <nelson@crynwr.com>"""

    k0 = 0.9996
    a = _ellipsoid[reference_ellipsoid][_equatorial_radius]
    ecc_squared = _ellipsoid[reference_ellipsoid][_eccentricity_squared]
    e1 = (1-sqrt(1-ecc_squared))/(1+sqrt(1-ecc_squared))
    #northern_hemisphere; //1 for northern hemispher, 0 for southern

    x = easting - 500000.0 #remove 500,000 meter offset for longitude
    y = northing

    zone_letter = zone[-1]
    zone_number = int(zone[:-1])
    if zone_letter >= 'N':
        northern_hemisphere = 1  # point is in northern hemisphere
    else:
        northern_hemisphere = 0  # point is in southern hemisphere
        y -= 10000000.0         # remove 10,000,000 meter offset used for southern hemisphere

    lon_origin = (zone_number - 1)*6 - 180 + 3  # +3 puts origin in middle of zone

    ecc_prime_squared = (ecc_squared)/(1-ecc_squared)

    M = y / k0
    mu = M/(a*(1-ecc_squared/4-3*ecc_squared*ecc_squared/64-5*ecc_squared*ecc_squared*ecc_squared/256))

    phi1_rad = (mu + (3*e1/2-27*e1*e1*e1/32)*sin(2*mu) 
               + (21*e1*e1/16-55*e1*e1*e1*e1/32)*sin(4*mu)
               +(151*e1*e1*e1/96)*sin(6*mu))
    phi1 = phi1_rad*_rad2deg;

    N1 = a/sqrt(1-ecc_squared*sin(phi1_rad)*sin(phi1_rad))
    T1 = tan(phi1_rad)*tan(phi1_rad)
    C1 = ecc_prime_squared*cos(phi1_rad)*cos(phi1_rad)
    R1 = a*(1-ecc_squared)/pow(1-ecc_squared*sin(phi1_rad)*sin(phi1_rad), 1.5)
    D = x/(N1*k0)

    lat = phi1_rad - (N1*tan(phi1_rad)/R1)*(D*D/2-(5+3*T1+10*C1-4*C1*C1-9*ecc_prime_squared)*D*D*D*D/24
                                          +(61+90*T1+298*C1+45*T1*T1-252*ecc_prime_squared-3*C1*C1)*D*D*D*D*D*D/720)
    lat = lat * _rad2deg

    lon = (D-(1+2*T1+C1)*D*D*D/6+(5-2*C1+28*T1-3*C1*C1+8*ecc_prime_squared+24*T1*T1)
            *D*D*D*D*D/120)/cos(phi1_rad)
    lon = lon_origin + lon * _rad2deg
    return (lat, lon)


def parse_utm(utm_str):
    """Parse UTM coordinates from a string.

    utm_str should be a string of the form 'zh n e', where z is a zone
    number, h a hemisphere identifier ('N' or 'S') and n and e the
    northing and easting.  h may be omitted, in which case 'N' is
    assumed.

    Return value: dictionary with keys (zone, hemisphere, n, e).

    """
    default_hemisphere = 'N'
    utm_re = '^\W*([0-9][0-9])([NS]?)\W+([0-9]*[.]?[0-9]+)\W+([0-9]*[.]?[0-9]+)\W*$'
    m = re.match(utm_re, utm_str)
    if m is None:
        raise Exception('incorrectly formatted UTM string "' + utm_str)
    utm = {}
    utm['zone'] = int(m.group(1))
    utm['hemisphere'] = m.group(2)
    if utm['hemisphere'] == '':
        utm['hemisphere'] = default_hemisphere
    utm['n'] = float(m.group(3))
    utm['e'] = float(m.group(4))
    return utm


def utm_str_to_lonlat(utm_str):
    """Convert UTM coordinates in string form (see parse_utm) to a
    (longitude,latitude) pair.

    """
    utm = parse_utm(utm_str)
    (lat, lon) = utm_to_ll(23, utm['n'], utm['e'],
                           '%d%s'%(utm['zone'], utm['hemisphere']))
    return (lon, lat)




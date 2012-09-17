#
# nav.py
# Navigation in Python
#
# Version 1.0
#
# (c) 2005-2006 Scott Raynel <scottraynel@gmail.com>
#
# The University of Waikato WAND Network Research Group
#
# Provides a GeoPoint class to encapsulate latitude and longitude data in both
# decimal and DMS formats, as well as providing an implementation of the
# algorithms to calculate distance (Great Circle) and bearings between two
# points, as well as useful helper functions.
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301,
# USA.
#

import math

# An approximation of the Earth's radius, in kilometers.
# 6367 is regarded as a good approximation, as it is based on the definition
# of the nautical mile. It lies between the currently accepted WGS84
# equatorial and polar radii of 6378 km and 6356 km repectively.
EARTH_RADIUS = 6367

class GeoPoint:
    """ Encapsulates latitude and longitude information.

    This class encapsulates latitude and longitude information, which can be
    specified in either decimal or DMS (degrees-minutes-seconds) format. When
    a "set" operation is performed, both representations will be stored
    internally. See the set_ and get_ methods for more information. """

    mLatitude = ("",0,0,0)
    mLatitudeDec = 0
    mLongitude = ("",0,0,0)
    mLongitudeDec = 0
    
    def set_latitude(self,(d,deg,mins,sec)):
        """ Sets the latitude of the GeoPoint object in DMS format.

        Param (d,deg,mins,sec) is a tuple where:
            d - a char representing direction, can be 'n','N','S' or 's'.
            deg - a float representing degrees
            mins - a float representing minutes
            sec - a float representing seconds.
            
        Raises an Exception if d is not valid.
        """

        if not (d=="N" or d=="n" or d=="S" or d=="s"):
            raise Exception("Latitude must be either N or S")
        self.mLatitude = (d,deg,mins,sec)
        self.mLatitudeDec = dms_to_dec(self.mLatitude)

    def set_longitude(self,(d,deg,mins,sec)):
        """ Sets the longitude of the GeoPoint object in DMS format.

        Param (d,deg,mins,sec) is a tuple where:
            d - a char representing direction, can be 'e','E','w' or 'W'.
            deg - a float representing degrees
            mins - a float representing minutes
            sec - a float representing seconds.

        Raises an Exception if d is not valid.
        """

        if not (d=="E" or d=="e" or d=="W" or d=="w"):
            raise Exception("Longitude must be either E or W")
        self.mLongitude = (d,deg,mins,sec)
        self.mLongitudeDec = dms_to_dec(self.mLongitude)

    def get_latitude(self):
        """ Returns the latitude of the GeoPoint object in DMS.

        Returns a tuple in the same format as given in set_latitude()
        """

        return self.mLatitude 

    def get_longitude(self):
        """ Returns the longitude of the GeoPoint object in DMS.

        Returns a tuple in the same format as given in set_longitude()
        """

        return self.mLongitude

    def set_latitude_dec(self, lat):
        """ Sets the latitude of the GeoPoint object in decimal format.

        Param lat is a float specifying the decimal latitude.
        """

        self.mLatitude = dec_to_dms(lat, lat = 1)
        self.mLatitudeDec = lat

    def set_longitude_dec(self, longitude):
        """ Sets the longitude of the GeoPoint object in decimal format.

        Param longitude is a float specifying the decimal longitude.
        """

        self.mLongitude = dec_to_dms(longitude, lat = 0)
        self.mLongitudeDec = longitude

    def get_latitude_dec(self):
        """ Gets the latitude of the GeoPoint object in decimal format.
        """
        return self.mLatitudeDec

    def get_longitude_dec(self):
        """ Gets the longitude of the GeoPoint object in decimal format.
        """
        return self.mLongitudeDec
    
    def get_distance_to(self, otherpoint):
        """ Calculates the distance from this GeoPoint to another GeoPoint.

        This method takes a GeoPoint object as a parameter and calculates the
        Great Circle Distance between the two points, returning a distance in
        kilometers. """

        lat1 = self.mLatitudeDec
        long1 = self.mLongitudeDec
        lat2 = otherpoint.get_latitude_dec()
        long2 = otherpoint.get_longitude_dec()
        return gcdist(lat1,long1,lat2,long2)

    def get_bearing_to(self, otherpoint):
        """ Calculates the compass bearing from this GeoPoint object to
        another GeoPoint object.

        This method takes a GeoPoint object as a parameter and calculates the
        bearing between the two points, using spherical geometry."""

        lat1 = self.mLatitudeDec
        long1 = self.mLongitudeDec
        lat2 = otherpoint.get_latitude_dec()
        long2 = otherpoint.get_longitude_dec()
        return bearing(lat1,long1,lat2,long2)

    def to_string(self):
        """ Returns a string representation of the GeoPoint.

        Returns a string formatted in DMS format, e.g:
          "37:56:12 S, 125:23:24 E"
        """

        (lad, ladeg, lamins, lasec) = self.mLatitude
        (lod, lodeg, lomins, losec) = self.mLongitude
        return "%s:%s:%s %s, %s:%s:%s %s" % (ladeg,lamins,lasec,lad,
                                             lodeg,lomins,losec,lod)
                                             
    
def dms_to_dec((d,deg,mins,sec)):
    """ Converts a location in DMS to decimal """

    dec = deg + (((sec / 60.0) + mins) / 60.0)
    if d == "W" or d == "w" or d == "S" or d == "s":
        dec = -dec
    return dec
    
def dec_to_dms(dec, lat = 1):
    """ Converts a location in decimal to DMS. 

    param dec = the decimal location
    param lat = boolean indicating whether the param dec should be treated as
                indicating latitude. 
    """

    d = ""
    if lat:
        if dec > 0:
            d = "N"
        elif dec < 0:
            d = "S"
    else:
        if dec > 0:
            d = "E"
        elif dec < 0:
            d = "W"
    dec = abs(dec)
    deg = math.floor(dec)
    mins = math.floor((dec-deg)*60)
    sec = math.floor((((dec-deg)*60) - mins) * 60)
    
    return (d, int(deg), int(mins), int(sec))
    

def torad(deg):
    """ Converts degrees to radians. """
    return deg * (math.pi / 180.0)

def todeg(rad):
    """ Converts radians to degrees. """
    return rad * (180.0 / math.pi)

def gcdist(lat1, long1, lat2, long2):
    """ Calculates the Great Circle distance between two points on a sphere,
    in this case, the sphere approximating Earth.
    """
    return EARTH_RADIUS * _gcdist(torad(lat1), torad(long1),
                                  torad(lat2), torad(long2))

def _gcdist(lat1, long1, lat2, long2):
    """ Helper to gcdist()  """
    return 2 * math.asin(math.sqrt((math.sin((lat1-lat2)/2))**2 +
                                   math.cos(lat1)*math.cos(lat2)*
                                   (math.sin((long1-long2)/2))**2))
def bearing(lat1,long1,lat2,long2):
    """ Calculates the bearing between two points on a sphere, and returns the
    result in radians. """
    return _bearing(torad(lat1), torad(long1),
                    torad(lat2), torad(long2))

def _bearing(lat1, long1, lat2, long2):
    """ Helper to bearing() """
    Drad = _gcdist(lat1, long1, lat2, long2)
      
    Crad = math.acos((math.sin(lat2) - (math.sin(lat1) * math.cos(Drad))) /
                       (math.cos(lat1) * math.sin(Drad)))

    Cdeg = todeg(Crad)
    if long1 > long2:
        Cdeg = 360 - Cdeg
    return math.floor(Cdeg)

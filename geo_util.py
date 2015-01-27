import flickrapi
import config
import json
# import time
import requests
import geopy
from geopy.distance import vincenty

def get_neighborhood(loc):
    # Get Flickr API's neighborhood name; NB must throttle at 1/s
    # neighborhood = get_neighborhood(loc)
    #   loc can be 'lat,lng' string or list

    # Parse input
    if type(loc) is str:
        (latitude, longitude) = eval(loc)
    else:
        [latitude, longitude] = loc

    # Query Flickr
    flickr_api = flickrapi.FlickrAPI(config.flickr['api_key'], config.flickr['api_secret'])
    temp_resp = json.loads(flickr_api.places.findByLatLon(lat=latitude, lon=longitude, format='json'))

    # note non-neighborhood names
    neighborhood = temp_resp['places']['place'][0]['woe_name']
    if temp_resp['places']['place'][0]['place_type'] != 'neighbourhood':
        print '%s is not a neighborhood, is %s ' % (temp_resp['places']['place'][0]['woe_name'], temp_resp['places']['place'][0]['place_type'])

    return neighborhood

def google_geo(location):
    # Google location lookup by name

    info = requests.get(
            'https://maps.googleapis.com/maps/api/geocode/json?address='+location+'&sensor=false').json()

    geo = {}
    if info['status'] != 'ZERO_RESULTS':
        geo = {'formatted_address': info['results'][0]['formatted_address'],
            'lat': info['results'][0]['geometry']['location']['lat'],
            'lng': info['results'][0]['geometry']['location']['lng']}
    else:
        print 'Could not find ' + location

    return geo

def geo_bounds(origin, distance):
    ''' get lat,lng bounding box of 'distance' km around a geo point

        geo_box = geo_bounds(origin, distance)

    :param origin: [lat,lng] list
    :param distance: radius in km
    :return: geo_box: (min lat, max lat, min lng, max lng)
    '''

    north = vincenty(kilometers=distance).destination(geopy.Point(origin), 0)
    east = vincenty(kilometers=distance).destination(geopy.Point(origin), 90)
    south = vincenty(kilometers=distance).destination(geopy.Point(origin), 180)
    west = vincenty(kilometers=distance).destination(geopy.Point(origin), 270)

    # get bounding box: (min lat, max lat, min lng, max lng)
    geo_box = (south.latitude, north.latitude, west.longitude, east.longitude)

    return geo_box
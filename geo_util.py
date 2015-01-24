import flickrapi
import config
import json
import time

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
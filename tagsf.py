import pandas as pd
import numpy as np
import flickrapi
import urllib
import json
import time
from datetime import datetime
from PIL import Image
from cStringIO import StringIO
import config

def load_data(reload):
    # (graffiti, flickr, prices) = load_data(reload[, timestamp])
    # if reload is False, timestamp must be provided

    # load SF graffiti reports, flickr #street art reports, Trulia home prices
    if reload:
        now = datetime.now().isoformat().replace(':', '_') # mac doesn't allow ':' in filenames

        ## Load SF city data
        reports = pd.read_csv(
            '%s/Case_Data_from_San_Francisco_311__SF311_.csv' % config.data_path)

        reports = reports[reports['CaseID'].notnull()]
        graffiti = reports[reports['Request Type'] == 'Graffiti'] #9440 results, most recent is Jan 9
        graffiti['Opened'] = pd.to_datetime(graffiti['Opened'])
        graffiti['Closed'] = pd.to_datetime(graffiti['Closed'])
        graffiti['Updated'] = pd.to_datetime(graffiti['Updated'])

        # get neighborhood name from flickr api, to be the same as flickr names
        graffiti['neighborhood'] = graffiti['Point'].apply(get_neighborhood)

        # convert "point" to lat long
        graffiti['latitude'] = graffiti['Point'].apply(get_lat)
        graffiti['longitude'] = graffiti['Point'].apply(get_lng)

        # TO DELETE:
        # DF = DF.drop('column_name', 1)

        # save - this one is important!
        graffiti.to_pickle('%sdf_graffiti-%s' % (config.data_path, now))

        ## Flickr data
        # file_name_csv = 'flickr_data-%s-neighborhood.csv' % config.flickr['file_time'] # has neighborhood
        file_name_csv = 'flickr_data-2015-01-16T19_24_33.067445-neighborhood.csv'
        flickr = pd.read_csv('%s%s' % (config.data_path, file_name_csv))

        # Convert to datetime
        flickr['datetaken'] = pd.to_datetime(flickr['datetaken'])

        flickr.to_pickle('%sdf_flickr-%s' % (config.data_path, now))

        ## Trulia data
        prices = pd.read_csv('%shome_prices.csv' % config.data_path)

        # save
        prices.to_pickle('%sdf_prices-%s' % (config.data_path, now))
    else: # load processed
        print 'Loading...'

        timestamp = '2015-01-19T15_13_52.276380'

        graffiti = pd.read_pickle('%sdf_graffiti-%s' % (config.data_path, timestamp))
        flickr = pd.read_pickle('%sdf_flickr-%s' % (config.data_path, timestamp))
        prices = pd.read_pickle('%sdf_prices-%s' % (config.data_path, timestamp))

    return graffiti, flickr, prices

def get_neighborhood(loc_str):
    # Get Flickr API's neighborhood name; throttled at 1/s

    # Flickr API stuffs
    api_key = '2a8751a5d69541e6c28667835c35cf11'
    api_secret = '6628ef02693fe943'
    flickr_api = flickrapi.FlickrAPI(api_key, api_secret)

    (latitude, longitude) = eval(loc_str)

    # query API
    time.sleep(1) # Flickr limits 3600/hour
    temp_resp = json.loads(flickr_api.places.findByLatLon(lat=latitude, lon=longitude, format='json'))

    # note non-neighborhood names
    neighborhood = temp_resp['places']['place'][0]['woe_name']
    if temp_resp['places']['place'][0]['place_type'] != 'neighbourhood':
        print '%s is not a neighborhood, is %s ' % (temp_resp['places']['place'][0]['woe_name'], temp_resp['places']['place'][0]['place_type'])

    return neighborhood

def google_map(flickr_loc, city_loc):
    # show a Google map of requested lat long pairs
    marker_colors = ['red', 'orange', 'yellow', 'green', 'blue', 'purple']
    bad_marker_colors = ['orange']


    # PASS THE FOLLOWING LINE:
    # flickr_loc = flickr[flickr['datetaken'] > pd.datetime(2015, 1, 1)][['latitude','longitude']]
    flickr_array = flickr_loc.get_values()

    # PASS THE FOLLOWING:
    # city_loc = graffiti[graffiti['Opened'] > pd.datetime(2015, 1, 1)][['latitude','longitude']]
    city_array = city_loc.get_values()

    # Generate URL with markers
    base_url = 'http://maps.googleapis.com/maps/api/staticmap?&size=1000x1000&sensor=false]'

    url_param = ''
    # markers for good hotspots
    url_param = '&markers=size:mid%%7Ccolor:%s' %marker_colors[0]
    for ind in range(0, 15):
        url_param += '&markers=size:mid%%7Ccolor:%s%%7Clabel:%i' \
                     % (marker_colors[0], 1)
        url_param += '%%7C%f,%f' %(flickr_array[ind, 0], flickr_array[ind, 1])

    url_param +=  '&markers=size:mid%%7Ccolor:%s' %marker_colors[0]
    for ind in range(0, 15):
        url_param += '&markers=size:mid%%7Ccolor:%s%%7Clabel:%i' \
                     % (marker_colors[1], 2)
        url_param += '%%7C%f,%f' %(city_array[ind, 0], city_array[ind, 1])


    image_bytes = urllib.urlopen(base_url+url_param).read()
    image = Image.open(StringIO(image_bytes))  # StringIO makes file object out of image data

    Image._show(image)

    return

# # Count cases in each neighborhood, since 2014; most recent is the 12th
# graffiti[graffiti['Opened'] > pd.datetime(2014, 1, 1)].groupby('Neighborhood')['CaseID'].nunique()

# # count instances per neighborhood
# flickr[(flickr['datetaken'] > pd.datetime(2014, 12, 1)) & (flickr['datetaken'] < pd.datetime(2014, 12, 7))].groupby('neighborhood')['url_s'].nunique()


# flickr_loc = flickr[flickr['datetaken'] > pd.datetime(2015, 1, 1)][['latitude','longitude']]
# flickr_array = flickr_loc.get_values()





def get_lat(loc_str):
    (lat, lng) = eval(loc_str)
    return lat

def get_lng(loc_str):
    (lat, lng) = eval(loc_str)
    return lng
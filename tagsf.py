import pandas as pd
import numpy as np
import flickrapi
import json
import time
from datetime import datetime

def load_data(reload):
    # (graffiti, flickr, prices) = load_data(reload[, timestamp])
    # if reload is False, timestamp must be provided

    # load SF graffiti reports, flickr #street art reports, Trulia home prices
    if reload:
        now = datetime.now().isoformat().replace(':', '_') # mac doesn't allow ':' in filenames

        ## Load SF city data
        reports = pd.read_csv(
            '/Users/Alexandra/Dropbox/Projects/Insight/tagsf/data/Case_Data_from_San_Francisco_311__SF311_.csv')

        reports = reports[reports['CaseID'].notnull()]
        graffiti = reports[reports['Request Type'] == 'Graffiti'] #9440 results, most recent is Jan 9
        graffiti['Opened'] = pd.to_datetime(graffiti['Opened'])
        graffiti['Closed'] = pd.to_datetime(graffiti['Closed'])
        graffiti['Updated'] = pd.to_datetime(graffiti['Updated'])

        # get neighborhood name from flickr api, to be the same as flickr names
        graffiti['neighborhood'] = graffiti['Point'].apply(get_neighborhood)

        # TO DELETE:
        # DF = DF.drop('column_name', 1)

        # save - this one is important!
        graffiti.to_pickle('/Users/Alexandra/Dropbox/Projects/Insight/tagsf/data/df_graffiti-%s' % now)

        # # Count cases in each neighborhood, since 2014; most recent is the 12th
        # graffiti[graffiti['Opened'] > pd.datetime(2014, 1, 1)].groupby('Neighborhood')['CaseID'].nunique()

        ## Flickr data
        file_name_csv = 'flickr_data-2015-01-16T19_24_33.067445-neighborhood.csv' # has neighborhood
        flickr = pd.read_csv('data/%s' % file_name_csv)

        # Convert to datetime
        flickr['datetaken'] = pd.to_datetime(flickr['datetaken'])

        flickr.to_pickle('/Users/Alexandra/Dropbox/Projects/Insight/tagsf/data/df_flickr-%s' % now)

        # # count instances per neighborhood
        # flickr[flickr['datetaken'] > pd.datetime(2014, 1, 1)].groupby('neighborhood')['url_s'].nunique()

        ## Trulia data
        prices = pd.read_csv('/Users/Alexandra/Dropbox/Projects/Insight/tagsf/data/home_prices.csv')

        # save
        prices.to_pickle('/Users/Alexandra/Dropbox/Projects/Insight/tagsf/data/df_prices-%s' % now)
    else: # load processed
        print 'Loading...'

        timestamp = '2015-01-19T15_13_52.276380'


        graffiti = pd.read_pickle('/Users/Alexandra/Dropbox/Projects/Insight/tagsf/data/df_graffiti-%s' % timestamp)
        flickr = pd.read_pickle('/Users/Alexandra/Dropbox/Projects/Insight/tagsf/data/df_flickr-%s' % timestamp)
        prices = pd.read_pickle('/Users/Alexandra/Dropbox/Projects/Insight/tagsf/data/df_prices-%s' % timestamp)

    return graffiti, flickr, prices



def get_neighborhood(loc_str):
    # Get Flickr API's neighborhood name; throttled at 1/s

    # Flickr API stuffs
    api_key = '2a8751a5d69541e6c28667835c35cf11'
    api_secret = '6628ef02693fe943'
    flickr = flickrapi.FlickrAPI(api_key, api_secret)

    (latitude, longitude) = eval(loc_str)

    # query API
    time.sleep(1) # Flickr limits 3600/hour
    temp_resp = json.loads(flickr.places.findByLatLon(lat=latitude, lon=longitude, format='json'))

    # note non-neighborhood names
    neighborhood = temp_resp['places']['place'][0]['woe_name']
    if temp_resp['places']['place'][0]['place_type'] != 'neighbourhood':
        print '%s is not a neighborhood, is %s ' % (temp_resp['places']['place'][0]['woe_name'], temp_resp['places']['place'][0]['place_type'])

    return neighborhood
#!/usr/bin/env python

import csv
import time
from datetime import datetime
from pprint import pprint
import flickrapi
import json

# Flickr API stuffs
#TODO : move to local config
api_key = '2a8751a5d69541e6c28667835c35cf11'
api_secret = '6628ef02693fe943'
flickr = flickrapi.FlickrAPI(api_key, api_secret)

fieldnames = sorted(['datetaken', 'datetakengranularity', 'datetakenunknown', 'dateupload', 'latitude', 'longitude', 'owner', 'place_id', 'url_s', 'woeid'])

def get_photos():
   # query flickr api for photos with "#streetart, #graffiti, #mural, #tag, #publicart" within SF

    # get all pages of photo data
    req_page = 1
    now = datetime.now().isoformat().replace(':', '_') # mac doesn't allow ':' in filenames
    with open('/Users/Alexandra/Dropbox/Projects/Insight/tagsf/data/flickr_data-%s.csv' % now, 'w') as output_file:

        # write header
        # writer = csv.DictWriter(output_file, fieldnames=fieldnames, delimiter='\t')
        writer = csv.DictWriter(output_file, fieldnames=fieldnames)
        writer.writeheader()

        req_page = 1
        while True:
            time.sleep(1)
            resp = json.loads(flickr.photos.search(tags='streetart,graffiti,mural,tag,publicart',
                     min_upload_date='1199145600',
                     sort='date-posted-desc',
                     has_geo='True',
                     lat='37.774929500000000000',
                     lon='-122.419415500000010000',
                     radius='9',
                     radius_units='km',
                     extras='date_taken,date_upload,geo,url_s',
                     per_page='500',
                     page=req_page,
                     format='json',
                     nojsoncallback='1'))

            # loop through photos
            for photo in resp['photos']['photo']:
                write_to_file(photo, fieldnames, writer)

            print 'progress: page %i/%i complete' % (resp['photos']['page'], resp['photos']['pages'])

            if resp['photos']['page'] == resp['photos']['pages']:
                break
            else:
                req_page += 1


def write_to_file(photo, fieldnames, writer):
    try:
        relevant_data = {my_key: photo[my_key] for my_key in fieldnames}
        writer.writerow(relevant_data)
    except KeyError, e:
        print 'KeyError, continuing: %s' % e


def get_neighborhood(timestamp):
    # get_neighborhood(timestamp) where timestamp is timestamp of file to update
    # get neighborhood name from lat, long
    # Function written after flickr data was accessed, so we create a second cvs file here,
    #   adding a neighborhood column

    # Working on reading, getting, and writing
    fieldnames_old = sorted(['datetaken', 'datetakengranularity', 'datetakenunknown', 'dateupload', 'latitude', 'longitude', 'owner', 'place_id', 'url_s', 'woeid'])
    fieldnames_new = fieldnames_old + ['neighborhood', 'place_type'] # + is immutable

    with open('flickr_data-%s.csv' % timestamp) as orig_f:
        with open('flickr_data-%s-neighborhood.csv' % timestamp, 'w') as new_f:
            # orig_f = open('flickr_data-2015-01-16T19_24_33.067445.csv')
            # new_f = open('flickr_data-2015-01-16T19_24_33.067445-neighborhood.csv', 'w')
            start = time.time() # to have a start value for timing later

            # Start dict reader & writer
            reader = csv.DictReader(orig_f, fieldnames=fieldnames_old)
            reader.next() # throw away header row

            writer = csv.DictWriter(new_f, fieldnames=fieldnames_new)
            writer.writeheader()

            # look up neighborhood
            for ind, row in enumerate(reader):

                # throttle to 3600/hour
                end = time.time()
                if (end-start) < 1:
                    time.sleep(end-start)

                # query API
                start = time.time()
                temp_resp = json.loads(flickr.places.findByLatLon(lat=row['latitude'], lon=row['longitude'], format='json'))


                if temp_resp['places']['total'] > 1:
                    print 'More than one place in this request'
                    pprint(temp_resp['places']['place'])
                else:
                    if temp_resp['places']['place'][0]['place_type'] == 'neighbourhood':
                        row['neighborhood'] = temp_resp['places']['place'][0]['woe_name']
                        row['place_type'] = 'neighborhood'
                    else:
                        print '%s is not a neighborhood, is %s, ' % (temp_resp['places']['place'][0]['woe_name'], temp_resp['places']['place'][0]['place_type'])
                        row['neighborhood'] = temp_resp['places']['place'][0]['woe_name']
                        row['place_type'] = temp_resp['places']['place'][0]['place_type']

                writer.writerow(row)

                if ind % 100 == 0:
                    print '%i rows complete, ~%.3f percent' % (ind, ind/12300. * 100)

# Run:
if __name__ == '__main__':
    get_photos()
    get_neighborhood()
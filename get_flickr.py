#!/usr/bin/env python

import requests
import csv
import time
from datetime import datetime
from pprint import pprint
import flickrapi
import json

def get_photos():
   # query flickr api for photos with "#streetart" within SF

    # list of working urls (on 1/17/15), having hard time forming correct api_sig
    query_url = [
        'https://api.flickr.com/services/rest/?method=flickr.photos.search&api_key=0f42fe846a36047efb1e75c42a8bf39a&tags=streetart&min_upload_date=1199145600&sort=date-posted-desc&has_geo=True&lat=37.774929500000000000&lon=-122.419415500000010000&radius=9&radius_units=km&extras=date_taken%2C+date_upload%2C+geo%2C+url_s&per_page=500&page=1&format=json&nojsoncallback=1&api_sig=7b56b8cfb62d621f702d8dafe19426cc',
        'https://api.flickr.com/services/rest/?method=flickr.photos.search&api_key=0f42fe846a36047efb1e75c42a8bf39a&tags=streetart&min_upload_date=1199145600&sort=date-posted-desc&has_geo=True&lat=37.774929500000000000&lon=-122.419415500000010000&radius=9&radius_units=km&extras=date_taken%2C+date_upload%2C+geo%2C+url_s&per_page=500&page=2&format=json&nojsoncallback=1&api_sig=429b354cbb1d2ba41dadcb60c30e8a8f',
        'https://api.flickr.com/services/rest/?method=flickr.photos.search&api_key=0f42fe846a36047efb1e75c42a8bf39a&tags=streetart&min_upload_date=1199145600&sort=date-posted-desc&has_geo=True&lat=37.774929500000000000&lon=-122.419415500000010000&radius=9&radius_units=km&extras=date_taken%2C+date_upload%2C+geo%2C+url_s&per_page=500&page=3&format=json&nojsoncallback=1&api_sig=1f4065555856ac808dfad336c85f993b',
        'https://api.flickr.com/services/rest/?method=flickr.photos.search&api_key=0f42fe846a36047efb1e75c42a8bf39a&tags=streetart&min_upload_date=1199145600&sort=date-posted-desc&has_geo=True&lat=37.774929500000000000&lon=-122.419415500000010000&radius=9&radius_units=km&extras=date_taken%2C+date_upload%2C+geo%2C+url_s&per_page=500&page=4&format=json&nojsoncallback=1&api_sig=7c7ca458e1cb624ca58a56b74e0aee42',
        'https://api.flickr.com/services/rest/?method=flickr.photos.search&api_key=0f42fe846a36047efb1e75c42a8bf39a&tags=streetart&min_upload_date=1199145600&sort=date-posted-desc&has_geo=True&lat=37.774929500000000000&lon=-122.419415500000010000&radius=9&radius_units=km&extras=date_taken%2C+date_upload%2C+geo%2C+url_s&per_page=500&page=5&format=json&nojsoncallback=1&api_sig=f1758f1fd269f17169986fb32b9ec801',
        'https://api.flickr.com/services/rest/?method=flickr.photos.search&api_key=0f42fe846a36047efb1e75c42a8bf39a&tags=streetart&min_upload_date=1199145600&sort=date-posted-desc&has_geo=True&lat=37.774929500000000000&lon=-122.419415500000010000&radius=9&radius_units=km&extras=date_taken%2C+date_upload%2C+geo%2C+url_s&per_page=500&page=6&format=json&nojsoncallback=1&api_sig=4c0d525052caf0f960fdc9fc818865cf',
        'https://api.flickr.com/services/rest/?method=flickr.photos.search&api_key=0f42fe846a36047efb1e75c42a8bf39a&tags=streetart&min_upload_date=1199145600&sort=date-posted-desc&has_geo=True&lat=37.774929500000000000&lon=-122.419415500000010000&radius=9&radius_units=km&extras=date_taken%2C+date_upload%2C+geo%2C+url_s&per_page=500&page=7&format=json&nojsoncallback=1&api_sig=47dae4d4aacfb2028689de5bcd3edd53',
        'https://api.flickr.com/services/rest/?method=flickr.photos.search&api_key=0f42fe846a36047efb1e75c42a8bf39a&tags=streetart&min_upload_date=1199145600&sort=date-posted-desc&has_geo=True&lat=37.774929500000000000&lon=-122.419415500000010000&radius=9&radius_units=km&extras=date_taken%2C+date_upload%2C+geo%2C+url_s&per_page=500&page=8&format=json&nojsoncallback=1&api_sig=f3c556b299b7f3da32bf516df5c74543',
        'https://api.flickr.com/services/rest/?method=flickr.photos.search&api_key=0f42fe846a36047efb1e75c42a8bf39a&tags=streetart&min_upload_date=1199145600&sort=date-posted-desc&has_geo=True&lat=37.774929500000000000&lon=-122.419415500000010000&radius=9&radius_units=km&extras=date_taken%2C+date_upload%2C+geo%2C+url_s&per_page=500&page=9&format=json&nojsoncallback=1&api_sig=f8a4f40859468c86b558e6319e315bf4',
        'https://api.flickr.com/services/rest/?method=flickr.photos.search&api_key=0f42fe846a36047efb1e75c42a8bf39a&tags=streetart&min_upload_date=1199145600&sort=date-posted-desc&has_geo=True&lat=37.774929500000000000&lon=-122.419415500000010000&radius=9&radius_units=km&extras=date_taken%2C+date_upload%2C+geo%2C+url_s&per_page=500&page=10&format=json&nojsoncallback=1&api_sig=2efd720b071e539f67c0a334ce28508d',
        'https://api.flickr.com/services/rest/?method=flickr.photos.search&api_key=0f42fe846a36047efb1e75c42a8bf39a&tags=streetart&min_upload_date=1199145600&sort=date-posted-desc&has_geo=True&lat=37.774929500000000000&lon=-122.419415500000010000&radius=9&radius_units=km&extras=date_taken%2C+date_upload%2C+geo%2C+url_s&per_page=500&page=11&format=json&nojsoncallback=1&api_sig=0d17c230242be60180a2bad7fcf7743f',
        'https://api.flickr.com/services/rest/?method=flickr.photos.search&api_key=0f42fe846a36047efb1e75c42a8bf39a&tags=streetart&min_upload_date=1199145600&sort=date-posted-desc&has_geo=True&lat=37.774929500000000000&lon=-122.419415500000010000&radius=9&radius_units=km&extras=date_taken%2C+date_upload%2C+geo%2C+url_s&per_page=500&page=12&format=json&nojsoncallback=1&api_sig=72af8edfd42bac0a56c24b4ccac2779b',
        'https://api.flickr.com/services/rest/?method=flickr.photos.search&api_key=0f42fe846a36047efb1e75c42a8bf39a&tags=streetart&min_upload_date=1199145600&sort=date-posted-desc&has_geo=True&lat=37.774929500000000000&lon=-122.419415500000010000&radius=9&radius_units=km&extras=date_taken%2C+date_upload%2C+geo%2C+url_s&per_page=500&page=13&format=json&nojsoncallback=1&api_sig=7fe4d8b1fe7277f458b7d30b03c641f0',
        'https://api.flickr.com/services/rest/?method=flickr.photos.search&api_key=0f42fe846a36047efb1e75c42a8bf39a&tags=streetart&min_upload_date=1199145600&sort=date-posted-desc&has_geo=True&lat=37.774929500000000000&lon=-122.419415500000010000&radius=9&radius_units=km&extras=date_taken%2C+date_upload%2C+geo%2C+url_s&per_page=500&page=14&format=json&nojsoncallback=1&api_sig=863e72595095bb37f5bc3c546f0eee05',
        'https://api.flickr.com/services/rest/?method=flickr.photos.search&api_key=0f42fe846a36047efb1e75c42a8bf39a&tags=streetart&min_upload_date=1199145600&sort=date-posted-desc&has_geo=True&lat=37.774929500000000000&lon=-122.419415500000010000&radius=9&radius_units=km&extras=date_taken%2C+date_upload%2C+geo%2C+url_s&per_page=500&page=15&format=json&nojsoncallback=1&api_sig=623724445f037d7c577190bc7d9947fb',
        'https://api.flickr.com/services/rest/?method=flickr.photos.search&api_key=0f42fe846a36047efb1e75c42a8bf39a&tags=streetart&min_upload_date=1199145600&sort=date-posted-desc&has_geo=True&lat=37.774929500000000000&lon=-122.419415500000010000&radius=9&radius_units=km&extras=date_taken%2C+date_upload%2C+geo%2C+url_s&per_page=500&page=16&format=json&nojsoncallback=1&api_sig=01cc0efa534ef5b00a2bc510f3e0f3f7',
        'https://api.flickr.com/services/rest/?method=flickr.photos.search&api_key=0f42fe846a36047efb1e75c42a8bf39a&tags=streetart&min_upload_date=1199145600&sort=date-posted-desc&has_geo=True&lat=37.774929500000000000&lon=-122.419415500000010000&radius=9&radius_units=km&extras=date_taken%2C+date_upload%2C+geo%2C+url_s&per_page=500&page=17&format=json&nojsoncallback=1&api_sig=dac6c0960a76dd0fd492cc5a2547ae67',
        'https://api.flickr.com/services/rest/?method=flickr.photos.search&api_key=0f42fe846a36047efb1e75c42a8bf39a&tags=streetart&min_upload_date=1199145600&sort=date-posted-desc&has_geo=True&lat=37.774929500000000000&lon=-122.419415500000010000&radius=9&radius_units=km&extras=date_taken%2C+date_upload%2C+geo%2C+url_s&per_page=500&page=18&format=json&nojsoncallback=1&api_sig=17c3c910799161b0c6719efdddb2c456',
        'https://api.flickr.com/services/rest/?method=flickr.photos.search&api_key=0f42fe846a36047efb1e75c42a8bf39a&tags=streetart&min_upload_date=1199145600&sort=date-posted-desc&has_geo=True&lat=37.774929500000000000&lon=-122.419415500000010000&radius=9&radius_units=km&extras=date_taken%2C+date_upload%2C+geo%2C+url_s&per_page=500&page=19&format=json&nojsoncallback=1&api_sig=2d392bda8f5b2ae6ca13cec3a6e4cfed',
        'https://api.flickr.com/services/rest/?method=flickr.photos.search&api_key=0f42fe846a36047efb1e75c42a8bf39a&tags=streetart&min_upload_date=1199145600&sort=date-posted-desc&has_geo=True&lat=37.774929500000000000&lon=-122.419415500000010000&radius=9&radius_units=km&extras=date_taken%2C+date_upload%2C+geo%2C+url_s&per_page=500&page=20&format=json&nojsoncallback=1&api_sig=2ce749258ca5add57ff408857c75e810',
        'https://api.flickr.com/services/rest/?method=flickr.photos.search&api_key=0f42fe846a36047efb1e75c42a8bf39a&tags=streetart&min_upload_date=1199145600&sort=date-posted-desc&has_geo=True&lat=37.774929500000000000&lon=-122.419415500000010000&radius=9&radius_units=km&extras=date_taken%2C+date_upload%2C+geo%2C+url_s&per_page=500&page=21&format=json&nojsoncallback=1&api_sig=02b018009372432a005f25c890f10932',
        'https://api.flickr.com/services/rest/?method=flickr.photos.search&api_key=0f42fe846a36047efb1e75c42a8bf39a&tags=streetart&min_upload_date=1199145600&sort=date-posted-desc&has_geo=True&lat=37.774929500000000000&lon=-122.419415500000010000&radius=9&radius_units=km&extras=date_taken%2C+date_upload%2C+geo%2C+url_s&per_page=500&page=22&format=json&nojsoncallback=1&api_sig=e6b68f75888e217d6fe171b8ebc6eb53',
        'https://api.flickr.com/services/rest/?method=flickr.photos.search&api_key=0f42fe846a36047efb1e75c42a8bf39a&tags=streetart&min_upload_date=1199145600&sort=date-posted-desc&has_geo=True&lat=37.774929500000000000&lon=-122.419415500000010000&radius=9&radius_units=km&extras=date_taken%2C+date_upload%2C+geo%2C+url_s&per_page=500&page=23&format=json&nojsoncallback=1&api_sig=c6f94588ad3c2079b3995237809e6d6b']


    fieldnames = sorted(['datetaken', 'datetakengranularity', 'datetakenunknown', 'dateupload', 'latitude', 'longitude', 'owner', 'place_id', 'url_s', 'woeid'])

    # get all pages of photo data
    req_page = 1
    now = datetime.now().isoformat().replace(':', '_') # mac doesn't allow ':' in filenames
    with open('/Users/Alexandra/PycharmProjects/graphiti/data/flickr_data-%s.csv' % now, 'w') as output_file:

        # write header
        # writer = csv.DictWriter(output_file, fieldnames=fieldnames, delimiter='\t')
        writer = csv.DictWriter(output_file, fieldnames=fieldnames)
        writer.writeheader()

        for x in query_url:
            time.sleep(1)
            resp = requests.get(x)

            # confirm page number match
            if resp.json()['photos']['page'] != req_page:
                print 'Requested page %i, got page %i' % (req_page, resp.json()['photos']['page'])
                continue

            # loop through photos
            for photo in resp.json()['photos']['photo']:
                write_to_file(photo, fieldnames, writer)

            print 'progress: page %i/%i complete' % (req_page, len(query_url))
            req_page += 1

def write_to_file(photo, fieldnames, writer):

    relevant_data = {my_key: photo[my_key] for my_key in fieldnames}
    writer.writerow(relevant_data)

def get_neighborhood():
    # get neighborhood name from lat, long
    # Function written after flickr data was accessed, so we create a second cvs file here,
    #   adding a neighborhood column

    # Flickr API stuffs
    api_key = '2a8751a5d69541e6c28667835c35cf11'
    api_secret = '6628ef02693fe943'
    flickr = flickrapi.FlickrAPI(api_key, api_secret)


    # Working on reading, getting, and writing
    fieldnames_old = sorted(['datetaken', 'datetakengranularity', 'datetakenunknown', 'dateupload', 'latitude', 'longitude', 'owner', 'place_id', 'url_s', 'woeid'])
    fieldnames_new = fieldnames_old + ['neighborhood', 'place_type'] # + is immutable

    with open('flickr_data-2015-01-16T19_24_33.067445.csv') as orig_f:
        with open('flickr_data-2015-01-16T19_24_33.067445-neighborhood.csv', 'w') as new_f:
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
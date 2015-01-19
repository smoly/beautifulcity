from instagram.client import InstagramAPI
import sys
import urllib
import json
import requests
import csv
import time
from datetime import datetime


def read_write(result):
    entries = 0
    for post in result['data']:
        if post['location'] is not None:
            if 'latitude' in post['location'].keys() \
                    and 37.7 <= post['location']['latitude'] <= 37.85 \
                    and -122.6 <= post['location']['longitude'] <= -122.35:
                row_dict = {'user_id':  post['user']['id'],
                    'image_url': post['images']['standard_resolution']['url'],
                    'created_time': post['created_time'],
                    'lat': post['location']['latitude'],
                    'long': post['location']['longitude'],
                    'post_url': post['link']
                }
                writer.writerow(row_dict)
                entries += 1
            # elif 'latitude' in post['location'].keys():
            #     print "lat = %f, long = %f" % (post['location']['latitude'], post['location']['longitude'])


    return entries

# first query
start_time = time.time()
access_token = '186061903.1fb234f.7e84aa71760b44cb9ab34f42a8ba00b0'
query_url = 'https://api.instagram.com/v1/tags/streetart/media/recent?access_token=%s' % access_token

# open file
max_entries = 100000
n_entries = 0

fieldnames = sorted(['created_time', 'image_url', 'lat', 'long', 'user_id', 'post_url'])
now = datetime.now().isoformat().replace(':', '_') # mac doesn't allow ':' in filenames
with open('/Users/Alexandra/PycharmProjects/graphiti/data/instagram_data-%s.tsv' % now, 'w') as output_file:
    writer = csv.DictWriter(output_file, fieldnames=fieldnames, delimiter='\t')
    writer.writeheader()

    # first query
    resp = requests.get(query_url)
    # if resp.status_code != 200:
    #     # raise Exception(resp.status_code, resp.url, resp.text)
    # else:
    new_entries = read_write(resp.json())
    n_entries += new_entries

    next_url = resp.json()['pagination']['next_url']
    while n_entries < max_entries:
        time.sleep(0.8)
        resp = requests.get(next_url)
        if resp.status_code != 200:
            if resp.status_code == 500:
                print resp.text

            # else:
                raise Exception(resp.status_code, resp.url, resp.text)

        else:

            new_entries = read_write(resp.json())
            n_entries += new_entries

            print 'progress: %i/%i (%3.f percent), time elapsed = %3.fs' % (n_entries, max_entries, n_entries/max_entries, time.time() - start_time)

            # print resp.json()['pagination']
            next_url = resp.json()['pagination']['next_url']

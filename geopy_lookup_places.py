#!/usr/bin/env python

import pandas as pd
import sqlalchemy
from geopy.geocoders import Nominatim
import geopy
from unidecode import unidecode
from datetime import datetime
import csv
import time


# load data since Aug 2014
engine = sqlalchemy.create_engine('mysql://root@localhost') # connect to server
engine.execute('use tagus') # select new db

sql_query = '''select id, date, lat, `long`
            from instagram
            where `date` between '2014-12-01' and '2015-01-22'
            and lat between 24.396308 and 49.384358
            and `long` between -124.848974 and -66.885444
            order by `date` desc'''
posts = pd.read_sql_query(sql_query, engine, parse_dates=['date'])

# init
geolocator = Nominatim()
use_keys = ['id', 'date', 'road', 'city', 'suburb', 'county', 'postcode', 'state', 'country', 'neighbourhood', 'country', 'country_code']

now = datetime.now().isoformat().replace(':', '_') # mac doesn't allow ':' in filenames
with open('/Users/Alexandra/Dropbox/Projects/Insight/tagsf/data/instagram_places%s.tsv' % now, 'w') as output_file:
    writer = csv.DictWriter(output_file, fieldnames=use_keys, delimiter='\t')
    writer.writeheader()

    start = time.time()
    n = 0.
    for row in posts.iterrows():

        # Call geolocator, throttle, retry if needed
        retry = True
        while retry:
            try:
                # throttle to 1/s
                end = time.time()
                if (end-start) < 1:
                    time.sleep(end-start)

                start = time.time()
                location = geolocator.reverse(list(row[1][['lat', 'long']]))
                retry = False

            except geopy.exc.GeocoderTimedOut:
                'geolocator.reverse timed out on row %i, retrying...' % n
            except geopy.exc.GeocoderServiceError:
                'geolocator.reverse internal server error on row %i, retrying...' % n
            # else error_name:
            #     'geolocator error'


        if 'error' in location.raw.keys():
            print 'Error getting location info for (%.4f, %.4f), continuing' % (row[1]['lat'], row[1]['long'])
        else:
            row_dict = {
                'id': row[1]['id'],
                'date': str(row[1]['date']),
            }

            for key in location.raw['address'].keys():
                if key in use_keys:
                    row_dict[key] = unidecode(location.raw['address'][key])

            writer.writerow(row_dict)

        n += 1
        print 'completed %i/%i rows (%.3f %%)' % (n, posts.shape[0],n/posts.shape[0] * 100)
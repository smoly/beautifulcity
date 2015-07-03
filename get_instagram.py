import requests
import csv
import time
from datetime import datetime, timedelta
import traceback
import config
import isodate
import sqlalchemy
import pandas as pd

# write list of posts to csv file, used below
def read_write(result, writer):
    entries = [0, 0]
    for post in result['data']:
        try:
            if post['location'] is not None:
                if 'latitude' in post['location'].keys(): # some are missing
                    row_dict = {'user_id':  post['user']['id'],
                        'image_url': post['images']['standard_resolution']['url'],
                        'created_time': post['created_time'],
                        'lat': post['location']['latitude'],
                        'long': post['location']['longitude'],
                        'post_url': post['link'],
                        'id': post['id'],
                        'likes': post['likes']['count']
                    }

                    # print datetime.fromtimestamp(int(post['created_time'])).isoformat()
                    # add text if available
                    if 'caption' in post.keys() and post['caption'] is not None:
                        if 'text' in post['caption'].keys():
                            row_dict['text'] = post['caption']['text'].encode('ascii', 'replace')

                    writer.writerow(row_dict)


                    # count posts in SF and elsewhere
                    if 37.7 <= post['location']['latitude'] <= 37.85 \
                        and -122.6 <= post['location']['longitude'] <= -122.35:
                        entries[0] += 1
                    else:
                        entries[1] += 1

        except Exception, e:
            print 'caught error in read_write, continuing: %s' % e
            traceback.print_exc()

    return entries

def get_instagram():
    '''
        get_instagram gets instagram data from the last 26 hours

        can import get_instagram from other modules

    '''

    # Determine most recent post timestamp
    engine = sqlalchemy.create_engine('mysql://%(user)s:%(pass)s@%(host)s' % config.database) # connect to server
    engine.execute('use %s' % config.database['name']) # select new db
    sql_query = '''select max(date) from instagram'''

    max_history = pd.read_sql_query(sql_query, engine).iloc[0,0]
    max_history = max(max_history, datetime.now() - timedelta(weeks=2))
    print 'Getting data back to ' +  max_history.isoformat()
    # max_history = datetime.now() - timedelta(hours=hours) # how far back in time to collect data

    # Start Instagram Collection
    start_time = time.time()
    # query_url = 'https://api.instagram.com/v1/tags/streetart/media/recent?access_token=%s&max_tag_id=%s' % (config.instagram['access_token'], max_tag_id)
    query_url = 'https://api.instagram.com/v1/tags/streetart/media/recent?access_token=%s' % (config.instagram['access_token'])

    # open file
    n_entries_SF = 0
    n_entries_all = 0

    fieldnames = sorted(['id', 'likes', 'text', 'created_time', 'image_url', 'lat', 'long', 'user_id', 'post_url'])
    timestamp = datetime.now().isoformat().replace(':', '_') # mac doesn't allow ':' in filenames
    filename = 'data/instagram_data_%s.tsv' % timestamp
    with open(filename, 'w') as output_file:
        writer = csv.DictWriter(output_file, fieldnames=fieldnames, delimiter='\t')
        writer.writeheader()

        # first query
        start = time.time()
        resp = requests.get(query_url)

        new_entries = read_write(resp.json(), writer)
        n_entries_SF += new_entries[0]
        n_entries_all += new_entries[1]

        earliest_post = datetime.fromtimestamp(int(resp.json()['data'][len(resp.json()['data'])-1]['created_time']))

        next_url = resp.json()['pagination']['next_url']
        # while True: # get data forever!
        while earliest_post > max_history:
            try:
                # throttle to 3600/hour
                end = time.time()
                if (end-start) < 1:
                    time.sleep(end-start)

                start = time.time()
                resp = requests.get(next_url)
                if resp.status_code != 200:
                    if resp.status_code == 500:
                        print resp.text
                    # else:
                        raise Exception(resp.status_code, resp.url, resp.text)
                else:
                    new_entries = read_write(resp.json(), writer)
                    n_entries_SF += new_entries[0]
                    n_entries_all += new_entries[1]

                    earliest_post = datetime.fromtimestamp(int(resp.json()['data'][len(resp.json()['data'])-1]['created_time']))

                    print 'progress: %i in SF, %i elsewhere, time elapsed = %3.fs' % (n_entries_SF, n_entries_all, time.time() - start_time)
                    print 'earliest post: ' + str(earliest_post)
                    next_url = resp.json()['pagination']['next_url']
            except Exception, e:
                print 'caught error in body, continuing: %s' % e
                traceback.print_exc()

    return filename

if __name__ == "__main__":
    get_instagram()
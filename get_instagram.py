import requests
import csv
import time
from datetime import datetime
import traceback

# write list of posts to csv file, used below
def read_write(result):
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

# first query
#TODO: move to config
start_time = time.time()
access_token = '186061903.1fb234f.7e84aa71760b44cb9ab34f42a8ba00b0'
query_url = 'https://api.instagram.com/v1/tags/streetart/media/recent?access_token=%s' % access_token

# open file
max_entries = 10000.
n_entries_SF = 0
n_entries_all = 0

fieldnames = sorted(['id', 'likes', 'text', 'created_time', 'image_url', 'lat', 'long', 'user_id', 'post_url'])
now = datetime.now().isoformat().replace(':', '_') # mac doesn't allow ':' in filenames
with open('/Users/Alexandra/Dropbox/Projects/Insight/tagsf/data/instagram_data_with_text_world-%s.tsv' % now, 'w') as output_file:
    writer = csv.DictWriter(output_file, fieldnames=fieldnames, delimiter='\t')
    writer.writeheader()

    # first query
    start = time.time()
    resp = requests.get(query_url)

    new_entries = read_write(resp.json())
    n_entries_SF += new_entries[0]
    n_entries_all += new_entries[1]

    next_url = resp.json()['pagination']['next_url']
    while True:
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
                new_entries = read_write(resp.json())
                n_entries_SF += new_entries[0]
                n_entries_all += new_entries[1]

                print 'progress: %i in SF, %i elsewhere, time elapsed = %3.fs' % (n_entries_SF, n_entries_all, time.time() - start_time)

                next_url = resp.json()['pagination']['next_url']
        except Exception, e:
            print 'caught error in body, continuing: %s' % e
            traceback.print_exc()


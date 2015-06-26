from flask import render_template, request
from app import app
import config
import pandas as pd
import tagsf as tg
import sqlalchemy
import geo_util
import string
import random
import numpy as np
import os
import pickle
import unidecode


# @app.route('/slides')
# def slides():
#     return render_template("slides.html")

@app.route('/about')
def about():
    return render_template("about.html")


@app.route('/hello')
def index():
    return render_template("index.html",
       title = 'Home', user = {'nickname': 'Alex' },
       )

@app.route('/error')
def oops():
    raise Exception("oops")

@app.route('/')
def tag_home():

    # Get location
    loc_name = request.args.get('loc', 'SF, CA')

    loc = geo_util.google_geo(loc_name)
    geo_box = geo_util.geo_bounds([loc['lat'], loc['lng']], distance=9)

    loc['formatted_address'] = unidecode.unidecode(loc['formatted_address'])
    print 'loc name: %s' % loc['formatted_address']

    # query data
    engine = sqlalchemy.create_engine('mysql://%(user)s:%(pass)s@%(host)s' % config.database) # connect to server
    engine.execute('use %s' % config.database['name']) # select new db

    recent_data = (datetime.now() - timedelta(weeks=2)).strftime("%Y-%m-%d")
    sql_query = '''select date, lat, `long`, image_url, likes, text
                from instagram
                where `date` > '%s'
                and lat between %s and %s
                and `long` between %s and %s
                order by `date` desc
                limit 1000''' % (recent_data, geo_box[0], geo_box[1],  geo_box[2],  geo_box[3])

    posts = pd.read_sql_query(sql_query, engine, parse_dates=['date'])
    n_points = posts.shape[0]

    # If location has cached data, use it
    filename = 'app/static/data/%s' % str(loc['formatted_address'].replace(',', '').replace(' ', ''))
    if os.path.exists(filename):
        print 'file exists!'

        with open(filename, "rb") as f:
            [cluster_id, artists_found, cluster_infos, ranked_clusters, cols_hex, map_name] \
                = pickle.load(f)
    else:
        try:
            cluster_id = tg.cluster_geo(posts, eps=0.13, min_samples=8) #.14 & 1500 not good; 0.13 x 1500 not good

            # Make map
            random_str = ''.join(random.choice(string.letters + string.digits) for i in range(20))
            map_name = 'map_%s.html' % random_str
            cols_hex = tg.make_map([loc['lat'], loc['lng']], posts, cluster_id, map_name=map_name)

            # Add ID to posts dataframe
            posts['cluster_id'] = cluster_id

            # Mine text
            unusual_tokens, cluster_tokens_all = tg.text_from_clusters(posts, cluster_id)
            artists_found = tg.find_artists(cluster_tokens_all)
            fun_text = [[]] * len(unusual_tokens)
            for ind, tokens in enumerate(unusual_tokens):
                fun_text[ind] = list(set(tokens + artists_found[ind]))

            # Rank clusters
            ranked_clusters = tg.rank_clusters(posts)

            # Make world cloud
            wordle_urls = []
            for ind, cluster_text in enumerate(fun_text):
                random_str = ''.join(random.choice(string.letters + string.digits) for i in range(20))
                this_path = 'static/data/word_cloud_%s.png' % random_str
                wordle_urls.append(this_path)
                tg.make_word_cloud(cluster_text, this_path, cols_hex[ind])

            # Get top photos
            photos = tg.top_photos(posts, n_photos=8)

            cluster_infos = list(enumerate(zip(wordle_urls, photos)))

        except ValueError:
            print 'Value error'
            # make map:

            cluster_id = np.array([-1] * posts.shape[0])
            random_str = ''.join(random.choice(string.letters + string.digits) for i in range(20))
            map_name = 'map_%s.html' % random_str
            cols_hex = tg.make_map([loc['lat'], loc['lng']], posts, cluster_id, map_name=map_name)

            artists_found = [[]]
            cluster_infos = []
            ranked_clusters = []

        data = [cluster_id, artists_found, cluster_infos, ranked_clusters, cols_hex, map_name]
        print 'does not exist, save'
        with open(filename, "wb") as f:
            pickle.dump(data, f)


    return render_template(
        'tag_home.html',
        unusual_tokens=artists_found,
        loc_name=loc['formatted_address'],
        cluster_infos=cluster_infos,
        ranked_clusters=ranked_clusters,
        cols_hex=cols_hex,
        map_name=map_name,
    )

if '__name__' == '__main__':
    app.run()
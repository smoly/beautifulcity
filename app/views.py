from flask import render_template, request
from app import app
# import pymysql as mdb
from a_Model import ModelIt

# db= mdb.connect(user="root", host="localhost", db="world_innodb", charset='utf8')


@app.route('/')
@app.route('/index')
def index():
    # FIXME: go to tag
    return render_template("index.html",
       title = 'Home', user = {'nickname': 'Miguel' },
       )

# @app.route('/db')
# def cities_page():
#     with db:
#         cur = db.cursor()
#         cur.execute("SELECT Name FROM City LIMIT 15;")
#         query_results = cur.fetchall()
#     cities = ""
#     for result in query_results:
#         cities += result[0]
#         cities += "<br>"
#     return cities
#
# @app.route("/db_fancy")
# def cities_page_fancy():
#     with db:
#         cur = db.cursor()
#         cur.execute("SELECT Name, CountryCode,\
#             Population FROM City ORDER BY Population LIMIT 15;")
#
#         query_results = cur.fetchall()
#     cities = []
#     for result in query_results:
#         cities.append(dict(name=result[0], country=result[1], population=result[2]))
#     return render_template('cities.html', cities=cities)

@app.route("/tag")
def tag_home():
    import pandas as pd
    import tagsf as tg
    import sqlalchemy
    import geo_util
    import string
    import random
    import numpy as np
    import os
    import pickle

    # Get location
    loc_name = request.args.get('loc', 'NYC, NY')

    loc = geo_util.google_geo(loc_name)
    geo_box = geo_util.geo_bounds([loc['lat'], loc['lng']], distance=9)

    print 'loc name: %s' % loc['formatted_address']

    # query data
    engine = sqlalchemy.create_engine('mysql://root@localhost') # connect to server
    engine.execute('use tagus') # select new db

    sql_query = '''select date, lat, `long`, image_url, likes, text
                from instagram
                where `date` > '2015-01-10'
                and lat between %s and %s
                and `long` between %s and %s
                order by `date` desc
                limit 1000''' % (geo_box[0], geo_box[1],  geo_box[2],  geo_box[3])

    posts = pd.read_sql_query(sql_query, engine, parse_dates=['date'])

    filename = 'app/static/data/%s' % str(loc['formatted_address'].replace(',', '').replace(' ', ''))
    if os.path.exists(filename):
        print 'file exists!'

        with open(filename, "rb") as f:
            data = pickle.load(f)

        [cluster_id, artists_found, cluster_infos, ranked_clusters, cols_hex] = data

        # make map
        cols_hex = tg.make_map([loc['lat'], loc['lng']], posts, cluster_id)
    else:
        try:
            cluster_id = tg.cluster_geo(posts, eps=0.13, min_samples=10) #.14 & 1500 not good; 0.13 x 1500 not good
            cols_hex = tg.make_map([loc['lat'], loc['lng']], posts, cluster_id)

            # Add ID
            posts['cluster_id'] = cluster_id

            # Text mine
            unusual_tokens, cluster_tokens_all = tg.text_from_clusters(posts, cluster_id)
            artists_found = tg.find_artists(cluster_tokens_all)
            fun_text = [[]] * len(unusual_tokens)
            for ind, tokens in enumerate(unusual_tokens):
                fun_text[ind] = list(set(tokens + artists_found[ind]))

            # Rank clusters
            ranked_clusters = tg.rank_clusters(posts)

            # make worldle
            wordle_urls = []
            for ind, cluster_text in enumerate(fun_text):
                random_str = ''.join(random.choice(string.letters + string.digits) for i in range(20))
                this_path = 'static/data/word_cloud_%s.png' % random_str
                wordle_urls.append(this_path)
                tg.make_word_cloud(cluster_text, this_path, cols_hex[ind])

            # get top photos
            photos = tg.top_photos(posts, n_photos=8)

            cluster_infos = list(enumerate(zip(wordle_urls, photos)))

        except ValueError:
            # make map:
            cols_hex = tg.make_map([loc['lat'], loc['lng']], posts,  np.array([-1] * posts.shape[0]))

            artists_found = [[]]
            cluster_infos = []
            ranked_clusters = []

        data = [cluster_id, artists_found, cluster_infos, ranked_clusters, cols_hex]
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
    )
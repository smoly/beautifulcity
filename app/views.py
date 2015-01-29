from flask import render_template, request
from app import app
import pymysql as mdb
from a_Model import ModelIt

db= mdb.connect(user="root", host="localhost", db="world_innodb", charset='utf8')


@app.route('/')
@app.route('/index')
def index():
    # return "Hello, World!"
    # user = { 'nickname': 'Miguel' } # fake user
    return render_template("index.html",
       title = 'Home', user = {'nickname': 'Miguel' },
       )

@app.route('/db')
def cities_page():
    with db:
        cur = db.cursor()
        cur.execute("SELECT Name FROM City LIMIT 15;")
        query_results = cur.fetchall()
    cities = ""
    for result in query_results:
        cities += result[0]
        cities += "<br>"
    return cities

@app.route("/db_fancy")
def cities_page_fancy():
    with db:
        cur = db.cursor()
        cur.execute("SELECT Name, CountryCode,\
            Population FROM City ORDER BY Population LIMIT 15;")

        query_results = cur.fetchall()
    cities = []
    for result in query_results:
        cities.append(dict(name=result[0], country=result[1], population=result[2]))
    return render_template('cities.html', cities=cities)

@app.route("/tag")
def tag_home():
    import pandas as pd
    import tagsf as tg
    import sqlalchemy
    import geo_util

    # Get location
    loc_name = request.args.get('loc', 'San Francisco, CA')

    loc = geo_util.google_geo(loc_name)
    geo_box = geo_util.geo_bounds([loc['lat'], loc['lng']], distance=9)

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

    # Cluster geo
    cluster_id = tg.cluster_geo(posts, eps=0.13, min_samples=10) #.14 & 1500 not good; 0.13 x 1500 not good
    tg.make_map([loc['lat'], loc['lng']], posts, cluster_id)

    # Text mine
    unusual_tokens, cluster_tokens_all = tg.text_from_clusters(posts, cluster_id)
    artists_found = tg.find_artists(cluster_tokens_all)

    #FIXME: artist names can be doubled!
    fun_text = [[]] * len(unusual_tokens)
    for ind, tokens in enumerate(unusual_tokens):
        fun_text[ind] = tokens + artists_found[ind]

    # was path = "app/static/data/test_cloud.png"

    wordle_urls = []
    for ind, cluster_text in enumerate(fun_text):
        this_path = 'static/data/word_cloud_%i.png' % ind
        wordle_urls.append(this_path)
        tg.make_word_cloud(cluster_text, this_path)


    # # # TODO replace:
    # ind = 8
    photo_urls = [list(posts.loc[ind*(x+1)-ind:ind*(x+1), 'image_url'].values)
              for x in range(len(cluster_tokens_all))]

    cluster_infos = list(enumerate(zip(wordle_urls, photo_urls)))

    return render_template('tag_home.html',
                           unusual_tokens=artists_found,
                           loc_name=loc['formatted_address'],
                           cluster_infos=cluster_infos)

# @app.route('/input')
# def cities_input():
#   return render_template("input.html")
#
# @app.route('/output')
# def cities_output():
#   #pull 'ID' from input field and store it
#   city = request.args.get('ID')
#
#   with db:
#     cur = db.cursor()
#     #just select the city from the world_innodb that the user inputs
#     cur.execute("SELECT Name, CountryCode,  Population FROM City WHERE Name='%s';" % city)
#     query_results = cur.fetchall()
#
#   cities = []
#   for result in query_results:
#     cities.append(dict(name=result[0], country=result[1], population=result[2]))
#   the_result = ''
#
#   #call a function from a_Model package. note we are only pulling one result in the query
#   pop_input = cities[0]['population']
#   the_result = ModelIt(city, pop_input)
#   return render_template("output.html", cities = cities, the_result = the_result)
from flask import render_template
from app import app
import pymysql as mdb

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


    #TODO: make loc name an input!
    loc_name = 'San Francisco'
    loc = geo_util.google_geo(loc_name)
    geo_box = geo_util.geo_bounds([loc['lat'], loc['lng']], distance=9)

    # query data
    engine = sqlalchemy.create_engine('mysql://root@localhost') # connect to server
    engine.execute('use tagus') # select new db

    sql_query = '''select date, lat, `long`, image_url, likes, text
                from instagram
                where `date` > '2015-01-10'
                and lat between %s and %s
                and `long` between %s and %s''' % (geo_box[0], geo_box[1],  geo_box[2],  geo_box[3])

    posts = pd.read_sql_query(sql_query, engine, parse_dates=['date'])

    cluster_id = tg.cluster_geo(posts)
    tg.make_map([loc['lat'], loc['lng']], posts, cluster_id)

    top_n, cluster_tokens = tg.text_from_clusters(posts, cluster_id)

    artists_found = tg.find_artists(cluster_tokens)

    return render_template('tag_home.html', unusual_tokens=artists_found)
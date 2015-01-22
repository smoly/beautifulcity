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
    import tagsf as tg

    c = tg.cluster_geo(tg.inst)
    tg.make_map(tg.inst, c)

    top_10 = tg.text_from_clusters(tg.inst, c)

    return render_template('tag_home.html', unusual_tokens=top_10)
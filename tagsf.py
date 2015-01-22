import pandas as pd
import numpy as np
import flickrapi
import urllib
import json
import time
from datetime import datetime
from PIL import Image
from cStringIO import StringIO
import config
from load_instagram import load_instagram

# Query for recent posts:
# TODO: add lat long for new instagram data
# TODO: make SQL!
instagram = load_instagram()
max_date = pd.datetime(2015, 1, 10)
inst = instagram[instagram['date'] > max_date]

# c = tg.cluster_geo(tg.inst)

def cluster_geo(posts):
    # expects lat and long columns
    from scipy.cluster.vq import kmeans,vq
    from scipy.spatial.distance import cdist
    from sklearn.cluster import KMeans

    # # TODO: set threshold on clusters:
    # K = range(1,30)
    #
    # # scipy.cluster.vq.kmeans
    # KM = [kmeans(posts[['lat', 'long']].values,k) for k in K] # apply kmeans 1 to 10
    # centroids = [cent for (cent,var) in KM]   # cluster centroids
    #
    # D_k = [cdist(posts[['lat', 'long']].values, cent, 'euclidean') for cent in centroids]
    #
    # cIdx = [np.argmin(D,axis=1) for D in D_k]
    # dist = [np.min(D,axis=1) for D in D_k]
    # avgWithinSS = [sum(d)/posts[['lat', 'long']].shape[0] for d in dist]

    # Classify into n_clusters:
    n_clust = int(np.sqrt(posts[['lat', 'long']].shape[0]/2))
    km = KMeans(n_clust, init='k-means++') # initialize
    km.fit(posts[['lat', 'long']])
    c = km.predict(posts[['lat', 'long']]) # classify

    return c

def make_map(posts, c):
    import colorsys
    from colors import rgb
    import os
    import folium
    import seaborn as sns

    cols = sns.color_palette("Set2", n_colors=len(np.unique(c)))
    marker_col = ['#%s' % str(rgb(cols[ic][0]*255, cols[ic][1]*255, cols[ic][2]*255).hex) for ic in c]

    # Check if map file already exists
    if os.path.exists('%s/map.html' % (config.paths['templates'])):
        print 'removing file'
        os.remove('%s/map.html' % (config.paths['templates']))

    # TODO: make global lat long
    # query google api
    map = folium.Map(location=[37.7833, -122.4167], zoom_start=13, tiles='Stamen Toner')
    map.create_map(path='%s/map.html' % (config.paths['templates']))

    # markers
    for ind, row in enumerate(posts.iterrows()):
        map.circle_marker([row[1]['lat'], row[1]['long']],
                      radius=20,
                      line_color=marker_col[ind],
                      fill_color=marker_col[ind],
                      popup=str(c[ind]))

    map.create_map(path='%s/map.html' % (config.paths['templates']))

def text_from_clusters(posts, c):

    # Get text from each cluster
    import nltk
    from nltk.tokenize import word_tokenize
    from gensim import corpora, matutils
    import string

    n_clust = len(np.unique(c))

    docs = posts['text'].values
    tokened_docs = [word_tokenize(doc) for doc in docs]

    cluster_tokens = [[]] * n_clust
    for ind, doc in enumerate(tokened_docs):
        cluster_tokens[c[ind]] = cluster_tokens[c[ind]] + doc

    # remove funny characters and spaces
    chars = string.punctuation + ' '
    temp_cleaned = [[''.join(ch for ch in word.lower() if ch not in chars) for word in doc] for doc in cluster_tokens]
    docs_cleaned = [[word for word in doc if word != ''] for doc in temp_cleaned]

    dictionary = corpora.dictionary.Dictionary(docs_cleaned) # indexing: dictionary.token2id['streetart']
    bow_corp = [dictionary.doc2bow(doc) for doc in docs_cleaned]
    token_freq = matutils.corpus2dense(bow_corp, len(dictionary.token2id.keys()))

    # normalize words by occurence
    from sklearn.feature_extraction.text import TfidfTransformer
    transformer = TfidfTransformer()

    tfidf = transformer.fit_transform(token_freq)
    norm_token_freq = tfidf.toarray()

    words = dictionary.token2id.keys()

    # Pick out unusual words
    threshold = 0.7

    # really horribly add cluster number into first element of list for web interface...
    unusual_tokens = [[x] for x in range(0,n_clust)] #* n_clust
    for word in words:
        for ind_cluster, p in enumerate(norm_token_freq[dictionary.token2id[word],:]):
            if p > threshold:
                if np.sum(token_freq[dictionary.token2id[word]]) > 1:
                    unusual_tokens[ind_cluster] = unusual_tokens[ind_cluster] + [(str(word), token_freq[dictionary.token2id[word], ind_cluster])]

    top_10 = [[]] * n_clust
    for ind, cluster in enumerate(unusual_tokens):
        temp = sorted(cluster[1:],key=lambda x: x[1], reverse=True)
        if len(temp) > 10:
            top_10[ind] = [cluster[0]] + temp[:9]
        else:
            top_10[ind] = [cluster[0]] + temp

    return top_10



# def load_data(reload):
#     # load SF graffiti reports, flickr #street art reports, Trulia home prices
#     if reload:
#         now = datetime.now().isoformat().replace(':', '_') # mac doesn't allow ':' in filenames
#
#         ## Load SF city data
#         reports = pd.read_csv(
#             '%s/Case_Data_from_San_Francisco_311__SF311_.csv' % config.data_path)
#
#         reports = reports[reports['CaseID'].notnull()]
#         graffiti = reports[reports['Request Type'] == 'Graffiti'] #9440 results, most recent is Jan 9
#         graffiti['Opened'] = pd.to_datetime(graffiti['Opened'])
#         graffiti['Closed'] = pd.to_datetime(graffiti['Closed'])
#         graffiti['Updated'] = pd.to_datetime(graffiti['Updated'])
#
#         # get neighborhood name from flickr api, to be the same as flickr names
#         graffiti['neighborhood'] = graffiti['Point'].apply(get_neighborhood)
#
#         # convert "point" to lat long
#         graffiti['latitude'] = graffiti['Point'].apply(get_lat)
#         graffiti['longitude'] = graffiti['Point'].apply(get_lng)
#
#         # TO DELETE:
#         # DF = DF.drop('column_name', 1)
#
#         # save - this one is important!
#         graffiti.to_pickle('%sdf_graffiti-%s' % (config.data_path, now))
#
#         ## Flickr data
#         # file_name_csv = 'flickr_data-%s-neighborhood.csv' % config.flickr['file_time'] # has neighborhood
#         file_name_csv = 'flickr_data-2015-01-16T19_24_33.067445-neighborhood.csv'
#         flickr = pd.read_csv('%s%s' % (config.data_path, file_name_csv))
#
#         # Convert to datetime
#         flickr['datetaken'] = pd.to_datetime(flickr['datetaken'])
#
#         flickr.to_pickle('%sdf_flickr-%s' % (config.data_path, now))
#
#         ## Trulia data
#         prices = pd.read_csv('%shome_prices.csv' % config.data_path)
#
#         # save
#         prices.to_pickle('%sdf_prices-%s' % (config.data_path, now))
#     else: # load processed
#         print 'Loading...'
#
#         timestamp = '2015-01-19T15_13_52.276380'
#
#         graffiti = pd.read_pickle('%sdf_graffiti-%s' % (config.data_path, timestamp))
#         flickr = pd.read_pickle('%sdf_flickr-%s' % (config.data_path, timestamp))
#         prices = pd.read_pickle('%sdf_prices-%s' % (config.data_path, timestamp))
#
#     return graffiti, flickr, prices
#
# def get_neighborhood(loc_str):
#     # Get Flickr API's neighborhood name; throttled at 1/s
#
#     # Flickr API stuffs
#     api_key = '2a8751a5d69541e6c28667835c35cf11'
#     api_secret = '6628ef02693fe943'
#     flickr_api = flickrapi.FlickrAPI(api_key, api_secret)
#
#     (latitude, longitude) = eval(loc_str)
#
#     # query API
#     time.sleep(1) # Flickr limits 3600/hour
#     temp_resp = json.loads(flickr_api.places.findByLatLon(lat=latitude, lon=longitude, format='json'))
#
#     # note non-neighborhood names
#     neighborhood = temp_resp['places']['place'][0]['woe_name']
#     if temp_resp['places']['place'][0]['place_type'] != 'neighbourhood':
#         print '%s is not a neighborhood, is %s ' % (temp_resp['places']['place'][0]['woe_name'], temp_resp['places']['place'][0]['place_type'])
#
#     return neighborhood

# def google_map(flickr_loc, city_loc):
#     # show a Google map of requested lat long pairs
#     marker_colors = ['red', 'orange', 'yellow', 'green', 'blue', 'purple']
#     bad_marker_colors = ['orange']
#
#
#     # PASS THE FOLLOWING LINE:
#     # flickr_loc = flickr[flickr['datetaken'] > pd.datetime(2015, 1, 1)][['latitude','longitude']]
#     flickr_array = flickr_loc.get_values()
#
#     # PASS THE FOLLOWING:
#     # city_loc = graffiti[graffiti['Opened'] > pd.datetime(2015, 1, 1)][['latitude','longitude']]
#     city_array = city_loc.get_values()
#
#     # Generate URL with markers
#     base_url = 'http://maps.googleapis.com/maps/api/staticmap?&size=1000x1000&sensor=false]'
#
#     url_param = ''
#     # markers for good hotspots
#     url_param = '&markers=size:mid%%7Ccolor:%s' %marker_colors[0]
#     for ind in range(0, 15):
#         url_param += '&markers=size:mid%%7Ccolor:%s%%7Clabel:%i' \
#                      % (marker_colors[0], 1)
#         url_param += '%%7C%f,%f' %(flickr_array[ind, 0], flickr_array[ind, 1])
#
#     url_param +=  '&markers=size:mid%%7Ccolor:%s' %marker_colors[0]
#     for ind in range(0, 15):
#         url_param += '&markers=size:mid%%7Ccolor:%s%%7Clabel:%i' \
#                      % (marker_colors[1], 2)
#         url_param += '%%7C%f,%f' %(city_array[ind, 0], city_array[ind, 1])
#
#
#     image_bytes = urllib.urlopen(base_url+url_param).read()
#     image = Image.open(StringIO(image_bytes))  # StringIO makes file object out of image data
#
#     Image._show(image)
#
#     return
#
#
# def get_lat(loc_str):
#     (lat, lng) = eval(loc_str)
#     return lat
#
# def get_lng(loc_str):
#     (lat, lng) = eval(loc_str)
#     return lng
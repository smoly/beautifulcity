import pandas as pd
import numpy as np
import config
from geopy.distance import vincenty


def cluster_geo(posts,
                method='dbscan', eps=0.15, min_samples=10,
                max_cluster_size=float('inf')):
    # cluster_labels = cluster_geo(posts, method='dbscan', eps=0.002, min_samples=5)
    #
    #   posts: dataframe, needs columns ['lat', 'long']
    #   methods: 'kmeans', 'dbscan'
    #       if 'dbscan', params:
    #           eps
    #           min_samples


    print 'Clustering %i points: ' % posts.shape[0]

    if method.lower() == 'kmeans':
        from sklearn.cluster import KMeans
        print 'clustering lat,long by kmeans'

        # Classify into n_clusters:
        n_clust = int(np.sqrt(posts[['lat', 'long']].shape[0]/2))

        km = KMeans(n_clust, init='k-means++') # initialize
        km.fit(posts[['lat', 'long']])
        cluster_labels = km.predict(posts[['lat', 'long']]) # classify

    elif method.lower() == 'dbscan':
        print 'clustering lat,long by dbscan'

        # if posts.shape[0]

        from sklearn.cluster import DBSCAN
        from sklearn import metrics
        from sklearn.datasets.samples_generator import make_blobs
        from sklearn.preprocessing import StandardScaler

        standardized = StandardScaler().fit_transform(posts[['lat', 'long']].values)

        # eps = 0.2
        db = DBSCAN(eps=eps, min_samples=min_samples).fit(standardized)
        # db = DBSCAN(eps=eps, min_samples=min_samples).fit(standardized)
        core_samples_mask = np.zeros_like(db.labels_, dtype=bool)
        core_samples_mask[db.core_sample_indices_] = True
        cluster_labels = db.labels_

        # Number of clusters in labels, ignoring noise if present.
        n_clust = len(set(cluster_labels)) - (1 if -1 in cluster_labels else 0)

        print('Estimated number of clusters: %d' % n_clust)
        print("Silhouette Coefficient: %0.3f" % metrics.silhouette_score(posts[['lat', 'long']].values, cluster_labels))

        for clust in list(set(cluster_labels[cluster_labels>=0])):
            # dat = posts
            geo_mean = posts.loc[cluster_labels == clust, ['lat', 'long']].mean()
            geo_std = posts.loc[cluster_labels == clust, ['lat', 'long']].std()

            lat_range = vincenty((geo_mean['lat'] - 2*geo_std['lat'], geo_mean['long']),
                                 (geo_mean['lat'] + 2*geo_std['lat'], geo_mean['long'])).miles
            long_range = vincenty((geo_mean['lat'], geo_mean['long'] - 2*geo_std['long']),
                                 (geo_mean['lat'], geo_mean['long'] + 2*geo_std['long'])).miles

            if (lat_range * long_range) > max_cluster_size:
                print 'cluster %i is %.3f, removing' % (clust, lat_range * long_range)
                cluster_labels[cluster_labels == clust] = -1 # remove cluster

    return cluster_labels


def make_map(map_center, posts, cluster_labels):
    '''cols_hex = make_map(map_center, posts, cluster_labels)

    :param map_center:
    :param posts:
    :param cluster_labels:
    :return:
        cols_hex: list of hex colors;
            NB last one is not used (but is neccessary) so this list is n_clus+1
    '''

    import colorsys
    from colors import rgb
    import os
    import folium
    import seaborn as sns

    # cols = sns.color_palette("hls", n_colors=max(cluster_labels)+1) # last one not used (kludgily reserved to work with -1 labels)
    # marker_col = ['#%s' % str(rgb(cols[ic][0]*255, cols[ic][1]*255, cols[ic][2]*255).hex) for ic in cluster_labels]
    # cols_hex = ['#%s' % str(rgb(col[0]*255, col[1]*255, col[2]*255).hex) for col in cols]

    # From color brewer
    cols_hex = '#a6cee3,#1f78b4,#b2df8a,#33a02c,#fb9a99,#e31a1c,#fdbf6f,#ff7f00,#cab2d6,#6a3d9a,#ffff99,#b15928,#8dd3c7,#ffffb3,#bebada,#fb8072,#80b1d3,#fdb462,#b3de69,#fccde5,#d9d9d9,#bc80bd,#ccebc5,#ffed6f'.split(',') * 24
    marker_col = [cols_hex[ic] for ic in cluster_labels]

    # Check if map file already exists
    if os.path.exists('%s/map.html' % (config.paths['templates'])):
        # print 'removing file'
        os.remove('%s/map.html' % (config.paths['templates']))

    map = folium.Map(location=map_center, zoom_start=12, width='100%', height=500, tiles='Stamen Toner')

    # markers
    for ind, row in enumerate(posts.iterrows()):
        img = '<a><img src='+row[1]['image_url']+' height="150px" width="200px"></a>'
        if cluster_labels[ind] == -1:
            map.circle_marker([row[1]['lat'], row[1]['long']],
                          radius=1,
                          line_color='#000000',
                          fill_color='#000000',
                          popup=img)
        else:
            map.circle_marker([row[1]['lat'], row[1]['long']],
                          radius=1,
                          line_color=marker_col[ind],
                          fill_color=marker_col[ind],
                          popup=str(cluster_labels[ind])) # str(cluster_labels[ind])


    map.create_map(path='%s/map.html' % (config.paths['templates']))

    return cols_hex


def text_from_clusters(posts, cluster_labels, threshold=0.7, top_n=10):
    ''' extract high tfidf tokens and artist names from each cluster

    unusual_tokens, cluster_tokens_cleaned = text_from_clusters(posts, cluster_labels, threshold=0.7, top_n=10)

    :param posts: DataFrame with 'text' column
    :param cluster_labels: array of cluster_labels of len=post.shape[0]
    :param threshold=0.7: tfidf threshold above which to return "unusual" tokens
    :param top_n: [deprecated] top # tokens to return
    :return: unusual_tokens, cluster_tokens_cleaned
    '''

    # Get text from each cluster
    from nltk.tokenize import word_tokenize
    from gensim import corpora, matutils
    import string

    # n_clust = len(set(cluster_labels)) - (1 if -1 in cluster_labels else 0)
    n_clust = max(cluster_labels)+1

    docs = posts['text'].values
    tokened_docs = [word_tokenize(doc) if doc is not None else ['#'] for doc in docs]

    cluster_tokens = [[]] *  n_clust # only includes clusters that are labeled (not "noise")
    for ind, doc in enumerate(tokened_docs):
        if cluster_labels[ind] == -1:
            pass # ignore points not considered to be in a cluster
        else:
            cluster_tokens[cluster_labels[ind]] = cluster_tokens[cluster_labels[ind]] + doc

    # remove funny characters and spaces
    bad_words = [' ', 'san', 'in', 'the']
    chars = string.punctuation + ' '
    temp_cleaned = [[''.join(ch for ch in word.lower() if ch not in chars) for word in doc] for doc in cluster_tokens]
    temp_cleaned = [[word for word in doc if len(word) > 1] for doc in temp_cleaned]
    cluster_tokens_cleaned = [[word for word in doc if word not in bad_words] for doc in temp_cleaned]

    dictionary = corpora.dictionary.Dictionary(cluster_tokens_cleaned) # indexing: dictionary.token2id['streetart']
    bow_corp = [dictionary.doc2bow(doc) for doc in cluster_tokens_cleaned]
    token_freq = matutils.corpus2dense(bow_corp, len(dictionary.token2id.keys()))

    # normalize words by occurrence
    from sklearn.feature_extraction.text import TfidfTransformer
    transformer = TfidfTransformer()

    tfidf = transformer.fit_transform(token_freq)
    norm_token_freq = tfidf.toarray()

    words = dictionary.token2id.keys()

    # Pick out unusual words
    unusual_tokens = [[]] * n_clust #[[x] for x in range(0,n_clust)] #* n_clust
    for word in words:
        for ind_cluster, p in enumerate(norm_token_freq[dictionary.token2id[word],:]):
            if p > threshold:
                if np.sum(token_freq[dictionary.token2id[word]]) > 1: # check appear more than once in entire corpus
                    unusual_tokens[ind_cluster] = unusual_tokens[ind_cluster] + [(str(word), token_freq[dictionary.token2id[word], ind_cluster])]

    # top_n_words = [[]] * n_clust
    # for ind, cluster in enumerate(unusual_tokens):
    #     temp = sorted(cluster[1:],key=lambda x: x[1], reverse=True)
    #     if len(temp) > top_n:
    #         top_n_words[ind] = [cluster[0]] + temp[:top_n-1]
    #     else:
    #         top_n_words[ind] = [cluster[0]] + temp

    return unusual_tokens, cluster_tokens_cleaned


def find_artists(cluster_tokens, city='San Francisco'):
    # artists_found = find_artists(cluster_tokens, city='San Francisco')

    # Get list of artists
    world = pd.read_csv('%s/%s' % (config.paths['data'], config.filenames['artists_world']))

    # GET SF ARTISTS:
    grouped = world.groupby('city')
    names = [str.lower(name) for name, stuff in grouped.get_group(city).groupby('name')]

    if city == 'San Francisco':
        sf = pd.read_csv('%s/%s' % (config.paths['data'], config.filenames['artists_SF']))
        names_sf = [str.lower(name) for name in sf['name'].values]
        names = list(set(names_sf + names))

    bad_chars = '. '
    clean_names = [''.join(ch for ch in name if ch not in bad_chars) for name in names]

    artists_found = [list(set(cluster) & set(clean_names)) for cluster in cluster_tokens]

    # count number of times each artist was mentioned
    artist_count = [[]] * len(artists_found) #[[x] for x in range(0, len(artists_found))] # [[]] * len(cluster_tokens)
    for ind, artists_in_cluster in enumerate(artists_found):
        for artist in artists_in_cluster:
            artist_count[ind] = artist_count[ind] + [(artist, cluster_tokens[ind].count(artist))]

    return artist_count

def cluster_geo_box(posts, cluster_labels):
    # Get bounding boxes for each cluster
    n_clust = len(set(cluster_labels)) - (1 if -1 in cluster_labels else 0)
    cluster_geo = [[]] * n_clust
    for ind, cluster in enumerate(range(0, n_clust)):
        cluster_geo[ind] = (min(posts[cluster_labels == cluster]['lat']),
                          max(posts[cluster_labels == cluster]['lat']),
                          min(posts[cluster_labels == cluster]['long']),
                          max(posts[cluster_labels == cluster]['long']))

    return cluster_geo


def make_word_cloud(text, save_path):
    # text expected to a string or a list of [(word, count), ...]
    from wordcloud import WordCloud
    import os

    if type(text) == str:
        big_string = text
    else:
        big_string = ''
        for word in text:
            big_string = big_string + ''.join((word[0]+' ') * word[1])

    # print 'trying to make cloud: %s' % save_path
    # print os.getcwd()
    wc = WordCloud(background_color="white",
                   max_words=10000,
                   font_path='app/static/fonts/NanumScript.ttc').generate(big_string)
    wc.generate(big_string)
    wc.to_file('app/%s' % save_path)
    # print 'saving wordcloud to %s' % save_path

def rank_clusters(posts):
    # rank clusters: currently only by # likes

    # rank by # likes/post (vs others)
    temp = posts.groupby('cluster_id')['likes'].sum() / posts.groupby('cluster_id')['likes'].count()
    likes_per_post = []
    for row in temp.iteritems():
        if row[0] >= 0:
            likes_per_post.append(row)

    ranked_clusters = sorted(likes_per_post, key=lambda tup: tup[1], reverse=True)

    return ranked_clusters

def top_photos(posts, n_photos=9):

    photos = []
    for name, group in posts.groupby('cluster_id')[['image_url', 'likes']]: # name is column grouped by, group is small df
        if name >= 0:
            urls_df = group.sort('likes', ascending=False)[['image_url']].head(n_photos)
            photos.append([row[1]['image_url'] for row in urls_df.iterrows()])

    return photos



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

import pandas as pd
import numpy as np
import config


def cluster_geo(posts, method='dbscan', eps=0.15, min_samples=5):
    # cluster_labels = cluster_geo(posts, method='dbscan', eps=0.002, min_samples=5)
    #
    #   posts: dataframe, needs columns ['lat', 'long']
    #   methods: 'kmeans', 'dbscan'
    #       if 'dbscan', params:
    #           eps
    #           min_samples

    from sklearn.cluster import KMeans
    from sklearn.cluster import DBSCAN
    from sklearn import metrics

    if method.lower() == 'kmeans':
        print 'clustering lat,long by kmeans'

        # Classify into n_clusters:
        n_clust = int(np.sqrt(posts[['lat', 'long']].shape[0]/2))

        km = KMeans(n_clust, init='k-means++') # initialize
        km.fit(posts[['lat', 'long']])
        cluster_labels = km.predict(posts[['lat', 'long']]) # classify

    elif method.lower() == 'dbscan':
        print 'clustering lat,long by dbscan'
        from sklearn.datasets.samples_generator import make_blobs
        from sklearn.preprocessing import StandardScaler

        standardized = StandardScaler().fit_transform(posts[['lat', 'long']].values)

        db = DBSCAN(eps=eps, min_samples=min_samples).fit(standardized)
        core_samples_mask = np.zeros_like(db.labels_, dtype=bool)
        core_samples_mask[db.core_sample_indices_] = True
        cluster_labels = db.labels_

        # Number of clusters in labels, ignoring noise if present.
        n_clust = len(set(cluster_labels)) - (1 if -1 in cluster_labels else 0)

        print('Estimated number of clusters: %d' % n_clust)
        print("Silhouette Coefficient: %0.3f" % metrics.silhouette_score(posts[['lat', 'long']].values, cluster_labels))

    return cluster_labels


def make_map(map_center, posts, cluster_labels):
    import colorsys
    from colors import rgb
    import os
    import folium
    import seaborn as sns

    cols = sns.color_palette("hls", n_colors=len(np.unique(cluster_labels)))
    marker_col = ['#%s' % str(rgb(cols[ic][0]*255, cols[ic][1]*255, cols[ic][2]*255).hex) for ic in cluster_labels]

    # Check if map file already exists
    if os.path.exists('%s/map.html' % (config.paths['templates'])):
        # print 'removing file'
        os.remove('%s/map.html' % (config.paths['templates']))

    # TODO: make global lat long,query google api

    map = folium.Map(location=map_center, zoom_start=13, tiles='Stamen Toner')
    # map.create_map(path='%s/map.html' % (config.paths['templates']))

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
                          popup=str(cluster_labels[ind]))


    map.create_map(path='%s/map.html' % (config.paths['templates']))


def text_from_clusters(posts, cluster_labels, top_n=10):
    # top_n_words = text_from_clusters(posts, cluster_labels, top_n=10)

    # Get text from each cluster
    from nltk.tokenize import word_tokenize
    from gensim import corpora, matutils
    import string

    n_clust = len(set(cluster_labels)) - (1 if -1 in cluster_labels else 0)

    docs = posts['text'].values
    tokened_docs = [word_tokenize(doc) if doc is not None else ['#'] for doc in docs]

    cluster_tokens = [[]] * n_clust # only includes clusters that are labeled (not "noise")
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
    threshold = 0.7

    # FIXME: really horribly add cluster number into first element of list for web interface...
    unusual_tokens = [[x] for x in range(0,n_clust)] #* n_clust
    for word in words:
        for ind_cluster, p in enumerate(norm_token_freq[dictionary.token2id[word],:]):
            if p > threshold:
                if np.sum(token_freq[dictionary.token2id[word]]) > 1: # check appear more than once in entire corpus
                    unusual_tokens[ind_cluster] = unusual_tokens[ind_cluster] + [(str(word), token_freq[dictionary.token2id[word], ind_cluster])]

    top_n_words = [[]] * n_clust
    for ind, cluster in enumerate(unusual_tokens):
        temp = sorted(cluster[1:],key=lambda x: x[1], reverse=True)
        if len(temp) > top_n:
            top_n_words[ind] = [cluster[0]] + temp[:top_n-1]
        else:
            top_n_words[ind] = [cluster[0]] + temp

    return top_n_words, cluster_tokens_cleaned


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
    artist_count = [[x] for x in range(0, len(artists_found))] # [[]] * len(cluster_tokens)
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

#TODO: remove text_recent??
# def text_recent(posts, cluster_geo, recent_start_date=pd.datetime(2014,12,1), top_n=10):
#     # top_n_words = text_recent(posts, cluster_geo, recent_start_date=pd.datetime(2014,12,1), top_n=10)
#
#     from nltk.tokenize import word_tokenize
#     from gensim import corpora, matutils
#     import string
#     from sklearn.feature_extraction.text import TfidfTransformer
#
#     print 'recent_start_date = %s' % recent_start_date
#
#     top_n_words = [[]] * len(cluster_geo)
#     for ind, cluster in enumerate(cluster_geo):
#         # # Get the "recent" docs from this cluster
#         docs_recent_raw = posts[(posts['date'] >= recent_start_date)
#                      & (posts['lat'] >= cluster[0])
#                      & (posts['lat'] <= cluster[1])
#                      & (posts['long'] >= cluster[2])
#                      & (posts['long'] <= cluster[3])]['text'].values
#
#         # remove nans
#         docs_recent = []
#         for doc in docs_recent_raw:
#             if type(doc) == str:
#                 docs_recent = docs_recent + [doc]
#         # tokenize, flatten into one
#         tokened_recent = [word_tokenize(doc) for doc in docs_recent]
#         flat_recent = []
#         for doc in tokened_recent:
#             flat_recent = flat_recent + doc
#
#
#         # # Get the "old" docs (each text post)
#         docs_old_raw = posts[(posts['date'] < recent_start_date) # important = all of history in the dataset here, before "this week"
#                      & (posts['lat'] >= cluster[0])
#                      & (posts['lat'] <= cluster[1])
#                      & (posts['long'] >= cluster[2])
#                      & (posts['long'] <= cluster[3])]['text'].values
#         # remove nans
#         docs_old = []
#         for doc in docs_old_raw:
#             if type(doc) == str:
#                 docs_old = docs_old + [doc]
#
#         # tokenize, flatten into one
#         tokened_old = [word_tokenize(doc) for doc in docs_old]
#         flat_old = []
#         for doc in tokened_old:
#             flat_old = flat_old + doc
#
#         # Combine and clean
#         docs = [flat_old, flat_recent]
#
#         chars = string.punctuation + ' '
#         temp_cleaned = [[''.join(ch for ch in word.lower() if ch not in chars) for word in doc] for doc in docs]
#         docs_cleaned = [[word for word in doc if word != ''] for doc in temp_cleaned]
#
#         dictionary = corpora.dictionary.Dictionary(docs_cleaned) # indexing: dictionary.token2id['streetart']
#         bow_corp = [dictionary.doc2bow(doc) for doc in docs_cleaned]
#         token_freq = matutils.corpus2dense(bow_corp, len(dictionary.token2id.keys()))
#
#         # normalize words by occurrence
#         transformer = TfidfTransformer()
#
#         tfidf = transformer.fit_transform(token_freq)
#         norm_token_freq = tfidf.toarray()
#
#         words = dictionary.token2id.keys()
#
#         # Pick out unusual words
#         threshold = 0.9
#         unusual_tokens = []
#         for word in words:
#             if norm_token_freq[dictionary.token2id[word],1] > threshold:
#                 if np.sum(token_freq[dictionary.token2id[word]]) > 1:
#                     unusual_tokens = unusual_tokens + [(str(word), token_freq[dictionary.token2id[word], 1])]
#
#         # get top 10
#         temp = sorted(unusual_tokens,key=lambda x: x[1], reverse=True)
#         if len(temp) >= top_n:
#             top_n_words[ind] = temp[:top_n]
#         else:
#             top_n_words[ind] = temp
#
#     return top_n_words



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


import config
import pandas as pd
import sqlalchemy
import os
from get_instagram import get_instagram
from datetime import datetime, timedelta


# Set up database connection
engine = sqlalchemy.create_engine('mysql://root@localhost') # connect to server
engine.execute('use beautifulcity') # select new db

# Get data
filename = get_instagram()
# filename = 'instagram_data_2015-06-21T15_23_56.060189.tsv'

# Load & format data
recent_posts = pd.read_csv(filename, sep='\t')
recent_posts['date'] = pd.to_datetime(recent_posts.created_time, unit='s')
recent_posts['date_year'] = recent_posts['date'].apply(lambda x: str(x)[:4])
recent_posts['date_month'] = recent_posts['date'].apply(lambda x: str(x)[:7])
recent_posts['date_week'] = recent_posts['date'].apply(lambda x: x.isocalendar()[1])

# Append data
recent_posts.to_sql('instagram', engine,
                 schema='beautifulcity',
                 if_exists='append',
                 chunksize=1000,
                 index=False)

# Remove old data
keep_date = (datetime.now() - timedelta(weeks=2)).strftime("%Y-%m-%d")
query = '''
	delete
	from instagram
	where date(`date`) < '%s'
	''' % keep_date
engine.execute(query)

# Delete all word clouds and maps
# TODO: store cities that were queried and re-generate?
for item in os.listdir(config.paths['cache']):
	if not (item.startswith('.') | item.startswith('..')):
		os.remove('%s/%s' % (config.paths['cache'], item))

#!/usr/bin/env python

# reload CSV -> DATABASE, re-create indexes

import config
import pandas as pd
import sqlalchemy

engine = sqlalchemy.create_engine('mysql://root@localhost') # connect to server
engine.execute('use tagus') # select new db

# Define schema so as to not have pandas guess at types
engine.execute('''
drop table if exists instagram;
create table instagram (
    # Data schema
    created_time bigint,
    id varchar(255),
    image_url varchar(255),
    lat double,
    likes int,
    `long` double,
    post_url varchar(255),
    text varchar(5000),
    user_id bigint,
    `date` datetime,
    date_year varchar(255),
    date_month varchar(255),
    date_day varchar(255),
    date_week varchar(255)
);
''')

# Load Instagram data
posts_all = pd.read_csv('%s/%s' % (config.data_path, config.instagram['file_name_world']), sep='\t')
posts_all['date'] = pd.to_datetime(posts_all.created_time, unit='s')

# Kludge more date info:
posts_all['date_year'] = posts_all['date'].apply(lambda x: str(x)[:4])
posts_all['date_month'] = posts_all['date'].apply(lambda x: str(x)[:7])
posts_all['date_week'] = posts_all['date'].apply(lambda x: x.isocalendar()[1])
posts_all['date_day'] = posts_all['date'].apply(lambda x: str(x)[:10])

# Put into table
posts_all.to_sql('instagram', engine,
                 schema='tagus',
                 if_exists='append',
                 chunksize=1000,
                 index=False)

# Create indices
engine.execute('create index idx_lat_lng on instagram (lat, `long`);')
engine.execute('create index idx_likes on instagram (likes)')
engine.execute('create index idx_date on instagram (`date`)')
engine.execute('create index idx_date_year on instagram (date_year)')
engine.execute('create index idx_date_month on instagram (date_month)')
engine.execute('create index idx_date_day on instagram (date_day)')
engine.execute('create index idx_date_week on instagram (date_week)')

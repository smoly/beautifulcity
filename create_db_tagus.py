#!/usr/bin/env python

import config
import pandas as pd
import sqlalchemy
from pandas.io import sql

engine = sqlalchemy.create_engine('mysql://root@localhost') # connect to server

# Select database, re-recreate table
engine.execute('use tagus') # select new db
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
posts_all['date_day'] = posts_all['date'].apply(lambda x: str(x)[:10])
posts_all['date_week'] = posts_all['date'].apply(lambda x: x.isocalendar()[1])

# Put into table
posts_all.to_sql('instagram', engine,
                 schema='tagus',
                 if_exists='append',
                 chunksize=1000,
                 index=False)

# Create indices
# create index idx_species_pk on sightings(species_pk);
# create index idx_locations_pk on sightings(locations_pk); # 37 minutes
# create index idx_observation_date on sightings(observation_date); # 14 minutes
# create index idx_observers_pk on sightings(observers_pk); # TODO: build!!
# create index idx_sei on sightings(sampling_event_identifier); # 30 minutes



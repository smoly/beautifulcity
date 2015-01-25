import pandas as pd
import sqlalchemy

def load_instagram():

    engine = sqlalchemy.create_engine('mysql://root@localhost') # connect to server
    instagram = pd.read_sql_table('instagram', engine,
                                  schema='tagus',
                                  index_col=None,
                                  coerce_float=False,
                                  parse_dates=['date'],
                                  columns=['lat', 'long', 'likes', 'text', 'image_url', 'date', 'date_year', 'date_month', 'date_day', 'date_week'],
                                  chunksize=None)

    return instagram

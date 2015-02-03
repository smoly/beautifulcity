#!/usr/bin/env python

from app import app # app variables hold Flask instance
# app.config.from_pyfile('aws.cfg')
app.run(host='0.0.0.0', debug = True)
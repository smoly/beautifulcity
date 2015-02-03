#!/usr/bin/env python

# Init standard python logging:
# - With debug=True, flask prints our exceptions and returns them in the html
# - With debug=False, flask doesn't print our exceptions
# - Init logging so that flask prints our exceptions when debug=False
#   - Because with debug=True, ubuntu flask tries and fails to import _winreg
import logging
logging.basicConfig(level=logging.DEBUG)

from app import app # app variables hold Flask instance
# app.config.from_pyfile('aws.cfg')
#app.run(host='0.0.0.0', debug = True) # debug=True barfs ubuntu flask
app.run(host='0.0.0.0')
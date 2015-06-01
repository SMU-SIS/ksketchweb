

# suggestion: generate your own random key using os.urandom(64)
# WARNING: Make sure you run os.urandom(64) OFFLINE and copy/paste the output to
# this file.  If you use os.urandom() to *dynamically* generate your key at
# runtime then any existing sessions will become junk every time you start,
# deploy, or update your app!
import os
def webapp_add_wsgi_middleware(app):
  from google.appengine.ext.appstats import recording
  app = recording.appstats_wsgi_middleware(app)
  return app

class _ConfigDefaults(object):
  ksketch_SENDGRID_username = 'ksketch'
  ksketch_SENDGRID_password = 'ksketchSIS2014'
  ksketch_EMAIL = 'ksketch@smu.edu.sg'
  ksketch_HOSTNAME = 'ksketch.smu.edu.sg'
  ksketch_FULL_HOSTNAME ='http://ksketch.smu.edu.sg'
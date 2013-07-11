import logging
from backend import Sketch
from backend import Permissions
from google.appengine.ext import deferred
from google.appengine.ext import db

BATCH_SIZE = 300  # ideal batch size may vary based on entity size.
# For batch updates - change as necessary.
def UpdateSchema(cursor=None, num_updated=0):
    # query = Sketch.all()
    # p_query = Permissions.all()
    # if cursor:
        # p_query.with_cursor(cursor)

    # to_put = []
    # for p in query.run():
        # In this example, the default values of 0 for num_votes and avg_rating
        # are acceptable, so we don't need this loop.  If we wanted to manually
        # manipulate property values, it might go something like this:
        # index = p.key().id()
        
        # new_entity = Permissions(sketch_id = index,
                                 # view = "Public",
                                 # edit = "Public",
                                 # comment = "Public")
        # new_entity.put()
        #to_put.append(new_entity)
    
    # if to_put:
        # db.put(to_put)
        # num_updated += len(to_put)
        # logging.debug(
            # 'Put %d entities to Datastore for a total of %d',
            # len(to_put), num_updated)
        # deferred.defer(
            # UpdateSchema, cursor=p_query.cursor(), num_updated=num_updated)
    # else:
        # logging.debug(
            # 'UpdateSchema complete with %d updates!', num_updated)
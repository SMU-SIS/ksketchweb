import logging
from google.appengine.ext import deferred
from google.appengine.ext import db

#Import necessary libraries as needed
#from backend import User

BATCH_SIZE = 300  # ideal batch size may vary based on entity size.
# For batch updates - change as necessary.
def UpdateSchema(cursor=None, num_updated=0):


    #u_query = User.all()

    #u_obj = u_query.run()
    
    #for u in u_obj:
    #  u.change_count = 0
    #  u.put()
        

    
    # if to_put:
        # db.put(to_put)
        # num_updated += len(to_put)
        # logging.debug(
            # # 'Put %d entities to Datastore for a total of %d',
            # len(to_put), num_updated)
        # deferred.defer(
            # UpdateSchema, cursor=p_query.cursor(), num_updated=num_updated)
    # else:
        # logging.debug(
            # 'UpdateSchema complete with %d updates!', num_updated)
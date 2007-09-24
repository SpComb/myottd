from pylons import Response, c, g, cache, request, session
from pylons.controllers import WSGIController
from pylons.decorators import jsonify, validate, decorator
from pylons.templating import render, render_response
from pylons.helpers import abort, redirect_to, etag_cache
from pylons.i18n import N_, _, ungettext
import web.models as model
import web.lib.helpers as h
from web.lib import rpc, settings
import sqlalchemy.exceptions

class BaseController(WSGIController):
    def __before__ (self) :
        if 'user_id' in session :
            c.user = model.User.get_by(id=session['user_id'])
        else :
            c.user = False

        print "sub_domain:", c.sub_domain

    def __call__(self, environ, start_response):
        # Insert any code to be run per request here. The Routes match
        # is under environ['pylons.routes_dict'] should you want to check
        # the action or route vars here
        return WSGIController.__call__(self, environ, start_response)

@decorator
def form_handler (func, *args, **kwargs) :
    try :
        # fsking routes and its magical function arguments crap
        
        return func(*args, **kwargs)
    except sqlalchemy.exceptions.SQLError, e :
        error = "Database: %s" % e.orig.pgerror
    except rpc.RpcError, e :
        error = "Internal MyOTTD Daemon error: %s" % e
    except ValueError, e :
        error = "Invalid value: %s" % e
    
    c.error = error
    return render_response('error.myt')

@decorator
def require_login (func, *args, **kwargs) :
    if c.user :
        return func(*args, **kwargs)
    else :
        h.redirect_to('login', sub_domain=c.sub_domain)

@decorator
def validate_id (func, id, *args, **kwargs) :
    print "sub_domain:", c.sub_domain

    if c.user :
        if model.Server.get_by(id=id).owner == c.user.id :
            return func(id, *args, **kwargs)
        else :
            return Response("Not your server")
    else :
        h.redirect_to('login', sub_domain=c.sub_domain)

# Include the '_' function in the public names
__all__ = [__name for __name in locals().keys() if not __name.startswith('_') \
           or __name == '_']
